"""
This file defines a facility on the NMR-station platform, and 
describes the tube handling behaviour for each facility
Settings of the facilities are stored in facility_config.json
Here we provide a function to load the facility_config.json data 

KingLam Kwong
"""

import copy

# Third-party imports

# Standard library imports
from collections import namedtuple
import json
from typing import Callable
import numpy as np

# current codespace imports
# This will cause 'circular import' problem when
# running robotarm.py. So it is commented out and a dummy type hint is made.
# from robotarm import RobotArm


# make a dummy class for the type hint: RobotArm.
class RobotArm:
    pass


CartPos = namedtuple("CartPos", ["x", "y", "z", "alpha", "beta", "gamma"])

aa = CartPos(1, 2, 3, 4, 5, 6)

facilities = []

with open("facility_config.json") as file:
    config_data = json.load(file)


class Facility:

    def __init__(
        self,
        pos_low: tuple,
        pos_high_z: float,
        # carousel_radius: float,
        tube_handling_strategy: Callable,
        name: str,
    ):
        self.pos = {}
        self.pos["low"] = pos_low
        self.pos["high"] = self.get_high_pos(pos_low, pos_high_z)
        # self.pos['carousel'] = self.get_carousel_pos(carousel_radius, self.pos['high'])
        self.handle_tube = tube_handling_strategy
        self.name = name

    def get_high_pos(self, pos_low: tuple, pos_high_z: float):
        coord_here = copy.deepcopy(list(pos_low))
        coord_here[2] = pos_high_z
        return tuple([float(i) for i in coord_here])  # add height to z

    def get_carousel_pos(self, carousel_radius: float, pos_high: tuple):

        pos_high_here = copy.deepcopy(pos_high)
        x0, y0 = pos_high_here[0], pos_high_here[1]

        x = (carousel_radius**2 / (y0**2 / x0**2 + 1)) ** 0.5
        x = abs(x) if pos_high_here[1] > 0 else -abs(x)  # make the sign the same

        y = (y0 / x0) * x

        return tuple(
            (
                x,
                y,
                pos_high_here[2],
                pos_high_here[3],
                pos_high_here[4],
                pos_high_here[5],
            )
        )


class Tube_pos(Facility):

    print("This is a Tube_pos!")


def handle_tube_at_tube_rack(self, robo: RobotArm):
    if robo.is_gripper_opened():
        robo.place_tube(self.pos["entrance"], self.pos["landing"])
    else:
        robo.pick_tube(self.pos["entrance"], self.pos["landing"])


def handle_tube_at_spinsolve80(self, robo: RobotArm):
    tilted_insert_tube(robo)
    robo.place_tube(
        self.pos["upper_landing"], self.pos["landing"], wait_for_picking=True
    )
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


# def load_facilities():
#
#     with open('facility_config.json') as file:
#         config_data = json.load(file)
#
#     for name, details in config_data.items():
#         print(name,details)
#         position_map = {key: CartPos(*value) for key, value in details["pos"].items()}
#         # tube_handling_strategy = getattr(globals(), details["handle_tube"])
#         tube_handling_strategy = globals().get(details["handle_tube"])
#         facilities[name] = Facility(position_map, tube_handling_strategy)
#
#     return facilities


def add_tubes():
    for key, value in config_data.items():
        pos_here = tuple(value["pos_low"])
        pos_high_z = value["pos_high_z"]
        tube_handling_strategy_here = value["handle_tube"]
        facility_here = Tube_pos(
            pos_low=pos_here,
            pos_high_z=pos_high_z,
            tube_handling_strategy=tube_handling_strategy_here,
            name=key,
        )
        facilities.append(facility_here)

    return facilities


add_tubes()

Tube1 = [i for i in facilities if i.name == "tube1"][0]
Tube2 = [i for i in facilities if i.name == "tube2"][0]
Tube3 = [i for i in facilities if i.name == "tube3"][0]
Tube4 = [i for i in facilities if i.name == "tube4"][0]
Washer1 = [i for i in facilities if i.name == "washer1"][0]
Washer2 = [i for i in facilities if i.name == "washer2"][0]
Flip_stand_gripper_bottomup_tube_bottomup = [
    i for i in facilities if i.name == "flip_stand_gripper_bottomup_tube_bottomup"
][0]
Flip_stand_gripper_topdown_tube_bottomup = [
    i for i in facilities if i.name == "flip_stand_gripper_topdown_tube_bottomup"
][0]
Flip_in_air = [i for i in facilities if i.name == "flip_in_air"][0]
Spinsolve = [i for i in facilities if i.name == "spinsolve"][0]

if __name__ == "__main__":

    facilities = add_tubes()

    print(1)
