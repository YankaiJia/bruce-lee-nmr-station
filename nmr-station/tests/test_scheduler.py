from queue import Queue
import threading


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
        pass 
    
    def run(self, shared_state: SharedState):
        while True:
            my_state = shared_state.get_state()['robot_arm']

            if shared_state.no_message():
                if my_state == 'idle':
                    shared_state.add_new_message("NextSample=?")
                
                continue

            message = shared_state.get_front_message()
            if message == "NextSample=1":
                shared_state.finish_front_message()
                shared_state.add_new_message("PauseRefill")

            elif message == "PauseRefillOkay":
                print("robo.move_to(\"tube_rack\")")
                shared_state.finish_front_message()
                shared_state.add_new_message("ResumeRefill")

                print("robo.move_to(\"spinsolve80\")")        
                print("robo.tilted_insert_tube()")
                print("robo.place_tube(\"spinsolve80\")")
                shared_state.add_new_message("NewSampleReady")

            elif message == "DitchUsedSample":
                print("robo.pick_tube(\"spinsolve80\")")
                print("robo.tilted_remove_tube()")


class Dummy_NMR_SpectrometerDecision:
    def __init__(self) -> None:
        pass

    def run(self, shared_state: SharedState):
        while True:
            my_state = shared_state.get_state()['NMR_spectrometer']

            if my_state == "completed":
                shared_state.add_new_message("DitchSample")
                continue

            if shared_state.no_message(): continue

            message = shared_state.get_front_message()
            if message == "NewSampleReady":
                print("remote_control.order_new_protocol()")
                shared_state.finish_front_message()

class DummyPipetterDecision:
    def __init__(self) -> None:
        pass
    
    def run(self, shared_state: SharedState):
        while True:
            my_state = shared_state.get_state()['pipetter']
            
            if shared_state.no_message(): continue

            message = shared_state.get_front_message()
            if message == "NextSample=?":
                if my_state == "idle":
                    shared_state.add_new_message("NextSample=None")
                else:
                    shared_state.add_new_message("NextSample=(int)")
                shared_state.finish_front_message()
            elif message == "PauseRefill":
                print("pipetter.stand_by()")
                if my_state == "stand_by":
                    shared_state.add_new_message("PauseRefillOkay")
                    shared_state.finish_front_message()
            elif message == "ResumeRefill":
                print("pipetter.refill()")
                shared_state.finish_front_message()
            

if __name__ == "__main__":
    # testing
    dummy_robot_arm = DummyRobotArmDecision()
    dummy_pipetter = DummyPipetterDecision()
    dummy_NMR_spectrometer = Dummy_NMR_SpectrometerDecision()
    # scheduler = Scheduler(sample_robot_arm, sample_NMR_spectrometer, sample_pipetter)
    scheduler = Scheduler(dummy_robot_arm, dummy_NMR_spectrometer, dummy_pipetter)
    scheduler.start()
