import time
import mecademicpy.robot as mdr


def reset_robot():
    # self.robo.DeactivateRobot()
    # self.robo.Disconnect()
    robot_here = mdr.Robot()
    robot_here.Connect(
        address='192.168.0.100',
        enable_synchronous_mode=True,
        disconnect_on_exception=False,
    )
    # self.config_robot_before_activate()
    robot_here.ActivateAndHome()
    robot_here.WaitHomed()
    robot_here.ResetError()
    robot_here.ResumeMotion()

    return robot_here

robot = mdr.Robot()
robot.Connect(address='192.168.0.100')

robot.ActivateRobot()
robot.Home()
print('Connected!')

