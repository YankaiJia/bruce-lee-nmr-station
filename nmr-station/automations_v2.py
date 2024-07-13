import time

from roboarm import TUBE_LENGTH, CartPos, Facility, RobotArm


def handle_tube_at_tube_rack(self, robo: RobotArm):
    if robo.is_gripper_opened():
        robo.place_tube(self.start_pos, self.land_pos)
    else:
        robo.pick_tube(self.start_pos, self.land_pos)


def handle_tube_at_spinsolve80(self, robo):
    robo.tilted_insert_tube()
    robo.place_tube(self.middle_pos, self.land_pos, wait_for_picking=True)
    # wait for analysis
    robo.pickTube(self.middle_pos, self.land_pos)
    robo.tilted_remove_tube()


def processTubeAtWaiter(self, robo):
    if not robo.is_girpper_inverted():
        robo.invert_gripper()
		
		# special handling the inverted state 
    robo.place_tube(self.start_pos, self.land_pos)
    robo.invert_gripper()
    robo.pick_tube(self.start_pos, self.land_pos)

def processTubeAtWasher(self, robo):
    robo.place_tube(self.start_pos, self.land_pos)
    # wait()
    #pickTube("slow")
    robo.pick_tube(self.start_pos, self.land_pos)


tube_rack = Facility(
    (45.191, 198.907, 338, -90, 12.8, 90),
    (45.191, 198.907, 78, -90, 12.8, 90),
    handle_tube_at_tube_rack
)

spinsolve80 = Facility(
    (45.191, 198.907, 338, -90, 12.8, 90),
    (45.191, 198.907, 78, -90, 12.8, 90),
    handle_tube_at_spinsolve80,
    middle_pos=(90.553, -188.997, 338.000, 90, 25.6, -90)
)

waiter = Facility(
    
)

washer = Facility(
    
)


def route(robo: RobotArm):
    for facility in [tube_rack, spinsolve80, waiter, washer, waiter, tube_rack]:
        robo.move_to(facility)
        facility.handle_tube(robo)