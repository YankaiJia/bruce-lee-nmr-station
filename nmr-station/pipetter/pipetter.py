"""
The pipetter module combines gantry and zeus, and deals with actions including pick_tip, discard_tip, draw_liquid,
dispense_liquid, transfer_liquid,etc.

by Yankai Jia, Natalia

"""
import logging
from dataclasses import dataclass
import json
import time
import numpy as np
import serial
import serial.tools.list_ports
import operator
import os
import sys

# if __name__ == '__main__':
#     import breadboard as brb
# else:
#     import pipetter.breadboard as brb

sys.path.append(os.path.abspath(os.path.pardir))

import breadboard as brb

from settings import (
    TUBE_COUNT,
    PIPETTER_LOG_PATH,
    PIPETTER_COORDINATES_FILE_PATH,
    PIPETTER_GRBL_SETTINGS_FILE_PATH,
    PIPETTER_TIP_RACK_FILE_PATH,
)

# NUM_OF_TUBES_IN_RACK=4
NUM_OF_TUBES_IN_RACK= TUBE_COUNT

def setup_logger():
    # better logging format in console
    class CustomFormatter(logging.Formatter):
        grey = "\x1b[38;20m"
        yellow = "\x1b[33;20m"
        red = "\x1b[31;20m"
        bold_red = "\x1b[31;1m"
        reset = "\x1b[0m"
        format = "%(asctime)s-%(name)s-%(levelname)s-%(message)s(%(filename)s:%(lineno)d)"

        FORMATS = {logging.DEBUG: grey + format + reset,
            logging.INFO: yellow + format + reset,
            logging.WARNING: yellow + format + reset,
            logging.ERROR: red + format + reset,
            logging.CRITICAL: bold_red + format + reset}

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    # create logger with 'main'
    logger = logging.getLogger('minipi')
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(PIPETTER_LOG_PATH)
    fh.setLevel(logging.INFO)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(CustomFormatter())
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

logger = setup_logger()

ports = list(serial.tools.list_ports.comports())
zeus_port_id = [i.description[-2] for i in ports if 'USB Serial Port' in i.description][0]

