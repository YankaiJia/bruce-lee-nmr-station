"""
Cylinderical movement system for MECA500
Used by the cli tool and auto scripts
Stores logic & functions that communicate with the MECA500 robot arm

deprecated now, only used by the cli_tool.py
use the roboarm.py instead

King Lam Kwong
"""

import mecademicpy.robot as mdr
import mecademicpy.mx_robot_def as mdr_def
import numpy as np

import math
import time
import datetime
import sys

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
    now = datetime.datetime.now()
    print(f'CartPos:{r.GetRtTargetCartPos()} at {now}.')
    print(f'JointPos:{r.GetRtTargetJointPos()} at {now}.')
    print()


# Simplified Movement Control Functions


# vertically moving up or down once
def change_vertical_height(
    robo: mdr.Robot, direction: str, dist: int, tilted_angle: float=None
):
    print(f"moving {direction} for {dist} mm with joint-6 {tilted_angle} deg tilted.")
    # is_moving_up = True if direction == "up" else False
    #
    # dx, dy = cal_tilted_angle_decompose(dist, tilted_angle)
    #
    # if is_moving_up != is_joint6_upside_down(robo, tilted_angle):
    #     dx, dy = -dx, -dy
    #
    # print(
    #     "Grippler Moving",
    #     ("up" if is_moving_up == True else "down"),
    #     f"for {dist} mm, dx={dx}, dy={dy}",
    # )
    # # robo.MoveLinRelTrf(dx, dy, 0, 0, 0, 0)

    if direction == "down" : dist = -dist
    robo.MoveLinRelWrf(0, 0, dist, 0, 0,0)
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


def invert_gripper(robo: mdr.Robot, tilted_angle: float = None):
    # d_theta = 180
    # cur_j6 = robo.GetRtTargetJointPos()[5]
    # if cur_j6 > 90:
    #     d_theta = -180

    d_theta = -180
    # print(f'the robot is {robo}')
    cur_j6 = robo.GetRtTargetJointPos()[5]

    if cur_j6 < -90:
        d_theta = 180

    robo.MoveJointsRel(0, 0, 0, 0, 0, d_theta)
    print("Gripper Inverted")
    print_RtTargetPos(robo)

def rotate_one_joint(robo:mdr.Robot, which_joint: int, theta: float):

    ts = [0]*6

    if which_joint not in range(1,7):
        print(f'ERROR: Wrong joint number: {which_joint}.')
        return False
    if theta > 30:
        print(f'ERROR: Angle is too big: {theta}. No move for safety!')
        return False

    ts = [theta if index == (which_joint-1) else 0 for index, _ in enumerate(ts)]

    t1,t2,t3,t4,t5,t6 = ts

    print(f'Moving joint {which_joint} by {theta} degrees...\n')
    robo.MoveJointsRel(t1,t2,t3,t4,t5,t6)
    print_RtTargetPos(robo)

def zero(robo: mdr.Robot):

    zero_position = [0, -23.27248, -44.76893, 0, 68.04142, 0]
    if (input('CAUTION! Arm going to (0,0,0,0,0,0). COLLISION MAY OCCUR! [y/n]?')
            in ["yes", "YES", 'Y', 'y']):

        time.sleep(2)
        if input('Reconfirm going to (0,0,0,0,0,0). COLLISION MAY OCCUR! [y/n]?') in ["yes","YES",'Y','y']:
            robo.MoveJoints(zero_position[0],
                            zero_position[1],
                            zero_position[2],
                            zero_position[3],
                            zero_position[4],
                            zero_position[5])

    else:
        print("Robot did not go to (0,0,0,0,0).")
        return

def connect_robot(r: mdr.Robot):
    r.Connect(address='192.168.0.100', enable_synchronous_mode=True, disconnect_on_exception=False)
    r.ActivateAndHome()
    r.WaitHomed()
    print('Homed!')

def reset_robot(a:None):
    r= mdr.Robot()
    connect_robot(r)
    r.ActivateAndHome()
    r.ResetError()
    r.ResumeMotion()
    print("Robot is reset!")


if __name__ == "__main__":
    print("===Testing Mode===")

    # print(cal_tilted_angle_decompose(100, -60))
    # change_vertical_height("d", 250, 0,0)
    # change_vertical_height("d", 100, -60, 0)

    # r = mdr.Robot()
    # connect_robot(r)
    # reset_robot()
    # zero()
    # change_vertical_height(r, 250, 0, 0)

    globals()[sys.argv[1]]()

