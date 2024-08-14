import mecademicpy.robot as mdr
import mecademicpy.mx_robot_def as mdr_def
import time
import numpy as np
import json

json_file = 'D:\\dropbox\\Dropbox\\robochem\\data\\nmr_station\\coordinates.json'


def load_coord(file:str):

    # save coordinate info
    with open(file,'r') as f:
        coord_dict = json.load(f)

    return coord_dict

def update_coord(key:str, value:tuple):

    coord_dict = load_coord()

    coord_dict[key]=value

    with open(json_file, 'w') as f:
        json.dump(coord_dict, f, indent=4)

    return coord_dict

def zero(r:mdr.Robot):

    move_joints(r,(0,0,0,0,0,0))


def move_pose(r: mdr.Robot, coord: tuple):
    r.MovePose(*coord)


def move_lin(r: mdr.Robot,
             x: float = 0,
             y: float = 0,
             z: float = 0,
             alpha: float = 0,
             beta: float = 0,
             gamma: float = 0):

    # if a single tuple is sent
    if isinstance(x, tuple):
        x, y, z, alpha, beta, gamma = x

    r.MoveLin(x, y, z, alpha, beta, gamma)

def move_lin_rel_trf(r: mdr.Robot,
                     x: float = 0,
                     y: float = 0,
                     z: float = 0,
                     alpha: float = 0,
                     beta: float = 0,
                     gamma: float = 0):

    # if a single tuple is sent
    if isinstance(x, tuple):
        x, y, z, alpha, beta, gamma = x

    r.MoveLinRelTrf(x, y, z, alpha, beta, gamma)


def move_joints(r: mdr.Robot,
                j1: float=0,
                j2: float=0,
                j3: float=0,
                j4: float=0,
                j5: float=0,
                j6: float=0):

    # if a single tuple is sent
    if isinstance(j1, tuple):
        j1, j2, j3, j4, j5, j6 = j1

    r.MoveJoints(j1, j2, j3, j4, j5, j6)


def move_joints_rel(r: mdr.Robot,
                    j1: float=0,
                    j2: float=0,
                    j3: float=0,
                    j4: float=0,
                    j5: float=0,
                    j6:float=0):

    # if a single tuple is sent
    if isinstance(j1, tuple):
        j1, j2, j3, j4, j5, j6 = j1

    r.MoveJointsRel(j1, j2, j3, j4, j5, j6)


def gripper_open(r: mdr.Robot):
    r.GripperOpen()
    r.WaitGripperMoveCompletion()


def gripper_close(r: mdr.Robot):
    r.GripperClose()
    r.WaitGripperMoveCompletion()


# coord_dict = {'spinsolve_high': (180, 0, 330, -60, 90, 0),
#               'spinsolve_low': (180, 0, 85, -60, 90, 0),
#               'stand1_high': (57, 244, 305, -90, 0, 30),
#               'stand1_low': (57, 244, 55, -90, 0, 30),
#               'stand2_high':(-63, 242, 305, -90, 0, 30),
#               'stand2_low':(-63, 242, 55, -90, 0, 30)}

def pick_tube(r: mdr.Robot, coord_dict, location='spinsolve'):

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


def place_tube(r: mdr.Robot, coord_dict, location='spinsolve'):

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

    r.Connect(address='192.168.0.100',
              enable_synchronous_mode=True,
              disconnect_on_exception=False)

    r.ActivateAndHome()
    r.WaitHomed()
    print('Homed!')

def config_robot(r: mdr.Robot):
   # r.SetGripperRange(12, 30)
   # short gripper
   r.SetGripperRange(0, 4.9)


if __name__ == '__main__':

    print(1)
    r = mdr.Robot()
    connect_robot(r)
    #
    # # config
    # config_robot(r)
    #
    # reset_robot()
    #
    # zero()
    # pick_tube(location='stand1')
    # place_tube(location='spinsolve')
    # time.sleep(2)
    # pick_tube(location='spinsolve')
    # place_tube(location='stand1')
    # time.sleep(2)
    # pick_tube(location='stand2')
    # place_tube(location='spinsolve')
    # pick_tube(location='spinsolve')
    # place_tube(location='stand2')
    # zero()
    
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

# CartPos:[49.81891, 213.45946, 111.26992, -90.00002, 13.137, 90] at 2024-08-05 22:36:25.197687.
# JointPos:[76.863, 47.20006, 36.89572, 0, -84.09576, 0]

# CartPos:[49.81893, 213.45952, 344.07792, -90.00002, 13.137, 90] at 2024-08-05 22:39:30.761362.
# JointPos:[76.863, 25.78884, -52.27125, 0, 26.48242, 0] at 2024-08-05 22:39:30.761362.

# CartPos:[13.73819, 58.86411, 344.07797, -90.00002, 13.137, 90] at 2024-08-05 22:42:56.315620.
# JointPos:[76.863, -37.80042, 0.92452, 0, 36.87592, 0] at 2024-08-05 22:42:56.315620.

# CartPos:[-51.42923, 212.85912, 111.47793, -90.00001, -13.58301, 90] at 2024-08-05 22:58:15.599417.
# JointPos:[103.58301, 47.07623, 37.02626, 0, -84.10248, 0] at 2024-08-05 22:58:15.599417.

# CartPos:[-51.42924, 212.85917, 344.07792, -90.00001, -13.58301, 90] at 2024-08-05 23:00:31.604093.
# JointPos:[103.58301, 25.60234, -51.96419, 0, 26.36187, 0] at 2024-08-05 23:00:31.604093.

# CartPos:[-16.20116, 67.05455, 344.07796, -90.00001, -13.58301, 90] at 2024-08-05 23:02:26.194915.
# JointPos:[103.58301, -35.53755, 1.08326, 0, 34.4543, 0] at 2024-08-05 23:02:26.194915.