class Zeus(object):
    # CANBus = None
    # transmission_retries = 5
    # remote_timeout = 1
    # serial_timeout = 0.1
    errorTable = {
            20: "No communication to EEPROM.",
            30: "Undefined command.",
            31: "Undefined parameter.",
            32: "Parameter out of range.",
            35: "Voltage outside the permitted range.",
            36: "Emergency stop is active or was sent during action.",
            38: "Empty liquid class.",
            39: "Liquid class write protected.",
            40: "Parallel processes not permitted.",
            50: "Initialization failed.",
            51: "Pipetting drive not initialized.",
            52: "Movement error on pipetting drive.",
            53: "Maximum volume of the tip reached.",
            54: "Maximum volume in pipetting drive reached.",
            55: "Volume check failed.",
            56: "Conductivity check failed.",
            57: "Filter check failed.",
            60: "Initialization failed.",
            61: "Z-drive is not initialized.",
            62: "Movement error on the z-drive.",
            63: "Container bottom search failed.",
            64: "Z-position not possible.",
            65: "Z-position not possible.",
            66: "Z-position not possible.",
            67: "Z-position not possible.",
            68: "Z-position not possible.",
            69: "Z-position not possible.",
            70: "Liquid level not detected.",
            71: "Not enough liquid present.",
            72: "Auto calibration of the pressure sensor not possible.",
            73: "cLLD adjust error. Check if adapter is touching conductive things during initialization. Also the grounding should be checked.",
            74: "Early liquid level detection.",
            75: "No tip picked up or no tip present.",
            76: "Tip already picked up.",
            77: "Tip not discarded.",
            80: "Clot detected during aspiration.",
            81: "Empty tube detected during aspiration.",
            82: "Foam detected during aspiration.",
            83: "Clot detected during dispensing.",
            84: "Foam detected during dispensing.",
            85: "No communication to the digital potentiometer.",
    }

    def __init__(self, id=815, COMport='COM' + zeus_port_id, COM_timeout=0.1, baudrate=19200):
        self.zeus_serial = serial.Serial(port=COMport,
                                    baudrate=baudrate,
                                    timeout=COM_timeout,
                                    parity=serial.PARITY_EVEN,
                                    stopbits=serial.STOPBITS_ONE,
                                    bytesize=serial.EIGHTBITS)
        self.id = id
        self.tip_on_zeus = ''

    def send_command(self, cmd, characteristic_str='er', n_tries = 100):

        self.zeus_serial.flushInput()
        self.zeus_serial.flushOutput()

        self.zeus_serial.write((cmd + '\r\n').encode("utf-8"))

        for i in range(n_tries):
            line_here = self.zeus_serial.readline().decode("utf-8")
            if (characteristic_str in line_here):
                # print(f'response line received: {line_here}')
                break
            time.sleep(0.01)

            if i == n_tries - 1:
                logger.error('No response received.')
                raise TimeoutError

        error_code = int(line_here.split(characteristic_str)[-1])
        if characteristic_str == 'er' and error_code != 0:
            if error_code == 75: # this means there is no tip on zeus
                self.tip_on_zeus = ''
                logger.info('tip_on_zeus is set to empty!')
            logger.error(f'cmd respond w/ error: {error_code}-{self.errorTable[error_code]}')

        return error_code

    def led_set(self, red=0, green=0, blue=1):
        self.send_command(f'00SLid{self.id:04d}sb{blue}sr{red}sg{green}')
    def led_blink(self, time_interval=0.5):
        """Check the serial communication by blinking the LED on Zeus LT five times on and off."""
        sm = f"00SMid{self.id:04d}sm1"
        sg = f"00SLid{self.id:04d}sg1"
        for i in range(3):
            logger.info("LED blinking\r")
            self.send_command(sg)
            time.sleep(time_interval)
            self.send_command(sm)
            time.sleep(time_interval)

    def firmware_version(self):
        """Request Firmware version"""
        self.send_command(f'RFid{self.id:04d}')

    def init(self):
        self.send_command(f'00DIid{self.id:04d}')
        self.tip_on_zeus = ''

    def tip_status_req(self):
        self.tip_on_zeus = self.send_command(f"00RTid{self.id:04d}", characteristic_str='rt')
        return self.tip_on_zeus

    def tip_pick_up(self, tip_type=6):
        ## pick up tip
        self.send_command(f"00TPid{self.id:04d}tt{tip_type:02d}")

    def tip_discard(self):
        self.send_command(f"00TDid{self.id:04d}")

    def clld_start(self, cr = 0, cs = 1):
        self.send_command(f"00CLid{self.id:04d}cr{cr:01d}cs{cs:01d}")

    def clld_stop(self):
        self.send_command(f"00CPid{self.id:04d}")

    def clld_re(self):
        self.send_command(f"00RNid{self.id:04d}")

    def plld_adj(self):
        self.send_command(f"00PAid{self.id:04d}")

    def plld_start(self):
        self.send_command(f"00PLid{self.id:04d}pr1ps4")

    def plld_stop(self):
        self.send_command(f"00PPid{self.id:04d}")

    def plld_re(self):
        """request plld status"""
        self.send_command(f"00RPid{self.id:04d}")

    def plld_blow_out(self, flow_rate=10):
        self.send_command(f"00PBid{self.id:04d}fr{flow_rate:05d}")

    def mixing_asp(self, mixing_volume=10, flow_rate=1000):
        self.send_command(f"00MAid{self.id:04d}ma{mixing_volume:05d}fr{flow_rate:05d}")

    def mixing_disp(self, flow_rate = 10):
        self.send_command(f"00MDid{self.id: 04d}fr{flow_rate: 05d}")

    def aspirate(self,asp_volume,
                       overasp = 100,
                       flow_rate = 2000,
                       stop_speed = 2000,
                       qpm = 0,
                       pressure_sensor = 0,
                       qpm_clot = 0,
                       qpm_foam = 0,
                       qpm_empty = 0,
                       time_after_asp = 10):

        self.send_command(f"00ALid{self.id:04d}av{asp_volume:05d}oa{overasp:05d}"
                          f"fr{flow_rate:05d}ss{stop_speed:05d}qm{qpm:01d}"
                          f"bi{pressure_sensor:01d}qc{qpm_clot:04d}qf{qpm_foam:04d}"
                          f"qe{qpm_empty:04d}to{time_after_asp:03d}")

    def asp_transport_air_volume(self, asp_transport_air_volume = 100, flow_rate = 1000):
        self.send_command(f"00ATid{self.id:04d}tv{asp_transport_air_volume:05d}fr{flow_rate:05d}")

    def start_adc(self):
        self.send_command(f"00AXid{self.id:04d}")

    def stop_adc(self):
        self.send_command(f"00AYid{self.id:04d}")

    def disp_transport_air_volume(self, flow_rate = 10):
        self.send_command(f"00DTid{self.id:04d}fr{flow_rate:05d}")

    def disp(self,  flow_rate=4000,
                    stop_speed=4000,
                    pressure_sensor=0,
                    qpm=0,
                    qpm_clot=0,
                    qpm_foam=0,
                    time_after_disp=10):

        self.send_command(f"00DEid{self.id:04d}fr{flow_rate:05d}ss{stop_speed:05d}"
                          f"bi{pressure_sensor:01d}qm{qpm:01d}qc{qpm_clot:04d}"
                          f"qf{qpm_foam:04d}to{time_after_disp:03d}")

    def re_number_of_pressure_data_recorded(self):
        self.send_command(f"00QHid{self.id:04d}")

    def re_pressure_data(self, start_index = 0, number_of_values_requested = 1):
        self.send_command(f"00QIid{self.id:04d}li{start_index:04d}ln{number_of_values_requested:04d}")

    def switch_dispensing_drive_power_off(self):
        self.send_command(f"00DOid{self.id:04d}")

    def re_number_of_lld_data_recorded(self, lld_channel = 0):
        self.send_command(f"00RBid{self.id:04d}lc{lld_channel}")

    def re_lld_data(self, start_index = 0, number_of_values = 0, lld_channel = 0):
        self.send_command(f"00RLid{self.id:04d}li{start_index:04d}ln{number_of_values:02d}lc{lld_channel}")

    def re_instrument_status(self):
        self.send_command(f"00RQid{self.id:04d}")

    def re_error_code(self):
        self.send_command(f"00REid{self.id:04d}")

    def re_parameter_value(self, parameter_name = "ai"):
        self.send_command(f"00RAid{self.id:04d}ra"+parameter_name)

    def re_instrument_init_status(self):
        self.send_command(f"00QWid{self.id:04d}")

    def re_name_of_last_faulty_parameter(self):
        self.send_command(f"00VPid{self.id:04d}")

    def re_cycle_counter(self):
        self.send_command(f"00RVid{self.id:04d}")

    def re_lifetime_counter(self):
        self.send_command(f"00RYid{self.id:04d}")

    def re_technical_status(self):
        self.send_command(f"00QTid{self.id:04d}")

    """tip status"""

    def re_tips_pressure_status(self):
        self.send_command(f"00RTid{self.id:04d}")

    def re_monitoring_of_volume_in_tip(self):
        self.send_command(f"00VTid{self.id:04d}")

    """special commends"""

    def emergency_stop_on(self):
        self.send_command(f"00ESid{self.id:04d}")

    def emergency_stop_off(self):
        self.send_command(f"00SRid{self.id:04d}")

    def test_mode_status(self, on_off = 0):
        self.send_command(f"00TMid{self.id:04d}at{on_off}")

    def reset_tip_counter_after_change_of_adapter(self):
        self.send_command(f"00SCid{self.id:04d}")

    def save_counters_before_power_off(self):
        self.send_command(f"00AVid{self.id:04d}")

    def switch_leds_manually(self, blue= 0, red = 0, green = 0):
        self.send_command(f"00AVid{self.id:04d}sb{blue}sr{red}sg{green}")

    def master_switch_led(self, master_switch = 0):
        self.send_command(f"00AVid{self.id:04d}sm{master_switch}")

    def asp_blow_out_vol(self, blow_out_vol=1000, flow_rate=15000):
        self.send_command(f"00ABid{self.id:04d}fr{blow_out_vol:05d}fr{flow_rate:05d}")

    def asp_all(self):
        self.asp_blow_out_vol()
        time.sleep(0.5)
        self.mixing_asp()
        time.sleep(0.5)
        self.asp()
        time.sleep(5)
        self.asp_transport_air_volume()
        time.sleep(2)
        self.start_adc()
        time.sleep(2)
        self.stop_adc()

