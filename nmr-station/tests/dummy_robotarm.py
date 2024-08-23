from robotic_arm import load_facilities, Facility

class DummyRobotArmControl:
    def __init__(self) -> None:
        print("\033[94mRobot Arm is initiated! \033[0m")
        self.facilities = load_facilities()

    def move_to_tube_rack(self, tube_rack_id: int):
        print(f"\033[94mRobot Arm moving to tube rack {tube_rack_id} \033[0m")

    def move_to(self, facility: str):
        print(f"\033[94mRobot Arm moving to {facility} \033[0m")

    def go_to_safe(self, mode):
        print(f"Go to safe in {mode} mode")

    def tilted_insert_tube(self):
        print("\033[94mThe Robot Arm is inserting the tube at a tilted angle \033[0m")

    def tilted_remove_tube(self):
        print("\033[94mThe Robot Arm is removing the tube at a tilted angle \033[0m")

    def place_tube(self, facility):
        print(f"\033[94mPlace tube on {str(facility)} \033[0m")

    def place_tube_to_spinsolve(self):
        print("\033[94mplace_tube_to_spinsolve... \033[0m")

    def pick_tube_from_spinsolve(self):
        print("\033[94mpick_tube_from_spinsolve... \033[0m")

    def pick_tube(self, facility):
        print(f"\033[94mPick tube on {str(facility)} \033[0m")

    def wash_tube(self):
        print(f"\033[94mwashing the tube \033[0m")

    def dry_tube(self):
        print("\033[94mdry tube... \033[0m")

    def flip_tube(self, location: str):
        print(f"\033[94mflip_tube at {location}... \033[0m")