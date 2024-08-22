import click

from queue import Queue
import threading
import time, re

from shared_state import SharedState
from robotic_arm import RobotArm
from pipetter import PipetterControl
from spectrometer import SpectrometerRemoteControl
from tests.dummy_robotarm import DummyRobotArmControl
from tests.dummy_pipetter import DummyPipetterControl
from tests.dummy_spectrometer import DummySpectrometerRemoteControl

# time spent (sec) in each cleaning units
T_WASTE_COLLECTOR = 2
T_WASHER1 = 30
T_WASHER2 = 30
T_DRYER = 60

class Scheduler:
    # dependency injection here
    def __init__(self, robot_arm, NMR_spectrometer, pipetter) -> None:
        self.shared_state = SharedState()
        self.robot_arm = robot_arm
        self.NMR_spectrometer = NMR_spectrometer
        self.pipetter = pipetter
    
    def start(self):
        threads = [
            threading.Thread(target=self.robot_arm.run, args=(self.shared_state,)),
            threading.Thread(target=self.NMR_spectrometer.run, args=(self.shared_state,)),
            threading.Thread(target=self.pipetter.run, args=(self.shared_state,)),
        ]

        for thread in threads: thread.start()
        
        for thread in threads: thread.join()


class RobotArmDecision:
    def __init__(self, robot_arm_control: RobotArm):
        self.robot_arm = robot_arm_control
        self.target_tube_id = -1
        self.is_return = False
        print(f"RobotArmDecision initiated")
    
    def run(self, shared_state: SharedState):
        tube_state = shared_state.tube 
        producer_mq = shared_state.producer_message_queue
        consumer_mq = shared_state.consumer_message_queue

        
        while True:
            time.sleep(0.5)

            print("\033[94m === Robot Arm === \033[0m")
            tube_state.print_status()
            print(f"\x1b[38;5;190m Producer Channel: {producer_mq.q.queue} \033[0m")
            print(f"\x1b[38;5;214m Consumer Channel: {consumer_mq.q.queue}\033[0m")
            print()
            
            """
            Priority 1: Take analyzed tube from spinsolve to waste collector
            """
            # get message from the consumer_mq
            spectrometer_msg = ""
            if not consumer_mq.no_message():
                spectrometer_msg = consumer_mq.get_front_message()
                if spectrometer_msg == "DitchSample":
                    self.robot_arm.pick_tube_from_spinsolve()
                    consumer_mq.finish_front_message()

                    tube_state.transferring_tube(tube_state.find("spectrometer"))
                    self.robot_arm.flip_tube(location = 'flip_stand_waste')
                    tube_state.in_waste_collector()

            """
            Priority 2: Take the tube of next unanalyzed sample from tube rack to spinsolve for analysis
            """
            pipetter_msg = ""
            if not producer_mq.no_message():
                pipetter_msg = producer_mq.get_front_message()

            # if pipetter_msg == "NoSampleLeft": 
            #     producer_mq.add_new_message("NoSampleLeft")
            #     break

            if pipetter_msg == "":
                producer_mq.add_new_message("NextSample?")
            elif pipetter_msg.startswith("TubeId="):
                new_target = re.search(r'TubeId=(\d+)', pipetter_msg)
                producer_mq.add_new_message("PauseRefill")
            elif pipetter_msg == "PauseRefillOkay":
                target_id = tube_state.find_next_filled_tube()
                self.robot_arm.pick_tube(self.robot_arm.facilities[f"tube{target_id + 1}"])
                producer_mq.finish_front_message()

                tube_state.transferring_tube(target_id)
                self.robot_arm.place_tube_to_spinsolve()
                producer_mq.add_new_message("ResumeRefill")
                tube_state.in_spectrometer(target_id)
                consumer_mq.add_new_message("NewSampleReady")


            """
            Priority 3: Reversely iterate each cleaning-related tube_state: each transit to next state
                i.e 
                    tube at "dryer" transit to "empty"
                    tube at "washer2" transit to "dryer"
                    tube at "washer1" transit to "washer2"
                    tube at "waste_collector" transit to "washer1"
                why reversely iterate?
                    prevent tube moving from washer1 to washer2 and still there is tube at washer2
            """
            for state in ["dryer", "washer2", "washer1", "waste_collecter"]:
                tube_id = tube_state.find(state)
                if tube_id == -1: continue 

                end_time = tube_state.time_finished[tube_id]
                if time.time() < end_time: continue

                if state == "dryer":
                    # move the tube back to its tube rack
                    if pipetter_msg != "ReturnTubeOkay":
                        producer_mq.add_new_message("ReturnTube")
                    else:
                        producer_mq.finish_front_message()
                        self.robot_arm.pick_tube(self.robot_arm.facilities["dryer"])
                        self.robot_arm.flip_tube(location = 'flip_stand_clean')
                        self.robot_arm.place_tube(self.robot_arm.facilities[f"tube{tube_id+1}"])
                        tube_state.empty_tube(tube_id)

                        self.robot_arm.go_to_safe("auto")
                        producer_mq.add_new_message("ResumeRefill")
                
                elif state == "washer2":
                    # move the tube from washer2 to dryer
                    self.robot_arm.place_tube(self.robot_arm.facilities["dryer"])
                    tube_state.in_dryer(tube_id)
                    tube_state.set_time_finished(time.time() + T_DRYER)

                elif state == "washer1":
                    # move the tube from washer1 to washer2
                    self.robot_arm.place_tube(self.robot_arm.facilities["washer2"])
                    tube_state.in_washer2(tube_id)
                    tube_state.set_time_finished(time.time() + T_WASHER2)
                
                elif state == "waste_collector":
                    # move the tube from waste_collector to washer1
                    self.robot_arm.place_tube(self.robot_arm.facilities["washer1"])
                    tube_state.in_washer1(tube_id)
                    tube_state.set_time_finished(time.time() + T_WASHER1)
        
