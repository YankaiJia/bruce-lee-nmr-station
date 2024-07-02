"""

The pipetter module combines gantry and zeus, and deals with actions including pick_tip, discard_tip, draw_liquid,
dispense_liquid, transfer_liquid and so on.

"""
import logging
import zeus_lt as zlt

pipetter_logger = logging.getLogger('main.pipetter')

import copy, json,time, numpy as np, serial,re, winsound


# import breadboard as brb
# from calibration import calibrations as calib
# import planner as pln


class Gantry():

    """
    The xy gantry moves with Zeus on it.

    Gantry() take zeus object as argument, which is used to request position of Z drive.
    Only when the Z drive position is in safe traverse height will the gantry be able to move.
    """

    def __init__(self,
                 zeus: object, # pass the zeus module to gantry, this is for checking traverse height,
                 max_x: int = -820,
                 max_y: int = -360,
                 horiz_speed: int = 200*60,# horizontal speed in mm / min
                 xy_offset: tuple = (-2.5, -0.5),# offsets in x and y, negative to right, closer; positive, to left, further
                 zeus_traverse_position: int = 880,
                 trash_xy: tuple = (-500, -70),
                 idle_xy: tuple = (-500, -250),

                 ):
        self.logger = logging.getLogger('main.gantry.Gantry')
        self.logger.info('gantry is initiating...')
        self.serial = serial.Serial('COM6', 115200, timeout=0.2)
        self.horiz_speed = horiz_speed # horizontal speed in mm/min
        self.xy_offset = xy_offset
        self.max_x = max_x
        self.max_y = max_y

        self.trash_xy = trash_xy
        self.idle_xy = idle_xy

        self.zm = zeus
        self.zeus_traverse_position = zeus_traverse_position
        self.xy_position = None
        self.ROBOT_NAME = 'Robowski1'
        # self.home_xy()

    def send_to_xy_stage(self,
                         command,
                         wait_for_ok=True,
                         verbose=False,
                         read_all=False) -> None:

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

    def configure_grbl(self):
        from pathlib import Path
        grbl_path = str(Path.cwd().parent.parent) + ("\\zeus-pipetter\\config\\miniPi\\grbl_settings.txt")
        with open(grbl_path, 'r') as grbl_config_file:
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
                use_time_estimate=True):

        # all coordinates are negative
        if xy[0] < self.max_x or xy[0] > 0:
            self.logger.error(f'XY STAGE ERROR: target X is beyond the limit ({self.max_x}, 0). Motion aborted.')
            return
        if xy[1] < self.max_y or xy[1] > 0:
            self.logger.error(f'XY STAGE ERROR: target Y is beyond the limit ({self.max_y}, 0). Motion aborted.')
            return

        # avoid collision with the balance
        if xy[0] < -760 and (xy[1] > -210 or xy[1] < -280):
            self.logger.error('XY STAGE ERROR: gantry is going to collide with the balance. Motion aborted.')
            return

        # if move from inside the balance to outside, or vice verse, move to the idle position first
        is_out_balance_to_in_balance = (self.xy_position[0] > -600) and (xy[0] < -600)
        is_in_balance_to_out_balance = (self.xy_position[0] < -600) and (xy[0] > -600)
        if is_out_balance_to_in_balance or is_in_balance_to_out_balance:
            self.send_to_xy_stage(
                command='G0 X{0:.3f} Y{1:.3f}'.format(self.idle_xy[0], self.idle_xy[1]),
                read_all=False)

        zeus_at_traverse_height = (self.zm.pos <= self.zeus_traverse_position)
        if ensure_traverse_height and not zeus_at_traverse_height:
            print(f'ERROR: ZEUS was not in traverse height before motion, but instead at {self.zm.pos}.\n'
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
                        print(f'Status read {i}')
                    self.serial.write(str.encode('?' + '\r\n'))
                    while True:
                        line = self.serial.readline()
                        if verbose:
                            print(line)
                        if b'Idle' in line:
                            finished_moving = True
                        if line == b'': # this means the motion is done!
                            break
                # print(f'{time.time() - t0}')

                if verbose:
                    print('Finished moving xy stage')
            self.xy_position = xy

    def home_xy(self, ensure_traverse_height=True) -> None:
        self.logger.info('The gantry is homing...')
        # self.zm.move_z(self.zm.ZeusTraversePosition)
        self.send_to_xy_stage(command = '$H', read_all=True, verbose=False,)
        self.xy_position = (0,0)
        self.xy_pos()
        print('The gantry is homed!')

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

    def move_z(self):
        # TODO
        pass

class Pipetter():

    def __init__(self,
                 zeus: object,
                 gantry: object,
                 ):
        self.zeus = zeus
        self.gantry = gantry
        self.logger = logging.getLogger('main.pipetter.Pipetter')
        self.logger.info('creating an instance of Pepetter')
        self.ROBOT_NAME = 'Robowski1'

    def home_xy(self):
        self.gantry.home_xy()

    def beep_n(self):
        duration = 600  # milliseconds
        freq = 1500  # Hz
        # time.sleep(0.2)
        for i in range(10):
            winsound.Beep(freq, duration)


    def beep(self):
        duration = 600  # milliseconds
        freq = 1000  # Hz
        # time.sleep(0.2)
        winsound.Beep(freq, duration)

    def pick_tip(self, tip_type: str):

        if self.zeus.tip_on_zeus != '':
            self.logger.error(f'ERROR: There is already a tip on ZEUS. Please remove it before picking up a new one.')
            return

        with open('data/tip_rack.json') as json_file:
            tip_rack = json.load(json_file)

        self.zeus.move_z(self.zeus.ZeusTraversePosition)
        self.zeus.wait_until_zeus_reaches_traverse_height()

        # if the rack is empty then ask user to reload
        if not any(item['exists'] for item in tip_rack[tip_type]['tips']):

            for i in range(30):
                winsound.Beep(1100, 200)
                time.sleep(0.3)

            input(f'ERROR: The tip rack is empty. Please reload the tip rack and hit enter.')
            tip_rack = brb.load_new_tip_rack(rack_reload=tip_type)

        # In the rack, find the first tip that exists
        for item in tip_rack[tip_type]['tips']:
            if item['exists']:
                # pick up tip
                self.gantry.move_xy(item['xy'], ensure_traverse_height=True)
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
                    with open('data/tip_rack.json', 'w', encoding='utf-8') as f:
                        json.dump(tip_rack, f, ensure_ascii=False, indent=4)
                else:
                    raise ValueError('No tip is picked up.')
                return True

        self.logger.info('ERROR: No tips in rack.')
        raise Exception

    def discard_tip(self):
        self.zeus.move_z(self.zeus.ZeusTraversePosition)

        self.zeus.wait_until_zeus_reaches_traverse_height()

        if self.zeus.tip_on_zeus != '':
            self.gantry.move_xy(self.gantry.trash_xy)
            self.zeus.discardTip(deckGeometryTableIndex=1)
            self.zeus.tip_on_zeus = ''
            # time.sleep(0.25)
            # self.zeus.move_z(self.zeus.ZeusTraversePosition)
            # self.zeus.move_z(self.zeus.ZeusTraversePosition)
            self.zeus.wait_until_zeus_responds_with_string('GUid')

        elif self.zeus.tip_on_zeus == '':
            self.logger.info('ERROR: No tip on zeus to discard. Continue...')

    def change_tip(self, tip_rack: str):
        if self.zeus.tip_on_zeus != '':
            self.discard_tip()

        self.pick_tip(tip_rack)
        # self.zeus.wait_until_zeus_responds_with_string('GUid')

    def check_volume_in_container(self, container: object,
                                  liquidClassTableIndex: int = 13, lld: int = 1,
                                  lldSearchPosition: int = 880, liquidSurface: int = 1500,
                                  tip_for_volume_check: str = '300ul',
                                  change_tip_after_each_check: bool = True):

        if change_tip_after_each_check:
            self.change_tip(tip_for_volume_check)
        else:
            if self.zeus.tip_on_zeus != tip_for_volume_check:
                self.change_tip(tip_for_volume_check)

        self.zeus.move_z(self.zeus.ZeusTraversePosition, raise_exception=False)
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
            liquid_surface = int(received_msg[received_msg.find('yl') + 2:received_msg.find('yl') + 6])
            # volume = received_msg[received_msg.find('aw') + 2:received_msg.find('aw') + 8] # This value is from Zeus and not precise.
            if container.name == 'vial_2ml':
                print("Liquid level is compensated by 0.8 mm for 2ml vial.")
                liquid_surface += 8

            ## calculate the volume manually
            volume = ((container.bottomPosition-int(liquid_surface)) / 10)  * container.area # this is in mm^3, uL

        else:
            print(f'Liquid level not detected')
            liquid_surface = 0
            volume = 0
            self.zeus.move_z(self.zeus.ZeusTraversePosition, raise_exception=False)
            self.change_tip(tip_for_volume_check)

        print(f'Volume Check done! liquid_surface: {liquid_surface}, volume: {volume}')

        return (int(liquid_surface), float(int(volume) / 10))  # after / 10, volume is in ul


    def draw_liquid(self, transfer_event: object, n_retries=3) -> bool:

        self.zeus.move_zeus_to_traverse_height()
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
                print(f'liquid surface height in source container: {transfer_event.source_container.liquid_surface_height} ')
                self.logger.info(f'liquid surface height in source container: {transfer_event.source_container.liquid_surface_height} ')

                # Replace this sleep with a proper check. Why do you even need a sleep if next function is zeus.wait_until...???
                # time.sleep(2)
                self.zeus.wait_until_zeus_responds_with_string('GAid')

                # time.sleep(0.5)
                self.zeus.move_z(self.zeus.ZeusTraversePosition)

                return True

            except ZeusError:
                if self.zeus.zeus_error_code(self.zeus.r.received_msg) == '81':
                    # Empty tube detected during aspiration
                    self.logger.info('ZEUS ERROR: Empty tube during aspiration. Dispensing and trying again.')
                    time.sleep(2)
                    self.zeus.move_z(self.zeus.ZeusTraversePosition)
                    time.sleep(2)
                    self.dispense_liquid(transfer_event)
                    time.sleep(2)
                    continue

        self.logger.info(f'Tried {n_retries} but zeus error is still there')
        raise Exception

    def dispense_liquid(self, transfer_event: object) -> None:

        self.zeus.move_zeus_to_traverse_height()
        self.gantry.move_xy(transfer_event.destination_container.xy)
        try:
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
        except ZeusError:
            self.logger.info('Zeus error during dispensing is ignored!')
            self.zeus.move_z(self.zeus.ZeusTraversePosition)
            pass

        self.zeus.wait_until_zeus_responds_with_string('GDid')
        self.zeus.move_z(self.zeus.ZeusTraversePosition)

        return True

    def calib(self, transfer_event:object, purpose:str):

        if transfer_event.solvent == 'water':
            print('The solvent is water. No calibration is needed.')
            return transfer_event

        transfer_event =copy.deepcopy(transfer_event)

        if self.ROBOT_NAME == 'Robowski1':

            target_volume = transfer_event.transfer_volume
            setting_volume = calib.Interpolation(transfer_event.solvent).interp_R1(target_volume, verbose= True, purpose=purpose)
            transfer_event.transfer_volume = setting_volume
            print(f'@@@@@@@@Volume valibrated. Target volume: {target_volume}. Setting volume: {setting_volume}')

        if transfer_event.transfer_volume <=50:
            transfer_event.tip_type = '50ul'
            print(f'the tip type is set to 50ul.')
        elif transfer_event.transfer_volume <=300:
            transfer_event.tip_type = '300ul'
            print(f'the tip type is set to 300ul.')
        elif transfer_event.transfer_volume<=1000:
            transfer_event.tip_type = '1000ul'
            print(f'the tip type is set to 1000ul.')

        print(f"@@@@@@@@The volume sent to Zeus is : {transfer_event.transfer_volume}")

        return transfer_event

    def get_liquid_class_index(self, solvent: str, mode: str, tip_type: str):
        liquid_class_dict = {
            'water_empty_50ul_clld': 21,
            'water_empty_300ul_clld': 1,
            'water_empty_1000ul_clld': 2,
            'water_part_50ul_clld': 3,
            'water_part_300ul_clld': 4,
            'water_part_1000ul_clld': 5,
            'serum_empty_50ul_clld': 6,
            'serum_empty_300ul_clld': 7,
            'serum_empty_1000ul_clld': 8,
            'serum_part_50ul_clld': 9,
            'serum_part_300ul_clld': 10,
            'serum_part_1000ul_clld': 11,
            'ethanol_empty_50ul_plld': 12,
            'ethanol_empty_300ul_plld': 13,
            'ethanol_empty_1000ul_plld': 14,
            'glycerin_empty_50ul_plld': 15,
            'glycerin_empty_300ul_plld': 16,
            'glycerin_empty_1000ul_plld': 17,
            'DMF_empty_300ul_clld': 22,
            'DMF_empty_1000ul_clld': 23,
            'DMF_empty_50ul_clld': 24,
            'Dioxane_empty_50ul_plld': 27,
            'Dioxane_empty_300ul_plld': 28,
            'Dioxane_empty_1000ul_plld': 29,
            'DCE_empty_50ul_clld': 36,
            'DCE_empty_300ul_clld': 37,
            'DCE_empty_1000ul_clld': 38,
        }
        solvent_para = {solvent, mode, tip_type}  # define a set of paras
        for liquid_class, index in liquid_class_dict.items():
            solvent_para_here = set(liquid_class.split('_'))
            # print(f'solvent_para_here: {solvent_para_here}')
            # print(f'solvent_para: {solvent_para}')
            if solvent_para.issubset(solvent_para_here):
                return index

    def transfer_liquid(self, transfer_event: object, purpose:str, max_volume: int=None, use_calibration: bool = True) -> None:

        # if transfer_event.solvent == 'water': ## water is the built-in solvent that needs no software calibration
        #     use_calibration = False

        if max_volume is None:

            print(transfer_event.tip_type, transfer_event.substance)
            max_volume = int(transfer_event.tip_type[:-2]) # extract volume from tip type

        print(f'transfer volume is set to : {transfer_event.transfer_volume}ul')

        # if transfer volume exceeds max_volume, do several pipettings
        N_max_vol_pipettings = int(transfer_event.transfer_volume // max_volume)
        # print(f'N_max_vol_pipettings: {N_max_vol_pipettings}')

        for i in range(N_max_vol_pipettings):
            # print(f'Pipetting {i+1} of {N_max_vol_pipettings}')
            _split_event_1 = copy.deepcopy(transfer_event)
            _split_event_1.transfer_volume = max_volume # volume in ul

            if use_calibration:
                # this is for calibration
                _split_event_1 = self.calib(_split_event_1, purpose=purpose)

                # change tip if necessary
                if self.zeus.tip_on_zeus != _split_event_1.tip_type:
                    self.change_tip(_split_event_1.tip_type)
                    # liquid class parameter is also needed to be updated.
                    _split_event_1.liquidClassTableIndex = self.get_liquid_class_index(solvent=_split_event_1.solvent,
                                                                                     mode='empty',
                                                                                     tip_type=_split_event_1.tip_type)

            # print(f'Aspiration volume: {_split_event_1.aspirationVolume}ul ')
            # print(f'Dispensing volume: {_split_event_1.dispensingVolume}ul ')
            self.draw_liquid(_split_event_1)
            # print(f'DEBUG: transfer_liquid()::disp_height: {transfer_event.disp_liquidSurface}')
            # liquid_surface_height_from_zeus = self.detect_liquid_surface()
            self.dispense_liquid(_split_event_1)

        volume_of_last_pipetting = transfer_event.transfer_volume % max_volume

        if volume_of_last_pipetting:
            _split_event_2 = copy.deepcopy(transfer_event)
            _split_event_2.transfer_volume = volume_of_last_pipetting
            _split_event_2.transfer_volume = volume_of_last_pipetting

            if use_calibration:
                _split_event_2 = self.calib(_split_event_2, purpose=purpose)

            # change tip if necessary
            if self.zeus.tip_on_zeus != _split_event_2.tip_type:
                self.change_tip(_split_event_2.tip_type)
                # liquid class parameter is also needed to be updated.
                _split_event_2.liquidClassTableIndex = self.get_liquid_class_index(solvent=_split_event_2.solvent,
                                                                                   mode='empty',
                                                                                   tip_type=_split_event_2.tip_type)

            self.draw_liquid(_split_event_2)
            liquid_surface_height_from_zeus = self.detect_liquid_surface()
            self.dispense_liquid(_split_event_2)
            time.sleep(0.5)

        # self.logger.info(f'Aspiration volume: {transfer_event.aspirationVolume}ul '
        #                  f'Dispensing volume: {transfer_event.dispensingVolume}ul')

    def detect_liquid_surface(self) -> int:
        self.zeus.sendCommand('GNid0001')
        time.sleep(0.25)
        liquid_surface_height_detected = re.findall('[0-9]+', self.zeus.r.received_msg)[1]

        # self.logger.info(f'liquid_surface_height_detected: {liquid_surface_height_detected}')
        return int(liquid_surface_height_detected)

    def prewet_new_tip(self,zm: object, pt: object, pipetting_event: object, use_calibration = False):

        print('Prewetting new tip...')

        event_adjusted = copy.deepcopy(pipetting_event)

        max_volume = int(re.findall(r'\d+', zm.tip_on_zeus)[0])
        event_adjusted.transfer_volume = max_volume
        event_adjusted.destination_container = event_adjusted.source_container
        event_adjusted.disp_liquidSurface = 1800

        print(f'Prewetting tip with {max_volume}ul of {event_adjusted.substance}')
        pt.transfer_liquid(event_adjusted, purpose='mixing', use_calibration=use_calibration)
        print('Prewet done! Continue with pipetting...')


    def close_ports_and_zeus(self):
        self.balance.close()
        self.gantry.serial.close()
        self.zeus.switchOff()

class ZeusError(Exception):
    pass


def initiate_hardware():
    # initiate zeus
    zm = zeus.ZeusModule(id=1)
    time.sleep(3)
    print("zeus is loaded as: zm")

    # initiate gantry
    gt = Gantry(zeus=zm)
    time.sleep(3)
    print("gantry is loaded as: gt")
    # gt.configure_grbl() # This only need to be done once.
    gt.home_xy()
    if gt.xy_position == (0, 0):
        print("gantry is homed")

    # initiate pipetter
    pt = Pipetter(zeus=zm, gantry=gt)
    time.sleep(2)
    print("pipetter is loaded as: pt")

    return zm, gt, pt


if __name__ == '__main__':


    # # initiate zeus
    zm = zlt.ZeusLTModule(id=815, COMport='COM5', COM_timeout=0.1, baudrate=19200)
    zm.pos = 800 # fake a z position 20240630
    # time.sleep(3)
    # print("zeus is loaded as: zm")

    # initiate gantry
    gt = Gantry(zeus=zm)
    time.sleep(3)
    print("gantry is loaded as: gt")
    # gt.configure_grbl() # This only need to be done once.
    gt.home_xy()
    # if gt.xy_position == (0, 0):
    #     print("gantry is homed")
    #
    # # initiate pipetter
    # pt = Pipetter(zeus=zm, gantry=gt)
    # time.sleep(2)
    # print("pipetter is loaded as: pt")


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


