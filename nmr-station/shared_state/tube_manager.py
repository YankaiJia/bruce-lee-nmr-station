import threading

class TubeManager:
    def __init__(self, tube_count: int) -> None:
        self.tube_count = tube_count
        self.sample_in_tube = [-1 for _ in range(tube_count)]
        self.tube_status = ["empty" for _ in range(tube_count)]
        self.time_finished = [-1 for _ in range(tube_count)] 
        self.lock = threading.Lock()

    def print_status(self):
        with self.lock:
            print("+----------------")
            print(f"  status    {self.tube_status}")
            print(f"  sample Id {self.sample_in_tube}")
            print("+----------------")

    def set_time_finished(self, id: int, timestamp):
        with self.lock:
            self.time_finished[id] = timestamp

    def filled_tube(self, id: int, sample_id: int):
        with self.lock:
            self.tube_status[id] = "filled"
            self.sample_in_tube[id] = sample_id
    
    def transferring_tube(self, id: int):
        with self.lock:    
            self.tube_status[id] = "transferring"

    def in_spectrometer(self, id: int):
        with self.lock:
            self.tube_status[id] = "in_spectrometer"

    def analyzing_tube(self, id: int):
        with self.lock:
            self.tube_status[id] = "analyzing"
    
    def washing_tube(self, id: int):
        with self.lock:
            self.tube_status[id] = "washing"

    def drying_tube(self, id: int):
        with self.lock:
            self.tube_status[id] = "drying"

    def in_waste_collector(self, id: int):
        with self.lock:
            self.tube_count[id] = "waste_collector"

    def in_washer1(self, id: int):
        with self.lock:
            self.tube_count[id] = "washer1"

    def in_washer2(self, id: int):
        with self.lock:
            self.tube_count[id] = "washer2"

    def in_dryer(self, id: int):
        with self.lock:
            self.tube_count[id] = "dryer"

    def empty_tube(self, id: int):
        with self.lock:
            self.sample_in_tube[id] = -1
            self.tube_status[id] = "empty"
            self.time_finished[id] = -1

    def find(self, type: str) -> int:
        next_pos = 0
        try:
            next_pos = self.tube_status.index(type)
        except ValueError:
            next_pos = -1
        return next_pos 

    def find_next_filled_tube(self) -> int:
        with self.lock:
            mn = self.tube_count + 1
            for i in range(self.tube_count):
                if self.tube_status[i] == "filled": 
                    mn = min(mn, self.sample_in_tube[i])
            return (mn if mn < self.tube_count + 1 else -1)
    
    def find_next_empty_tube(self) -> int:
        return self.find("empty")