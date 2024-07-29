"""
This file defines a facility on the NMR-station platform, and 
describes the tube handling behaviour for each facility
Settings of the facilities are stored in facility_config.json
Here we provide a function to load the facility_config.json data 

KingLam Kwong
"""
# Third-party imports

# Standard library imports
from collections import namedtuple
import json
from typing import Callable

# current codespace imports
from robotarm import RobotArm

CartPos = namedtuple(
    "CartPos", ["x", "y", "z", "alpha", "beta", "gamma"]
)

class Facility:
    def __init__(self, pos: dict, tube_handling_strategy: Callable):
        self.pos = pos
        self.handle_tube = tube_handling_strategy

def handle_tube_at_tube_rack(self, robo: RobotArm):
    if robo.is_gripper_opened():
        robo.place_tube(self.pos["entrance"], self.pos["landing"])
    else:
        robo.pick_tube(self.pos["entrance"], self.pos["landing"])

def handle_tube_at_spinsolve80(self, robo: RobotArm):
    tilted_insert_tube(robo)
    robo.place_tube(self.pos["upper_landing"], self.pos["landing"], wait_for_picking=True)
    # wait for analysis
    robo.pick_tube(self.pos["upper_landing"], self.pos["landing"])
    tilted_remove_tube(robo)

def tilted_insert_tube(robo: RobotArm):
   robo.move_joints_rel(j6=-27)
   robo.change_vertical_height(-47)
   robo.move_joints_rel(j1=-10, j6=10)
   robo.change_radial_distance(10)
   robo.move_joints_rel(j1=-10, j6=10)
   robo.change_radial_distance(7)
   robo.move_joints_rel(j1=-6, j6=7)

def tilted_remove_tube(robo: RobotArm):
    robo.move_joints_rel(j1=6, j6=-7)
    robo.change_radial_distance(-7)
    robo.move_joints_rel(j1=10, j6=-10)
    robo.change_radial_distance(-10)
    robo.move_joints_rel(j1=10, j6=-10)
    robo.change_vertical_height(47)
    robo.move_joints_rel(j6=27)


def handle_tube_at_waiter(self, robo: RobotArm):
    landing_pos_name = "landing"
    if not robo.is_girpper_inverted():
        robo.invert_gripper()

        landing_pos_name = "inverted_landing"
    robo.place_tube(self.pos["entrance"], self.pos[landing_pos_name])

    robo.invert_gripper()

    if landing_pos_name == "inverted_landing":
        landing_pos_name = "landing"
    robo.pick_tube(self.start_pos, self.pos[landing_pos_name])


def handle_tube_at_washer(self, robo: RobotArm):
    robo.place_tube(self.pos["entrance"], self.pos["landing"])
    # wait()
    # pickTube("slow")
    robo.pick_tube(self.pos["entrance"], self.pos["landing"])


def load_facilities() -> dict:
    facilities = {}

    with open('facility_config.json') as file:
        config_data = json.load(file)
    
    for name, details in config_data.items():
        position_map = {key: CartPos(*value) for key, value in details["pos"].itmes()}
        tube_handling_strategy = getattr(globals(), details["handle_tube"])
        facilities[name] = Facility(position_map, tube_handling_strategy)
    
    return facilities