"""
Model part of the testing kit
Stores logic & functions that communicate with the MECA500 robot arm

King Lam Kwong
"""

import mecademicpy.robot as mdr
import mecademicpy.mx_robot_def as mdr_def
import numpy as np

import math
import time

from meca import move_lin_rel_trf 


# theta is the tilted angle of Joint 6 in degree
def cal_tilted_angle_decompose(d: int, theta: float):
    # if no angle tilted
    if round(theta % 360, 2) == 0.00: 
        return d, 0
    theta_rad = math.radians(-theta)
    x = round(d * math.cos(theta_rad), 4)
    y = round(d * math.sin(theta_rad), 4) 
    return x, y

# vertically moving up or down once
def change_vertical_height(robo: mdr.Robot, direction: str, dist: int, tilted_angle: float):
    print(f"moving {direction} for {dist} mm with joint-6 {tilted_angle} deg tilted.")
    is_moving_up = (True if direction == "up" else False)
    
    dx, dy = cal_tilted_angle_decompose(dist, tilted_angle)
    
    # get the actual current angle of joint 6
    _, _, _, _, _, cur_angle_j6 = robo.GetRtTargetJointPos()
    # _, _, _, _, _, cur_angle_j6 = [-90, 0, 0, 0, 0, 120]
    actu_angle_j6 = cur_angle_j6 - tilted_angle
    is_upside_down = (True if round(actu_angle_j6, 2) == 180.00 else False)

    if is_moving_up != is_upside_down: dx, dy = -dx, -dy

    print("Grippler Moving", ("up" if is_moving_up == True else "down"), f"for {dist} mm, dx={dx}, dy={dy}")
    robo.MoveLinRelTrf(dx, dy, 0, 0, 0, 0) 

    print(robo.GetRtTargetCartPos())


if __name__ == "__main__" :
    print("===Testing Mode===")
    
    print(cal_tilted_angle_decompose(100, -60))
    change_vertical_height("d", 250, 0)
    change_vertical_height("d", 100, -60)    