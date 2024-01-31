"""

The pipetter module combines gantry and zeus, and deals with actions including pick_tip, discard_tip, draw_liquid,
dispense_liquid, transfer_liquid and so on.

"""
import asyncio
import logging

pipetter_logger = logging.getLogger('main.pipetter')

import copy, json, time, numpy as np, serial, re, winsound

# import breadboard as brb, sound


## get config file path from breadboard
CONFIG_PATH = brb.CONFIG_PATH
STATUS_PATH = brb.STATUS_PATH

# load config file from json
with open(CONFIG_PATH + 'pipetter.json', 'r') as config_file:
    config_pt = json.load(config_file)

class Gantry():
    """
    The xy gantry moves with Zeus on it.

    Gantry() take zeus object as argument, which is used to request position of Z drive.
    Only when the Z drive position is in safe traverse height will the gantry be able to move.
    """

    xy_position = ((0, 0)) # this is to store the gantry position after every move.

    def __init__(self,
                 zeus: object, # pass the zeus module to gantry, this is for checking traverse height,
                 max_x: int = config_pt['gantry']['max_x'], # -820,
                 max_y: int = config_pt['gantry']['max_y'], #-360,
                 horiz_speed: int = config_pt['gantry']['horiz_speed'],#200*60,# horizontal speed in mm / min
                 xy_offset: tuple = config_pt['gantry']['xy_offset'], #(-2.5, 0),# offsets in x and y, negative to right, closer; positive, to left, further
                 zeus_traverse_position: int = config_pt['gantry']['zeus_traverse_position'], #880,
                 trash_xy: tuple = config_pt['gantry']['trash_xy'], #(-500, -70),
                 idle_xy: tuple = config_pt['gantry']['idle_xy'], #(-500, -220),

                 ):
        self.logger = logging.getLogger('main.gantry.Gantry')
        self.logger.info('gantry is initiating...')
        self.serial = serial.Serial('COM5', 115200, timeout=0.2)
        self.horiz_speed = horiz_speed # horizontal speed in mm/min
        self.xy_offset = xy_offset
        self.max_x = max_x
        self.max_y = max_y

        self.trash_xy = trash_xy
        self.idle_xy = idle_xy

        self.zm = zeus
        self.zeus_traverse_position = zeus_traverse_position
        # self.home_xy()
        self.left_balance = config_pt['gantry']['balance_left_boundary']
        self.upper_balance = config_pt['gantry']['balance_chamber_upper_boundary']
        self.lower_balance = config_pt['gantry']['balance_chamber_lower_boundary']

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
                    self.send_to_xy_stage('$X')
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
        with open(CONFIG_PATH + "\\grbl_settings.txt", 'r') as grbl_config_file:
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

        # print(f'Moving to {xy}...')

        if xy[0] < self.max_x or xy[0] > 0:
            self.logger.error(f'XY STAGE ERROR: target X is beyond the limit ({self.max_x}, 0). Motion aborted.')
            raise ValueError(f'XY STAGE ERROR: target X is beyond the limit ({self.max_x}, 0). Motion aborted.')

        if xy[1] < self.max_y or xy[1] > 0:
            self.logger.error(f'XY STAGE ERROR: target Y is beyond the limit ({self.max_y}, 0). Motion aborted.')
            raise ValueError(f'XY STAGE ERROR: target Y is beyond the limit ({self.max_y}, 0). Motion aborted.')

        # avoid collision with the balance

        if xy[0] < self.left_balance and (xy[1] > -self.upper_balance or xy[1] < -self.lower_balance):
            self.logger.error('XY STAGE ERROR: gantry is going to collide with the balance. Motion aborted.')
            return

        # if move from inside the balance to outside, or vice verse, move to the idle position first
        if (self.xy_position[0] < -600 and xy[1] > -200) or\
                (self. xy_position[1] > -200 and xy[0] < -600 ):
            self.send_to_xy_stage(
                command='G0 X{0:.3f} Y{1:.3f}'.format(self.idle_xy[0], self.idle_xy[1]),
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

    def home_xy(self, ensure_traverse_height=True) -> None:
        self.logger.info('The gantry is homing...')
        self.zm.move_z(self.zm.ZeusTraversePosition)
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

    def move_to_trash_bin(self, ensure_traverse_height=True):
        self.move_xy(self.trash_xy, ensure_traverse_height=ensure_traverse_height)

    def move_to_idle_position(self, ensure_traverse_height=True):
        self.move_xy(self.idle_xy, ensure_traverse_height=ensure_traverse_height)


class Pipetter():

    def __init__(self,
                 zeus: object,
                 gantry: object,
                 is_balance_involved: bool = False
                 ):
        self.zeus = zeus
        self.gantry = gantry
        if is_balance_involved:
            self.balance = serial.Serial(port=config_pt["balance_port"]["port"],
                                         baudrate=config_pt["balance_port"]["baudrate"],
                                         stopbits=serial.STOPBITS_ONE,
                                         parity=serial.PARITY_NONE,
                                         timeout=config_pt["balance_port"]["timeout"])
            print('A balance is installed.')
        else:
            print('No balance is installed.')

        self.logger = logging.getLogger('main.pipetter.Pipetter')
        self.logger.info('creating an instance of Pepetter')

    def home_xy(self):
        self.gantry.home_xy()

    def beep_n(self):
        duration = 600  # milliseconds
        freq = 1000  # Hz
        # time.sleep(0.2)
        for i in range(10):
            winsound.Beep(freq, duration)

    def pick_tip(self, tip_type: str):

        with open(STATUS_PATH + 'tip_rack.json') as json_file:
            tip_rack = json.load(json_file)

        self.zeus.move_z(config_pt['gantry']['zeus_traverse_position'])
        self.zeus.wait_until_zeus_reaches_traverse_height()

        # if the rack is empty then ask user to reload
        if not any(item['exists'] for item in tip_rack[tip_type]['tips']):
            sound.beep_for_tip_changing()
            input(f'ERROR: The tip rack is empty. Please reload the tip rack and hit enter.')
            tip_rack = brb.load_new_tip_rack(rack_reload=tip_type)

        # In the rack, find the first tip that exists
        for item in tip_rack[tip_type]['tips']:
            if item['exists']:
                # pick up tip
                self.gantry.move_xy(item['xy'], ensure_traverse_height=True)
                time.sleep(0.5)
                self.zeus.pickUpTip(tipTypeTableIndex=item['tipTypeTableIndex'],
                                    deckGeometryTableIndex=item['deckGeometryTableIndex'])

                self.zeus.wait_until_zeus_responds_with_string('GTid')
                tip_is_picked = self.zeus.getTipPresenceStatus()

                if tip_is_picked:
                    # print(f'tip_status: {self.zeus.getTipPresenceStatus()}')
                    self.zeus.tip_on_zeus = tip_type
                    logging.info(f'Now the tip on zeus is : {tip_type}')
                    item['exists'] = False
                    # wait_until_zeus_reaches_traverse_height()
                    # update json file
                    with open(STATUS_PATH + 'tip_rack.json', 'w', encoding='utf-8') as f:
                        json.dump(tip_rack, f, ensure_ascii=False, indent=4)
                else:
                    raise ValueError('No tip is picked up.')
                return True
        self.logger.info('ERROR: No tips in rack.')
        raise Exception

    def discard_tip(self):
        self.zeus.move_z(config_pt['gantry']['zeus_traverse_position'])
        self.zeus.wait_until_zeus_reaches_traverse_height()
        self.gantry.move_xy(self.gantry.trash_xy)
        self.zeus.discardTip(deckGeometryTableIndex=1)
        self.zeus.tip_on_zeus = ''
        # time.sleep(0.25)
        # self.zeus.move_z(self.zeus.ZeusTraversePosition)
        self.zeus.wait_until_zeus_responds_with_string('GUid')

    def change_tip(self, tip_rack: str):
        if self.zeus.tip_on_zeus != '':
            self.discard_tip()
        self.pick_tip(tip_rack)
        # self.zeus.wait_until_zeus_responds_with_string('GUid')

    def check_volume_in_container(self, container: object,
                                  liquidClassTableIndex: int = 13, lld: int = 1,
                                  lldSearchPosition: int = 1300, liquidSurface: int = 1300,
                                  tip_for_volume_check: str = '300ul',
                                  change_tip_after_each_check: bool = True):

        if change_tip_after_each_check:
            self.change_tip(tip_for_volume_check)
        else:
            if self.zeus.tip_on_zeus != tip_for_volume_check:
                self.change_tip(tip_for_volume_check)

        self.zeus.move_z(config_pt['gantry']['zeus_traverse_position'], raise_exception=False)
        time.sleep(1)
        self.gantry.move_xy(container.xy)

        self.zeus.volumeCheck(containerGeometryTableIndex=container.containerGeometryTableIndex,
                              deckGeometryTableIndex=brb.deckGeometryTableIndex[tip_for_volume_check],
                              liquidClassTableIndex=liquidClassTableIndex,
                              lld=lld,
                              lldSearchPosition=lldSearchPosition,
                              liquidSurface=liquidSurface)

        received_msg = self.zeus.r.received_msg
        while 'yl' not in received_msg:
            time.sleep(1)
            received_msg = self.zeus.r.received_msg

        if not self.zeus.zeus_had_error(received_msg):
            # print(received_msg)
            liquid_surface = received_msg[received_msg.find('yl') + 2:received_msg.find('yl') + 6]
            # volume = received_msg[received_msg.find('aw') + 2:received_msg.find('aw') + 8] # This value is from Zeus and not precise.

            ## calculate the volume manually
            volume = ((container.bottomPosition-int(liquid_surface)) / 10)  * container.area # this is in mm^3, uL
            print(f'Volume Check done! liquid_surface: {liquid_surface}, volume: {volume}')

        else:
            print(f'Liquid level not detected')
            liquid_surface = 0
            volume = 0
            self.zeus.move_z(config_pt['gantry']['zeus_traverse_position'], raise_exception=False)
            # self.change_tip(tip_for_volume_check, raise_exception=False)
            self.change_tip(tip_for_volume_check)

        print(f'Volume Check done! liquid_surface: {liquid_surface}, volume: {volume}')
        return (int(liquid_surface), float(int(volume) / 10))  # after / 10, volume is in ul


    def draw_liquid(self, transfer_event: object, n_retries=3) -> bool:

        self.zeus.move_z(config_pt['gantry']['zeus_traverse_position'])
        self.gantry.move_xy(transfer_event.source_container.xy)

        for retry in range(n_retries):
            try:
                # print(f'Aspiration volume for zeus: {int(round(transfer_event.aspirationVolume * 10))}')
                self.zeus.aspiration(aspirationVolume=int(round(transfer_event.transfer_volume * 10)), # volume in 0.1 ul
                                     containerGeometryTableIndex=transfer_event.asp_containerGeometryTableIndex,
                                     deckGeometryTableIndex=transfer_event.asp_deckGeometryTableIndex,
                                     liquidClassTableIndex=transfer_event.liquidClassTableIndex,
                                     qpm=transfer_event.asp_qpm,
                                     lld=transfer_event.asp_lld,
                                     liquidSurface = transfer_event.source_container.liquid_surface_height,
                                     lldSearchPosition= transfer_event.source_container.liquid_surface_height - 50,
                                     mixVolume=transfer_event.asp_mixVolume,
                                     mixFlowRate=transfer_event.asp_mixFlowRate,
                                     mixCycles=transfer_event.asp_mixCycles)
                print(f'DEBUG:liquid surface height in source container: {transfer_event.source_container.liquid_surface_height} ')

                # Replace this sleep with a proper check. Why do you even need a sleep if next function is zeus.wait_until...???
                # time.sleep(2)
                self.zeus.wait_until_zeus_responds_with_string('GAid')
                return True

            except ZeusError:
                if self.zeus.zeus_error_code(self.zeus.r.received_msg) == '81':
                    # Empty tube detected during aspiration
                    self.logger.info('ZEUS ERROR: Empty tube during aspiration. Dispensing and trying again.')
                    time.sleep(2)
                    self.zeus.move_z(config_pt['gantry']['zeus_traverse_position'])
                    time.sleep(2)
                    self.dispense_liquid(transfer_event)
                    time.sleep(2)
                    continue

        self.logger.info(f'Tried {n_retries} but zeus error is still there')
        raise Exception

    async def draw_liquid_async(self, transfer_event: object, n_retries=3) -> bool:

        self.zeus.move_z(config_pt['gantry']['zeus_traverse_position'])
        self.gantry.move_xy(transfer_event.source_container.xy)

        await asyncio.sleep(1)

        for retry in range(n_retries):
            try:
                # print(f'Aspiration volume for zeus: {int(round(transfer_event.aspirationVolume * 10))}')
                self.zeus.aspiration(aspirationVolume=int(round(transfer_event.transfer_volume * 10)), # volume in 0.1 ul
                                     containerGeometryTableIndex=transfer_event.asp_containerGeometryTableIndex,
                                     deckGeometryTableIndex=transfer_event.asp_deckGeometryTableIndex,
                                     liquidClassTableIndex=transfer_event.liquidClassTableIndex,
                                     qpm=transfer_event.asp_qpm,
                                     lld=transfer_event.asp_lld,
                                     liquidSurface = transfer_event.source_container.liquid_surface_height,
                                     lldSearchPosition= transfer_event.source_container.liquid_surface_height - 50,
                                     mixVolume=transfer_event.asp_mixVolume,
                                     mixFlowRate=transfer_event.asp_mixFlowRate,
                                     mixCycles=transfer_event.asp_mixCycles)
                print(f'DEBUG:liquid surface height in source container: {transfer_event.source_container.liquid_surface_height} ')

                # Replace this sleep with a proper check. Why do you even need a sleep if next function is zeus.wait_until...???
                # time.sleep(2)
                self.zeus.wait_until_zeus_responds_with_string('GAid')
                return True

            except ZeusError:
                if self.zeus.zeus_error_code(self.zeus.r.received_msg) == '81':
                    # Empty tube detected during aspiration
                    self.logger.info('ZEUS ERROR: Empty tube during aspiration. Dispensing and trying again.')
                    time.sleep(2)
                    self.zeus.move_z(config_pt['gantry']['zeus_traverse_position'])
                    time.sleep(2)
                    self.dispense_liquid(transfer_event)
                    time.sleep(2)
                    continue

        self.logger.info(f'Tried {n_retries} but zeus error is still there')
        raise Exception

    def dispense_liquid(self, transfer_event: object) -> None:

        self.zeus.move_z(config_pt['gantry']['zeus_traverse_position'])
        self.gantry.move_xy(transfer_event.destination_container.xy)

        self.zeus.dispensing(dispensingVolume=int(round(transfer_event.transfer_volume * 10)),
                             containerGeometryTableIndex=transfer_event.disp_containerGeometryTableIndex,
                             deckGeometryTableIndex=transfer_event.disp_deckGeometryTableIndex,
                             liquidClassTableIndex=transfer_event.liquidClassTableIndex,
                             lld=transfer_event.disp_lld,
                             lldSearchPosition=transfer_event.destination_container.liquid_surface_height - 50,
                             liquidSurface=transfer_event.destination_container.liquid_surface_height,
                             searchBottomMode=transfer_event.searchBottomMode,
                             mixVolume=transfer_event.disp_mixVolume,
                             mixFlowRate=transfer_event.disp_mixVolume,
                             mixCycles=transfer_event.disp_mixCycles)
        # print(f'DEBUG::dispense_liquid():: disp_liquidSurface: {transfer_event.disp_liquidSurface} ')

        # time.sleep(0.25)
        # wait_until_zeus_reaches_traverse_height()
        self.zeus.wait_until_zeus_responds_with_string('GDid')

    def transfer_liquid(self, transfer_event: object, max_volume: int=None):

        if max_volume is None:
            max_volume = int(transfer_event.tip_type[:-2])

        # check if container is full.
        # if transfer_event.destination_container.liquid_volume > transfer_event.destination_container.volume_max:
        #     print(f'transfer_event.destination_container.liquid_volume:{transfer_event.destination_container.container_id}, {transfer_event.destination_container.liquid_volume}')
        #     raise ValueError('The target container is full. Dispensing is aborted')

        # if it exceeds max_volume, then do several pipettings
        N_max_vol_pipettings = int(transfer_event.transfer_volume // max_volume)
        # print(f'N_max_vol_pipettings: {N_max_vol_pipettings}')

        for i in range(N_max_vol_pipettings):
            # print(f'Pipetting {i+1} of {N_max_vol_pipettings}')
            _split_event_1 = copy.deepcopy(transfer_event)
            _split_event_1.transfer_volume = max_volume # volume in ul
            _split_event_1.transfer_volume = max_volume # volume in ul
            # print(f'Aspiration volume: {_split_event_1.aspirationVolume}ul ')
            # print(f'Dispensing volume: {_split_event_1.dispensingVolume}ul ')
            self.draw_liquid(_split_event_1)
            # print(f'DEBUG: transfer_liquid()::disp_height: {transfer_event.disp_liquidSurface}')
            liquid_surface_height_from_zeus = self.detect_liquid_surface()
            self.dispense_liquid(_split_event_1)

        volume_of_last_pipetting = transfer_event.transfer_volume % max_volume
        if volume_of_last_pipetting:
            _split_event_2 = copy.deepcopy(transfer_event)
            _split_event_2.transfer_volume = volume_of_last_pipetting
            _split_event_2.transfer_volume = volume_of_last_pipetting
            self.draw_liquid(_split_event_2)
            liquid_surface_height_from_zeus = self.detect_liquid_surface()
            self.dispense_liquid(_split_event_2)

        # self.logger.info(f'Aspiration volume: {transfer_event.aspirationVolume}ul '
        #                  f'Dispensing volume: {transfer_event.dispensingVolume}ul')

        return liquid_surface_height_from_zeus

    def detect_liquid_surface(self) -> int:
        self.zeus.sendCommand('GNid0001')
        time.sleep(0.25)
        liquid_surface_height_detected = re.findall('[0-9]+', self.zeus.r.received_msg)[1]

        # self.logger.info(f'liquid_surface_height_detected: {liquid_surface_height_detected}')
        return int(liquid_surface_height_detected)

    def send_command_to_balance(self, command, read_all=True, verbose=False):

        self.balance.write(str.encode(command + '\n'))
        while True:
            line = self.balance.readline()
            if verbose:
                print(f'Response from balance. {line}')
            if line == b'':
                break

    def balance_tare(self, verbose=False):
        self.balance.write(str.encode('T\n'))
        taring_complete = False
        while True:
            line = self.balance.readline()
            if b'T' in line:
                taring_complete = True
            if verbose:
                pass
                # print(f'Tare in progress. Response from balance. {line}')
            if line == b'':
                if taring_complete:
                    print('The balance is tared.')
                    break

    def balance_zero(self, verbose=True):
        self.balance.write(str.encode('Z\n'))
        zeroing_complete = False
        time_stamp = time.time()
        while True:
            line = self.balance.readline()
            if b'Z' in line:
                zeroing_complete = True
            if verbose:
                print(f'Tare in progress. Response from balance. {line}')
                # pass
            if line == b'':
                if zeroing_complete:
                    print('The balanced is zeroed.')
                    break
            if time.time() - time_stamp > 10:
                self.logger.error(f'Balance zeroing took more than 10 seconds. Aborting.')
                zeroing_complete = False
                break
        return zeroing_complete

    def balance_value(self, read_all=True, verbose=False):
        value = 0
        self.balance.write(str.encode('SI\n'))
        measurement_successful = False
        while True:
            line = self.balance.readline()
            # print(f'balance line: {line}')
            if (b'S D' in line) or (b'S S' in line):
                raw_parsed = line.split(b' g\r\n')[0][-8:] # this is for balance XPE205
                raw_parsed = re.findall(r"[-+]?(?:\d*\.*\d+)", line.decode("utf-8") )[0] # this is for balance ME204

                if verbose:
                    print(f"Raw parsed: {raw_parsed}")
                value: float = float(raw_parsed)
                measurement_successful = True
            if b'S I' in line:
                'Balance command not executed.'
                time.sleep(5)
                self.balance.write(str.encode('SI\n'))
            if verbose:
                print(line)
            if line == b'':
                if measurement_successful:
                    break
        return value

    def open_balance_door(self):
        self.send_command_to_balance('WS 1')

    def close_balance_door(self):
        self.send_command_to_balance('WS 0')

    def move_to_balance(self, xy: tuple = brb.balance_cuvette.xy):
        self.open_balance_door()
        self.zeus.move_z(config_pt['gantry']['zeus_traverse_position'])
        self.gantry.move_xy(xy)

    def pipetting_to_balance_and_weight(self, transfer_event, timedelay= 5):
        global xy_position
        global weighted_values
        # print(f'xy_position: {xy_position}')
        # print(f'weighted_values: {weighted_values}')
        # if xy_position[0] < -80:
        #     move_xy((-80, -195))
        self.close_balance_door()
        print('Waiting for balance to settle...')
        time.sleep(timedelay)
        # balance_tare()
        # self.balance_zero(verbose=False)
        # print('Balance zeroed.')
        weight_before = self.balance_value()
        # print(f'weight_before: {weight_before} g')
        self.open_balance_door()
        # print('Waiting for liquid transfer...')
        self.transfer_liquid(transfer_event=transfer_event)

        # transfer_event.excute_event()

        time.sleep(0.5)
        self.gantry.move_to_idle_position()
        # self.close_balance_door()
        time.sleep(timedelay)
        weight_after = self.balance_value()
        # print(f'weight_after: {weight_after} g')

        pipetting_weight = round((weight_after - weight_before) * 1000, 6)  # mg
        pipetting_volume = round(pipetting_weight / transfer_event.source_container.substance_density, 2)
        self.logger.info(f'Weight of liquid transferred: {pipetting_weight} mg')
        self.logger.info(f'Volume of aliquottransferred: {pipetting_volume} ul')
        return pipetting_weight, pipetting_volume

    def pipetting_to_balance_and_weight_n_times(self, transfer_event, n_times=3,
                                                change_tip_after_every_pipetting:bool = False):
        print(f'this is transfer_event: {transfer_event}')
        transfer_volume = transfer_event.transfer_volume
        dict_for_one_event = {}
        dict_for_one_event[f'{transfer_event.substance}_{transfer_volume}ul'] = \
            {'weight': [], 'volume': [], 'liquid_class_index': [], 'tip_type': []}
        temp_dict = dict_for_one_event[f'{transfer_event.substance}_{transfer_volume}ul']

        for i in range(n_times):
            print(f'this is n_times: {i}/{n_times}')
            print(transfer_event.event_label)

            weight, volume = self.pipetting_to_balance_and_weight(transfer_event=transfer_event)

            if change_tip_after_every_pipetting:
                self.change_tip(transfer_event.tip_type)
                time.sleep(0.5)
                print(f'Changed tip to {transfer_event.tip_type} after {i}th pipetting.')
            temp_dict['weight'].append(weight)
            temp_dict['volume'].append(volume)
            temp_dict['liquid_class_index'].append(transfer_event.liquidClassTableIndex)
            temp_dict['tip_type'].append(transfer_event.tip_type)

        print(dict_for_one_event)
        return dict_for_one_event

    def pipetting_to_balance_and_weight_n_times_from_different_stock_vials(self, transfer_event, n_times=54,
                                                                           change_tip_after_every_pipetting:bool = False):
        # print(f'this is transfer_event: {transfer_event[0]}')
        dict_for_one_event = {}
        dict_for_one_event[f'{transfer_event[0][0].substance_name}_{transfer_event[0][0].aspirationVolume}ul'] = \
            {'weight': [], 'volume': [], 'liquid_class_index': [], 'tip_type': []}
        temp_dict = dict_for_one_event[f'{transfer_event[0][0].substance_name}_{transfer_event[0][0].aspirationVolume}ul']
        for i in range(n_times):
            print(f'this is n_times: {i}')
            print(transfer_event[0][0].event_label)
            weight, volume = self.pipetting_to_balance_and_weight(transfer_event=transfer_event[0][i])
            if change_tip_after_every_pipetting:
                self.change_tip(transfer_event[0][0].tip_type)
                time.sleep(0.5)
                print(f'Changed tip to {transfer_event[0][0].tip_type} after {i}th pipetting.')
            temp_dict['weight'].append(weight)
            temp_dict['volume'].append(volume)
            temp_dict['liquid_class_index'].append(transfer_event[0][0].asp_liquidClassTableIndex)
            temp_dict['tip_type'].append(transfer_event[0][0].tip_type)

        print(dict_for_one_event)
        return dict_for_one_event

    def close_ports_and_zeus(self):
        self.balance.close()
        self.gantry.serial.close()
        self.zeus.switchOff()

class ZeusError(Exception):
    pass


if __name__ == '__main__':
    import zeus
    import breadboard as brb
    #
    zm = zeus.ZeusModule(id = 1)
    time.sleep(3)
    #
    gt = Gantry(zeus=zm)
    time.sleep(2)
    #
    # # gt.kill_alarm()
    gt.home_xy()
    # time.sleep(5)
    #
    pt = Pipetter(zeus=zm, gantry=gt)
    time.sleep(2)
    # pt.close_balance_door()
    #
    # print("Init done!")

    # pt.check_volume_in_container(container = brb.plate5.containers[0],
    #                              containerGeometryTableIndex = brb.bottle_20ml.containerGeometryTableIndex,
    #                              deckGeometryTableIndex = brb.deckgeom_50ul.index,
    #                              liquidClassTableIndex = '21',
    #                              lld = 1,
    #                              lldSearchPosition = '1700',
    #                              liquidSurface='1700',
    #                              tip_for_volume_check='50ul')
    # time.sleep(2)
    # print(zm.r.received_msg)
    #
    # time.sleep(2)
    # print(zm.r.received_msg)

