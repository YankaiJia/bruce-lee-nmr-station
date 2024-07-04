"""
Cylinderical movement system for MECA500
Used by the cli tool and auto scripts
Stores logic & functions that communicate with the MECA500 robot arm

King Lam Kwong
"""

import mecademicpy.robot as mdr
import mecademicpy.mx_robot_def as mdr_def
import numpy as np

import math
import time

from meca import move_lin_rel_trf

"""
Calculation / Utility Functions

"""


# theta is the tilted angle of Joint 6 in degree
def cal_tilted_angle_decompose(d: int, theta: float):
    # if no angle tilted
    if round(theta % 360, 2) == 0.00:
        return d, 0
    theta_rad = math.radians(-theta)
    x = round(d * math.cos(theta_rad), 4)
    y = round(d * math.sin(theta_rad), 4)
    return x, y


def is_joint6_upside_down(r: mdr.Robot, tilted_angle: float):
    actual_angle_j6 = r.GetRtTargetJointPos()[5] - tilted_angle
    return True if abs(round(actual_angle_j6, 2)) == 180.00 else False


def print_RtTargetPos(r: mdr.Robot):
    print(r.GetRtTargetCartPos())
    print(r.GetRtTargetJointPos())
    print()


"""
Simplified Movement Control Functions

"""


# vertically moving up or down once
def change_vertical_height(
    robo: mdr.Robot, direction: str, dist: int, tilted_angle: float
):
    print(f"moving {direction} for {dist} mm with joint-6 {tilted_angle} deg tilted.")
    is_moving_up = True if direction == "up" else False

    dx, dy = cal_tilted_angle_decompose(dist, tilted_angle)

    if is_moving_up != is_joint6_upside_down(robo, tilted_angle):
        dx, dy = -dx, -dy

    print(
        "Grippler Moving",
        ("up" if is_moving_up == True else "down"),
        f"for {dist} mm, dx={dx}, dy={dy}",
    )
    robo.MoveLinRelTrf(dx, dy, 0, 0, 0, 0)

    print_RtTargetPos(robo)


def change_radial_distance(robo: mdr.Robot, dz: int):
    print("Moving", ("forward" if dz > 0 else "backward"), f"for {dz} mm")

    robo.MoveLinRelTrf(0, 0, dz, 0, 0, 0)

    print_RtTargetPos(robo)


def change_azimuth(robo: mdr.Robot, theta: float):
    print("Rotate Joint 1", ("forward" if theta > 0 else "backward"), f"for {theta}°")

    robo.MoveJointsRel(theta, 0, 0, 0, 0, 0)

    print_RtTargetPos(robo)


def change_gripper_state(robo: mdr.Robot):
    is_opened = robo.GetRtGripperState().opened
    if is_opened == True:
        robo.GripperClose()
        print("Gripper Opened!")
    else:
        robo.GripperOpen()
        print("Gripper Closed!")

    print_RtTargetPos(robo)


def invert_gripper(robo: mdr.Robot, tilted_angle: float):
    # d_theta = 180
    # cur_j6 = robo.GetRtTargetJointPos()[5]
    # if cur_j6 > 90:
    #     d_theta = -180

    d_theta = -180
    cur_j6 = robo.GetRtTargetJointPos()[5]

    if cur_j6 < -90:
        d_theta = 180

    robo.MoveJointsRel(0, 0, 0, 0, 0, d_theta)
    print("Gripper Inverted")
    print_RtTargetPos(robo)


if __name__ == "__main__":
    print("===Testing Mode===")

    print(cal_tilted_angle_decompose(100, -60))
    change_vertical_height("d", 250, 0)
    change_vertical_height("d", 100, -60)
