import mecademicpy.robot as mdr
import mecademicpy.mx_robot_def as mdr_def
import time
import numpy as np

def reset():
    r.ResetError()
    r.ResumeMotion()


def zero():
    move_joints((0,0,0,0,0,-60))


def move_pose(coord: tuple):
    r.MovePose(*coord)


def move_lin(coord: tuple):
    r.MoveLin(*coord)

def move_lin_rel_trf(coord: tuple):
    r.MoveLinRelTrf(*coord)

def move_joints(coord: tuple):
    r.MoveJoints(*coord)


def gripper_open():
    r.GripperOpen()
    r.WaitGripperMoveCompletion()


def gripper_close():
    r.GripperClose()
    r.WaitGripperMoveCompletion()


coord_dict = {'spinsolve_high': (180, 0, 330, -60, 90, 0),
              'spinsolve_low': (180, 0, 85, -60, 90, 0),
              'stand1_high': (57, 244, 305, -90, 0, 30),
              'stand1_low': (57, 244, 55, -90, 0, 30),
              'stand2_high':(-63, 242, 305, -90, 0, 30),
              'stand2_low':(-63, 242, 55, -90, 0, 30)}

def pick_tube(location='spinsolve'):
    gripper_open()

    # if the arm is not in 'high' position, move to the 'high' position.
    if False in np.isclose(r.GetPose(), coord_dict[f'{location}_high']):
        print("Not in high position, moving...")
        move_pose(coord_dict[f'{location}_high'])
    else:
        print('Robot in high position, continue...')

    move_lin(coord_dict[f'{location}_low'])
    gripper_close()
    move_lin(coord_dict[f'{location}_high'])


def place_tube(location='spinsolve'):

    # if the arm is not in 'high' position, move to the 'high' position.
    if False in np.isclose(r.GetPose(), coord_dict[f'{location}_high']):
        print("Not in high position, moving...")
        move_pose(coord_dict[f'{location}_high'])
    else:
        print('Robot in high position, continue...')

    move_lin(coord_dict[f'{location}_low'])
    gripper_open()
    move_lin(coord_dict[f'{location}_high'])

def get_robot():
    return mdr.Robot()

def connect_robot(r: mdr.Robot):
    r.Connect(address='192.168.0.100', enable_synchronous_mode=True, disconnect_on_exception=False)
    r.ActivateAndHome()
    r.WaitHomed()
    print('Homed!')

def config_robot(r: mdr.Robot):
    r.SetGripperRange(10, 40)


if __name__ == '__main__':
    r = mdr.Robot()
    connect_robot(r)

    # config
    config_robot(r)

    reset()

    zero()
    pick_tube(location='stand1')
    place_tube(location='spinsolve')
    time.sleep(2)
    pick_tube(location='spinsolve')
    place_tube(location='stand1')
    time.sleep(2)
    pick_tube(location='stand2')
    place_tube(location='spinsolve')
    pick_tube(location='spinsolve')
    place_tube(location='stand2')
    zero()
import mecademicpy.robot as mdr
# Connect, activate, and home robot...

# response_codes = [mdr_def.MX_ST_ERROR_RESET, mdr_def.MX_ST_NO_ERROR_RESET]
# response_codes = [2005, 2006]
#
# response = r.SendCustomCommand('GetConf', timeout=10)

# r.MoveJoints(0, 0, 0, 0, 0, 0)
# r.SetConf(1,1, -1)
# r.MoveLin(140, 250, 200, -110, 30, 60)
# r.MoveJoints(0, 0, 0, 0, 0, 0)
# r.SetConf(1,1, 1)
# r.MoveLin(140, 250, 200, -110, 30, 60)
# r.GetPose()
# for i in [1,-1]:
#     for j in [1,-1]:
#         for k in [1, -1]:
#             # print(f'this is the conf: {i,j,k}')
#             r.SetConf(1,1,1)
#             b = (0,0,0,0,0,0)
#             r.MoveJoints(*b)
#             # time.sleep(1)
#             r.SetConf(i,j, k)
#             a = (77, 210, 300, -103, 36, 175)
#             r.MovePose(*a)
#             time.sleep(6)
#             # print(r.GetPose())
#             print(r.GetJoints())




# robot.MoveJoints(0, -60, 60, 0, 0, 0)

# # Print robot position while it's moving
# for _ in range(100):
#     print(robot.GetJoints())
#     time.sleep(0.05)
#
# robot.WaitIdle()
# robot.DeactivateRobot()
# robot.WaitDeactivated()
# robot.Disconnect()

