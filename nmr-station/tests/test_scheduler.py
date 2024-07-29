from queue import Queue
import threading


from tests.dummy_pipetter import DummyPipetterControl as PipetterControl
from tests.dummy_pipetter import TubeRack
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
        return self.message_queue.empty()

    def get_front_message(self) -> str :
        return self.message_queue.get()
    
    def add_new_message(self, message: str):
        self.message_queue.put(message)
    
    def finish_front_message(self):
        self.message_queue.task_done()
    

class Scheduler:
    # dependency injection here
    def __init__(self, robot_arm, NMR_spectrometer, pipetter) -> None:
        self.shared_state = SharedState()
        self.robot_arm = robot_arm
        self.NMR_spectrometer = NMR_spectrometer
        self.pipetter = pipetter
    
    def start(self):
        threading.Thread(target=self.robot_arm.run, args=(self.shared_state,)).start()
        threading.Thread(target=self.NMR_spectrometer.run, args=(self.shared_state,)).start()
        threading.Thread(target=self.pipetter.run, args=(self.shared_state,)).start()


class DummyRobotArmDecision:
    def __init__(self):
        self.robot_arm = RobotArmControl()
        self.target_tube_id = 0
        print(f"RobotArmDecision initiated")   
    
    def run(self, shared_state: SharedState):
        while True:
            my_state = shared_state.get_state()['robot_arm']

            if shared_state.no_message():
                if my_state == 'idle':
                    shared_state.add_new_message("NextSample=?")
                
                continue

            message = shared_state.get_front_message()
            if message.startswith("NextTubeId="):
                self.target_tube_id = int(message[11:])
                print(f"self.target_tube_id = {self.target_tube_id}")
                shared_state.finish_front_message()
                shared_state.add_new_message("PauseRefill")

            elif message == "PauseRefillOkay":
                self.robot_arm.move_to_tube_rack(self.target_tube_id)
                shared_state.finish_front_message()
                shared_state.add_new_message("ResumeRefill")

                self.robot_arm.move_to("spinsolve80")
                self.robot_arm.tilted_insert_tube()
                self.robot_arm.place_tube("spinsolve80")
                shared_state.add_new_message("NewSampleReady")

            elif message == "DitchSample":
                self.robot_arm.pick_tube("spinsolve80")
                self.robot_arm.tilted_remove_tube()
                shared_state.finish_front_message()

                self.robot_arm.move_to("washer")
                self.robot_arm.wash_tube()

                shared_state.add_new_message(f"ReturnTubeId={self.target_tube_id}")                


class Dummy_NMR_SpectrometerDecision:
    def __init__(self, message: str) -> None:
        self.remote_control = SpectrometerRemoteControl()
        self.request_xml_message = message
        print("Spectrometer initiated!")

    def run(self, shared_state: SharedState):
        while True:
            message = shared_state.get_front_message()

            if message == "NewSampleReady":
                self.remote_control.send_request_to_spinsolve80(self.request_xml_message)
                print("finished NMR analysis")
                shared_state.finish_front_message()
                shared_state.add_new_message("DitchSample")

class DummyPipetterDecision:
    def __init__(self, process_order: list[int], tube_rack_capacity: int=1) -> None:
        self.pipettor = PipetterControl()
        self.process_order = process_order
        self.tube_rack = TubeRack(tube_rack_capacity)
        self.standby = False

        print("Pipetter initiated")

    def run(self, shared_state: SharedState):
        while True:
            next_vial_pos = (-1 if self.process_order == [] else self.process_order[0])
            next_refill_pos = self.tube_rack.find_next()

            if next_vial_pos != -1 and next_refill_pos != -1 and not self.standby:
                self.pipettor.aspirate(next_vial_pos)
                self.pipettor.refill(next_refill_pos)
                self.tube_rack.tube_filled(next_refill_pos)
                process_order.pop(0)
            
            # if shared_state.no_message(): continue

            message = shared_state.get_front_message()

            if message == "NextTubeId=?":
                if next_refill_pos == -1:
                    shared_state.add_new_message("NextTubeId=None")
                else:
                    shared_state.add_new_message(f"NextTubeId={next_refill_pos}")
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
