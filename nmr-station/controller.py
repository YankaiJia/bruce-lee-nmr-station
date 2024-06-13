import mecademicpy.robot as mdr
import mecademicpy.mx_robot_def as mdr_def
import numpy as np

import math
import time

from meca import move_lin_rel_trf 


# theta is the tilted angle of Joint 6 in degree
def cal_tilted_angle_decompose(d: float, theta: float):
    theta_rad = math.radians(-theta)
    x = round(d * math.cos(theta_rad), 4)
    y = round(d * math.sin(theta_rad), 4) 
    return x, y

# vertically moving up or down once
def change_vertical_height(direction: str, dist: float, tilted_angle: float):
    is_moving_up = (True if direction == "u" else False)
    
    dx, dy = cal_tilted_angle_decompose(dist, tilted_angle)
    
    # get the actual current angle of joint 6
    _, _, _, _, _, cur_angle_j6 = mdr.Robot().GetRtTargetJointPos()
    actu_angle_j6 = cur_angle_j6 - tilted_angle
    is_upside_down = (True if round(actu_angle_j6, 2) == 180.00 else False)

    if is_moving_up != is_upside_down: dx, dy = -dx, -dy

    move_lin_rel_trf(dx, dy, 0, 0, 0, 0)
    pass 



if __name__ == "__main__" :
    print("===Testing Mode===")
    
    print(cal_tilted_angle_decompose(100, -60))
    