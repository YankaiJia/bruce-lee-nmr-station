'''
This is the pipetter module. Its function includes pick_tip, discard_tip, draw_liquid,
dispense_liquid, transfer_liquid and so on. It takes gantry and zeus as arguments.

'''

import json
import time
import serial



class Pipetter():

    def __init__(self, zeus, gantry):
        self.zeus = zeus
        self.gantry = gantry
        self.balance_port = serial.Serial('COM7', 19200, stopbits=serial.STOPBITS_ONE,
                                          parity=serial.PARITY_NONE, timeout=0.2)

    def pick_tip(self, tip_type: int):
        global tip_on_zeus
        with open('data/tip_rack.json') as json_file:
            tip_rack = json.load(json_file)

        self.zeus.move_z(tip_rack[str(tip_type) + 'ul']['wells'][0]['ZeusTraversePosition'])
        # wait_until_zeus_reaches_traverse_height()
        # In the rack, find the first tip that exists
        for item in tip_rack[str(tip_type)+'ul']['wells']:
            if item['exists']:
                # pick up tip
                self.gantry.move_xy(item['xy'], ensure_traverse_height= True)
                self.zeus.pickUpTip(tipTypeTableIndex=item['tipTypeTableIndex'], deckGeometryTableIndex=item['deckGeometryTableIndex'])
                tip_on_zeus = str(tip_type) + 'ul'
                print(f'Now the tip on zeus is : {tip_type}')
                item['exists'] = False
                # wait_until_zeus_reaches_traverse_height()
                self.zeus.wait_until_zeus_responds_with_string('GTid')
                # update json file
                with open('data/tip_rack.json', 'w', encoding='utf-8') as f:
                    json.dump(tip_rack, f, ensure_ascii=False, indent=4)
                return True
        print('ERROR: No tips in rack.')
        raise Exception

    def discard_tip(self):
        self.zeus.move_z(self.zeus.ZeusTraversePosition)
        # wait_until_zeus_reaches_traverse_height()
        self.gantry.move_xy(self.gantry.trash_xy)
        self.zeus.discardTip(deckGeometryTableIndex=1)
        self.zeus.tip_on_zeus = ''
        self.zeus.wait_until_zeus_responds_with_string('GUid')

    def change_tip(self, tip_rack):
        if self.zeus.tip_on_zeus != '':
            self.discard_tip()
        self.pick_tip(tip_rack)

    def draw_liquid(self, transfer_event , n_retries=3):

        self.zeus.move_zeus_to_traverse_height()
        self.gantry.move_xy(transfer_event.source_container.xy)

        for retry in range(n_retries):
            try:
                print(f'Aspiration volume: {int(round(transfer_event.aspirationVolume * 10))}')
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
                    print('ZEUS ERROR: Empty tube during aspiration. Dispensing and trying again.')
                    time.sleep(2)
                    self.zeus.move_z(self.zeus.ZeusTraversePosition)
                    time.sleep(2)
                    self.dispense_liquid(transfer_event)
                    time.sleep(2)
                    continue

        print(f'Tried {n_retries} but zeus error is still there')
        raise Exception

    def dispense_liquid(self, transfer_event):

        self.zeus.move_zeus_to_traverse_height()
        self.gantry.move_xy(transfer_event.destination_container.xy)

        # check if container is full.
        if transfer_event.destination_container.liquid_volume >= transfer_event.destination_container.volume_max:
            print("The target container is full. Dispensing is aborted.")
            return

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

    def transfer_liquid(self, transfer_event,max_volume=300):

        # check if container is full.
        if transfer_event.destination_container.liquid_volume >= transfer_event.destination_container.volume_max:
            print("The target container is full. Dispensing is aborted.")
            return

        # if it exceeds max_volume, then do several pipettings
        N_max_vol_pipettings = int(transfer_event.aspirationVolume // max_volume)

        for i in range(N_max_vol_pipettings):
            self.draw_liquid(transfer_event)
            self.dispense_liquid(transfer_event)

        volume_of_last_pipetting = transfer_event.aspirationVolume % max_volume
        if volume_of_last_pipetting:
            self.draw_liquid(transfer_event)
            self.dispense_liquid(transfer_event)

    def send_command_to_balance(self, command, read_all=True, verbose=True):

        self.balance_port.write(str.encode(command + '\n'))
        while True:
            line = self.balance_port.readline()
            if verbose:
                print(f'Response from balance. {line}')
            if line == b'':
                break

    def balance_tare(self, verbose=True):
        self.balance_port.write(str.encode('T\n'))
        taring_complete = False
        while True:
            line = self.balance_port.readline()
            if b'T' in line:
                taring_complete = True
            if verbose:
                print(f'Tare in progress. Response from balance. {line}')
            if line == b'':
                if taring_complete:
                    break

    def balance_zero(self, verbose = True):
        self.balance_port.write(str.encode('Z\n'))
        zeroing_complete = False
        while True:
            line = self.balance_port.readline()
            if b'Z' in line:
                zeroing_complete = True
            if verbose:
                print(f'Tare in progress. Response from balance. {line}')
            if line == b'':
                if zeroing_complete:
                    break

    def balance_value(self, read_all=True, verbose=True):
        value = 0
        self.balance_port.write(str.encode('SI\n'))
        measurement_successful = False
        while True:
            line = self.balance_port.readline()
            if (b'S D' in line) or (b'S S' in line):
                raw_parsed = line.split(b' g\r\n')[0][-8:]
                if verbose:
                    print(f"Raw parsed: {raw_parsed}")
                value: float = float(raw_parsed)
                measurement_successful = True
            if b'S I' in line:
                'Balance command not executed.'
                time.sleep(5)
                self.balance_port.write(str.encode('SI\n'))
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

    def move_to_balance(self, container):
        self.open_balance_door()
        self.zeus.move_z(self.zeus.ZeusTraversePosition)
        self.gantry.move_xy(container['xy'])

    def dispense_to_balance(self, volume, liquidClassTableIndex, container,
                        liquid_surface_margin=50, deckGeometryTableIndex=0):

        print(f" balance_ vial volume is now : { container['volume']}")
        self.zeus.move_zeus_to_traverse_height()
        self.move_to_balance(container)
        zm.dispensing(dispensingVolume=int(round(volume*10)),
                      containerGeometryTableIndex=container['containerGeometryTableIndex'],
                      deckGeometryTableIndex=deckGeometryTableIndex,
                      liquidClassTableIndex=liquidClassTableIndex,
                      lld=0, lldSearchPosition=container.lld_search_position,
                      liquidSurface=container.liquid_surface_in_container - liquid_surface_margin,
                      searchBottomMode=0, mixVolume=0, mixFlowRate=0, mixCycles=0)
        time.sleep(1.5)
        # wait_until_zeus_reaches_traverse_height(traverse_height=balance_traverse_height)
        self.zeus.wait_until_zeus_responds_with_string('GDid')
        self.gantry.move_xy(self.gantry.xy_idle)
        container['volume'] += volume
        print(f" balance_ vial volume is now : { container['volume']}")


    def dispense_to_balance_and_weight(self, source_container, volume, lld, liquid_class_index, tip_type, container,
                                       timedelay=5):
        global xy_position
        global weighted_values
        # if xy_position[0] < -80:
        #     move_xy((-80, -195))
        self.close_balance_door()
        time.sleep(timedelay)
        # balance_tare()
        # balance_zero(verbose=True)
        self.draw_liquid(container=source_container, volume=volume, lld = lld, liquidClassTableIndex= liquid_class_index, tip_type= tip_type)
        weight_before = self.balance_value()
        print(f'weight_before: {weight_before} g')
        self.dispense_to_balance(volume=volume, liquidClassTableIndex= liquid_class_index, container= container)
        self.close_balance_door()
        time.sleep(timedelay)
        weight_after = self.balance_value()
        print(f'weight_after: {weight_after} g')
        print(f'Weight of aliquot: {(weight_after - weight_before)*1000} mg')
        print(f'Volume of aliquot: {volume}')
        return round((weight_after - weight_before)*1000, 1)


    def dispense_to_balance_and_weight_n_times(self, source_container, volume,lld, liquid_class_index,  ntimes, tip_type, timedelay=3):
        result = []
        t0 = time.time()
        for i in range(ntimes):
            print(f'Dispensing to balance and weighting: iteration {i} out of {ntimes}')
            weight_here = self.dispense_to_balance_and_weight(source_container=source_container,
                                                         volume=volume, timedelay=timedelay, lld=lld,
                                                         liquid_class_index=liquid_class_index, tip_type=tip_type)
            result.append(weight_here)
            time.sleep(timedelay)
            print(f'Dispensing to balance and weighting took {time.time()-t0:.2f} seconds')
        return result



class ZeusError(Exception):
    pass

def main():
    import zeus
    import gantry
    zm =  zeus.ZeusModule(id=1)
    time.sleep(5)
    gt = gantry.Gantry(zeus = zm)
    # gt.home_xy()
    time.sleep(5)
    pt = Pipetter(zeus = zm, gantry = gt)

    return zm, gt, pt

if __name__ == '__main__':
    zm, gt, pt = main()