import click

from queue import Queue
import threading
import time, re
import logging

from settings import (
            T_WASTE_COLLECTOR, T_WASHER1, T_WASHER2, T_DRYER,
            MAX_SAMPLE_COUNT_AFTER_SHIMMING, REGULAR_SHIM_XML,
            ROBOT_ARM_LOG_PATH
            )
from shared_state import SharedState
# if __name__ != "__main__":
from robotic_arm import RobotArm
from pipetter import PipetterControl
from spectrometer import SpectrometerRemoteControl

from tests.dummy_robotarm import DummyRobotArmControl
from tests.dummy_pipetter import DummyPipetterControl
from tests.dummy_spectrometer import DummySpectrometerRemoteControl



def setup_logger(name = 'Scheduler'):
    # better logging format in console
    class CustomFormatter(logging.Formatter):
        grey, yellow, red, bold_red, reset = [
            "\x1b[38;20m",
            "\x1b[33;20m",
            "\x1b[31;20m",
            "\x1b[31;1m",
            "\x1b[0m",
        ]
        format = (
            "%(asctime)s-%(name)s-%(levelname)s-%(message)s (%(filename)s:%(lineno)d)"
        )
        FORMATS = {
            logging.DEBUG: grey + format + reset,
            logging.INFO: yellow + format + reset,
            logging.WARNING: yellow + format + reset,
            logging.ERROR: red + format + reset,
            logging.CRITICAL: bold_red + format + reset,
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    # create logger with 'main'
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(ROBOT_ARM_LOG_PATH + "nmr_station.log")
    fh.setLevel(logging.INFO)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter("%(asctime)s-%(name)s-%(levelname)s-%(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(CustomFormatter())
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

logger = setup_logger()

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
    # def __init__(self, robot_arm_control: RobotArm):
    def __init__(self, robot_arm_control):
        self.robot_arm = robot_arm_control
        self.target_tube_id = -1
        self.asked_return_tube = False

        self.sample_count_after_shimming = MAX_SAMPLE_COUNT_AFTER_SHIMMING
        self.logger = setup_logger(name = 'RobotArmDecision')

        self.init_timestamp = time.time()
        print(f"RobotArmDecision initiated")
    
    def cur_time(self) -> float:
        return round(time.time() - self.init_timestamp, 2)

    def run(self, shared_state: SharedState):
        tube_state = shared_state.tube 
        producer_mq = shared_state.producer_message_queue
        consumer_mq = shared_state.consumer_message_queue

        
        while True:
            time.sleep(0.5)

            print("\033[94m === Robot Arm === \033[0m")
            tube_state.print_status()
            print(self.robot_arm.get_cart_pos())
            print(f"\x1b[38;5;190m Producer Channel: {producer_mq.q.queue} \033[0m")
            print(f"\x1b[38;5;214m Consumer Channel: {consumer_mq.q.queue}\033[0m")
            print()
            
            # get message from the consumer_mq
            spectrometer_msg = ""
            if not consumer_mq.no_message():
                spectrometer_msg = consumer_mq.get_front_message()
            

            """
            Regular Shimming
            """
            if self.sample_count_after_shimming >= MAX_SAMPLE_COUNT_AFTER_SHIMMING:
                if spectrometer_msg == "":
                    self.robot_arm.pick_tube(self.robot_arm.facilities["reference_slot"])
                    self.robot_arm.place_tube_to_spinsolve()
                    consumer_mq.add_new_message("ShimReference")

                    continue
                          
                elif spectrometer_msg == "RemoveReference":
                    self.robot_arm.pick_tube_from_spinsolve()
                    self.robot_arm.place_tube(self.robot_arm.facilities["reference_slot"])

                    consumer_mq.finish_front_message()

                    self.sample_count_after_shimming = 0
                else:
                    continue
                

            """
            Priority 1: Take analyzed tube from spinsolve to waste collector
            """
            
            if spectrometer_msg == "DitchSample":
                self.robot_arm.pick_tube_from_spinsolve()
                consumer_mq.finish_front_message()

                target_tube_id = tube_state.find("spectrometer")
                tube_state.transferring_tube(target_tube_id)
                self.robot_arm.flip_tube(location='flip_stand_waste',
                                            is_pick=False)
                tube_state.in_waste_collector(target_tube_id)
                tube_state.set_time_finished(target_tube_id, self.cur_time() + T_WASTE_COLLECTOR)

                self.sample_count_after_shimming += 1

            """
            Priority 2: Take the tube of next unanalyzed sample from tube rack to spinsolve for analysis
            """
            pipetter_msg = ""
            if not producer_mq.no_message():
                pipetter_msg = producer_mq.get_front_message()

            # only run this block when no tube is in the spectrometer
            if tube_state.find("analyzing") == -1 and tube_state.find("spectrometer") == -1:
                if pipetter_msg == "":
                    producer_mq.add_new_message("NextSample?")
                elif pipetter_msg.startswith("TubeId="):
                    new_target = re.search(r'TubeId=(\d+)', pipetter_msg)
                    producer_mq.add_new_message("PauseRefill")
                    producer_mq.finish_front_message()
                elif pipetter_msg == "PauseRefillOkay":
                    target_tube_id = tube_state.find_next_filled_tube()
                    self.robot_arm.pick_tube(self.robot_arm.facilities[f"tube{target_tube_id + 1}"])
                    producer_mq.finish_front_message()

                    tube_state.transferring_tube(target_tube_id)
                    self.robot_arm.place_tube_to_spinsolve()
                    producer_mq.add_new_message("ResumeRefill")
                    tube_state.in_spectrometer(target_tube_id)
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
            for state in ["dryer", "washer2", "washer1", "waste_collector"]:
                tube_id = tube_state.find(state)
                print(f"=> current state: {state}, tube_id: {tube_id}")

                if tube_id == -1: continue 
                
                cur_time = self.cur_time()
                end_time = tube_state.time_finished[tube_id]

                print(f"==> cur_time: {cur_time}, end_time: {end_time}")

                if cur_time <= end_time: continue

                print(f"===> okay")    


                if state == "dryer":
                    # move the tube back to its tube rack
                    if pipetter_msg != "ReadyToReturnTube":
                        if not self.asked_return_tube:
                            producer_mq.add_new_message("ReturnTube")
                            self.asked_return_tube = True
                        
                    else:
                        producer_mq.finish_front_message()
                        self.robot_arm.pick_tube(self.robot_arm.facilities["dryer"])
                        self.robot_arm.flip_tube(location = 'flip_stand_clean')
                        self.robot_arm.place_tube(self.robot_arm.facilities[f"tube{tube_id+1}"])
                        time.sleep(30)# this time is for cooling of tube after drying
                        tube_state.empty_tube(tube_id)

                        # self.robot_arm.go_to_safe("auto")
                        self.robot_arm.retract_to_carousel()
                        producer_mq.add_new_message("ResumeRefill")
                        self.asked_return_tube = False
                
                elif state == "washer2":
                    # move the tube from washer2 to dryer
                    if tube_state.find("dryer") == -1:
                        self.robot_arm.pick_tube(self.robot_arm.facilities['washer2'])
                        self.robot_arm.place_tube(self.robot_arm.facilities["dryer"])
                        tube_state.in_dryer(tube_id)
                        tube_state.set_time_finished(tube_id, cur_time + T_DRYER)

                elif state == "washer1":
                    # move the tube from washer1 to washer2
                    if tube_state.find("washer2") == -1:
                        self.robot_arm.pick_tube(self.robot_arm.facilities['washer1'])
                        self.robot_arm.place_tube(self.robot_arm.facilities["washer2"])
                        tube_state.in_washer2(tube_id)
                        tube_state.set_time_finished(tube_id, cur_time + T_WASHER2)
                
                elif state == "waste_collector":
                    # move the tube from waste_collector to washer1
                    if tube_state.find("washer1") == -1:
                        self.robot_arm.pick_tube(
                            self.robot_arm.facilities['flip_stand_waste_gripper_upright'])
                        self.robot_arm.place_tube(self.robot_arm.facilities["washer1"])
                        tube_state.in_washer1(tube_id)
                        tube_state.set_time_finished(tube_id, cur_time + T_WASHER1)

            """
            Block 4: Terminate this thread if ended
            """
            if pipetter_msg == "Terminate":
                consumer_mq.add_new_message("Terminate")
                break
        
class NMR_SpectrometerDecision:
    # def __init__(self, remote_control: SpectrometerRemoteControl, message: list[str]) -> None:
    def __init__(self, remote_control, spectrum_storage_dir: str, message: list[str]) -> None:
        self.remote_control = remote_control
        self.spectrum_storage_dir = spectrum_storage_dir
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

            if message == "Terminate":
                break
            
            if message == "NewSampleReady":
                tube_id = tube_state.find("spectrometer")
                sample_id = tube_state.sample_in_tube[tube_id]
                print(f"Analyzing sample {sample_id} in tube {tube_id}")
                tube_state.analyzing_tube(tube_id)

                """
                # TODO: Update the folder path
                folder_path = self.spectrum_storage_dir + "\\" + str(tube_id)
                """

                for message in self.request_xml_messages:
                    self.remote_control.send_request_to_spinsolve80(message)
                    time.sleep(2) 

                print("finished NMR analysis")
                tube_state.in_spectrometer(tube_id)
                consumer_mq.finish_front_message()
                consumer_mq.add_new_message("DitchSample")
            
            elif message == "ShimReference":
                print("Shimming Reference")

                """
                # TODO: Update the folder path  
                folder_path = self.spectrum_storage_dir + "\\" + "RegularShim"
                """
                self.remote_control.send_request_to_spinsolve80(REGULAR_SHIM_XML)
                consumer_mq.finish_front_message()
                consumer_mq.add_new_message("RemoveReference")


class PipetterDecision:
    # def __init__(self, pipetter_control: PipetterControl, process_order: list[int]) -> None:
    def __init__(self, pipetter_control, process_order: list[int]) -> None:
        self.pipettor = pipetter_control
        self.process_order = process_order
        
        self.standby = False

        self.prev_log_msg = ""

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
                
                # elif next_available_tube == -1 and next_sample_id == -1:
                #     producer_mq.add_new_message("NoSampleLeft")
                
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
                producer_mq.add_new_message("ReadyToReturnTube")
                producer_mq.finish_front_message()

            if tube_state.is_all_empty() and self.process_order == []:
                producer_mq.add_new_message("Terminate")
                break

@click.command()
@click.option('--test', is_flag=True, required=True, help='Use dummy components')
def main(test):
    if not test:
        click.echo("This application can only run in test mode.")
        return
    
    # Test case 1: Success!
    # process_order = [1, 4, 9]

    # Test case 2: Success!
    # process_order = [0, 1, 2, 3, 4, 5, 6, 7, 54, 55, 56]

    # Test case 3: 
    process_order = [i for i in range(22)]

    pipetter_decision = PipetterDecision(DummyPipetterControl(), process_order)

    robot_arm_decision = RobotArmDecision(DummyRobotArmControl())

    xml_request_message = ["""<?xml version="1.0" encoding="utf-8"?>
<Message>
        <Start protocol="1D PROTON">
                <Option name="Scan" value="QuickShim1st2nd" />
        </Start>
</Message>"""]
    spectrometer_decision = NMR_SpectrometerDecision(DummySpectrometerRemoteControl(), "", xml_request_message)

    scheduler = Scheduler(robot_arm_decision, spectrometer_decision, pipetter_decision)
    scheduler.start()


if __name__ == "__main__":
    main()