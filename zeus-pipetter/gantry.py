
import logging
module_logger = logging.getLogger('main.gantry')

import serial
import numpy as np
import time

class Gantry():

    """
    The xy gantry moving with Zeus on it.

    Gantry() take zeus object as argument, which is used to request position of Z drive.
    Only when the Z drive position is in safe traverse height will the gantry be able to move.
    """

    xy_position = ((0, 0)) # this is to store the gantry position after every move.

    def __init__(self,
                 zeus: object, # pass the zeus module to gantry, this is for checking traverse height,
                 max_x: int = -810,
                 max_y: int = -357,
                 horiz_speed: int = 200*60,# horizontal speed in mm / min
                 xy_offset: tuple = (4, 0),# offsets in x and y, negative to right, closer; positive, to left, further
                 trash_xy: tuple = (-500, -70),
                 zeus_traverse_position: int = 880,
                 ):
        self.logger = logging.getLogger('main.gantry.Gantry')
        self.logger.info('gantry is initiating...')
        self.serial = serial.Serial('COM6', 115200, timeout=0.2)
        self.horiz_speed = horiz_speed # horizontal speed in mm/min
        self.xy_offset = xy_offset
        self.trash_xy = trash_xy
        self.idle_xy = self.trash_xy
        self.max_x = max_x
        self.max_y = max_y
        self.zm = zeus
        self.zeus_traverse_position = zeus_traverse_position

        # self.home_xy()

    def send_to_xy_stage(self, command, wait_for_ok=True, verbose=False, read_all=False,
                         ensure_traverse_height=True) -> None:
        ser = self.serial
        ser.write(str.encode(command + '\r\n'))
        # ser.write(str.encode(command))
        if verbose:
            print('SENT: {0}'.format(command))
        # time.sleep(1)

        if wait_for_ok:
            if verbose:
                print('Waiting for ok...')
            while True:
                line = ser.readline()
                if b'Alarm' in line:
                    print('GRBL ALARM: GRBL wend into alarm. Overrode it with $X.')
                    self.send_to_xy_stage(ser, '$X')
                    break
                if verbose:
                    print(line)
                if b'ok' in line:
                    break

        if read_all:
            if verbose:
                print('Reading all...')
            while True:
                line = ser.readline()
                if verbose:
                    print(line)
                if line == b'':
                    break

    def configure_grbl(self) -> None:
        with open("grbl_source_code\\grbl_settings.txt", 'r') as grbl_config_file:
            for line in grbl_config_file:
               self.send_to_xy_stage(command = line.split('    (')[0], read_all= True, verbose= True)
        print("XY stage configured!")

    def xy_pos(self) -> None:
        self.send_to_xy_stage(command= '?', read_all= True, verbose= False)

    def time_that_xy_motion_takes(self, dx: int, dy: int, acceleration=2000, max_speed=333.33333):

        travel_times = []
        for distance in [abs(dx), abs(dy)]:
            halfdistance = distance / 2
            # constant acceleration scenario
            constant_acceleration_halftime = np.sqrt(halfdistance * 2 / acceleration)
            speed_at_midpoint = constant_acceleration_halftime * acceleration
            if speed_at_midpoint <= max_speed:
                time_here = constant_acceleration_halftime * 2
            else:
                # this means that the stage reaches max speed before midpoint and then
                #   continues at his max speed
                constant_acceleration_halftime = max_speed / acceleration
                dist_traveled_at_constant_acceleration = acceleration * (constant_acceleration_halftime ** 2) / 2
                distance_traveled_at_constant_speed = halfdistance - dist_traveled_at_constant_acceleration
                const_speed_halftime = distance_traveled_at_constant_speed / max_speed
                time_here = 2 * (constant_acceleration_halftime + const_speed_halftime)
            travel_times.append(time_here)
        # print(max(travel_times))
        return max(travel_times)

    def move_xy(self, xy: tuple, verbose=False, ensure_traverse_height=True, block_until_motion_is_completed=True,
                use_time_estimate=True) -> None:
        if xy[0] < self.max_x or xy[0] > 0:
            print(f'XY STAGE ERROR: target X is beyond the limit ({self.max_x}, 0). Motion aborted.')
            return
        if xy[1] < self.max_y or xy[1] > 0:
            print(f'XY STAGE ERROR: target Y is beyond the limit ({self.max_y}, 0). Motion aborted.')
            return

        zeus_at_traverse_height = self.zm.pos <= self.zeus_traverse_position
        if ensure_traverse_height and not zeus_at_traverse_height:
            print(f'ERROR: ZEUS was not in traverse height before motion, but instead at {self.zm.pos}.\n'
                  f'Motion aborted!')
            return

        # if np.linalg.norm(np.array((x, y))) <= R:
        self.send_to_xy_stage(command= 'G0 X{0:.3f} Y{1:.3f}'.format(xy[0] + self.xy_offset[0], xy[1] + self.xy_offset[1]),
                         read_all=False, ensure_traverse_height=ensure_traverse_height)
        if block_until_motion_is_completed:
            if use_time_estimate:
                time.sleep(self.time_that_xy_motion_takes(dx=xy[0] - self.xy_position[0],
                                                     dy=xy[1] - self.xy_position[1]))
            else:
                t0 = time.time()
                time.sleep(0.1)
                finished_moving = False
                for i in range(100):
                    if finished_moving:
                        break
                    if verbose:
                        print(f'Status read {i}')
                    self.serial.write(str.encode('?' + '\r\n'))
                    while True:
                        line = self.serial.readline()
                        if verbose:
                            print(line)
                        if b'Idle' in line:
                            finished_moving = True
                        if line == b'':
                            break
                # print(f'{time.time() - t0}')
                if verbose:
                    print('Finished moving xy stage')
        self.xy_position = xy

    def move_to_idle(self):
        self.move_xy(self.idle_xy)

    def home_xy(self, ensure_traverse_height=True) -> None:
        self.logger.info('The gantry is homing...')
        self.send_to_xy_stage(command = '$H', read_all=True, verbose=False,
                              ensure_traverse_height=ensure_traverse_height)
        self.xy_pos()

    def kill_alarm(self) -> None:
        self.send_to_xy_stage("$X", read_all= True, verbose= True)

    def close_gantry(self)-> None:
        time.sleep(2)
        self.serial.close()

    def view_grbl_settings(self)-> None:
        self.send_to_xy_stage('$$', read_all=True, verbose=True)
        self.xy_pos()

    def move_through_wells(self, plate: object, dwell_time=0.1, ensure_traverse_height=True):
        for container in plate.containers:
            print(f'This is well index: {container}')
            self.move_xy(container.xy, ensure_traverse_height=ensure_traverse_height)
            time.sleep(dwell_time)

def main():

    import zeus
    zm = zeus.ZeusModule(id=1)
    time.sleep(5)
    gt = Gantry(zeus = zm)
    time.sleep(3)
    # gt.configure_grbl() # This only need to be done once.
    gt.home_xy()
    zm.switchOff()

    return gt, zm

if __name__ == '__main__':
    gt, zm = main()