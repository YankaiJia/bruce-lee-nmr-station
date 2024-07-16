from queue import Queue
import threading


class SharedState:
    def __init__(self) -> None:
        self.state = {
            'robot': 'idle',
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

    def get_front_message(self) -> str :
        return self.message_queue.get()
    
    def enqueue_message(self, message: str):
        self.message_queue.put(message)
    
    def dequeue_message(self):
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


class RobotArmLogic:
    pass

if __name__ == "__main__":
    # testing
    sample_robot_arm = SampleRobotArm()
    sample_NMR_spectrometer = Sample_NMR_Spectrometer()
    sample_pipetter = SamplePipetter()
    scheduler = Scheduler(sample_robot_arm, sample_NMR_spectrometer, sample_pipetter)
    scheduler.start()
