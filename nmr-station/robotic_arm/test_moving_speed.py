"""
Test how to set faster moving speed while accurate displacement


King Lam Kwong
"""




from meca import get_robot, connect_robot, config_robot
# from automations import pick_tube_from_slot1


def test_z_axis_speed():
   for i in range(1, 5):
       r.SetCartLinVel(i * 150)
       r.MoveLinRelWrf(0, 0, -150, 0, 0, 0)
       r.MoveLinRelWrf(0, 0, 150, 0, 0, 0)


def test_slot1_pickup_speed():
   r.MoveJoints(77.19999, 12.99229, -30.00896, 0, 17.01568, 0)


   for i in range(1, 5):
       r.SetCartLinVel(i * 150)
       # pick_tube_from_slot1()
      
       r.GripperOpen()


       r.MoveLinRelWrf(0, 0, -262, 0, 0, 0)
       r.GripperClose()
       r.MoveLinRelWrf(0, 0, 262, 0, 0, 0)


       r.MoveLinRelWrf(0, 0, -262, 0, 0, 0)
       r.GripperOpen()
       r.MoveLinRelWrf(0, 0, 262, 0, 0, 0)


if __name__ == "__main__":
   r = get_robot()
   connect_robot(r)
   config_robot(r)


   test_slot1_pickup_speed()
