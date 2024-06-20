from meca import get_robot, connect_robot, config_robot


def demo_20June():
   # // Pick the tube from Slot 1
   r.GripperOpen()


   r.MoveJoints(77.19999, 7.26299, -12.64184, 0, 5.37785, 0)
   r.MoveLinRelWrf(0, 0, -242, 0, 0, 0)
   r.GripperClose()
   # r.MoveLinRelWrf(0, 0, 242, 0, 0, 0)
   # avoid clashing the waiting slot
   r.MoveLinRelWrf(0, 0, 272, 0, 0, 0)


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




if __name__ == '__main__':
   r = get_robot()
   connect_robot(r)
   config_robot(r)


   r.ResetError()
   r.ResumeMotion()


   # r.SetJointLimitsCfg(1)
   # r.SetJointLimits(6, -270, 270)


   demo_20June()