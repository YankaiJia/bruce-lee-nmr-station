import mecademicpy.robot as mdr

from collections import namedtuple
from typing import Callable
import time

TUBE_LENGTH = 275

CartPos = namedtuple(
    "CartPos", ["x", "y", "z", "alpha", "beta", "gamma"]
)

class Facility:
    def __init__(
        self,
        start_pos: tuple,
        land_pos: tuple,
        tube_handling_strategy: Callable,
        middle_pos: tuple = None
    ):
        self.start_pos = CartPos(*start_pos)
        if middle_pos: self.intermediate_pos = CartPos(*middle_pos)
        self.land_pos = CartPos(*land_pos)

        self.handle_tube = tube_handling_strategy


class RobotArm:
    def __init__(self):
        self.robo = mdr.Robot()
        self.connect_robot()
        self.config_robot()

    # Robot Setup Functions

    def reset_robot(self):
        self.robo.ResetError()
        self.robo.ResumeMotion()

    def connect_robot(self):
        self.robo.Connect(
            address="192.168.0.100",
            enable_synchronous_mode=True,
            disconnect_on_exception=False,
        )
        self.robo.ActivateAndHome()
        self.robo.WaitHomed()
        print("Homed!")

    def config_robot(self):
        # self.robo.SetGripperRange(12, 30)

        # short gripper
        self.robo.SetGripperRange(0, 4.9)

    # Robot Status Getter Functions

    def get_cart_pos(self):
        CartPos(self.GetRtTargetCartPos())
        return CartPos(self.GetRtTargetCartPos())

    def print_rt_target_pos(self):
        print(self.robo.GetRtTargetCartPos())
        print(self.robo.GetRtTargetJointPos())
        print()

    def is_located_at(self, tar_pos: CartPos):
        cur_pos = self.get_cart_pos()
        rt = True
        rt &= round(cur_pos.x, 2) == round(tar_pos.x, 2)
        rt &= round(cur_pos.y, 2) == round(tar_pos.y, 2)
        rt &= round(cur_pos.z, 2) == round(tar_pos.z, 2)
        rt &= round(cur_pos.alpha, 2) == round(tar_pos.alpha, 2)
        rt &= round(cur_pos.beta, 2) == round(tar_pos.beta, 2)
        rt &= round(cur_pos.gamma, 2) == round(tar_pos.gamma, 2)

        return rt

    def is_gripper_opened(self):
        return self.robo.GetRtGripperState().opened

    def is_gripper_inverted(self):
        cur_j6 = self.robo.GetRtTargetJointPos()[5]
        return cur_j6 < -90

    # Warpped Built-in Movement Functions

    def move_pose(
        self,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        alpha: float = 0,
        beta: float = 0,
        gamma: float = 0,
    ):
        self.robo.MovePose(x, y, z, alpha, beta, gamma)

    def move_lin(
        self,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        alpha: float = 0,
        beta: float = 0,
        gamma: float = 0,
    ):
        self.robo.MoveLin(x, y, z, alpha, beta, gamma)

    def move_lin_rel_trf(
        self,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        alpha: float = 0,
        beta: float = 0,
        gamma: float = 0,
    ):
        self.robo.MoveLinRelTrf(x, y, z, alpha, beta, gamma)

    def move_lin_rel_wrf(
        self,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        alpha: float = 0,
        beta: float = 0,
        gamma: float = 0,
    ):
        self.robo.MoveLinRelWrf(x, y, z, alpha, beta, gamma)

    def move_joints(
        self,
        j1: float = 0,
        j2: float = 0,
        j3: float = 0,
        j4: float = 0,
        j5: float = 0,
        j6: float = 0,
    ):
        # if a single tuple is sent
        if isinstance(j1, tuple):
            j1, j2, j3, j4, j5, j6 = j1

        self.robo.MoveJoints(j1, j2, j3, j4, j5, j6)

    def move_joints_rel(
        self,
        j1: float = 0,
        j2: float = 0,
        j3: float = 0,
        j4: float = 0,
        j5: float = 0,
        j6: float = 0,
    ):
        # if a single tuple is sent
        if isinstance(j1, tuple):
            j1, j2, j3, j4, j5, j6 = j1

        self.robo.MoveJointsRel(j1, j2, j3, j4, j5, j6)

    def gripper_open(self):
        self.robo.GripperOpen()
        self.robo.WaitGripperMoveCompletion()

    def gripper_close(self):
        self.robo.GripperClose()
        self.robo.WaitGripperMoveCompletion()

    # Simplified System Movement Functions

    def change_vertical_height(self, dist: int):
        self.robo.MoveLinRelWrf(0, 0, dist, 0, 0, 0)

        direction = "up" if dist > 0 else ("down" if dist < 0 else "nothing")
        print(f"vertically moving {direction} for {abs(dist)} mm.")
        self.print_rt_target_pos()

    def change_radial_distance(self, dz: int):
        self.robo.MoveLinRelTrf(0, 0, dz, 0, 0, 0)

        print("Moving", ("forward" if dz > 0 else "backward"), f"for {dz} mm")
        self.print_rt_target_pos()

    def change_azimuth(self, theta: float):
        self.robo.MoveJointsRel(theta, 0, 0, 0, 0, 0)

        print(
            "Rotate Joint 1",
            ("clockwise" if theta > 0 else "anticlockwise"),
            f"for {theta}°",
        )
        self.print_rt_target_pos()

    def change_gripper_state(self):
        if self.is_gripper_opened():
            self.robo.GripperClose()
            print("Gripper Opened!")
        else:
            self.robo.GripperOpen()
            print("Gripper Closed!")

        self.print_rt_target_pos()

    def invert_gripper(self, tilted_angle: float = None):
        d_theta = -180
        if self.is_gripper_inverted():
            d_theta = 180
        self.robo.MoveJointsRel(0, 0, 0, 0, 0, d_theta)

        print("Gripper Inverted")
        self.print_rt_target_pos()


	# NMR-station feature functions
    
    def move_to(self, there: Facility):
		# if the tube not above the high pos
        cur = self.get_cart_pos()
        dist_above_land = cur.z - TUBE_LENGTH - there.land_pos.z
        if dist_above_land < 5:
            self.change_vertical_height(5 - dist_above_land)
        
        self.move_pose(*there.start_pos)
    
    def place_tube(self, high_pos, low_pos, wait_for_picking: bool=False):
        if self.is_located_at(high_pos):
            self.move_lin(*low_pos)
        self.gripper_open()
        if not wait_for_picking: 
            self.move_lin(*high_pos)

    def pick_tube(self, high_pos, low_pos):
        if self.is_located_at(high_pos):
            self.move_lin(*low_pos)
        self.gripper_close()
        self.move_lin(*high_pos)