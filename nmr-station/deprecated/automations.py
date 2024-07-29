import time

from robotarm import RobotArm
from facility import load_facilities

def route(robo: RobotArm):
    robo = RobotArm()
    facility_map = load_facilities()
    for name in ["tube_rack", "spinsolve80", "waiter", "washer", "waiter", "tube_rack"]:
        facility = facility_map[name]
        robo.move_to(facility)
        facility.handle_tube(robo)

# import time
#
#
# from meca import get_robot, connect_robot, config_robot, move_joints, move_joints_rel
#
# from meca_movements import change_radial_distance, change_vertical_height, invert_gripper, change_gripper_state
#
#
# def pick_tube_from_slot1():
#    r.GripperOpen()
#
#
#    r.MoveJoints(77.19999, 12.99229, -30.00896, 0, 17.01568, 0)
#    r.MoveLinRelWrf(0, 0, -262, 0, 0, 0)
#    r.GripperClose()
#    r.MoveLinRelWrf(0, 0, 262, 0, 0, 0)
#
#
# def slot1_to_spinsolve():
#    r.MoveJoints(-93.70001, 1.31509, -16.46217, 0, 15.14709, 0)
#
#
#    r.MoveLinRelWrf(0, 0, -260, 0, 0, 0)
#    r.GripperOpen()
#    r.MoveLinRelWrf(0, 0, 260, 0, 0, 0)
#
#
#    r.MoveLinRelWrf(0, 0, -260, 0, 0, 0)
#    r.GripperClose()
#    r.MoveLinRelWrf(0, 0, 260, 0, 0, 0)
#
#
# def slot1_to_waiter():
#    r.MoveJoints(0, 21.2873, -54.27506, 0, 32.98676, 0)
#    invert_gripper(r)
#
#
#    r.MoveLinRelWrf(0, 0, -340, 0, 0, 0)
#    r.GripperOpen()
#    r.MoveLinRelWrf(0, 0, 340, 0, 0, 0)
#
#
#    invert_gripper(r)
#
#
#    r.MoveLinRelWrf(0, 0, -252, 0, 0, 0)
#    r.GripperClose()
#    r.MoveLinRelWrf(0, 0, 252, 0, 0, 0)
#
#
# def spinsolve_to_waiter():
#    r.MoveJoints(0, 21.2873, -54.27506, 0, 32.98676, 0)
#
#
#    invert_gripper(r)
#
#
#    r.MoveLinRelWrf(0, 0, -340, 0, 0, 0)
#    r.GripperOpen()
#    r.MoveLinRelWrf(0, 0, 340, 0, 0, 0)
#
#
#    invert_gripper(r)
#
#
#    r.MoveLinRelWrf(0, 0, -252, 0, 0, 0)
#    r.GripperClose()
#    r.MoveLinRelWrf(0, 0, 252, 0, 0, 0)
#
#
# def waiter_to_washer():
#    r.MoveJoints(33.65, 18.81975, -38.51321, 0, 19.69246, 0)
#
#
#    r.MoveLinRelWrf(0, 0, -267, 0, 0, 0)
#    time.sleep(5)
#    r.MoveLinRelWrf(0, 0, 17, 0, 0, 0)
#    for i in range(10):
#        r.MoveLinRelWrf(0, 0, 25, 0, 0, 0)
#        time.sleep(1)
#    # r.MoveLinRelWrf(0, 0, 267, 0, 0, 0)
#
#
# def washer_to_waiter():
#    r.MoveJoints(0, 21.2873, -54.27506, 0, 32.98676, 0)
#    r.MoveLinRelWrf(0, 0, -252, 0, 0, 0)
#    r.GripperOpen()
#    r.MoveLinRelWrf(0, 0, 252, 0, 0, 0)
#
#
#    invert_gripper(r)
#    r.MoveLinRelWrf(0, 0, -340, 0, 0, 0)
#    r.GripperClose()
#    r.MoveLinRelWrf(0, 0, 340, 0, 0, 0)
#
#
# def waiter_to_slot1():
#    r.MoveJoints(77.19999, 12.99229, -30.00896, 0, 17.01568, 0)
#
#
#    r.MoveLinRelWrf(0, 0, -260, 0, 0, 0)
#    r.GripperOpen()
#    r.MoveLinRelWrf(0, 0, 260, 0, 0, 0)
#
#
# def demo_27June():
#    pick_tube_from_slot1()
#
#
#    # slot1_to_spinsolve()
#    # spinsolve_to_waiter()
#
#
#    slot1_to_waiter()
#
#
#    waiter_to_washer()
#
#
#    washer_to_waiter()
#
#
#    waiter_to_slot1()
#
#
# def test_washer_needle():
#    r.MoveJoints(33.65, 23.56935, -50.52051, 0, 26.95017, 0)
#    r.MoveLinRelWrf(0, 0, -280, 0, 0, 0)
#    r.GripperOpen()
#    r.GripperClose()
#    r.MoveLinRelWrf(0, 0, 280, 0, 0, 0)
#    time.sleep(5)
#
#
# def test_from_washer_to_slot1():
#    r.MoveJoints(33.65, 23.56935, -50.52051, 0, 26.95017, 0)
#
#
#    # go to waiting part to flip again
#    r.MoveJoints(0, 21.2873, -54.27506, 0, 32.98676, 0)
#    r.MoveLinRelWrf(0, 0, -252, 0, 0, 0)
#    r.GripperOpen()
#    r.MoveLinRelWrf(0, 0, 252, 0, 0, 0)
#
#
#    invert_gripper(r)
#    r.MoveLinRelWrf(0, 0, -340, 0, 0, 0)
#    r.GripperClose()
#    r.MoveLinRelWrf(0, 0, 340, 0, 0, 0)
#
#
#    # return to slot 1
#    r.MoveJoints(77.19999, 12.99229, -30.00896, 0, 17.01568, 0)
#    r.MoveLinRelWrf(0, 0, -260, 0, 0, 0)
#    r.GripperOpen()
#    r.MoveLinRelWrf(0, 0, 260, 0, 0, 0)
#
# def reset_position_spinsolve80_z291():
#    move_joints(r, -90.4,14.253, -8.21, 0, -6.044, 0)
#
#
#
#
# def pickup_tube_at_spinsolve80():
#    r.GripperOpen()
#    r.MoveLinRelWrf(0, 0, -204, 0, 0, 0)
#    change_gripper_state(r)
#    r.MoveLinRelWrf(0, 0, 204, 0, 0, 0)
#
# def reset_tube_at_last_tip_spinsolve80():
#    r.MoveJoints(-90.4, 14.253, -8.21, 0, -6.044, 0)
#    r.MoveLinRelWrf(0, 0, -192.5, 0, 0, 0)
#    change_gripper_state(r)
#    r.MoveLinRelWrf(0, 0, 192.5, 0, 0, 0)
#
#
# def remove_tube_from_spinsolve80():
#    move_joints(r, -90.4,14.253, -8.21, 0, -6.044, 0)
#    # r.MoveJointsRel(6, 0, 0, 0, 0, -7)
#    # r.MoveLinRelTrf(0, 0, -7, 0, 0, 0)
#
#    move_joints_rel(r, j1=6, j6=-7)
#    change_radial_distance(r, -7)
#
#    move_joints_rel(r, j1=10, j6=-10)
#    change_radial_distance(r, -10)
#
#    move_joints_rel(r, j1=10, j6=-10)
#
#    # change_vertical_height(r, "up",37)
#    r.MoveLinRelWrf(0, 0, 47, 0, 0, 0)
#    move_joints_rel(r, j6=27)
#
#
# if __name__ == '__main__':
#    r = get_robot()
#    connect_robot(r)
#    config_robot(r)
#
#
#    r.ResetError()
#    r.ResumeMotion()
#
#
#    # r.SetJointLimitsCfg(1)
#    # r.SetJointLimits(6, -270, 270)
#
#
#    # test_from_washer_to_slot1()
#    # waiter_to_washer()
#
#
#    # demo_27June()
#    # pick_tube_from_slot1()
#    # slot1_to_waiter()
#    # r.MoveJoints(33.65, 18.81975, -38.51321, 0, 19.69246, 0)
#
#    # reset_position_spinsolve80_z291()
#
#    insert_tube_to_spinsolve80()
#
#    # reset_tube_at_last_tip_spinsolve80()
#    pickup_tube_at_spinsolve80()
#    remove_tube_from_spinsolve80()
