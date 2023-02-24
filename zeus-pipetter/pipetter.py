"""

The pipetter module combines gantry and zeus, and deals with actions including pick_tip, discard_tip, draw_liquid,
dispense_liquid, transfer_liquid and so on.

"""
import copy
import json
import time

import serial
import logging
pipetter_logger = logging.getLogger('main.pipetter')


class Pipetter():

    def __init__(self, zeus, gantry):
        self.zeus = zeus
        self.gantry = gantry
        self.balance = serial.Serial(port='COM7',
                                     baudrate=19200,
                                     stopbits=serial.STOPBITS_ONE,
                                     parity=serial.PARITY_NONE,
                                     timeout=0.2)

        self.logger = logging.getLogger('main.pipetter.Pipetter')
        self.logger.info('creating an instance of Pepetter')

    def pick_tip(self, tip_type: str):
        global tip_on_zeus
        with open('data/tip_rack.json') as json_file:
            tip_rack = json.load(json_file)

        self.zeus.move_z(self.zeus.ZeusTraversePosition)
        self.zeus.wait_until_zeus_reaches_traverse_height()

        # In the rack, find the first tip that exists
        for item in tip_rack[tip_type]['wells']:
            if item['exists']:
                # pick up tip
                self.gantry.move_xy(item['xy'], ensure_traverse_height= True)
                self.zeus.pickUpTip(tipTypeTableIndex=item['tipTypeTableIndex'], deckGeometryTableIndex=item['deckGeometryTableIndex'])
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
        self.gantry.move_xy(self.gantry.trash_xy)
        self.zeus.discardTip(deckGeometryTableIndex=1)
        self.zeus.tip_on_zeus = ''
        self.zeus.wait_until_zeus_responds_with_string('GUid')

    def change_tip(self, tip_rack):
        self.zeus.getTipPresenceStatus()
        time.sleep(1)
        if self.zeus.getTipPresenceStatus():
            self.discard_tip()
        self.pick_tip(tip_rack)

    def draw_liquid(self, transfer_event, n_retries=3):

        self.zeus.move_zeus_to_traverse_height()
        self.gantry.move_xy(transfer_event.source_container.xy)

        for retry in range(n_retries):
            try:
                # print(f'Aspiration volume: {int(round(transfer_event.aspirationVolume * 10))}')
                self.zeus.aspiration(aspirationVolume=int(round(transfer_event.aspirationVolume * 10)),
                              containerGeometryTableIndex=transfer_event.asp_containerGeometryTableIndex,
                              deckGeometryTableIndex=transfer_event.asp_deckGeometryTableIndex,
                              liquidClassTableIndex=transfer_event.asp_liquidClassTableIndex,
                              qpm=transfer_event.asp_qpm,
                              lld=transfer_event.asp_lld,
                              lldSearchPosition=transfer_event.asp_lldSearchPosition,
                              liquidSurface=transfer_event.asp_liquidSurface,
                              mixVolume=transfer_event.asp_mixVolume,
                              mixFlowRate=transfer_event.asp_mixFlowRate,
                              mixCycles=transfer_event.asp_mixCycles)
                time.sleep(2)
                self.zeus.wait_until_zeus_responds_with_string('GAid')
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

    def dispense_liquid(self, transfer_event):

        self.zeus.move_zeus_to_traverse_height()
        self.gantry.move_xy(transfer_event.destination_container.xy)

        # # check if container is full.
        # if transfer_event.destination_container.liquid_volume >= transfer_event.destination_container.volume_max:
        #     logging.warning("The target container is full. Dispensing is aborted.")
        #     return

        self.zeus.dispensing(dispensingVolume=int(round(transfer_event.dispensingVolume * 10)),
                      containerGeometryTableIndex=transfer_event.disp_containerGeometryTableIndex,
                      deckGeometryTableIndex=transfer_event.disp_deckGeometryTableIndex,
                      liquidClassTableIndex=transfer_event.disp_liquidClassTableIndex,
                      lld=transfer_event.disp_lld,
                      lldSearchPosition=transfer_event.disp_lldSearchPosition,
                      liquidSurface=transfer_event.disp_liquidSurface,
                      searchBottomMode=transfer_event.searchBottomMode,
                      mixVolume=transfer_event.disp_mixVolume,
                      mixFlowRate=transfer_event.disp_mixVolume,
                      mixCycles=transfer_event.disp_mixCycles)

        time.sleep(1.5)
        # wait_until_zeus_reaches_traverse_height()
        self.zeus.wait_until_zeus_responds_with_string('GDid')

    def transfer_liquid(self, transfer_event, max_volume=300):

        # check if container is full.
        # if transfer_event.destination_container.liquid_volume > transfer_event.destination_container.volume_max:
        #     print(f'transfer_event.destination_container.liquid_volume:{transfer_event.destination_container.container_id}, {transfer_event.destination_container.liquid_volume}')
        #     raise ValueError('The target container is full. Dispensing is aborted')

        # if it exceeds max_volume, then do several pipettings
        N_max_vol_pipettings = int(transfer_event.aspirationVolume // max_volume)

        for i in range(N_max_vol_pipettings):
            _split_event_1 = copy.deepcopy(transfer_event)
            _split_event_1.aspirationVolume = max_volume
            _split_event_1.dispensingVolume = max_volume
            self.draw_liquid(_split_event_1)
            self.dispense_liquid(_split_event_1)

        volume_of_last_pipetting = transfer_event.aspirationVolume % max_volume
        if volume_of_last_pipetting:
            _split_event_2 = copy.deepcopy(transfer_event)
            _split_event_2.aspirationVolume = volume_of_last_pipetting
            _split_event_2.dispensingVolume = volume_of_last_pipetting
            self.draw_liquid(_split_event_2)
            self.dispense_liquid(_split_event_2)

        self.logger.info(f'Aspiration volume: {transfer_event.aspirationVolume}ul '
                         f'Dispensing volume: {transfer_event.dispensingVolume}ul')

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
                    break

    def balance_zero(self, verbose = False):
        self.balance.write(str.encode('Z\n'))
        zeroing_complete = False
        while True:
            line = self.balance.readline()
            if b'Z' in line:
                zeroing_complete = True
            if verbose:
                pass
                # print(f'Tare in progress. Response from balance. {line}')
            if line == b'':
                if zeroing_complete:
                    break

    def balance_value(self, read_all=True, verbose= False):
        value = 0
        self.balance.write(str.encode('SI\n'))
        measurement_successful = False
        while True:
            line = self.balance.readline()
            # print(f'balance line: {line}')
            if (b'S D' in line) or (b'S S' in line):
                raw_parsed = line.split(b' g\r\n')[0][-8:]
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

    def move_to_balance(self, xy: tuple):
        self.open_balance_door()
        self.zeus.move_z(self.zeus.ZeusTraversePosition)
        self.gantry.move_xy(xy)

    def pipetting_to_balance_and_weight(self, transfer_event, timedelay=5) -> tuple[float, float]:
        global xy_position
        global weighted_values
        # if xy_position[0] < -80:
        #     move_xy((-80, -195))
        self.close_balance_door()
        time.sleep(timedelay)
        # balance_tare()
        self.balance_zero(verbose=False)
        weight_before = self.balance_value()
        print(f'weight_before: {weight_before} g')
        self.open_balance_door()
        self.transfer_liquid(transfer_event=transfer_event)
        time.sleep(0.5)
        self.gantry.move_to_idle()
        self.close_balance_door()
        time.sleep(timedelay)
        weight_after = self.balance_value()
        print(f'weight_after: {weight_after} g')

        pipetting_weight = round((weight_after- weight_before) *1000, 6) # mg
        pipetting_volume = pipetting_weight / transfer_event.source_container.substance_density
        self.logger.info(f'Weight of aliquot: {pipetting_weight} mg')
        self.logger.info(f'Volume of aliquot: {pipetting_volume} ul')
        return pipetting_weight, pipetting_volume

    def pipetting_to_balance_and_weight_n_times(self, transfer_event, n_times = 3):
        dict_for_one_event = {}
        dict_for_one_event[f'{transfer_event.substance_name}_{transfer_event.aspirationVolume}ul'] = \
            {'weight':[], 'volume':[], 'liquid_class_index':[], 'tip_type': []}
        temp_dict = dict_for_one_event[f'{transfer_event.substance_name}_{transfer_event.aspirationVolume}ul']
        for i in range(n_times):
            weight, volume =self.pipetting_to_balance_and_weight(transfer_event=transfer_event)
            temp_dict['weight'].append(weight)
            temp_dict['volume'].append(volume)
            temp_dict['liquid_class_index'].append(transfer_event.asp_liquidClassTableIndex)
            temp_dict['tip_type'].append(transfer_event.tip_type)

        print(dict_for_one_event)
        return dict_for_one_event


class ZeusError(Exception):
    pass

def main():
    import zeus
    import gantry
    import breadboard as brb
    zm =  zeus.ZeusModule(id=1)
    time.sleep(5)
    gt = gantry.Gantry(zeus = zm)
    # gt.home_xy()
    time.sleep(5)
    pt = Pipetter(zeus = zm, gantry = gt)

    return zm, gt, pt

if __name__ == '__main__':
    zm, gt, pt = main()