import time
import mecademicpy.robot as mdr
import logging
from functools import partial

robot1 = mdr.Robot()
robot1.logger.setLevel(logging.DEBUG)
robot1.logger.addHandler(logging.FileHandler("debug_2025-02-24YJ.log"))
robot1.Connect(address='192.168.0.100')
# robot1.SetMonitoringInterval(1) #YJ

robot1.ActivateRobot()
robot1.Home()
robot1.WaitHomed()
robot1.DeactivateRobot()
robot1.Disconnect()

robot1.Connect(address='192.168.0.100', enable_synchronous_mode=True)
# robot1.SetMonitoringInterval(1) #YJ

robot1.ActivateRobot()
robot1.Home()
robot1.WaitHomed()
robot1._enable_synchronous_mode = True # YJ


time.sleep(5)
robot1.MoveJoints(20, -30, 0, 0, 0, 0)
time.sleep(5)

# robot1.Disconnect()

# time.sleep(5)
# robot1.MoveJoints(0, -30, 0, 0, 0, 0)
# time.sleep(5)
#
# # robot1.Disconnect()
# # time.sleep(5)
# # robot1.Connect(address='192.168.0.100')
#
# robot1.MoveJoints(-10, -30, 0, 0, 0, 0)
# time.sleep(5)
#
# robot1.DeactivateRobot()
# robot1.Disconnect()


#
# def execute_with_autoreconnect(robot_instance,
#                                command_here,
#                                max_retries=10,
#                                address='192.168.0.100'):
#     for retries in range(max_retries):
#         try:
#             command_here()
#             break
#         except mdr.InvalidStateError as e:
#             print(f'Detected InvalidStateError during retry {retries}. The message is:')
#             print(str(e))
#             print('Establishing new TCP/IP connection...')
#             robot_instance.Connect(address=address)
#             print('Connection reestablished. Retrying the motion command...')
#
#     if retries == max_retries - 1:
#         print(f'After {max_retries} retries, we still failed. Giving up...')
#         # raise e
#         raise mdr.InvalidStateError(str(e))
#
#     robot_instance.WaitIdle()
#
#

for i in range(100):
    print(f'{i}/100')

    for coordinates_x in [10, 0, -10]:
        # execute_with_autoreconnect(robot_instance=robot1,
        #                            command_here=partial(robot1.MoveJoints, *coordinates))

        # robot1.SetMonitoringInterval(1)
        # robot1.ActivateRobot()
        robot1.MoveJoints(coordinates_x, -30, 0, 0, 0, 0)
        # robot1.Disconnect()
        print(f'motion to coordinate set {coordinates_x} done.')
        # time.sleep(180)
        # time.sleep(5)
        # robot1.Connect(address='192.168.0.100')
        # robot1.SetMonitoringInterval(1)
        time.sleep(180)
        # robot1.ActivateRobot()
        # robot1.WaitIdle()

robot1.WaitIdle()
