class DummyRobotArm:
    def __init__(self) -> None:
        print("Robot Arm is initiated!")

    def move_to_tube_rack(self, tube_rack_id: int):
        print(f"Robot Arm moving to tube rack {tube_rack_id}")

    def move_to(self, facility: str):
        print(f"Robot Arm moving to {facility}")

    def tilted_insert_tube():
        print("The Robot Arm is inserting the tube at a tilted angle")

    def tilted_remove_tube():
        print("The Robot Arm is removing the tube at a tilted angle")

    def place_tube(facility: str):
        print(f"Place tube on {facility}")

    def pick_tube(facility: str):
        print(f"Pick tube on {facility}")

    def wash_tube():
        print(f"washing the tube")