@dataclass
class Aspirate_event:
    source_container:object
    volume:float = 0

@dataclass
class Dispense_event:
    destination_container:object
    volume: float = 0


class Planner():
    def __init__(self):
        self.source_plate = brb.plate0 # only one plate in brb
        self.destination_plate = brb.tube_rack # only one tube rack in brb
        self.sequence = {'asp':[],'disp':[]}

    def generate_events(self, samples:list, volume:float):

        for index, sample_id in enumerate(samples):

            tube_id = index % NUM_OF_TUBES_IN_RACK

            aspirate_event_here = Aspirate_event(source_container=self.source_plate.containers[sample_id],
                                                 volume=volume)
            self.sequence['asp'].append(aspirate_event_here)

            if index < 4:
                dispense_event_here = Dispense_event(destination_container=self.destination_plate.tubes[tube_id],
                                                     volume=volume)
                self.sequence['disp'].append(dispense_event_here)

        logger.debug('Pipette asp and disp sequence is generated.')

        return self.sequence


class PipetterControl():

    '''
    Primary methods includes: draw_liquid_with_id(), dispense_liquid_with_id(), draw_and_dispense_liquid_with_sequence()
    '''

    def __init__(self, re_config_grbl=False):

        self.ROBOT_NAME = 'miniPi'
        self.serial = serial.Serial('COM3', 115200, timeout=0.2)

        # load settings from json
        with open(PIPETTER_COORDINATES_FILE_PATH, 'r') as config_file:
            self.config = json.load(config_file)

        self.time_step_for_pick_tip = self.config['time_step_for_pick_tip']
        self.ZeusTraversePosition = self.config['ZeusTraversePosition']
        self.max_x = self.config['max_x']
        self.max_y = self.config['max_y']
        self.xy_offset = self.config['xy_offset'] # offsets in x and y, negative to right, closer; positive, to left, further
        self.trash_xy = self.config['trash_xy']
        self.idle_xy = self.config['idle_xy']
        self.xy_position = None
        self.z_position = None

        # generate pipetting sequence
        self.sequence = Planner().generate_events(samples=list(range(54)), volume=5000) #5000 means 500ul, subject to change
        time.sleep(2) # not sure why, but his sleep is needed.

        # config grbl if needed
        if re_config_grbl:
            self.configure_grbl()

        # home xyz
        self.home()
        time.sleep(2)

        # init zeus
        self.zeus = Zeus()
        time.sleep(1)
        self.zeus.init()
        time.sleep(1)

        # if pipetter is at standby location
        self.is_at_standby = False
        logger.info(f'The miniPi is initialized!')

    def send_to_xy_stage(self,
                         command,
                         wait_for_ok=True,
                         verbose=False,
                         read_all=False) -> None:

        ser = self.serial
        ser.write(str.encode(command + '\r\n'))
        if verbose:
            logger.info('SENT: {0}'.format(command))

        if wait_for_ok:
            if verbose:
                logger.info('Waiting for ok...')
            while True:
                line = ser.readline()
                if b'Alarm' in line:
                    logger.error('GRBL ALARM: GRBL wend into alarm. Overrode it with $X.')
                    self.send_to_xy_stage('$X')
                    break
                if verbose:
                    logger.info(line)
                if b'ok' in line:
                    break

        if read_all:
            if verbose:
                logger.info('Reading all...')
            while True:
                line = ser.readline()
                if verbose:
                    logger.info(line)
                if line == b'':
                    break

    def configure_grbl(self):
        from pathlib import Path
        grbl_path = str(Path.cwd()) + ("\\config\\miniPi\\grbl_settings.txt")
        with open(grbl_path, 'r') as grbl_config_file:
            for line in grbl_config_file:
               self.send_to_xy_stage(command = line.split('    (')[0], read_all= True, verbose= True)

        logger.info("XY stage configured!")

    def xy_pos(self) -> None:
        self.send_to_xy_stage(command= '?', read_all= True, verbose= False)

    def time_that_xy_motion_takes(self, dx: int, dy: int):

        acceleration, max_speed_x = None,None

        with open(PIPETTER_GRBL_SETTINGS_FILE_PATH,'r') as file:
            for line in file:
                if '$120' in line:
                    acceleration_x = float(line.split(' ')[2])
                if '$121' in line:
                    acceleration_y = float(line.split(' ')[2])
                if '$110' in line:
                    max_speed_x = float(line.split(' ')[2])/60
                if '$111' in line:
                    max_speed_y = float(line.split(' ')[2])/60

        travel_times = []

        for index, distance in enumerate([abs(dx), abs(dy)]):

            if index == 0:
                acceleration = acceleration_x
                max_speed = max_speed_x
            elif index == 1:
                acceleration = acceleration_y
                max_speed = max_speed_y

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

    def time_that_z_motion_takes(self, dz:float):

        with open(PIPETTER_GRBL_SETTINGS_FILE_PATH,'r') as file:
            for line in file:
                if '$122' in line:
                    acceleration_z = float(line.split(' ')[2])
                if '$112' in line:
                    max_speed_z = float(line.split(' ')[2])/60

        halfdistance = dz / 2
        # constant acceleration scenario
        constant_acceleration_halftime = np.sqrt(halfdistance * 2 / acceleration_z)
        speed_at_midpoint = constant_acceleration_halftime * acceleration_z
        if speed_at_midpoint <= max_speed_z:
            time_here = constant_acceleration_halftime * 2
        else:
            # this means that the stage reaches max speed before midpoint and then
            #   continues at his max speed
            constant_acceleration_halftime = max_speed_z / acceleration_z
            dist_traveled_at_constant_acceleration = acceleration_z * (constant_acceleration_halftime ** 2) / 2
            distance_traveled_at_constant_speed = halfdistance - dist_traveled_at_constant_acceleration
            const_speed_halftime = distance_traveled_at_constant_speed / max_speed_z
            time_here = 2 * (constant_acceleration_halftime + const_speed_halftime)
        # print(max(travel_times))
        return time_here
    def reload_tip_rack(self):
        brb.load_new_tip_rack(rack_reload='1000ul')

    def move_xy(self, xy: tuple, verbose=False, ensure_traverse_height=True, block_until_motion_is_completed=True,
                use_time_estimate=True):

        # all coordinates are negative
        if xy[0] < self.max_x or xy[0] > 0:
            logger.error(f'XY STAGE ERROR: target X is beyond the limit ({self.max_x}, 0). Motion aborted.')
            return
        if xy[1] < self.max_y or xy[1] > 0:
            logger.error(f'XY STAGE ERROR: target Y is beyond the limit ({self.max_y}, 0). Motion aborted.')
            return


        zeus_at_traverse_height = (self.z_position >= self.ZeusTraversePosition) or self.z_position == 0

        if ensure_traverse_height and not zeus_at_traverse_height:
            logger.error(f'ERROR: ZEUS was not in traverse height before motion, but instead at {self.z_position}.\n'
                  f'Motion aborted!')
            return

        # if np.linalg.norm(np.array((x, y))) <= R:
        self.send_to_xy_stage(command= 'G0 X{0:.3f} Y{1:.3f}'.format(xy[0] + self.xy_offset[0], xy[1] + self.xy_offset[1]),
                         read_all=False)

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
                        logger.debug(f'Status read {i}')
                    self.serial.write(str.encode('?' + '\r\n'))
                    while True:
                        line = self.serial.readline()
                        if verbose:
                            logger.info(line)
                        if b'Idle' in line:
                            finished_moving = True
                        if line == b'': # this means the motion is done!
                            break
                # print(f'{time.time() - t0}')

                if verbose:
                    logger.debug('Finished moving xy stage')
            self.xy_position = xy

    def move_xy_rel(self, displacement: tuple = (0,0)):
        current_position = self.xy_position
        target_position = tuple(map(operator.add, current_position, displacement))

        self.move_xy(target_position)


    def move_z(self, target_z:int, limit = -140, use_time_estimate=True):

        if target_z < limit:
            logger.error(f"z_pos {target_z} is not possible, limit: {limit} reached!")
            return

        self.send_to_xy_stage(command=f'G0 Z{target_z}',
                         read_all=False, verbose=False)

        t0 = time.time()
        # monitor if the movement is completed.
        if use_time_estimate:
            dz = abs(abs(target_z)-abs(self.z_position))
            time_for_movement = self.time_that_z_motion_takes(dz=dz)
            # wait until the movement finishes.
            while 1:
                if time.time() - t0 > time_for_movement:
                    # print(f'time needed is {time_for_movement}')
                    break

        self.z_position = target_z

        return True

    def move_z_rel(self, distance):
        current_z_position = self.z_position
        target_position = current_z_position + distance
        self.move_z(target_z=target_position)


    def wait_until_zeus_reaches_traverse_height(self):

        while 1:
            if self.z_position == self.ZeusTraversePosition:
                break

        return True

    def home(self):
        self.send_to_xy_stage(command = '$H', read_all=True, verbose=False,)
        self.xy_position = (-2,-2) # home pull-off distance is 2mm, see grbl settings $27
        self.z_position = -2 # home pull-off distance is 2mm, see grbl settings $27
        logger.info('The gantry is homed!')

    def kill_alarm(self) -> None:
        self.send_to_xy_stage("$X", read_all= True, verbose= True)

    def view_grbl_settings(self)-> None:
        self.send_to_xy_stage('$$', read_all=True, verbose=True)
        self.xy_pos()

    def move_through_wells(self, plate: object, dwell_time=0.1, ensure_traverse_height=True):
        for container in plate.containers:
            logger.debug(f'This is well index: {container}')
            self.move_xy(container.xy, ensure_traverse_height=ensure_traverse_height)
            time.sleep(dwell_time)

    def move_to_trash_bin(self, ensure_traverse_height=True):
        self.move_xy(self.trash_xy, ensure_traverse_height=ensure_traverse_height)

    def move_to_idle_position(self, ensure_traverse_height=True):
        self.move_xy(self.idle_xy, ensure_traverse_height=ensure_traverse_height)

    def move_to_traverse_height(self):
        self.move_z(self.ZeusTraversePosition)

    # def beep_n(self):
    #     duration = 600  # milliseconds
    #     freq = 1500  # Hz
    #     # time.sleep(0.2)
    #     for i in range(10):
    #         winsound.Beep(freq, duration)

    # def beep(self):
    #     duration = 600  # milliseconds
    #     freq = 1000  # Hz
    #     # time.sleep(0.2)
    #     winsound.Beep(freq, duration)

    def pick_tip(self):

        tip_type = '1000ul' # for miniPi, only 1000 ul tips are used.

        if self.zeus.tip_status_req():
            logger.error(f'ERROR: There is already a tip on ZEUS. Please remove it before picking up a new one.')
            return

        with open(PIPETTER_TIP_RACK_FILE_PATH) as json_file:
            tip_rack = json.load(json_file)

        self.move_z(self.ZeusTraversePosition)

        # if the rack is empty then ask user to reload
        if not any(item['exists'] for item in tip_rack[tip_type]['tips']):

            for i in range(30):
                # winsound.Beep(1100, 200)
                time.sleep(0.3)

            input(f'ERROR: The tip rack is empty. Please reload the tip rack and hit enter.')
            tip_rack = brb.load_new_tip_rack(rack_reload=tip_type)

        # In the rack, find the first tip that exists
        for item in tip_rack[tip_type]['tips']:
            if item['exists']:
                # pick up tip
                self.move_xy(item['xy'], ensure_traverse_height=True)

                self.zeus.tip_pick_up(tip_type=item['tipTypeTableIndex'])

                self.move_z(self.config['beginningofTipPickPosition'])

                for step in range(1,12): # go downward slowly step by step
                    downward_step = -self.config['downwardDistance']/11
                    self.move_z_rel(downward_step) # each step is one tenth of downward distance
                    time.sleep(self.time_step_for_pick_tip)
                    if self.zeus.tip_status_req():
                        # When the tip touch the end of the zeus, the tip is still not sealed. So two more steps are added.
                        self.move_z_rel(downward_step)
                        break

                self.move_z(self.ZeusTraversePosition)

                if self.zeus.tip_status_req():

                    self.zeus.tip_on_zeus = '1000ul'

                    item['exists'] = False
                    with open(PIPETTER_TIP_RACK_FILE_PATH, 'w', encoding='utf-8') as f:
                        json.dump(tip_rack, f, ensure_ascii=False, indent=4)
                else:
                    self.zeus.tip_on_zeus=''
                    logger.info("tips_on_zeus is set to empty!")
                    raise ValueError('No tip is picked up.')

                return True

        logger.error('ERROR: No tips in rack.')
        raise Exception

    def discard_tip(self):
        self.move_z(self.ZeusTraversePosition)

        if self.zeus.tip_on_zeus != '':
            self.move_xy(self.trash_xy)
            self.zeus.tip_discard()
            self.zeus.tip_on_zeus = ''

        elif self.zeus.tip_on_zeus == '':
            logger.error('ERROR: No tip on zeus to discard. Continue...')

    def change_tip(self):
        if self.zeus.tip_on_zeus != '':
            self.discard_tip()

        self.pick_tip()

    def draw_liquid(self, xy:tuple, asp_height: float, volume:float, n_retries=3) -> bool:

        if self.zeus.tip_on_zeus =='':
            self.pick_tip()

        if self.zeus.tip_on_zeus == '':
            logger.error('ERROR: No tip on zeus to draw.')
            return False

        self.move_to_traverse_height()
        self.move_xy(xy)
        self.move_z(asp_height)
        time.sleep(0.5)

        for retry in range(n_retries):
            try:
                self.zeus.asp_blow_out_vol()
                self.zeus.mixing_asp()
                self.zeus.aspirate(asp_volume=volume,
                                 overasp=100,
                                 flow_rate=2000,
                                 stop_speed=2000,
                                 qpm=0,
                                 pressure_sensor=0,
                                 qpm_clot=0,
                                 qpm_foam=0,
                                 qpm_empty=0,
                                 time_after_asp=10)
                self.zeus.asp_transport_air_volume()
                self.zeus.start_adc()
                self.zeus.stop_adc()

                self.move_z(self.ZeusTraversePosition)

                return True

            except ValueError:
                if self.zeus.zeus_error_code(self.zeus.r.received_msg) == '81': # Empty tube detected during aspiration
                    logger.error('ZEUS ERROR: Empty tube during aspiration. Dispensing and trying again.')
                    continue

        logger.error(f'Tried {n_retries} but zeus error is still there')
        raise Exception

    def dispense_liquid(self, xy: tuple=brb.tube_rack.tubes[0].xy, disp_height=brb.tube_rack.tubes[0].disp_height):

        self.move_to_traverse_height()
        self.move_xy(xy)
        self.move_z(disp_height)

        try:
            self.zeus.disp(flow_rate=4000,
                           stop_speed=4000,
                           pressure_sensor=0,
                           qpm=0,
                           qpm_clot=0,
                           qpm_foam=0,
                           time_after_disp=10)
            self.move_to_traverse_height()
            # print(f'DEBUG::dispense_liquid():: disp_liquidSurface: {transfer_event.disp_liquidSurface} ')

        except ValueError:
            logger.error('Zeus error during dispensing is ignored!')
            self.zeus.move_z(self.ZeusTraversePosition)
            pass

        return True

    def draw_and_dispense_liquid_with_sequence(self, ids:list):

        sequence_here = [self.sequence[i] for i in ids if self.sequence[i].source_container.id == i]
        logger.debug(f'sequence to be executed: {sequence_here}')

        for event in sequence_here:
            self.draw_liquid(xy=event.source_container.xy,
                             asp_height=event.source_container.asp_height,
                             volume=event.volume)
            self.dispense_liquid(xy=event.destination_container.xy,
                                 disp_height=event.destination_container.disp_height)
            self.discard_tip()

    def find_event_with_correct_vial_id(self, sample_id):
        event_here = None

        for event in self.sequence:
            if sample_id == event.source_container.id:
                event_here = event
        return event_here

    def aspirate(self, sample_id):

        """
        The method draws one liquid into a tip according to the sample id.
        sample id: 0-53
        """
        event_here = None
        for event in self.sequence['asp']:
            if event.source_container.id == sample_id:
                event_here = event

        assert (event_here is not None), 'Error: the aspirate event to be run is empty!'

        logger.debug(f'sequence to be executed: {event_here}')

        self.draw_liquid(xy=event_here.source_container.xy,
                         asp_height=event_here.source_container.asp_height,
                         volume=event_here.volume)
    def refill(self, tube_id):

        """
        The method dispenses one liquid from the tip into the vial
        with the specified id.

        tube_id: 1-4
        """

        event_here = None
        for event in self.sequence['disp']:
            if event.destination_container.id == tube_id:
                event_here = event
        assert (event_here is not None), 'Error: the dispense event to be run is empty!'

        logger.debug(f'sequence to be executed: {event_here}')

        self.dispense_liquid(xy=event_here.destination_container.xy,
                             disp_height=event_here.destination_container.disp_height)

        self.discard_tip()

    def standby(self):

        """
        A series of actions will be executed: move to traverse height,
        move to trash bin, and init zeus (tip will be discarded).
        """

        if not self.is_at_standby:
            self.move_to_traverse_height()
            self.move_to_trash_bin()
            self.zeus.init()
            self.is_at_standby = True
            return True

        elif self.is_at_standby:
            logger.debug('Pipetter is already at standby.')
            return True

        else:
            raise ValueError('Pipetter is_at_standy state is messed up, double check.')


if __name__ == '__main__':

    pt = PipetterControl()

    ls = pt.sequence
    lsa = pt.sequence['asp']
    lsb = pt.sequence['disp']

    # for i in range(4):
    #     pt.aspirate(i)
    #     pt.refill(i)












