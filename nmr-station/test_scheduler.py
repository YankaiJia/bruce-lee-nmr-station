from queue import Queue
import threading
import time, re

# from dummy_pipetter import DummyPipetterControl as PipetterControl
from dummy_robotarm import DummyRobotArm as RobotArmControl

from shared_state import SharedState
from robotic_arm import RobotArm
from pipetter import PipetterControl

# from dummy_spectrometer import DummySpectrometerRemoteControl as SpectrometerRemoteControl
from spectrometer import SpectrometerRemoteControl
    

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


class DummyRobotArmDecision:
    def __init__(self):
        self.robot_arm = RobotArm()
        self.target_tube_id = -1
        self.is_return = False
        print(f"RobotArmDecision initiated")
    
    def run(self, shared_state: SharedState):
        tube_state = shared_state.tube 
        message_queue = shared_state.message_queue
        
        while True:
            time.sleep(1)

            print(" === Robot Arm === ")
            tube_state.print_status()
            print(f"Robot Arm's Turn {message_queue.q.queue}")
            print()


            if message_queue.no_message() and self.target_tube_id == -1:
                message_queue.add_new_message("NextSample?")
                continue

            message = message_queue.get_front_message()

            if message == "NoSampleLeft":
                break

            if message.startswith("TubeId="):
                new_target = re.search(r'TubeId=(\d+)', message)

                # no tube assigned right now:
                if self.target_tube_id == -1:
                    self.target_tube_id = int(new_target.group(1))
                    message_queue.add_new_message("PauseRefill")

                message_queue.finish_front_message()

            elif message == "PauseRefillOkay" and self.is_return == False:

                self.robot_arm.pick_tube(self.robot_arm.facilities[f"tube{self.target_tube_id+1}"])
                message_queue.finish_front_message()
                
                tube_state.transferring_tube(self.target_tube_id)
                message_queue.add_new_message("ResumeRefill")

                self.robot_arm.place_tube_to_spinsolve()
                tube_state.in_spectrometer(self.target_tube_id)
                message_queue.add_new_message("NewSampleReady")
                
            elif message == "DitchSample":
                self.robot_arm.pick_tube_from_spinsolve()
                message_queue.finish_front_message()

                tube_state.transferring_tube(self.target_tube_id)
                self.robot_arm.flip_tube(location = 'flip_stand_waste')
                ## first wash
                self.robot_arm.place_tube(self.robot_arm.facilities["washer1"])
                tube_state.washing_tube(self.target_tube_id)
                self.robot_arm.wash_tube()
                self.robot_arm.pick_tube(self.robot_arm.facilities["washer1"])
                ## second wash
                self.robot_arm.place_tube(self.robot_arm.facilities["washer2"])
                tube_state.washing_tube(self.target_tube_id)
                self.robot_arm.wash_tube()
                self.robot_arm.pick_tube(self.robot_arm.facilities["washer2"])

                self.robot_arm.place_tube(self.robot_arm.facilities['dryer'])
                tube_state.drying_tube(self.target_tube_id)
                self.robot_arm.dry_tube()

                self.is_return = True
                message_queue.add_new_message("PauseRefill")

            elif message == "PauseRefillOkay" and self.is_return == True:
                self.robot_arm.pick_tube(self.robot_arm.facilities["dryer"])
                self.robot_arm.flip_tube(location = 'flip_stand_clean')
                self.robot_arm.place_tube(self.robot_arm.facilities[f"tube{self.target_tube_id+1}"])
                message_queue.finish_front_message()
                
                message_queue.add_new_message(f"ReturnTubeId={self.target_tube_id}")
                self.target_tube_id = -1
                self.is_return = False
            


class Dummy_NMR_SpectrometerDecision:
    def __init__(self, message: str) -> None:
        self.remote_control = SpectrometerRemoteControl()
        self.request_xml_messages = message
        print("Spectrometer initiated!")
        print(f"\t with NMR requests {self.request_xml_messages}")

    def run(self, shared_state: SharedState):
        tube_state = shared_state.tube
        message_queue = shared_state.message_queue
        
        while True:
            time.sleep(1)

            print(" === Spectrometer === ")

            if message_queue.no_message(): continue
            print(f"Spectrometer's Turn {message_queue.q.queue}")

            message = message_queue.get_front_message()

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
                message_queue.finish_front_message()
                message_queue.add_new_message("DitchSample")


class DummyPipetterDecision:
    def __init__(self, process_order: list[int]) -> None:
        self.pipettor = PipetterControl()
        self.process_order = process_order
        
        self.standby = False

        print("Pipetter initiated")
        print(f"\t with process order {self.process_order}")
    def run(self, shared_state: SharedState):
        tube_state = shared_state.tube
        message_queue = shared_state.message_queue

        while True:
            time.sleep(1)
            
            print(" === Pipetter === ")
            print(self.process_order)
            tube_state.print_status()

            next_sample_id = (-1 if self.process_order == [] else self.process_order[0])
            next_refill_tube_id = tube_state.find_next_empty_tube()

            print(f"  --> next_sample {next_sample_id}\n  --> next_refill {next_refill_tube_id}\n  --> is_standby? {self.standby}")

            if next_sample_id != -1 and next_refill_tube_id != -1 and not self.standby:
                self.pipettor.aspirate(next_sample_id)
                self.pipettor.refill(next_refill_tube_id)
                tube_state.filled_tube(next_refill_tube_id, next_sample_id)
                self.process_order.pop(0)
            
            

            print(f"Pipetter's Turn: {message_queue.q.queue}")

            if message_queue.no_message(): continue

            message = message_queue.get_front_message()

            if message == "NextSample?":
                next_available_tube = tube_state.find_next_filled_tube()
                if next_available_tube != -1:
                    print(f"Next available tube is at rack id {next_available_tube}")
                    message_queue.add_new_message(f"TubeId={next_available_tube}, SampleId={tube_state.sample_in_tube[next_available_tube]}")
                
                elif next_available_tube == -1 and next_sample_id == -1:
                    message_queue.add_new_message("NoSampleLeft")
                
                message_queue.finish_front_message()
            
            elif message == "PauseRefill":
                self.pipettor.standby()
                self.standby = True
                message_queue.add_new_message("PauseRefillOkay")
                message_queue.finish_front_message()
            
            elif message == "ResumeRefill":
                self.standby = False
                message_queue.finish_front_message()
            
            elif message.startswith("ReturnTubeId="):
                returned_tube_id = int(message[13:])
                tube_state.empty_tube(returned_tube_id)
                self.standby = False
                message_queue.finish_front_message()

            elif message == "NoSampleLeft":
                break


if __name__ == "__main__":
    xml_request_message = """<?xml version="1.0" encoding="utf-8"?>
<Message>
        <Start protocol="1D PROTON">
                <Option name="Scan" value="QuickScan" />
        </Start>
</Message>"""

    process_order = [1, 4, 9, 16, 25, 36, 49]
    # process_order = [11, 22, 33]

    # # testing
    # dummy_robot_arm = DummyRobotArmDecision()
    # dummy_pipetter = DummyPipetterDecision(process_order)
    # dummy_NMR_spectrometer = Dummy_NMR_SpectrometerDecision(xml_request_message)
    # ## scheduler = Scheduler(sample_robot_arm, sample_NMR_spectrometer, sample_pipetter)
    # scheduler = Scheduler(dummy_robot_arm, dummy_NMR_spectrometer, dummy_pipetter)
    # scheduler.start()

    dr = DummyRobotArmDecision()
    # dp = DummyPipetterDecision(process_order)