class NMR_SpectrometerDecision:
    def __init__(self, remote_control: SpectrometerRemoteControl, message: list[str]) -> None:
        self.remote_control = remote_control
        self.request_xml_messages = message
        print("Spectrometer initiated!")
        print(f"\t with NMR requests {self.request_xml_messages}")

    def run(self, shared_state: SharedState):
        tube_state = shared_state.tube
        consumer_mq = shared_state.consumer_message_queue
        
        while True:
            time.sleep(1)

            print(" === Spectrometer === ")

            if consumer_mq.no_message(): continue
            print(f"\x1b[38;5;214m Consumer Channel: {consumer_mq.q.queue}\033[0m")

            message = consumer_mq.get_front_message()

            if message == "NoSampleLeft":
                break
            
            if message == "NewSampleReady":
                tube_id = tube_state.find("in_spectrometer")
                sample_id = tube_state.sample_in_tube[tube_id]
                print(f"Analyzing sample {sample_id} in tube {tube_id}")
                tube_state.analyzing_tube(tube_id)

                for message in self.request_xml_messages:
                    self.remote_control.send_request_to_spinsolve80(message)
                    time.sleep(2) 
                print("finished NMR analysis")
                tube_state.in_spectrometer(tube_id)
                consumer_mq.finish_front_message()
                consumer_mq.add_new_message("DitchSample")


class PipetterDecision:
    def __init__(self, pipetter_control: PipetterControl, process_order: list[int]) -> None:
        self.pipettor = pipetter_control
        self.process_order = process_order
        
        self.standby = False

        print("Pipetter initiated")
        print(f"\t with process order {self.process_order}")
    def run(self, shared_state: SharedState):
        tube_state = shared_state.tube
        producer_mq = shared_state.producer_message_queue

        while True:
            time.sleep(1)
            
            print(" === Pipetter === ")
            print(f"\x1b[38;5;190m Producer Channel: {producer_mq.q.queue} \033[0m")
            tube_state.print_status()

            next_sample_id = (-1 if self.process_order == [] else self.process_order[0])
            next_refill_tube_id = tube_state.find_next_empty_tube()

            print(f"  --> next_sample {next_sample_id}\n  --> next_refill {next_refill_tube_id}\n  --> is_standby? {self.standby}")

            if next_sample_id != -1 and next_refill_tube_id != -1 and not self.standby:
                self.pipettor.aspirate(next_sample_id)
                self.pipettor.refill(next_refill_tube_id)
                tube_state.filled_tube(next_refill_tube_id, next_sample_id)
                self.process_order.pop(0)
            

            if producer_mq.no_message(): continue

            message = producer_mq.get_front_message()

            if message == "NextSample?":
                next_available_tube = tube_state.find_next_filled_tube()
                if next_available_tube != -1:
                    print(f"Next available tube is at rack id {next_available_tube}")
                    producer_mq.add_new_message(f"TubeId={next_available_tube}, SampleId={tube_state.sample_in_tube[next_available_tube]}")
                
                elif next_available_tube == -1 and next_sample_id == -1:
                    producer_mq.add_new_message("NoSampleLeft")
                
                producer_mq.finish_front_message()
            
            elif message == "PauseRefill":
                self.pipettor.standby()
                self.standby = True
                producer_mq.add_new_message("PauseRefillOkay")
                producer_mq.finish_front_message()
            
            elif message == "ResumeRefill":
                self.standby = False
                producer_mq.finish_front_message()
            
            elif message == "ReturnTube":
                self.pipettor.standby()
                self.standby = True
                producer_mq.add_new_message("ReturnTubeOkay")
                producer_mq.finish_front_message()

            elif message == "NoSampleLeft":
                break

@click.command()
@click.option('--test', is_flag=True, required=True, help='Use dummy components')
def main(test):
    if not test:
        click.echo("This application can only run in test mode.")
        return

    process_order = [1, 4, 9]
    pipetter_decision = PipetterDecision(DummyPipetterControl(), process_order)

    robot_arm_decision = RobotArmDecision(DummyRobotArmControl())

    xml_request_message = ["""<?xml version="1.0" encoding="utf-8"?>
<Message>
        <Start protocol="1D PROTON">
                <Option name="Scan" value="QuickScan" />
        </Start>
</Message>"""]
    spectrometer_decision = NMR_SpectrometerDecision(DummySpectrometerRemoteControl(), xml_request_message)

    scheduler = Scheduler(robot_arm_decision, spectrometer_decision, pipetter_decision)
    scheduler.start()


if __name__ == "__main__":
    main()