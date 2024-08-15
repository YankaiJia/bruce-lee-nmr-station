"""
This files defines the RobotArm class for the NMR-station, its methods include
 - wrapped functions from the mecademicpy library
 - The simplified cylindrical coordinate system movement function written by me
 - Automation features used in the NMR-station

KingLam Kwong, Yankai Jia
"""

# Third-party imports
import mecademicpy.robot as mdr

# Standard library imports
import time, math, copy, logging
from functools import wraps

# current code space imports
from .facility import *

# Constants
TUBE_LENGTH = 275
SAFE_POS = [0, -23.27248, -44.76893, 0, 68.04142, 0]
HIGH_Z = 345  # this is the Z position for arm when moving between spots.
CAROUSEL_RADIUS = 80
SPINSOLVE_ENTRANCE_HEIGHT = 203.5
LOG_PATH = "D:\\dropbox\\Dropbox\\robochem\\data\\loggings\\nmr_station\\"


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        # first item in the args, ie `args[0]` is `self`
        print(f"Function {func.__name__} Took {total_time:.4f} s")
        return result

    return timeit_wrapper


def setup_logger():
    # better logging format in console
    class CustomFormatter(logging.Formatter):
        grey, yellow, red, bold_red, reset = [
            "\x1b[38;20m",
            "\x1b[33;20m",
            "\x1b[31;20m",
            "\x1b[31;1m",
            "\x1b[0m",
        ]
        format = (
            "%(asctime)s-%(name)s-%(levelname)s-%(message)s (%(filename)s:%(lineno)d)"
        )
        FORMATS = {
            logging.DEBUG: grey + format + reset,
            logging.INFO: yellow + format + reset,
            logging.WARNING: yellow + format + reset,
            logging.ERROR: red + format + reset,
            logging.CRITICAL: bold_red + format + reset,
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    # create logger with 'main'
    logger = logging.getLogger("meca500")
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(LOG_PATH + "nmr_station.log")
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter("%(asctime)s-%(name)s-%(levelname)s-%(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(CustomFormatter())
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


class RobotArm:
    def __init__(self, running_vel="fast"):
        self.logger = setup_logger()
        self.running_vel = running_vel
        self.robo = mdr.Robot()
        self.robo.Connect(
            address="192.168.0.100",
            enable_synchronous_mode=True,
            disconnect_on_exception=False,
        )
        time.sleep(1)
        # self.config_robot_before_activate() # this needs to be run only once
        self.robo.ActivateAndHome()
        self.config_robot_after_activate()
        self.robo.WaitHomed()

        self.robo.SetRealTimeMonitoring("all")

        self.tube_status: int = (
            0  # 0: no tube. 1: with tube, topdown. -1: with tube, bottomup.
        )

        if self.is_gripper_gripping_item():
            self.tube_status = int(
                input("Tube is gripped.\nInput statue: 1(topdown)/-1(inverted)?")
            )
            if not self.tube_status in [0, -1, 1]:
                raise ValueError("tube_status is incorrect!")

        self.logger.info("Robotic arm is initiated!")

    def reset_robot(self):
        # self.robo.DeactivateRobot()
        # self.robo.Disconnect()
        self.robo.Connect(
            address="192.168.0.100",
            enable_synchronous_mode=True,
            disconnect_on_exception=False,
        )
        # self.config_robot_before_activate()
        self.robo.ActivateAndHome()
        self.robo.WaitHomed()
        self.robo.ResetError()
        self.robo.ResumeMotion()
        self.logger.info("Robot is reset!")

    def config_robot_before_activate(self):
        self.robo.DeactivateRobot()
        # set join 6 angle limit, this is to protect the cable of end effector
        self.robo.SetJointLimits(6, -200, 90)  # this needs to be done once.
        self.robo.SetJointLimitsCfg(1)
        self.logger.info("meca500 config done before activation.")

    def set_speed(self, limits: tuple):
        """How these limits are implemented for confining final velocity,
        see meca500 program manual: Figure14."""

        # joint space for: MoveJoints, MoveJointsRel, MovePose, MoveJump
        self.robo.SetJointVel(limits[0])  # range 0.001-150, default 25
        self.robo.SetJointAcc(limits[1])  # range 0.001-150, default 100
        # Cartesian space
        self.robo.SetCartLinVel(limits[2])  # range 0.001-5000, default 150
        self.robo.SetCartAngVel(limits[3])  # range 0.001-1000, default 45
        self.robo.SetCartAcc(limits[4])  # range 0.001-600, default 50
        # for both
        self.robo.SetJointVelLimit(limits[5])  # range 0.001-150, default 100
        # logging
        self.logger.debug(
            f"vel limits set to : {[limits[0],limits[1],limits[2],limits[3],limits[4],limits[5]]}"
        )

    def config_robot_after_activate(self, set_vel: str = "fast"):
        # short gripper
        self.robo.SetGripperRange(0, 4.9)
        # long gripper
        # self.robo.SetGripperRange(12, 30)
        limits = None
        if set_vel == "fast":
            limits = (75, 150, 500, 300, 100, 150)
        elif set_vel == "default":
            limits = (25, 100, 150, 45, 50, 100)
        self.set_speed(limits)

        self.logger.info("meca500 config done after activation.")

    # Robot Status Getter Functions

    def get_cart_pos(self):
        """This method takes short to execute, no worries about its delay"""
        return self.robo.GetRtTargetCartPos()

    def get_radial_distance(self, x: float, y: float):
        return math.sqrt(x * x + y * y)

    def find_delta_joint_1(self, cur_x, cur_y, tar_x, tar_y):
        dot_product = cur_x * tar_x + cur_y * tar_y
        cur_rad = self.get_radial_distance(cur_x, cur_y)
        tar_rad = self.get_radial_distance(tar_x, tar_y)
        delta_joint_1 = math.acos(dot_product / (cur_rad * tar_rad))

        direction = -1 if tar_y > cur_y * tar_x / cur_x else 1

        return direction * math.degrees(delta_joint_1)

    def find_delta_by_atan2(self, cur_x, cur_y, tar_x, tar_y):
        """see this link for more info on this method:
        https://stackoverflow.com/questions/14066933/direct-way-of-computing-the-clockwise-angle-between-two-vectors

        Using atan2(-det, -dot) + π will be better.
        """

        dot = cur_x * tar_x + cur_y * tar_y  # Dot product between [x1, y1] and [x2, y2]
        det = cur_x * tar_y - cur_y * tar_x  # Determinant
        angle = math.atan2(det, dot)  # atan2(y, x) or atan2(sin, cos)
        # print(angle)

        if cur_x < 0 and tar_x > 0 and cur_y > 0 and tar_y < 0:
            angle_with_y_axis_cur = math.atan(abs(cur_x / cur_y))
            angle_with_y_axis_tar = math.atan(abs(tar_x / tar_y))
            if angle_with_y_axis_cur > angle_with_y_axis_tar:
                angle = angle - 2 * np.pi

        elif cur_x > 0 and tar_x < 0 and cur_y < 0 and tar_y > 0:
            angle_with_y_axis_cur = math.atan(abs(cur_x / cur_y))
            angle_with_y_axis_tar = math.atan(abs(tar_x / tar_y))
            if angle_with_y_axis_cur < angle_with_y_axis_tar:
                angle = 2 * np.pi + angle

        return math.degrees(angle)

    def print_rt_target_pos(self):
        self.logger.debug(f"current_cart:{self.robo.GetRtTargetCartPos()}")
        self.logger.debug(f"current_joint:{self.robo.GetRtTargetJointPos()}")
        # print()

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
        return cur_j6 < -150

    def change_tube_inverted_status(self):
        assert self.tube_status in [-1, 1], "Arm is without tube!"
        self.tube_status = (-1) * self.tube_status

    def is_tube_inverted(self):
        return self.tube_status == -1

    def get_gripper_force(self):
        force = self.robo.GetRobotRtData().rt_gripper_force.data[0]
        return float(force)

    def is_gripper_gripping_item(self):
        # when gripping, the applied force is about -40 N.
        if self.get_gripper_force() < -20:
            return True

        return False

    def is_arm_at_carousel(self, carousel_radius=CAROUSEL_RADIUS):

        cur_cart = self.get_cart_pos()
        cur_radius = abs((cur_cart[0] ** 2 + cur_cart[1] ** 2) ** 0.5)
        if math.isclose(cur_radius, CAROUSEL_RADIUS, rel_tol=0.1):
            return True
        else:
            return False

    def go_to_safe(self):

        safe_position = SAFE_POS
        if input("CAUTION! Arm going to SAFE_POS. COLLISION MAY OCCUR! [y/n]?") in [
            "yes",
            "YES",
            "Y",
            "y",
        ]:

            # time.sleep(2)
            if input("Reconfirm going to SAFE_POS. COLLISION MAY OCCUR! [y/n]?") in [
                "yes",
                "YES",
                "Y",
                "y",
            ]:
                self.robo.MoveJoints(
                    safe_position[0],
                    safe_position[1],
                    safe_position[2],
                    safe_position[3],
                    safe_position[4],
                    safe_position[5],
                )

        else:
            print("Robot did not go to SAFE_POS.")
            return

    def zero(self):
        """Be VERY careful when running this method. Collision may occur.
        Use retract_to_carousel() and then go_to_safe(), instead."""

        zero_position = [0, 0, 0, 0, 0, 0]
        if input(
            "CAUTION! Arm going to (0,0,0,0,0,0). COLLISION MAY OCCUR! [y/n]?"
        ) in ["yes", "YES", "Y", "y"]:
            time.sleep(2)
            if input(
                "Reconfirm going to (0,0,0,0,0,0). COLLISION MAY OCCUR! [y/n]?"
            ) in ["yes", "YES", "Y", "y"]:
                self.robo.MoveJoints(
                    zero_position[0],
                    zero_position[1],
                    zero_position[2],
                    zero_position[3],
                    zero_position[4],
                    zero_position[5],
                )

        else:
            print("Robot did not go to (0,0,0,0,0).")
            return

    # Wrapped Built-in Movement Functions

    def move_pose(
        self,
        x: float,
        y: float,
        z: float,
        alpha: float,
        beta: float,
        gamma: float,
    ):
        self.robo.MovePose(x, y, z, alpha, beta, gamma)

    def move_lin(
        self,
        x: float,
        y: float,
        z: float,
        alpha: float,
        beta: float,
        gamma: float,
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
        j1: float,
        j2: float,
        j3: float,
        j4: float,
        j5: float,
        j6: float,
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

    def refresh_j4(self):
        """This function is for avoiding singularity when using MoveLin for large displacement.
        It is done by rounding j4 and j6 to zero when they are close to zero.
        This method needs to be used with care, bugs may occur."""

        cur_joints = copy.deepcopy(self.robo.GetRtTargetJointPos())

        if (
            math.isclose(cur_joints[3], 0, abs_tol=0.5)
            and math.isclose(cur_joints[5], 0, abs_tol=0.5)
            and cur_joints[5] != 0
            and cur_joints[3] != 0
            and math.isclose(cur_joints[3] + cur_joints[5], 0, abs_tol=0.3)
        ):

            cur_joints[3] = 0
            cur_joints[5] = 0
            self.move_joints(*cur_joints)

    # Simplified System Movement Functions.
    # Complex movements should be decomposed to the following
    # three methods: change_vertica_height(), chang_radial_distance() and change_azimuth().

    def change_vertical_height(self, dist: float):
        self.robo.MoveLinRelWrf(0, 0, dist, 0, 0, 0)

        direction = "up" if dist > 0 else ("down" if dist < 0 else "nothing")
        self.logger.debug(f"vertically moving {direction} for {abs(dist)} mm.")
        self.print_rt_target_pos()

    def change_radial_distance(self, dz: float):
        self.robo.MoveLinRelTrf(0, 0, dz, 0, 0, 0)

        self.logger.debug(
            "Moving" + ("forward" if dz > 0 else "backward") + f"for {dz} mm"
        )
        self.print_rt_target_pos()

    def change_azimuth(self, theta: float):
        self.robo.MoveJointsRel(theta, 0, 0, 0, 0, 0)

        self.logger.debug(
            "Rotate Joint 1"
            + ("clockwise" if theta > 0 else "anticlockwise")
            + f"for {theta}°"
        )
        self.print_rt_target_pos()

    def change_gripper_state(self):
        if self.is_gripper_opened():
            self.robo.GripperClose()
            # logger.debug("Gripper Opened!")
        else:
            self.robo.GripperOpen()
            # logger.debug("Gripper Closed!")
            self.tube_status = 0

        self.print_rt_target_pos()

    def invert_gripper(self):

        j6 = self.robo.GetRtTargetJointPos()[5]

        if math.isclose(j6, 0, abs_tol=0.1):  # j6 is at 0
            self.robo.MoveJointsRel(0, 0, 0, 0, 0, -180)
        elif math.isclose(j6, -180, abs_tol=0.1):  # j6 is at 0
            self.robo.MoveJointsRel(0, 0, 0, 0, 0, 180)
        else:
            raise ValueError(f"Joint 6 is at bad angle: {j6}")

        # update tube status
        if self.is_gripper_gripping_item():
            self.tube_status = self.tube_status * (-1)

    def get_carousel_pos(self, carousel_radius: float, current_pos: tuple):

        pos_here = copy.deepcopy(current_pos)
        x0, y0 = pos_here[0], pos_here[1]

        x = (carousel_radius**2 / (y0**2 / x0**2 + 1)) ** 0.5
        x = abs(x) if pos_here[0] > 0 else -abs(x)  # make the sign the same

        y = (y0 / x0) * x

        return tuple((x, y, pos_here[2], pos_here[3], pos_here[4], pos_here[5]))

    def go_to_high_z(self, high_z: float = HIGH_Z):

        current_cart = self.get_cart_pos()
        # move arm to high_z: 352
        d_z = high_z - current_cart[2]
        self.robo.MoveLinRelWrf(0, 0, d_z, 0, 0, 0)

    def retract_to_carousel(
        self, carousel_radius: float = CAROUSEL_RADIUS, high_z: float = HIGH_Z
    ):

        cur_z = self.get_cart_pos()[2]
        d_z = high_z - cur_z
        if not math.isclose(d_z, 0, abs_tol=0.01):
            self.change_vertical_height(d_z)

        cur_cart = self.get_cart_pos()
        dr = carousel_radius - self.get_radial_distance(cur_cart[0], cur_cart[1])
        if not math.isclose(dr, 0, abs_tol=0.01):
            self.change_radial_distance(dr)

    def move_inside_carousel(
        self, target_cart: CartPos, carousel_radius: float = CAROUSEL_RADIUS
    ):

        cur_cart = self.get_cart_pos()
        cur_x, cur_y = cur_cart[0], cur_cart[1]
        tar_x, tar_y = target_cart[0], target_cart[1]

        dr1 = carousel_radius - self.get_radial_distance(cur_x, cur_y)
        if not math.isclose(dr1, 0, abs_tol=0.01):
            self.change_radial_distance(dr1)

        # d_j1 = self.find_delta_joint_1(cur_x, cur_y, tar_x, tar_y)
        d_j1 = self.find_delta_by_atan2(cur_x, cur_y, tar_x, tar_y)

        self.change_azimuth(d_j1)

        dr2 = self.get_radial_distance(tar_x, tar_y) - carousel_radius
        if not math.isclose(dr2, 0, abs_tol=0.01):
            self.change_radial_distance(dr2)

    def go_to_high_location(self, target_cart):

        self.print_rt_target_pos()

        assert target_cart[2] >= HIGH_Z, (
            f"Target cart NOT high enough. "
            f"\ntarget_cart[2]:{target_cart[2]}. "
            f"HIGH_Z: {HIGH_Z}"
        )

        if not self.is_arm_at_carousel():
            self.retract_to_carousel()
            print("Retracted to carousel")
            self.print_rt_target_pos()

        target_carousel_cart = self.get_carousel_pos(
            carousel_radius=CAROUSEL_RADIUS, current_pos=target_cart
        )
        self.logger.debug(f"after get_carousel_pos: {target_carousel_cart}")
        self.print_rt_target_pos()

        self.move_inside_carousel(target_carousel_cart)

        self.logger.debug(f"target {target_cart} \n current {self.get_cart_pos()}")

        # for this orientation, gripper should be bottomup/inverted
        if (
            math.isclose(target_cart[3], -90, abs_tol=0.1)
            and math.isclose(target_cart[5], -90, abs_tol=0.1)
            and not self.is_gripper_inverted()
        ):
            self.invert_gripper()
            print(f"flipped @{time.time()}")
        # for this orientation, gripper should be topdown/upright
        if (
            math.isclose(target_cart[3], -90, abs_tol=0.1)
            and math.isclose(target_cart[5], 90, abs_tol=0.1)
            and self.is_gripper_inverted()
        ):
            self.invert_gripper()
            self.logger.debug(f"Gripper flipped @{time.time()}")

        # change z with respect to wrf
        cur_cart = self.get_cart_pos()
        dz = target_cart[2] - cur_cart[2]
        if not math.isclose(dz, 0, abs_tol=0.01):
            self.change_vertical_height(dz)

        # change radial distance.
        cur_cart = self.get_cart_pos()
        cur_rad_dist = self.get_radial_distance(cur_cart[0], cur_cart[1])
        target_rad_dist = self.get_radial_distance(target_cart[0], target_cart[1])
        self.logger.debug(f"cur_cart:{cur_cart}.\n targe_cart:{target_cart}")
        self.change_radial_distance(target_rad_dist - cur_rad_dist)
        self.print_rt_target_pos()

    def pick_tube(
        self, location, target_tube_status: int = 1, wait_after_place: float = 0.2
    ):

        assert (
            not self.is_gripper_gripping_item()
        ), "Gripper is already gripping item, action aborted!"
        assert target_tube_status in [-1, 1], "Tube status is incorrect!"

        if location in [Washer1, Washer2]:
            target_tube_status = -1

        target_cart_high, target_cart_low = location.pos["high"], location.pos["low"]

        if not self.is_arm_at_carousel():
            self.retract_to_carousel()
        time.sleep(0.2)

        self.go_to_high_location(target_cart_high)
        self.refresh_j4()

        if not self.is_gripper_opened():
            self.change_gripper_state()

        cur_cart = self.get_cart_pos()
        d_z = target_cart_low[2] - cur_cart[2]
        self.change_vertical_height(d_z)
        self.change_gripper_state()
        time.sleep(wait_after_place)

        self.refresh_j4()

        cur_cart = self.get_cart_pos()
        d_z = target_cart_high[2] - cur_cart[2]
        self.change_vertical_height(d_z)
        time.sleep(wait_after_place)

        self.retract_to_carousel()

        # make sure tube is gripped.
        if not self.is_gripper_gripping_item():
            raise ValueError("No item is picked up for pick_tube(), please check!")
        # update tube status
        self.tube_status = target_tube_status

        self.logger.debug("Pick tube done!")

    def place_tube(self, location, wait_after_place: float = 0.5):

        assert not self.is_gripper_opened(), "Gripper is open! Abort!"

        if location in [Washer1, Washer2]:
            assert self.tube_status == -1, "When put to washers, tube must be inverted!"
        if location in [Tube1, Tube2, Tube3, Tube4]:
            assert self.tube_status == 1, (
                "When put to tube stands, tube must be upright!"
                f"\n current tube status: {self.tube_status}"
            )

        if not self.is_gripper_gripping_item():
            raise ValueError("Gripper is not gripping item, action aborted!")

        target_cart_high, target_cart_low = location.pos["high"], location.pos["low"]

        if not self.is_arm_at_carousel():
            self.retract_to_carousel()

        self.go_to_high_location(target_cart_high)
        self.refresh_j4()

        cur_cart = self.get_cart_pos()
        d_z = target_cart_low[2] - cur_cart[2]

        # self.move_lin(*target_cart_low)
        self.change_vertical_height(d_z)
        self.change_gripper_state()
        time.sleep(wait_after_place)
        self.refresh_j4()
        # self.move_lin(*target_cart_high)
        correction_factor = 0.02  # correct the tube into place
        self.change_vertical_height(-d_z * correction_factor)
        time.sleep(wait_after_place)
        self.change_vertical_height(-d_z * (1 - correction_factor))
        self.retract_to_carousel()

        if self.is_gripper_gripping_item():
            raise ValueError("Gripper is still gripping item, please check!")

        # mark robotic arm not gripping tube
        self.tube_status = 0

        self.logger.debug("Place tube done!")

    @timeit
    def flip_tube(self, mode: str):

        if mode == "topdown_to_bottomup":
            assert self.tube_status == 1, "Tube musted be topdown!"
            place_loc = Flip_stand_gripper_bottomup_tube_bottomup
            pick_loc = Flip_stand_gripper_topdown_tube_bottomup

        elif mode == "bottomup_to_topdown":
            assert self.tube_status == -1, "Tube musted be bottomup!"
            place_loc = Flip_stand_gripper_topdown_tube_bottomup
            pick_loc = Flip_stand_gripper_bottomup_tube_bottomup

        else:
            raise ValueError(f"flip_tube mode is incorrect: {mode}!")

        # move arm to carousel
        if not self.is_arm_at_carousel():
            self.retract_to_carousel()

        self.place_tube(place_loc, wait_after_place=0.5)
        self.pick_tube(pick_loc, target_tube_status=-1)

        if self.is_gripper_inverted():
            self.logger.debug("Gripper is inverted!")
            self.invert_gripper()

        time.sleep(0.1)

    def tilted_remove_tube(self):
        self.move_joints_rel(j1=6, j6=-7)
        self.change_radial_distance(-7)
        self.move_joints_rel(j1=10, j6=-10)
        self.change_radial_distance(-10)
        self.move_joints_rel(j1=10, j6=-10)
        # self.change_vertical_height(47)
        self.change_vertical_height(34)
        self.move_joints_rel(j6=27)

    def tilted_insert_tube(self):
        self.move_joints_rel(j6=-27)
        # robo.change_vertical_height(-47)
        self.change_vertical_height(-34)
        self.move_joints_rel(j1=-10, j6=10)
        self.change_radial_distance(10)
        self.move_joints_rel(j1=-10, j6=10)
        self.change_radial_distance(7)
        self.move_joints_rel(j1=-6, j6=7)

    def place_tube_to_spinsolve(
        self, height_from_entrance: float = SPINSOLVE_ENTRANCE_HEIGHT
    ):

        assert self.tube_status == 1, "Tube status is incorrect!"
        assert self.is_gripper_gripping_item(), "Gripper status is incorrect"

        entrance_point = Spinsolve.pos["high"]
        self.go_to_high_location(entrance_point)
        self.tilted_insert_tube()
        self.change_vertical_height(-height_from_entrance)
        self.change_gripper_state()
        self.change_vertical_height(height_from_entrance)
        self.tilted_remove_tube()
        self.retract_to_carousel()

        assert not self.is_gripper_gripping_item(), "Gripper status is incorrect"
        self.tube_status = 0

    def pick_tube_from_spinsolve(
        self, height_from_entrance: float = SPINSOLVE_ENTRANCE_HEIGHT
    ):

        assert self.tube_status == 0, "Tube status is incorrect!"
        assert not self.is_gripper_gripping_item(), "Gripper status is incorrect"

        entrance_point = Spinsolve.pos["high"]
        self.go_to_high_location(entrance_point)
        self.tilted_insert_tube()
        self.change_vertical_height(-height_from_entrance)
        self.change_gripper_state()
        self.change_vertical_height(height_from_entrance)
        self.tilted_remove_tube()
        self.retract_to_carousel()

        assert self.is_gripper_gripping_item(), "Gripper status is incorrect"
        self.tube_status = 1

    @timeit
    def test(self, washer=Washer1):
        self.pick_tube(Tube1)
        self.flip_tube("topdown_to_bottomup")
        self.place_tube(washer)
        self.pick_tube(washer)
        self.flip_tube("bottomup_to_topdown")
        self.place_tube(Tube1)

    @timeit
    def test_sp(self, tube=Tube1, washer=Washer1):
        self.pick_tube(tube)
        self.place_tube_to_spinsolve()
        time.sleep(2)
        self.pick_tube_from_spinsolve()
        self.flip_tube("topdown_to_bottomup")
        self.place_tube(washer)
        time.sleep(3)
        self.pick_tube(washer)
        self.flip_tube("bottomup_to_topdown")
        self.place_tube(tube)


if __name__ == "__main__":
    r = RobotArm()
