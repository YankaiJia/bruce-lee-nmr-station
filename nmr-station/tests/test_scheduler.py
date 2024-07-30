from queue import Queue
import threading
import time, re

from dummy_pipetter import DummyPipetterControl as PipetterControl
from dummy_pipetter import TubeRack
from dummy_robotarm import DummyRobotArm as RobotArmControl
from dummy_spectrometer import DummySpectrometerRemoteControl as SpectrometerRemoteControl

class SharedState:
    def __init__(self) -> None:
        self.state = {
            'robot_arm': 'idle',
            'NMR_spectrometer': 'idle',
            'pipetter': 'idle'
        }
        self.message_queue = Queue()
        self.lock = threading.Lock()

    def get_state(self) -> dict[str, str] :
        with self.lock:
            return self.state.copy()

    def update_state(self, facility_name: str, latest_state: str):
        with self.lock:
            self.state[facility_name] = latest_state

    def no_message(self) -> bool:
        with self.lock:
            return (self.message_queue.qsize() == 0)

    def get_front_message(self) -> str :
        with self.lock:
            return self.message_queue.get()
    
    def add_new_message(self, message: str):
        with self.lock:
            self.message_queue.put(message)
    
    def finish_front_message(self):
        self.message_queue.task_done()
    

class Scheduler:
    # dependency injection here
    def __init__(self, robot_arm, NMR_spectrometer, pipetter) -> None:
        self.shared_state = SharedState()
        print(self.shared_state)

        self.robot_arm = robot_arm
        self.NMR_spectrometer = NMR_spectrometer
        self.pipetter = pipetter
        self.queue_monitor = QueueMonitor()
    
    def start(self):
        threads = [
            threading.Thread(target=self.robot_arm.run, args=(self.shared_state,)),
            threading.Thread(target=self.NMR_spectrometer.run, args=(self.shared_state,)),
            threading.Thread(target=self.pipetter.run, args=(self.shared_state,)),
            # threading.Thread(target=self.queue_monitor.run, args=(self.shared_state,))
        ]

        for thread in threads: thread.start()
        
        # for thread in threads: thread.join()

class QueueMonitor:
    def __init__(self) -> None:
        pass 
    def run(self, shared_state: SharedState):
        print("QueueMonitor run!", shared_state)

        while True:
            print(f"* Queue Status * {shared_state.message_queue.queue}")
            time.sleep(0.05)


class DummyRobotArmDecision:
    def __init__(self):
        self.robot_arm = RobotArmControl()
        self.target_tube_id = 0
        self.is_return = False
        print(f"RobotArmDecision initiated")   
    
    def run(self, shared_state: SharedState):

        while True:
            # my_state = shared_state.get_state()['robot_arm']

            print(f"Robot Arm's Turn {shared_state.message_queue.queue}")


            if shared_state.no_message():
                shared_state.add_new_message("NextSample?")
                continue

            message = shared_state.get_front_message()

            if message == "NoSampleLeft":
                break

            if message.startswith("TubeId="):
                new_target = re.search(r'TubeId=(\d+), SampleId=(\d+)', message)
                self.target_tube_id = int(new_target.group(1))
                self.target_sample_id = int(new_target.group(2))

                shared_state.finish_front_message()
                shared_state.add_new_message("PauseRefill")
                time.sleep(0.1)

            elif message == "PauseRefillOkay" and self.is_return != False:
                self.robot_arm.move_to_tube_rack(self.target_tube_id)
                shared_state.finish_front_message()
                shared_state.add_new_message("ResumeRefill")
                time.sleep(0.1)

                self.robot_arm.move_to("spinsolve80")
                self.robot_arm.tilted_insert_tube()
                self.robot_arm.place_tube("spinsolve80")
                shared_state.add_new_message("NewSampleReady")
                time.sleep(0.1)
                
            elif message == "DitchSample":
                self.robot_arm.pick_tube("spinsolve80")
                self.robot_arm.tilted_remove_tube()
                shared_state.finish_front_message()

                self.robot_arm.move_to("washer")
                self.robot_arm.wash_tube()

                self.is_return = True
                shared_state.add_new_message("PauseRefill")

            elif message == "PauseRefillOkay" and self.is_return == True:
                self.robot_arm.pick_tube("washer")
                self.robot_arm.move_to_tube_rack(self.target_tube_id)
                self.robot_arm.place_tube("washer")
                shared_state.finish_front_message()
                
                shared_state.add_new_message(f"ReturnTubeId={self.target_tube_id}")    
                self.is_return = False
            
            time.sleep(0.1)


