class DummyPipetterControl:
    def __init__(self) -> None:
        pass
    
    def aspirate(self, id: int):
        print(f"aspirate at grid {id}")

    def refill(self, id: int):
        print(f"refill at tube rack {id}")

    def standby(self):
        print("Moved to standby position!")
    
class TubeRack:
    def __init__(self, capacity: int) -> None:
        self.status = ["empty" for _ in range(capacity)]
        self.sample_id = [-1 for _ in range(capacity)]
        self.capacity = capacity
    
    def tube_filled(self, rack_id: int, sample_id):
        self.status[rack_id] = "filled"
        self.sample_id[rack_id] = sample_id

    def tube_emptied(self, rack_id: int):
        self.status[rack_id] = "empty"
        self.sample_id[rack_id] = -1
    
    def tube_in_use(self, rack_id: int):
        self.status[rack_id] = "in use"

    def find_next(self, type: str) -> int:
        next_pos = 0
        try:
            next_pos = self.status.index(type)
        except ValueError:
            next_pos = -1
        return next_pos