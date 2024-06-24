import time


from meca import get_robot, connect_robot, config_robot


def demo_27June():
   # // Pick the tube from Slot 1
   r.GripperOpen()


   r.MoveJoints(77.19999, 12.99229, -30.00896, 0, 17.01568, 0)
   r.MoveLinRelWrf(0, 0, -262, 0, 0, 0)
   r.GripperClose()
   # r.MoveLinRelWrf(0, 0, 242, 0, 0, 0)
   # avoid clashing the waiting slot
   r.MoveLinRelWrf(0, 0, 262, 0, 0, 0)


   # // from slot 1 to spinsolve
   r.MoveJoints(-93.70001, -3.09134, -1.85067, 0, 4.94203, 0)


   r.MoveLinRelWrf(0, 0, -240, 0, 0, 0)
   r.GripperOpen()
   r.MoveLinRelWrf(0, 0, 240, 0, 0, 0)


   r.MoveLinRelWrf(0, 0, -240, 0, 0, 0)
   r.GripperClose()
   r.MoveLinRelWrf(0, 0, 240, 0, 0, 0)


   # // moving to waiter part and grip inverted tube
   r.MoveJoints(0, 21.2873, -54.27506, 0, 32.98676, 0)


   r.MoveJointsRel(0, 0, 0, 0, 0, 180)


   r.MoveLinRelWrf(0, 0, -340, 0, 0, 0)
   r.GripperOpen()
   r.MoveLinRelWrf(0, 0, 340, 0, 0, 0)


   r.MoveJointsRel(0, 0, 0, 0, 0, -180)


   r.MoveLinRelWrf(0, 0, -252, 0, 0, 0)
   r.GripperClose()
   r.MoveLinRelWrf(0, 0, 252, 0, 0, 0)


   # moving to the washer part
   r.MoveJoints(33.65, 23.56935, -50.52051, 0, 26.95017, 0)
   r.MoveLinRelWrf(0, 0, -280, 0, 0, 0)
   time.sleep(0.5)
   r.MoveLinRelWrf(0, 0, 280, 0, 0, 0)


   # go to waiting part to flip again
   r.MoveJoints(0, 21.2873, -54.27506, 0, 32.98676, 0)
   r.MoveLinRelWrf(0, 0, -252, 0, 0, 0)
   r.GripperOpen()
   r.MoveLinRelWrf(0, 0, 252, 0, 0, 0)


   r.MoveJointsRel(0, 0, 0, 0, 0, 180)
   r.MoveLinRelWrf(0, 0, -340, 0, 0, 0)
   r.GripperClose()
   r.MoveLinRelWrf(0, 0, 340, 0, 0, 0)


   # return to slot 1
   r.MoveJoints(77.19999, 12.99229, -30.00896, 0, 17.01568, 0)
   r.MoveLinRelWrf(0, 0, -260, 0, 0, 0)
   r.GripperOpen()
   r.MoveLinRelWrf(0, 0, 260, 0, 0, 0)


def test_washer_needle():
   r.MoveJoints(33.65, 23.56935, -50.52051, 0, 26.95017, 0)
   r.MoveLinRelWrf(0, 0, -280, 0, 0, 0)
   r.GripperOpen()
   r.GripperClose()
   r.MoveLinRelWrf(0, 0, 280, 0, 0, 0)
   time.sleep(5)


def test_from_washer_to_slot1():
   r.MoveJoints(33.65, 23.56935, -50.52051, 0, 26.95017, 0)


   # go to waiting part to flip again
   r.MoveJoints(0, 21.2873, -54.27506, 0, 32.98676, 0)
   r.MoveLinRelWrf(0, 0, -252, 0, 0, 0)
   r.GripperOpen()
   r.MoveLinRelWrf(0, 0, 252, 0, 0, 0)


   r.MoveJointsRel(0, 0, 0, 0, 0, 180)
   r.MoveLinRelWrf(0, 0, -340, 0, 0, 0)
   r.GripperClose()
   r.MoveLinRelWrf(0, 0, 340, 0, 0, 0)


   # return to slot 1
   r.MoveJoints(77.19999, 12.99229, -30.00896, 0, 17.01568, 0)
   r.MoveLinRelWrf(0, 0, -260, 0, 0, 0)
   r.GripperOpen()
   r.MoveLinRelWrf(0, 0, 260, 0, 0, 0)




if __name__ == '__main__':
   r = get_robot()
   connect_robot(r)
   config_robot(r)


   r.ResetError()
   r.ResumeMotion()


   # r.SetJointLimitsCfg(1)
   # r.SetJointLimits(6, -270, 270)


   # demo_20June()


   # test_from_washer_to_slot1()
   demo_27June()