class Dummy_NMR_SpectrometerDecision:
    def __init__(self, message: str) -> None:
        self.remote_control = SpectrometerRemoteControl()
        self.request_xml_message = message
        print("Spectrometer initiated!")

    def run(self, shared_state: SharedState):

        loopCount = 0

        while True:
            if shared_state.no_message(): continue
            print(f"Spectrometer's Turn {shared_state.message_queue.queue}")

            message = shared_state.get_front_message()

            if message == "NoSampleLeft":
                break
            
            if message == "NewSampleReady":
                self.remote_control.send_request_to_spinsolve80(self.request_xml_message)
                print("finished NMR analysis")
                shared_state.finish_front_message()
                shared_state.add_new_message("DitchSample")
            
            time.sleep(3)


class DummyPipetterDecision:
    def __init__(self, process_order: list[int], tube_rack_capacity: int=1) -> None:
        self.pipettor = PipetterControl()
        self.process_order = process_order
        self.tube_rack = TubeRack(tube_rack_capacity)
        # self.current_
        self.standby = False

        print("Pipetter initiated")

    def run(self, shared_state: SharedState):

        loopCount = 0

        while True:
            if loopCount > 35: break
            loopCount += 1


            next_vial_pos = (-1 if self.process_order == [] else self.process_order[0])
            next_refill_pos = self.tube_rack.find_next("empty")

            if next_vial_pos != -1 and next_refill_pos != -1 and not self.standby:
                self.pipettor.aspirate(next_vial_pos)
                self.pipettor.refill(next_refill_pos)
                self.tube_rack.tube_filled(next_refill_pos, next_vial_pos)
                process_order.pop(0)
            
            elif next_vial_pos == -1 and next_refill_pos == -1:
                shared_state.add_new_message("NoSampleLeft")
                break

            print(f"Pipetter's Turn: {shared_state.message_queue.queue}")

            if shared_state.no_message(): continue

            message = shared_state.get_front_message()

            if message == "NextSample?":
                next_available_tube = self.tube_rack.find_next("filled")
                print(f"Next available tube is at rack id {next_available_tube}")
                if next_available_tube != -1:
                    shared_state.add_new_message(f"TubeId={next_available_tube}, SampleId= {self.tube_rack.sample_id[next_available_tube]}")
                    print(f"Pipetter added msg, {shared_state.message_queue.queue}")
                shared_state.finish_front_message()
            elif message == "PauseRefill":
                self.pipettor.standby()
                self.standby = True
                shared_state.add_new_message("PauseRefillOkay")
                shared_state.finish_front_message()
            elif message == "ResumeRefill":
                self.standby = False
                shared_state.finish_front_message()
            elif message.startswith("ReturnTubeId="):
                returned_tube_id = int(message[13:])
                self.tube_rack.tube_emptied(returned_tube_id)
                shared_state.finish_front_message()

            time.sleep(0.1)

if __name__ == "__main__":
    xml_request_message = """<?xml version="1.0" encoding="utf-8"?>
<Message>
        <Start protocol="1D PROTON">
                <Option name="Scan" value="QuickScan" />
        </Start>
</Message>"""

    process_order = [1, 4, 9, 16, 25, 36, 49]

    # testing
    dummy_robot_arm = DummyRobotArmDecision()
    dummy_pipetter = DummyPipetterDecision(process_order)
    dummy_NMR_spectrometer = Dummy_NMR_SpectrometerDecision(xml_request_message)
    # scheduler = Scheduler(sample_robot_arm, sample_NMR_spectrometer, sample_pipetter)
    scheduler = Scheduler(dummy_robot_arm, dummy_NMR_spectrometer, dummy_pipetter)
    scheduler.start()