# for i in range(30):
#     robot.MoveJoints(0, 0, 0, 0, 0, 0)
#     robot.MoveJoints(60, 20, 50, 50, 60, 0)
#     robot.MoveJoints(160, 20, -50, 50, 60, 0)
#     robot.MoveJoints(-160, -20, 50, -50, -60, 0)

# r.GripperOpen()
# r.MoveJoints(0, 0, 0, 0, 0, -60)
# r.MovePose(180,0,258,-60, 90, 0)
# r.GripperClose()



# r.MoveJoints(0, 0, 0, 0, 0, -60)
# r.GripperOpen()
# # A down
# r.MoveLin(200, 0, 10, -60, 90, 0)
# r.GripperClose()
# time.sleep(3)
# # A up
# r.MoveLin(200, 0, 250, -60, 90, 0)
# # B up
# r.MoveLin(0, 200, 250, -90, 0, 30)
# # B down
# r.MoveLin(0, 200, 10, -90, 0, 30)
# time.sleep(2)
# r.GripperOpen()
# # B up
# r.MoveLin(0, 200, 250, -90, 0, 30)
# r.MoveJoints(0, 0, 0, 0, 0, -60)
#
#
#
#
# r.MoveJoints(0, 0, 0, 0, 0, -60)
# r.GripperOpen()
# # A down
# r.MoveLin(200, 0, 10, -60, 90, 0)
# time.sleep(4)
# r.GripperClose()
# time.sleep(2)
# # A up
# r.MoveLin(200, 0, 250, -60, 90, 0)
# # C up
# r.MoveLin(150, 180, 250, -90, 0, 30)
# r.MovePose(150, 180, 250, -90, 0, 210)
# time.sleep(2)
# # C down
# r.MoveLin(150, 180, 20, -90, 0, 210)
# time.sleep(3)
# r.GripperOpen()
# time.sleep(3)
# # C up
# r.MovePose(150, 180, 250, -90, 0, 210)
# r.MovePose(150, 180, 310, -90, 0, 210)# A up
# r.MoveJoints(0, 0, 0, 0, 0, -60)
#
#
#
#
#
# a = r.GetJoints()
# a[5] = a[5] + 180
# r.MoveJoints(*a)
#
# # C down
# r.MoveLin(150, 180, 20, -90, 0, 30)
# r.GripperOpen()
# time.sleep(2)
# # C up
# r.MovePose(150, 180, 250, -90, 0, 30)
#
# r.MoveJoints(0, 0, 0, 0, 0, -60)
#
#
#
#
#
# time.sleep(3)
# r.GripperClose()
# time.sleep(3)
# r.MoveLin(200, 0, 250, -60, 90, 0)
# time.sleep(3)
# a= r.GetJoints()
# a[5] = a[5] + 180
# r.MoveJoints(*a)
# time.sleep(3)
# a[5] = a[5] - 180
# r.MoveJoints(*a)
# time.sleep(3)
# r.MovePose(200, 0, 250, -60, 90, 0)
# r.MoveLin(200, 0, 10, -60, 90, 0)
# time.sleep(3)
# r.GripperOpen()
# r.MoveLin(200, 0, 250, -60, 90, 0)
# r.MoveJoints(0, 0, 0, 0, 0, -60)
#
#
#
# # B up
# r.MoveLin(0, 200, 250, -90, 0, 30)
#
# # B down
# r.MoveLin(0, 200, 10, -90, 0, 30)
#
#
#
#
#
# r.MovePose(50, 200, 250, -60, 90, 0)
# r.MovePose(50, 200, 250, 120, 90, 0)
#
# r.MovePose(50, 200, 40, 120, 90, 0)
#
# r.MovePose(50, 200, 250, 120, 90, 0)
# r.MovePose(50, 200, 250, -60, 90, 0)
# r.MovePose(200, 0, 250, -60, 90, 0)
#
# time.sleep(1)
# r.MoveLin(200, 0, 250, -60, 90, 0)
# r.MoveLin(200, 0, 10, -60, 90, 0)
# time.sleep(3)
#
# r.MoveLin(200, 0, 250, -60, 90, 0)
#
#
# r.MoveJoints(0, 0, 0, 0, 0, -60)
#
#
#
#
# r.ResetError()
# r.ResumeMotion()
#
# # a = r.GetJoints()
# for i in range(5):
#     a = r.GetJoints()
#     a[5] = a[5]+20
#     r.MoveJoints(*a)

# r.MoveLin(180,0,80,-60, 90, 0)
# r.GripperClose()
# r.MoveLin(180,0,330,-60, 90, 0)
# r.GripperClose()
# r.MoveLin(180,0,80,-60, 90, 0)
# r.GripperOpen()
# r.MoveLin(180,0,330,-60, 90, 0)

