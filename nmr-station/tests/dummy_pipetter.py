class DummyPipetterControl:
    def __init__(self) -> None:
        pass
    
    def aspirate(self, id: int):
        print(f"aspirate at grid {id}")

    def refill(self, id: int):
        print(f"refill at grid {id}")

    def standby(self):
        print("Moved to standby position!")
    
class TubeRack:
    def __init__(self, capacity: int) -> None:
        self.status = [False for _ in range(capacity)]
        self.capacity = capacity
        self.filled_cnt = 0
    
    def tube_filled(self, rack_id: int):
        self.status[rack_id] = True
        self.filled_cnt += 1

    def tube_emptied(self, rack_id: int):
        self.status[rack_id] = False
        self.filled_cnt -= 1
    
    def find_next(self) -> int:
        next_pos = 0
        try:
            next_pos = self.status.index(False)
        except ValueError:
            next_pos = -1
        return next_pos
    
