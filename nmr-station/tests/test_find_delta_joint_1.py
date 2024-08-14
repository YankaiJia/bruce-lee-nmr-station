import math
import numpy as np

def get_radial_distance(x: float, y: float):
    return math.sqrt(x * x + y * y)


def find_delta_joint_1(cur_x, cur_y, tar_x, tar_y):
    dot_product = cur_x * tar_x + cur_y * tar_y
    cur_rad = get_radial_distance(cur_x, cur_y)
    tar_rad = get_radial_distance(tar_x, tar_y)
    delta_joint_1 = math.acos(dot_product / (cur_rad * tar_rad))

    direction = (1 if tar_y > cur_y * tar_x / cur_x else -1)

    return direction * math.degrees(delta_joint_1)

def find_delta_by_atan2(cur_x, cur_y, tar_x, tar_y):
    dot = cur_x * tar_x + cur_y * tar_y  # Dot product between [x1, y1] and [x2, y2]
    det = cur_x * tar_y - cur_y * tar_x  # Determinant
    angle = math.atan2(det, dot)  # atan2(y, x) or atan2(sin, cos)
    # print(angle)

    return math.degrees(angle)

if __name__ == "__main__":
    pos = dict()
    pos['safe'] = [26.2705, 1.01272]
    pos['tube'] = [158.15678, 72.80897]

    # print(f"radialDist of safe pos: {get_radial_distance(26.2705, 1.01272)}")
    # print(f"radialDist of tube pos: {get_radial_distance(158.15678, 72.80897)}")
    # print()
    # print(f"change of j1 between safe & tube pos :{find_delta_joint_1(26.2705, 1.01272, 158.15678, 72.80897)}")
    # print(f"change of j1 between safe & tube pos :{find_delta_joint_1(158.15678, 72.80897, 26.2705, 1.01272)}")
    # print()
    # print(f"<1, -2> -> <-2, 1> :{find_delta_joint_1(1, -2, -2, 1)}")
    # print(f"<-2, 1> -> <1, -2> :{find_delta_joint_1(-2, 1, 1, -2)}")

    print(f"change of j1 between safe & tube pos :{find_delta_by_atan2(26.2705, 1.01272, 158.15678, 72.80897)}")
    print(f"change of j1 between safe & tube pos :{find_delta_by_atan2(158.15678, 72.80897, 26.2705, 1.01272)}")
    print()
    print(f"<1, -2> -> <-2, 1> :{find_delta_by_atan2(1, -2, -2, 1)}")
    print(f"<-2, 1> -> <1, -2> :{find_delta_by_atan2(-2, 1, 1, -2)}")