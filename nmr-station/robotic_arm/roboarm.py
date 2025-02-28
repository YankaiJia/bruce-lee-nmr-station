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
import time, math, copy, logging, os, sys
from functools import wraps

sys.path.append(os.path.abspath(os.path.pardir))

# current code space imports
from settings import (
    ROBOT_ARM_HOST,
    ROBOT_ARM_LOG_PATH,
    TUBE_LENGTH,
    SAFE_POS,
    HIGH_Z,
    CAROUSEL_RADIUS
)
if __name__ == '__main__':
    from facility import *
else:
    from .facility import *


def setup_logger(logging_level=logging.INFO):
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
    logger = logging.getLogger("roboarm.py")
    logger.setLevel(logging_level)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(ROBOT_ARM_LOG_PATH + "nmr_station.log")
    fh.setLevel(logging_level)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging_level)
    # create formatter and add it to the handlers
    formatter = logging.Formatter("%(asctime)s-%(name)s-%(levelname)s-%(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(CustomFormatter())
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

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

def log_exception(func):
    @wraps(func)
    def log_exception_wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except:
            setup_logger().exception(f'---Got exception in roboarm.py at function: {func.__name__}---')
            raise
        return result
    return log_exception_wrapper


class RobotArm:
    def __init__(self, running_vel="default",
                 is_check_item_gripping: bool = True):

        self.logger = setup_logger(logging.INFO)
        self.running_vel = running_vel
        self.facilities = load_facilities()
        self.robo = mdr.Robot()
        self.robo.Connect(
            address="192.168.0.100",
            enable_synchronous_mode=True,
            disconnect_on_exception=True,)
        # self.robo.SetMonitoringInterval(1)
        print('Robot connected!')

        self.robo.ActivateRobot()
        self.robo.Home()
        self.robo.WaitHomed()

        self.config_robot_after_activate() # this needs to be run only once

        self.robo.SetRealTimeMonitoring("all")

        self.tube_status: int = 0 # 0: no tube. 1: with tube, topdown. -1: with tube, bottomup.
        if self.is_gripper_gripping_item():
            self.tube_status = int(input("A tube is gripped.\nInput statue: 1(upright)/-1(inverted)?"))
            if not self.tube_status in [0, -1, 1]:
                raise ValueError("tube_status is incorrect!")

        # self.robo.StartMovementMonitor()

        self.logger.info("Robotic arm is initiated!")

        self.is_check_item_gripping = is_check_item_gripping

    def reset_robot(self):
        # self.robo.DeactivateRobot()
        # self.robo.Disconnect()
        self.robo.Connect(
            address=ROBOT_ARM_HOST,
            enable_synchronous_mode=True,
            disconnect_on_exception=True,
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
        self.robo.SetJointLimits(6, -90, 200)  # this needs to be done once.
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
        self.robo.SetGripperRange(0, 5.3)
        # long gripper
        # self.robo.SetGripperRange(12, 30)
        limits = None
        if set_vel == "fast":
            limits = (100, 150, 180, 200, 100, 150)
            print('Will set speed as fast')
        elif set_vel == "default":
            limits = (25*0.8, 100*0.8, 100*0.8, 45*0.8, 50*0.8, 100*0.8)
            print('Will set speed as default')
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

    def angle_between_two_vectors(self, x1, y1, x2, y2):

        if np.allclose((x1, y1), (x2, y2), atol=0.001):
            return 0
        # find the angle between two vectors. This angle will be sent to the arm for rotating.
        # During rotation, angle needs to be in the range(-170, +170)
        def angle_with_x_axis(x, y):
            cos = x / np.sqrt((x ** 2 + y ** 2))
            theta = np.degrees(np.arccos(cos))
            return theta if y >= 0 else 360 - theta

        theta_A = angle_with_x_axis(x1, y1)
        theta_B = angle_with_x_axis(x2, y2)

        if (theta_A <= 185 and theta_A >= 175) or (theta_B <= 185 and theta_B >= 175):
            raise ValueError("Arm is wrong position!")

        if (theta_A <= 175) and (theta_B >= 185):
            result = (theta_B - theta_A) - 360
        elif (theta_A >= 175) and (theta_B <= 185):
            result = 360 + (theta_B - theta_A)
        else:
            result = theta_B - theta_A

        return float(result)

    def print_rt_target_pos(self):
        self.logger.debug(f"current_cart:{self.robo.GetRtTargetCartPos()}")
        self.logger.debug(f"current_joint:{self.robo.GetRtTargetJointPos()}")

        # print(f"current_cart:{self.robo.GetRtTargetCartPos()}")
        # print(f"current_joint:{self.robo.GetRtTargetJointPos()}")

    # def is_located_at(self, tar_pos: CartPos):
    #     cur_pos = self.get_cart_pos()
    #     rt = True
    #     rt &= round(cur_pos.x, 2) == round(tar_pos.x, 2)
    #     rt &= round(cur_pos.y, 2) == round(tar_pos.y, 2)
    #     rt &= round(cur_pos.z, 2) == round(tar_pos.z, 2)
    #     rt &= round(cur_pos.alpha, 2) == round(tar_pos.alpha, 2)
    #     rt &= round(cur_pos.beta, 2) == round(tar_pos.beta, 2)
    #     rt &= round(cur_pos.gamma, 2) == round(tar_pos.gamma, 2)
    #
    #     return rt

    def is_located_at(self, loc_coord: tuple, coord_num:int = 6):
        '''
        if coord_num is 6, check all coordinates
        if coord_num is 2, check only x and y coordinates.
        '''
        cur_cart = self.get_cart_pos()
        if np.allclose(cur_cart[:coord_num], loc_coord[:coord_num], atol=0.05):
            return True
        else:
            return False

    def is_gripper_opened(self):
        return self.robo.GetRtGripperState().opened

    def is_gripper_inverted(self):
        cur_j6 = self.robo.GetRtTargetJointPos()[5]
        return cur_j6 > 150

    def change_tube_inverted_status(self):
        assert self.tube_status in [-1, 1], "Arm is without tube!"
        self.tube_status = (-1) * self.tube_status

    def is_tube_inverted(self):
        return self.tube_status == -1

    def get_gripper_force(self):
        force = self.robo.GetRobotRtData().rt_gripper_force.data[0]
        # force = self.robo.GetRtGripperForce()

        # self.robo.SetRealTimeMonitoring(2321)
        return float(force)



    def is_gripper_gripping_item(self):

        time.sleep(0.2)

        # when gripping, the applied force is about -40 N.
        if self.get_gripper_force() < -10:
            return True

        return False

    def is_arm_at_carousel(self, carousel_radius=CAROUSEL_RADIUS):

        cur_cart = self.get_cart_pos()
        cur_radius = abs((cur_cart[0] ** 2 + cur_cart[1] ** 2) ** 0.5)
        if math.isclose(cur_radius, CAROUSEL_RADIUS, rel_tol=0.1):
            return True
        else:
            return False

    def go_to_safe(self, mode:str = 'manual'):

        safe_position = SAFE_POS

        if mode == 'manual':
            if not input("CAUTION! Arm going to SAFE_POS. COLLISION MAY OCCUR! [y/n]?") in ["yes","YES","Y","y",]:
                print("Robot did not go to SAFE_POS.")
                return
            if not input("Reconfirm going to SAFE_POS. COLLISION MAY OCCUR! [y/n]?") in ["yes", "YES", "Y", "y", ]:
                print("Robot did not go to SAFE_POS.")
                return
        elif mode == 'auto':
            print('Arm going to safe position....')
            time.sleep(1)
        else:
            raise Exception('mode incorrect!')


        self.retract_to_carousel()
        self.robo.MoveJoints(*safe_position)


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

        # The arm frequently stops on this commend, raising the
        # error: No command rx thread, are you in monitor mode?
        # I do not know the reason for this. So, it is replaced with MoveJoints
        # self.robo.MoveJointsRel(j1, j2, j3, j4, j5, j6)

        # get current joints
        curt_joints = self.robo.GetRtTargetJointPos()
        target_joints = np.array(curt_joints) + np.array([j1, j2, j3, j4, j5, j6])
        self.robo.MoveJoints(*target_joints)

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

        # self.robo.MoveJointsRel(theta, 0, 0, 0, 0, 0)
        self.move_joints_rel(theta, 0, 0, 0, 0, 0)

        self.logger.debug(
            "Rotate Joint 1"
            + ("clockwise" if theta > 0 else "anticlockwise")
            + f"for {theta}°"
        )
        self.print_rt_target_pos()

    def change_gripper_state(self):
        if self.is_gripper_opened():
            self.robo.GripperClose()
            self.robo.WaitGripperMoveCompletion(timeout=3)
            # logger.debug("Gripper Opened!")
        else:
            self.robo.GripperOpen()
            self.robo.WaitGripperMoveCompletion(timeout=3)
            # logger.debug("Gripper Closed!")
            self.tube_status = 0

        self.print_rt_target_pos()

    def invert_gripper(self):

        j6 = self.robo.GetRtTargetJointPos()[5]

        if math.isclose(j6, 0, abs_tol=0.2):  # j6 is at 0
            self.move_joints_rel(0, 0, 0, 0, 0, 180)

        elif math.isclose(j6, 180, abs_tol=0.2):  # j6 is at 0
            self.move_joints_rel(0, 0, 0, 0, 0, -180)
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

    @log_exception
    def retract_to_carousel(self, carousel_radius: float = CAROUSEL_RADIUS, high_z: float = HIGH_Z):

        j1 = self.robo.GetRtTargetJointPos()[0]
        if j1 < -65 and j1> -140:
            self.logger.info('Please retract arm manually.')
            return

        for key, facility in self.facilities.items():
            # check if arm is at one of the facilities, by checking x and y.
            # if yes, overwrite high_z
            self.logger.debug(self.get_cart_pos())
            if self.is_located_at(loc_coord=facility.pos['high'], coord_num=2):
                self.logger.debug(f'Arm at a facility! {facility.name}-{facility.pos}')
                high_z = facility.pos['high'][2] # z height
                break

        cur_z = self.get_cart_pos()[2]
        d_z = high_z - cur_z

        if not math.isclose(d_z, 0, abs_tol=0.05):
            self.logger.debug(f'high_z: {high_z}')
            self.logger.debug(f'cur_z: {cur_z}')
            self.logger.debug(f'd_z: {d_z}')
            self.change_vertical_height(d_z)

        cur_cart = self.get_cart_pos()
        dr = carousel_radius - self.get_radial_distance(cur_cart[0], cur_cart[1])
        if not math.isclose(dr, 0, abs_tol=0.05):
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
        d_j1 = self.angle_between_two_vectors(cur_x, cur_y, tar_x, tar_y)

        # print(f'cur_x, cur_y, tar_x, tar_y: {cur_x},{cur_y},{tar_x},{tar_y}')
        # print(f'angle between two vectors: {d_j1}')

        self.change_azimuth(d_j1)

        dr2 = self.get_radial_distance(tar_x, tar_y) - carousel_radius
        if not math.isclose(dr2, 0, abs_tol=0.01):
            self.change_radial_distance(dr2)

    def go_to_high_location(self, target_cart):

        self.print_rt_target_pos()
        self.logger.debug('####before move')

        assert target_cart[2] >= HIGH_Z, (
            f"Target cart NOT high enough. "
            f"\ntarget_cart[2]:{target_cart[2]}. "
            f"HIGH_Z: {HIGH_Z}")

        if self.is_located_at(target_cart):
            self.logger.info('meca500 already at target location: go_to_high_location.')
            return

        if not self.is_arm_at_carousel():
            self.retract_to_carousel()
            self.logger.debug('#### after retract_to_carousel')
            self.print_rt_target_pos()

        target_carousel_cart = self.get_carousel_pos(
            carousel_radius=CAROUSEL_RADIUS, current_pos=target_cart
        )
        self.logger.debug(f"after get_carousel_pos: {target_carousel_cart}")

        self.logger.debug('#### before moving inside carousel')
        self.print_rt_target_pos()
        self.move_inside_carousel(target_carousel_cart)
        self.logger.debug('#### after moving inside carousel')
        self.logger.debug(f"target {target_cart} \n current {self.get_cart_pos()}")

        # change z with respect to wrf
        cur_cart = self.get_cart_pos()
        dz = target_cart[2] - cur_cart[2]
        if not math.isclose(dz, 0, abs_tol=0.01):
            self.logger.debug('###before change vertical height')
            self.change_vertical_height(dz)
            self.logger.debug('###after change vertical height')


        # change radial distance.
        cur_cart = self.get_cart_pos()
        cur_rad_dist = self.get_radial_distance(cur_cart[0], cur_cart[1])
        target_rad_dist = self.get_radial_distance(target_cart[0], target_cart[1])
        self.logger.debug('###before change radial distance')
        self.logger.debug(f"cur_cart:{cur_cart}.\n targe_cart:{target_cart}")
        self.change_radial_distance(target_rad_dist - cur_rad_dist)
        self.logger.debug('###after change radial distance')
        self.print_rt_target_pos()

    @log_exception
    def pick_tube(self, location:Facility,
                  target_tube_status: int = 1,
                  wait_after_place: float = 0.2,
                  is_retract: bool = True):

        self.logger.info(f"Executing pick_tube({location.name}) at {time.time()}")

        assert not self.is_gripper_gripping_item(), "Gripper is already gripping item, action aborted!"
        assert target_tube_status in [-1, 1], "Tube status is incorrect!"

        if ('tubes' in location.name
            or 'spinsolve' in location.name
            or 'washer' in location.name):
            assert not self.is_gripper_inverted(), 'gripper should not be inverted.'

        if location in [self.facilities['washer1'],
                        self.facilities['washer2'],
                        self.facilities['dryer'],
                        self.facilities['flip_stand_waste_gripper_upright']]:
            target_tube_status = -1

        target_cart_high, target_cart_low = location.pos["high"], location.pos["low"]

        if not self.is_located_at(target_cart_high):
            if not self.is_arm_at_carousel():
                self.retract_to_carousel()
                time.sleep(0.1)
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

        # time.sleep(2)

        if is_retract:
            self.retract_to_carousel()

        if self.is_check_item_gripping:
            # make sure a tube is gripped.
            if not self.is_gripper_gripping_item():
                self.logger.debug(f'gripper force: {self.get_gripper_force()}')
                raise ValueError('No item is picked up for pick_tube(), please check!')

        # update tube status
        self.tube_status = target_tube_status

        self.logger.debug("Pick tube done!")

    @log_exception
    def place_tube(self, location, wait_after_place: float = 0.2):

        self.logger.info(f"Executing place_tube({location.name}) at {time.time()}")

        assert not self.is_gripper_opened(), "Gripper is open! Abort!"

        if location in [self.facilities['washer1'],
                        self.facilities['washer2'],
                        self.facilities['dryer'],
                        self.facilities['flip_stand_waste_gripper_upright']]:
            assert self.tube_status == -1, "Tube must be inverted!"

        if location in [self.facilities['tube1'],
                        self.facilities['tube2'],
                        self.facilities['tube3'],
                        self.facilities['tube4']]:
            assert self.tube_status == 1, (
                "When put to tube stands, tube must be upright!"
                f"\n current tube status: {self.tube_status}")

        if self.is_check_item_gripping:
            if not self.is_gripper_gripping_item():
                raise ValueError("Gripper is not gripping item, action aborted!")

        target_cart_high, target_cart_low = location.pos["high"], location.pos["low"]


        if not self.is_located_at(target_cart_high):
            # print(self.get_cart_pos())
            # print(target_cart_high)
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

        if self.is_check_item_gripping:
            if self.is_gripper_gripping_item():
                raise ValueError("Gripper is still gripping item, please check!")

        # mark robotic arm not gripping tube
        self.tube_status = 0

        self.logger.debug("Place tube done!")

    @timeit
    @log_exception
    def flip_tube(self, location:str = 'flip_stand_waste', is_pick:bool = True):

        assert location in ['flip_stand_waste',
                            'flip_stand_clean'], 'Location for flip_tube() is incorrect!'

        assert self.tube_status in [-1, 1], 'Incorrect tube status.'

        self.logger.info(f"Executing flip_tube({location}) at {time.time()}")


        # move arm to carousel
        if not self.is_arm_at_carousel():
            self.retract_to_carousel()

        if self.tube_status == 1: # flip mode: upright_to_bottomup
            place_loc = self.facilities[f'{location}_gripper_inverted']
            pick_loc = self.facilities[f'{location}_gripper_upright']
            if not self.is_gripper_inverted():
                self.change_azimuth(5)
                self.invert_gripper()
            tube_status_after_flip = -1

        elif self.tube_status == -1: # flip mode: bottomup to upright
            place_loc = self.facilities[f'{location}_gripper_upright']
            pick_loc = self.facilities[f'{location}_gripper_inverted']
            tube_status_after_flip = 1

        else:
            raise ValueError(f"Tube status is incorrect!")

        self.place_tube(place_loc, wait_after_place=0.5)
        self.invert_gripper()
        if is_pick:
            self.pick_tube(pick_loc)

        if self.is_gripper_inverted() and self.is_gripper_gripping_item():
            # self.change_azimuth(5)
            self.invert_gripper()
            self.logger.debug("Gripper is inverted!")

        if self.is_gripper_gripping_item():
            self.logger.debug('Tube status is multiplied by -1.')
            self.tube_status = tube_status_after_flip

    @log_exception
    def tilted_remove_tube(self):
        self.logger.info(f"Executing tilted_remove_tube() at {time.time()}")

        # if not self.is_located_at(self.facilities['spinsolve_insert_vertical'].pos['high']):
        #     self.logger.warning('meca500 location is incorrect for titled_remove_tube()!')
        #     return
        self.change_radial_distance(1.25)
        self.move_joints_rel(j1=6, j6=-7)
        self.change_radial_distance(-7)
        self.move_joints_rel(j1=10, j6=-10)
        self.change_radial_distance(-10)
        self.move_joints_rel(j1=10, j6=-10)
        # self.change_vertical_height(47)
        self.change_vertical_height(34)
        self.move_joints_rel(j6=27)

    @log_exception
    def tilted_insert_tube(self):
        self.logger.info(f"Executing tilted_remove_tube() at {time.time()}")

        # if not self.is_located_at(self.facilities['spinsolve'].pos['high']):
        #     self.logger.warning('meca500 is not at spinsolve entrance point!')
        #     return

        self.move_joints_rel(j6=-27)
        # robo.change_vertical_height(-47)
        self.change_vertical_height(-34)
        self.move_joints_rel(j1=-10, j6=10)
        self.change_radial_distance(10)
        self.move_joints_rel(j1=-10, j6=10)
        self.change_radial_distance(7)
        self.move_joints_rel(j1=-6, j6=7)
        self.change_radial_distance(-1.25)

        # go to self.facilities['spinsolve'].pos['high']
        # cart: 6.95207, -229.91789, 316.58462, 90, 1.73193, -90
        # angles: -88.26807, 20.27291, -28.58442, 0, 8.31151, 0
        # self.move_joints(-88.26807, 20.27291, -28.58442, 0, 8.31151, 0)

    @log_exception
    def place_tube_to_spinsolve(self, delay:float = 0.5):

        self.logger.info(f"Executing place_tube_to_spinsolve() at {time.time()}")


        vertical_height_for_insert = self.facilities['spinsolve_insert_vertical'].pos['high'][2]- \
                                     self.facilities['spinsolve_insert_vertical'].pos['low'][2]

        assert self.tube_status == 1, "Tube status is incorrect!"
        assert self.is_gripper_gripping_item(), "Gripper status is incorrect"

        if not self.is_located_at(
                self.facilities['spinsolve_insert_vertical'].pos['high']):
            entrance_point = self.facilities['spinsolve'].pos["high"]
            self.go_to_high_location(entrance_point)
            self.tilted_insert_tube()

        self.change_vertical_height(-vertical_height_for_insert)
        self.change_gripper_state()
        self.change_vertical_height(vertical_height_for_insert)
        time.sleep(delay)
        self.tilted_remove_tube()
        self.retract_to_carousel()

        assert not self.is_gripper_gripping_item(), "Gripper status is incorrect"
        self.tube_status = 0

    @log_exception
    def pick_tube_from_spinsolve(self):

        self.logger.info(f"Executing pick_tube_from_spinsolve() at {time.time()}")


        vertical_height_for_insert = self.facilities['spinsolve_insert_vertical'].pos['high'][2]- \
                                     self.facilities['spinsolve_insert_vertical'].pos['low'][2]

        assert self.tube_status == 0, "Tube status is incorrect!"

        assert not self.is_gripper_gripping_item(), "Gripper status is incorrect"

        if not self.is_located_at(
                self.facilities['spinsolve_insert_vertical'].pos['high']):
            entrance_point = self.facilities['spinsolve'].pos["high"]
            self.go_to_high_location(entrance_point)
            self.tilted_insert_tube()

        self.change_vertical_height(-vertical_height_for_insert)
        self.change_gripper_state()
        self.change_vertical_height(vertical_height_for_insert)
        time.sleep(0.1)
        self.tilted_remove_tube()
        self.retract_to_carousel()

        if self.is_check_item_gripping:
            # make sure tube is gripped.
            if not self.is_gripper_gripping_item():
                raise ValueError('No item is picked up for pick_tube(), please check!')

        self.tube_status = 1

    @log_exception
    def move_to(self, location: Facility):

        self.logger.info(f"Executing move_to({location.name}) at {time.time()}.")

        loc_coord = location.pos['high']

        if location in [self.facilities["washer1"], self.facilities["washer1"]]:
            if not self.tube_status in [0, -1]:
                raise ValueError("Tube status is incorrect for move_to().")

        if self.is_located_at(loc_coord):
            self.logger.info("meca500 is already at move_to location.")
            return

        self.go_to_high_location(loc_coord)

    ## The internal threads drop sometimes. This method manually terminate all the
    ## internal threads. This is for testing the reconnecting methods after dropping.
    def kill_all_command_threads(self):
        # r.robo._command_response_handler_thread = None
        r.robo._command_tx_thread = None
        # r.robo._command_rx_thread = None

    def pause_with_visual(self, seconds):
        """
        Pauses the program for a given number of seconds while displaying a visual countdown
        in hundredths of a second in the console.
        """
        if seconds == 0:
            return

        total_steps = seconds * 10  # Convert seconds to hundredths
        for remaining in range(total_steps, -1, -1):
            progress = (total_steps - remaining) / total_steps
            bar_length = 30  # Length of the progress bar
            filled_length = int(progress * bar_length)

            bar = "#" * filled_length + "-" * (bar_length - filled_length)
            sys.stdout.write(f"\rPausing: {remaining / 10:.2f} sec [{bar}]")
            sys.stdout.flush()

            time.sleep(0.1)  # Pause for 0.01 seconds (hundredths)

        sys.stdout.write("\rPause complete!                              \n")


    def wash_tube(self):
        time.sleep(2)
        self.logger.info("Washing tube is done!")

    def dry_tube(self):
        time.sleep(2)
        self.logger.info('Drying tube is done!')

    # For testing
    def test(self,n=1):
        for i in range(n):
            print(f'##################{i}/{n}################')
            self.pick_tube(self.facilities['tube1'])
            self.pause_with_visual(25)
            # self.flip_tube()
            # self.place_tube(self.facilities['washer1'])
            # self.pick_tube(self.facilities['washer1'])
            # self.flip_tube()
            self.place_tube(self.facilities['tube1'])
            # self.go_to_safe('auto')
            # self.robo._command_response_handler_thread = None
            # self.robo._command_tx_thread = None
            # self.robo._command_rx_thread = None
            self.pause_with_visual(25)

    @timeit
    def test_sp(self):
        tube = self.facilities['tube1']
        washer = self.facilities['washer1']
        self.pick_tube(tube)
        self.place_tube_to_spinsolve()
        time.sleep(1)
        self.pick_tube_from_spinsolve()
        self.flip_tube("topdown_to_bottomup")
        self.place_tube(washer)
        time.sleep(1)
        self.pick_tube(washer)
        self.flip_tube("bottomup_to_topdown")
        self.place_tube(tube)

    @timeit
    def test_flip(self, n_times:int):
        for i in range(n_times):
            self.pick_tube(self.facilities['tube1'])
            # self.place_tube_to_spinsolve()
            # self.pick_tube_from_spinsolve()
            self.flip_tube()
            time.sleep(2)
            self.flip_tube()
            self.place_tube(self.facilities['tube1'])
            print(f'Finished flip NO. {i}')
            self.kill_all_command_threads()
    def test_flip_segmented(self, n_times):

        for i in range(n_times):
            self.pick_tube(r.facilities['tube1'])
            self.flip_tube(location='flip_stand_waste',is_pick=False)
            time.sleep(1)
            self.pick_tube(self.facilities['flip_stand_waste_gripper_upright'])
            self.flip_tube(location='flip_stand_clean')
            self.place_tube(self.facilities['tube1'])
            print(f'Finished flip NO. {i}')
    def wait_for_input(self):
        if input() in ['y','Y']:
            print('Continues')
        else:
            raise KeyError
    @timeit
    def test_all(self,
                 tube_id: int=1,
                 n: int = 1,
                 is_step_control: bool=False,
                 is_pause: bool = True,
                 pause: int = 1):
        for i in range(n):
            print(f'runing: {i+1}/{n} at {time.time()}')
            self.pick_tube(self.facilities[f'tube{tube_id}'])
            if is_pause: self.pause_with_visual(pause)
            if is_step_control: self.wait_for_input()

            self.place_tube_to_spinsolve()
            if is_pause: self.pause_with_visual(pause)
            if is_step_control: self.wait_for_input()

            self.pick_tube_from_spinsolve()
            if is_pause: self.pause_with_visual(pause)
            if is_step_control: self.wait_for_input()

            self.flip_tube()
            if is_pause: self.pause_with_visual(pause)
            if is_step_control: self.wait_for_input()

            self.place_tube(self.facilities['washer1'])
            if is_pause: self.pause_with_visual(pause)
            if is_step_control: self.wait_for_input()

            self.pick_tube(self.facilities['washer1'])
            if is_pause: self.pause_with_visual(pause)
            if is_step_control: self.wait_for_input()

            self.place_tube(self.facilities['washer2'])
            if is_pause: self.pause_with_visual(pause)
            if is_step_control: self.wait_for_input()

            self.pick_tube(self.facilities['washer2'])
            if is_pause: self.pause_with_visual(pause)
            if is_step_control: self.wait_for_input()

            self.place_tube(self.facilities['dryer'])
            if is_pause: self.pause_with_visual(pause)
            if is_step_control: self.wait_for_input()

            self.pick_tube(self.facilities['dryer'])
            if is_pause: self.pause_with_visual(pause)
            if is_step_control: self.wait_for_input()


            self.flip_tube('flip_stand_clean')
            if is_pause: self.pause_with_visual(pause)
            if is_step_control: self.wait_for_input()


            self.place_tube(self.facilities[f'tube{tube_id}'])
            if is_pause: self.pause_with_visual(pause)
            if is_step_control: self.wait_for_input()


if __name__ == '__main__':
    r = RobotArm()
    # r.robo.GetRtTargetJointPos()
    #
    # r.robo._command_rx_thread = None
    # r.robo.GetRtTargetJointPos()
    # print(r.robo)
    # print(r.robo._command_socket)
    # r.robo._shut_down_queue_threads()
    # r.robo._shut_down_socket_threads()
    # r.robo.Disconnect()
    # r.robo.Connect(address="192.168.0.100", enable_synchronous_mode=True, disconnect_on_exception=False, )
    # print(r.robo)
    # print(r.robo._command_socket)
    # for i in range(10):
    #     r.place_tube(r.facilities['dryer'])
    #     r.pick_tube(r.facilities['dryer'])

