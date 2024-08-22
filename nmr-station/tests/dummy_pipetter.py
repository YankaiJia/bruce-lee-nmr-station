class DummyPipetterControl:
    def __init__(self) -> None:
        pass
    
    def aspirate(self, id: int):
        print(f"aspirate at grid {id}")

    def refill(self, id: int):
        print(f"refill at tube rack {id}")

    def standby(self):
        print("Moved to standby position!")
   