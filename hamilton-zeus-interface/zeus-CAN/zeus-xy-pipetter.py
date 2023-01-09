# -*- coding: utf-8 -*-
"""
Script for operating an ad-hoc pipetter robot based on:
1) Hamilton ZEUS automatic pipette with embedded vertical Z axis and
2) Ad-hoc XY stage controlled by Arduino running GRBL firmware.

ZEUS is mounted on the XY stage.

Author: Yaroslav I. Sobolev, Yankai Jia
Date: 6 Dec 2022
"""
import zeus
import time
import numpy as np
import matplotlib
import pandas as pd

# import liquid_class

matplotlib.use('TkAgg')
import serial
import os
import pickle
from scipy import interpolate
import matplotlib.pyplot as plt
import json

# plt.ion()

class ZeusError(Exception):
    pass

# ZeusTraversePosition_300ul = 650
ZeusTraversePosition_1000ul = 880
xy_idle = (-345, -187)

balance_traverse_height = 880
floor_z = 2317
manual_vial_surface = 2152

weighted_values = {'100ul':[], '200ul':[], '300ul':[], '400ul':[],'500ul':[], '600ul':[],'700ul':[], '800ul':[],'900ul':[]}


# # ZEUS
zm = zeus.ZeusModule(id=1)
time.sleep(3)


# Deck loading
deckgeom = zeus.DeckGeometry(index=0, endTraversePosition=ZeusTraversePosition_1000ul,
                             beginningofTipPickingPosition=1530,
                             positionofTipDepositProcess=1817)
zm.setDeckGeometryParameters(deckGeometryParameters=deckgeom)
print('Zeus deck geometry loaded')


deckgeom_1000ul= zeus.DeckGeometry(index=1, endTraversePosition=ZeusTraversePosition_1000ul,
                                   beginningofTipPickingPosition=1210,
                                   positionofTipDepositProcess=1600)
zm.setDeckGeometryParameters(deckGeometryParameters=deckgeom_1000ul)
print('Zeus deck geometry loaded')


deckgeom_balance = zeus.DeckGeometry(index=2, endTraversePosition=balance_traverse_height,
                             beginningofTipPickingPosition=1530,
                             positionofTipDepositProcess=2217)
zm.setDeckGeometryParameters(deckGeometryParameters=deckgeom_balance)
print('Zeus deck geometry loaded')



# Container loading
# TODO: In the object-oriented version this will be depend on target container dictionaries passed by
#  the module's user
container_2mL_vial = zeus.ContainerGeometry(index=0, diameter=98, bottomHeight=0, bottomSection=10000,
                 bottomPosition=2177, immersionDepth=20, leavingHeight=20, jetHeight=130,
                 startOfHeightBottomSearch=30, dispenseHeightAfterBottomSearch=80,
                 )
zm.setContainerGeometryParameters(containerGeometryParameters=container_2mL_vial)
print('2ml vial container loaded')


container_20mL_bottle = zeus.ContainerGeometry(index=1, diameter=255, bottomHeight=0, bottomSection=10000,
                 bottomPosition=2110, immersionDepth=20, leavingHeight=30, jetHeight=130,
                 startOfHeightBottomSearch=20, dispenseHeightAfterBottomSearch=50,
                 )
zm.setContainerGeometryParameters(containerGeometryParameters=container_20mL_bottle)
print('20 ml bottle container loaded')


container_jar = zeus.ContainerGeometry(index=2, diameter=520, bottomHeight=0, bottomSection=10000,
                                       bottomPosition=2217, immersionDepth=40, leavingHeight=40, jetHeight=130,
                                       startOfHeightBottomSearch=50, dispenseHeightAfterBottomSearch=50,
                                       )
zm.setContainerGeometryParameters(containerGeometryParameters=container_jar)
print('Large bottle container loaded')


container_balance_vial = zeus.ContainerGeometry(index=3, diameter=1000, bottomHeight=0, bottomSection=10000,
                 bottomPosition=1680, immersionDepth=20, leavingHeight=20, jetHeight=200,
                 startOfHeightBottomSearch=30, dispenseHeightAfterBottomSearch=100,
                 )
zm.setContainerGeometryParameters(containerGeometryParameters=container_balance_vial)
print('Large bottle container loaded')


# Liquid class loading from JSON file

with open('data/liquid_class_table_para_ALL.json') as json_file:
    liquid_class_table_para = json.load(json_file)

def load_liquid_class ():

    for i in range(21, 30):
        zeus.LiquidClass(**liquid_class_table_para[str(i).zfill(2)])

load_liquid_class()


def wait_until_zeus_reaches_traverse_height(n_retries=70, traverse_height=ZeusTraversePosition_1000ul):
    time.sleep(0.5)
    for i in range(n_retries):
        print(f'Waiting for Zeus to get back to traverse height: attempt {i}')
        zm.getAbsoluteZPosition()
        time.sleep(0.6)
        idx = zm.r.received_msg.find("gy")
        if idx == -1:
            # this means that there is an error. Retry
            zm.parseErrors(zm.r.received_msg)
            time.sleep(0.5)
            continue
        else:
            position = int(zm.r.received_msg[idx+2:])
            print(f'Current position (true): {position}')
        if position <= traverse_height:
            print('Traverse height is reached.')
            return True
    print(f'Traverse height was not reached after {n_retries} retries. This is dangerous, so we do emergency stop')
    raise Exception
    return False

def zeus_had_error(errorString):
    cmd = str(errorString[:2])
    eidx = errorString.find("er")
    if (eidx == -1):
        return False
    ec = str(errorString[(eidx + 2): (eidx + 4)])
    if ec == '00':
        return False

    return True

def zeus_error_code(errorString):
    cmd = str(errorString[:2])
    eidx = errorString.find("er")
    if (eidx == -1):
        return False
    return str(errorString[(eidx + 2): (eidx + 4)])


def wait_until_zeus_responds_with_string(search_pattern, n_retries=200):
    time.sleep(0.5)
    print(f'Waiting for Zeus to respond')
    for i in range(n_retries):
        # print(f'Waiting for Zeus to respond: attempt {i}')
        # zm.getAbsoluteZPosition()
        # time.sleep(0.6)
        if zeus_had_error(zm.r.received_msg):
            print('Zeus responded with error message. Aborting all operations.')
            raise ZeusError

        idx = zm.r.received_msg.find(search_pattern)
        if idx == -1:
            # this means that there is no pattern. Retry
            # zm.parseErrors(zm.r.received_msg)
            time.sleep(0.1)
            continue
        else:
            print(f'Competion response received after {i} attempts.')
            return True
    print(f'Response not received after {n_retries} retries. This is dangerous, so we do emergency stop')
    raise Exception
    return False

def move_z(z):
    zm.moveZDrive(z, 'fast')
    wait_until_zeus_responds_with_string('GZid')

# BALANCE
balance_port = ser = serial.Serial('COM7', 19200, stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE,
                                   timeout=0.2)

def send_command_to_balance(command, balance_port=balance_port, read_all=True, verbose=True):
    balance_port.write(str.encode(command + '\n'))
    while True:
        line = balance_port.readline()
        if verbose:
            print(f'Response from balance. {line}')
        if line == b'':
            break

def balance_tare(verbose=True):
    balance_port.write(str.encode('T\n'))
    taring_complete = False
    while True:
        line = balance_port.readline()
        if b'T' in line:
            taring_complete = True
        if verbose:
            print(f'Tare in progress. Response from balance. {line}')
        if line == b'':
            if taring_complete:
                break

def balance_value(balance_port=balance_port, read_all=True, verbose=True):
    balance_port.write(str.encode('SI\n'))
    measurement_successful = False
    while True:
        line = balance_port.readline()
        if (b'S D' in line) or (b'S S' in line):
            raw_parsed = line.split(b' g\r\n')[0][-8:]
            if verbose:
                print(f"Raw parsed: {raw_parsed}")
            value = float(raw_parsed)
            measurement_successful = True
        if b'S I' in line:
            'Balance command not executed.'
            time.sleep(5)
            balance_port.write(str.encode('SI\n'))
        if verbose:
            print(line)
        if line == b'':
            if measurement_successful:
                break
    return value

def open_balance_door():
    send_command_to_balance('WS 1')

def close_balance_door():
    send_command_to_balance('WS 0')

def move_to_balance(balance_vial):
    open_balance_door()
    move_z(balance_traverse_height)
    move_xy(balance_vial['xy'])

def dispense_to_balance_and_weight(source_container, volume, timedelay=5):
    global xy_position
    global weighted_values
    # if xy_position[0] < -80:
    #     move_xy((-80, -195))
    close_balance_door()
    time.sleep(timedelay)
    balance_tare()
    weight_before = balance_value()
    print(f'weight_before: {weight_before} g')

    draw_liquid(container=source_container, volume=volume)
    dispense_to_balance(volume=volume)
    close_balance_door()
    time.sleep(timedelay)
    weight_after = balance_value()
    print(f'weight_after: {weight_after} g')
    print(f'Weight of aliquot: {(weight_after - weight_before)*1000} mg')
    print(f'Volume of aliquot: {volume}')
    return round((weight_after - weight_before)*1000, 1)

def dispense_to_balance_and_weight_n_times(source_container, volume, ntimes, timedelay=5):
    result = []
    global weighted_values
    t0 = time.time()
    for i in range(ntimes):
        print(f'Dispensing to balance and weighting: iteration {i} out of {ntimes}')
        weight_here = dispense_to_balance_and_weight(source_container=source_container,
                                                     volume=volume, timedelay=timedelay)
        result.append(weight_here)
        weighted_values[str(volume)+'ul'].append(weight_here)
        time.sleep(timedelay)
        print(f'Dispensing to balance and weighting took {time.time()-t0:.2f} seconds')
    return result

def calibrate_volume_by_balance(source_container, volume, ntimes=5, timedelay=5, density=1):
    # TODO: Volumes here must be nominal, not already corrected by calibration
    # One way to do it is to load a 1:1 calibration dictionary
    measured_masses = np.array(dispense_to_balance_and_weight_n_times(source_container=source_container,
                                                             volume=volume,
                                                             ntimes=ntimes,
                                                             timedelay=timedelay))
    measured_volumes = measured_masses / density
    return np.mean(measured_volumes), np.std(measured_volumes)


def update_volume_calibration(calibration_file, source_container, volume_list, ntimes=5, timedelay=5, density=1):
    if os.path.exists(calibration_file):
        with open(calibration_file, 'rb') as handle:
            calibration_dictionary = pickle.load(handle)
            print('Calibration file loaded.')
    else:
        calibration_dictionary = dict()
    for volume in volume_list:
        calibration_dictionary[volume] = calibrate_volume_by_balance(source_container, volume,
                                                                     ntimes, timedelay, density)
    with open(calibration_file, 'wb') as handle:
        pickle.dump(calibration_dictionary, handle, protocol=pickle.HIGHEST_PROTOCOL)
        print(f'Calibration saved to: {calibration_file}')
        print(f'Dictionary data now: {calibration_dictionary}')
    return calibration_dictionary

# calibration_dict = update_volume_calibration(
#     calibration_file='calibration/calibration_DMF_300ul_lld_qpm__empty_jet.pickle',
#     source_container=bottle6, volume_list=[10, 20, 30, 50, 70, 110], density=0.9445)

def load_calibration_dict_from_file(calibration_file):
    if os.path.exists(calibration_file):
        with open(calibration_file, 'rb') as handle:
            calibration_dictionary = pickle.load(handle)
            print('Calibration file loaded.')
    return calibration_dictionary

calibration_dict = load_calibration_dict_from_file(
    calibration_file='calibration/calibration_DMF_300ul_lld_qpm__empty_jet.pickle')

def volume_for_zeus(real_volume, calibration_dict=calibration_dict):
    zeus_volumes = [0]
    real_volumes = [0]
    sigmas = []
    for zeus_volume in sorted(calibration_dict.keys()):
        zeus_volumes.append(zeus_volume)
        real_volumes.append(calibration_dict[zeus_volume][0])
        sigmas.append(calibration_dict[zeus_volume][1])
    zeus_volumes = np.array(zeus_volumes)
    real_volumes = np.array(real_volumes)
    sigmas = np.array(sigmas)
    calibration_interpolator = interpolate.interp1d(x=real_volumes, y=zeus_volumes, fill_value='extrapolate')
    result = calibration_interpolator(real_volume)
    if not result.shape:
        result = result.tolist()
    return result


# XY stage

# move_z(880)

def pos_z():
    print(zm.getAbsoluteZPosition())


horiz_speed = 200 * 60 # horizontal speed in mm / min
# xy_offset = (-0.3, 7) # offsets in x and y that are automatically added to each move_xy()
xy_offset = (0, 0)
trash_xy = (-345, -187) # can for discarding the pipette tips into
xy_position = (593.760, -1.000)
min_x = -720
min_y = -357

ser = serial.Serial('COM6', 115200, timeout=0.2)
time.sleep(1)
t0 = time.time()
while time.time() - t0 < 8:
    line = ser.readline()
    print(line)

def zeus_is_at_traverese_height():
    if zm.pos <= ZeusTraversePosition_1000ul:
        return True
    else:
        print(f'ERROR: ZEUS was not in traverse height before motion, but instead at {zm.pos}')
        return False


def send_to_xy_stage(ser, command, wait_for_ok=True, verbose=True, read_all=False, ensure_traverse_height = True):
    # start_time = datetime.now()
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
                send_to_xy_stage(ser, '$X')
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


# send configuration parameters from grbl_settings.txt into the GRBL firmware
with open('grbl_settings.txt', 'r') as grbl_config_file:
    for line in grbl_config_file:
        # extract command before the comments
        send_to_xy_stage(ser, command=line.split('    (')[0], read_all=True, verbose=True)


print('XY stage initiated.')


def xy_pos():
    send_to_xy_stage(ser, '?', read_all=True, verbose=True)
def pos_xy():
    xy_pos()


# def move_xy(x, y):
def time_that_xy_motion_takes(dx, dy, acceleration=2000, max_speed=333.33333):
    """

    Parameters
    ----------
    dx:
    dy:
    acceleration: mm/s^2
    max_speed: in mm/s

    Returns
    -------

    """
    travel_times = []
    for distance in [abs(dx), abs(dy)]:
        halfdistance = distance/2
        # constant acceleration scenario
        constant_acceleration_halftime = np.sqrt(halfdistance * 2 / acceleration)
        speed_at_midpoint = constant_acceleration_halftime * acceleration
        if speed_at_midpoint <= max_speed:
            time_here = constant_acceleration_halftime * 2
        else:
            # this means that the stage reaches max speed before midpoint and then
            #   continues at his max speed
            constant_acceleration_halftime = max_speed / acceleration
            dist_traveled_at_constant_acceleration = acceleration * (constant_acceleration_halftime**2) / 2
            distance_traveled_at_constant_speed = halfdistance - dist_traveled_at_constant_acceleration
            const_speed_halftime = distance_traveled_at_constant_speed / max_speed
            time_here = 2 * (constant_acceleration_halftime + const_speed_halftime)
        travel_times.append(time_here)
    print(max(travel_times))
    return max(travel_times)


def move_xy(xy, verbose=False, ensure_traverse_height=True, block_until_motion_is_completed=True,
            use_time_estimate=True):
    if xy[0] < min_x or xy[0] > 0:
        print(f'XY STAGE ERROR: target X is beyond the limit ({min_x}, 0). Motion aborted.')
        return
    if xy[1] < min_y or xy[1] > 0:
        print(f'XY STAGE ERROR: target Y is beyond the limit ({min_y}, 0). Motion aborted.')
        return

    if ensure_traverse_height and not zeus_is_at_traverese_height():
        return
    global xy_position
    # if ensure_traverse_height:
    #     if zm.pos > ZeusTraversePosition:
    #         print(f'ERROR: ZEUS was not in traverse height before motion, but instead at {zm.pos}')
    #         return
    # if np.linalg.norm(np.array((x, y))) <= R:
    send_to_xy_stage(ser, 'G0 X{0:.3f} Y{1:.3f}'.format(xy[0] + xy_offset[0], xy[1] + xy_offset[1]),
                     read_all=False, ensure_traverse_height=ensure_traverse_height)
    if block_until_motion_is_completed:
        if use_time_estimate:
            time.sleep(time_that_xy_motion_takes(dx=xy[0]-xy_position[0],
                                                 dy=xy[1]-xy_position[1]))
        else:
            t0 = time.time()
            time.sleep(0.1)
            finished_moving = False
            for i in range(100):
                if finished_moving:
                    break
                if verbose:
                    print(f'Status read {i}')
                ser.write(str.encode('?' + '\r\n'))
                while True:
                    line = ser.readline()
                    if verbose:
                        print(line)
                    if b'Idle' in line:
                        finished_moving = True
                    if line == b'':
                        break
            print(f'{time.time()-t0}')
            if verbose:
                print('Finished moving xy stage')
    xy_position = xy


def home_xy(ensure_traverse_height=True):
    if ensure_traverse_height and not zeus_is_at_traverese_height():
        return
    send_to_xy_stage(ser, '$H', read_all=True, verbose=True, ensure_traverse_height= True)
    xy_pos()


def close_the_xy_stage():
    time.sleep(2)
    ser.close()


def view_grbl_settings():
    send_to_xy_stage(ser, '$$', read_all = True, verbose = True)
    xy_pos()


def kill_alarm():
    send_to_xy_stage(ser, "$X", read_all= True, verbose= True)


def generate_well_coordinates(Nwells, topleft, topright, bottomleft, bottomright):
    '''generate coordinates for all wells of a well plate from coordinates of corner wells.'''
    # left_side_wells
    xs = np.linspace(topleft[0], bottomleft[0], Nwells[0])
    ys = np.linspace(topleft[1], bottomleft[1], Nwells[0])
    left_side_wells = np.stack((xs, ys)).T

    # right side wells
    xs = np.linspace(topright[0], bottomright[0], Nwells[0])
    ys = np.linspace(topright[1], bottomright[1], Nwells[0])
    right_side_wells = np.stack((xs, ys)).T

    wells = []
    for i in range(Nwells[0]):
        xs = np.linspace(left_side_wells[i, 0], right_side_wells[i, 0], Nwells[1])
        ys = np.linspace(left_side_wells[i, 1], right_side_wells[i, 1], Nwells[1])
        wells.append(np.stack((xs, ys)).T)
    return np.vstack(wells)


def create_well_plate(template_well, Nwells, topleft, topright, bottomleft, bottomright):
    well_positions = generate_well_coordinates(Nwells, topleft, topright, bottomleft, bottomright)
    plate = {'wells': list()}
    for well_index in range(well_positions.shape[0]):
        plate['wells'].append(template_well.copy())
        plate['wells'][-1]['xy'] = well_positions[well_index, :]
    return plate


well1 = {'volume': 0,
         'xy': (-37, -52),
         'volume_max': 1800,
         'area': 75.56,  # container's horizontal cross-section area is in square mm
         'min_z': 12,  # location of container's # bottom above the floor
         'top_z': 32,  # height of container
         'containerGeometryTableIndex': 0,
         'lldSearchPosition': 'auto',
         'safety_margin_for_lldsearch_position': 40
         }
# This is for the 2-ml vial
# balance_vial = {'volume': 0,
#          'xy': (-715, -187),
#          'volume_max': 15000,
#          'area': 75.56*10,  # container's horizontal cross-section area is in square mm
#          'min_z': 59 + 1.2,  # location of container's # bottom above the floor
#          'top_z': 59 + 32,  # height of container
#          'containerGeometryTableIndex': 3,
#          'lldSearchPosition': 1410,
#          'safety_margin_for_lldsearch_position': 40
#          }

# This is the 40*40*40 square glass container
balance_vial = {'volume': 0,
         'xy': (-715, -187),
         'volume_max': 15000,
         'area': 40*40,  # container's horizontal cross-section area is in square mm
         'min_z': 73,  # location of container's # bottom above the floor
         'top_z': 73 + 40,  # height of container
         'containerGeometryTableIndex': 3,
         'lldSearchPosition': 1410,
         'safety_margin_for_lldsearch_position': 40
         }

tip_300ul = {'tip_vol': 300,
             'xy': (300, -100),
             'tipTypeTableIndex': 4,
            'deckGeometryTableIndex': 0,
            'ZeusTraversePosition': 650,
             'exists': True,
             'substance': 'None'
             }

tip_1000ul = {'tip_vol': 1000,
             'xy': (-296.5,-32.5),
             'tipTypeTableIndex': 6,
            'deckGeometryTableIndex': 1,
            'ZeusTraversePosition': 880,
              'exists': True,
             'substance': 'None'
             }

bottle_20ml = {'volume': 0,
               'xy': (-51.0, -6.0),
               'volume_max': 20000,
               'area': 510.7,  # container's horizontal cross-section area is in square mm
               'min_z': 10,  # location of container's # bottom above the floor
               'top_z': 62,  # height of container
               'containerGeometryTableIndex': 1,
               'lldSearchPosition': 'auto',
               'safety_margin_for_lldsearch_position': 40
               }

bottle1 = bottle_20ml.copy()
bottle2 = bottle_20ml.copy()
bottle3 = bottle_20ml.copy()
bottle4 = bottle_20ml.copy()
bottle5 = bottle_20ml.copy()
bottle6 = bottle_20ml.copy()
bottle7 = bottle_20ml.copy()
bottle8 = bottle_20ml.copy()

bottle1['xy'] = (-13,-172) # upper left
bottle2['xy'] = (-42, -172)
bottle3['xy'] = (-71, -172)
bottle4['xy'] = (-100, -172) # upper right
bottle5['xy'] = (-13, -202) # bottom left
bottle6['xy'] = (-42, -202)
bottle7['xy'] = (-71, -202)
bottle8['xy'] = (-100, -202)

bottle1['volume'] = 10000 # volume in ul. 15000 means 15 mL
bottle2['volume'] = 10000
bottle3['volume'] = 5000
bottle4['volume'] = 15000
bottle5['volume'] = 15000
bottle6['volume'] = 15000
bottle7['volume'] = 15000
bottle8['volume'] = 15000


jar1 = {'volume': 91500,
                'xy': ((-177, -187)),
                'volume_max': 100000,
                'area': 2123.7,  # container's horizontal cross-section area is in square mm
                'min_z': 5,  # location of container's # bottom above the floor in mm
                'top_z': 70,  # height of container in mm
                'neck_r': 3,  # inner radius of the neck in mm
                'containerGeometryTableIndex': 2,
                'lldSearchPosition': 1700

        }

jar2 = {'volume': 91500,
                'xy': (-238.5, -187),
                'volume_max': 100000,
                'area': 2123.7,  # container's horizontal cross-section area is in square mm
                'min_z': 5,  # location of container's # bottom above the floor in mm
                'top_z': 70,  # height of container in mm
                'neck_r': 3,  # inner radius of the neck in mm
                'containerGeometryTableIndex': 2,
                'lldSearchPosition': 1700
        }

def liquid_surface_in_container(container, verbose=True):
    height_of_liquid_from_floor = container['min_z'] + container['volume'] / container['area']
    if verbose:
        print(f'Height of liquid from the floor = {height_of_liquid_from_floor:.2f}')
    return int(round(floor_z - height_of_liquid_from_floor * 10))


def lld_search_position(container):
    if container['lldSearchPosition'] == 'auto':
        return int(round(liquid_surface_in_container(container) - container['safety_margin_for_lldsearch_position']))
    else:
        return container['lldSearchPosition']


# generate plate with tips
# generate coordinates for all wells of a well plate from coordinates of corner wells.
# tips_rack = create_well_plate(template_well=tip_300ul,
#                               Nwells=(8, 12),
#                               topleft=(398.5, -107),
#                               topright=(292, -107),
#                               bottomleft=(399, -174),
#                               bottomright=(293, -174))
# updated Dec27_2022
tips_rack_300ul = create_well_plate(template_well=tip_300ul,
                                    Nwells=(8, 12),
                                    topleft=(-158.5, -44.5),
                                    topright=(-257.5, -44.5),
                                    bottomleft=(-158.5, -107),
                                    bottomright=(-257.5, -107))

tips_rack_1000ul = create_well_plate(template_well=tip_1000ul,
                                    Nwells=(8, 12),
                                    topleft=(-296.5, -32.5),
                                    topright=(-396, -32.5),
                                    bottomleft=(-296.5, -95),
                                    bottomright=(-396, -95))

def pick_tip(tips_rack):
    move_z(tips_rack['wells'][0]['ZeusTraversePosition'])
    # wait_until_zeus_reaches_traverse_height()
    # In the rack, find the first tip that exists
    for tip in tips_rack['wells']:
        if tip['exists']:
            # pick up tip
            move_xy(tip['xy'], ensure_traverse_height= True)
            zm.pickUpTip(tipTypeTableIndex=tip['tipTypeTableIndex'], deckGeometryTableIndex=tip['deckGeometryTableIndex'])
            tip['exists'] = False
            # wait_until_zeus_reaches_traverse_height()
            wait_until_zeus_responds_with_string('GTid')
            return True
    print('ERROR: No tips in rack.')
    raise Exception

def discard_tip():
    move_z(ZeusTraversePosition_1000ul)
    # wait_until_zeus_reaches_traverse_height()
    move_xy(trash_xy)
    zm.discardTip(deckGeometryTableIndex=1)
    wait_until_zeus_responds_with_string('GUid')

# def discard_tip_1000():
#     move_z(ZeusTraversePosition_1000ul)
#     # wait_until_zeus_reaches_traverse_height()
#     move_xy(trash_xy)
#     zm.discardTip(deckGeometryTableIndex=1)
#     wait_until_zeus_responds_with_string('GUid')

def change_tip(tips_rack):
    discard_tip()
    pick_tip(tips_rack)


# generate coordinates for all wells of a well plate from coordinates of corner wells.
plate1 = create_well_plate(template_well=well1,
                          Nwells=(6, 9),
                          topleft=(-7, -255.5),
                          topright=(-111.5, -255.5),
                          bottomleft=(-7, -321),
                          bottomright=(-111.5, -321))

plate2 = create_well_plate(template_well=well1,
                          Nwells=(6, 9),
                          topleft=(-156.5, -255.5),
                          topright=(-261, -255.5),
                          bottomleft=(-156.5, -321),
                          bottomright=(-261, -321))

# save data to JSON file
def save_data():
    with open('data/plate1.json', 'w', encoding='utf-8') as f:
        for i in plate1['wells']:
            if not isinstance(i['xy'], list):
                i['xy'] =  i['xy'].tolist()
        json.dump(plate1, f, ensure_ascii=False, indent=4)
    with open('data/plate2.json', 'w', encoding='utf-8') as f:
        for i in plate1['wells']:
            if not isinstance(i['xy'], list):
                i['xy'] =  i['xy'].tolist()
        json.dump(plate2, f, ensure_ascii=False, indent=4)
    with open('data/tips_rack_300ul.json', 'w', encoding='utf-8') as f:
        for i in tips_rack_300ul['wells']:
            if not isinstance(i['xy'], list):
                i['xy'] =  i['xy'].tolist()
        json.dump(tips_rack_300ul, f, ensure_ascii=False, indent=4)
    with open('data/tips_rack_1000ul.json', 'w', encoding='utf-8') as f:
        for i in tips_rack_1000ul['wells']:
            if not isinstance(i['xy'], list):
                i['xy'] =  i['xy'].tolist()
        json.dump(tips_rack_1000ul, f, ensure_ascii=False, indent=4)


def move_through_wells(plate, dwell_time=1):
    for well in plate['wells']:
        move_xy(well['xy'])
        time.sleep(dwell_time)


def draw_liquid(container, volume, lld,  liquidClassTableIndex, liquidSurface=manual_vial_surface,
                n_retries=3):

    container['volume'] -= volume
    if zm.pos > ZeusTraversePosition_1000ul:
        move_z(ZeusTraversePosition_1000ul)
    #     wait_until_zeus_reaches_traverse_height()
    move_xy(container['xy'])
    for retry in range(n_retries):
        try:
            # This is used for organic solvents, e.g.BMF
            # print(f'Volume for zeus {int(round(volume_for_zeus(volume) * 10))}') # this is to offset the difference between water and the organic solvent, e.g. BMF
            # zm.aspiration(aspirationVolume=int(round(volume_for_zeus(volume)*10)),
            #               containerGeometryTableIndex=container['containerGeometryTableIndex'],
            #               deckGeometryTableIndex=1, liquidClassTableIndex=liquidClassTableIndex,
            #               qpm=1, lld=1, lldSearchPosition=lld_search_position(container),
            #               liquidSurface=liquid_surface_in_container(container),
            #               mixVolume=0, mixFlowRate=0, mixCycles=0)

            # This is used to test water
            print(f'Volume for zeus {int(round(volume * 10))}')
            zm.aspiration(aspirationVolume=int(round(volume * 10)),
                          containerGeometryTableIndex=container['containerGeometryTableIndex'],
                          deckGeometryTableIndex=1, liquidClassTableIndex=liquidClassTableIndex,
                          qpm=1, lld= lld, lldSearchPosition=lld_search_position(container),
                          liquidSurface=liquid_surface_in_container(container),
                          mixVolume=0, mixFlowRate=0, mixCycles=0)

            # time.sleep(1.5)
            time.sleep(2)
            wait_until_zeus_responds_with_string('GAid')
            return True
        except ZeusError:
            if zeus_error_code(zm.r.received_msg) == '81':
                # Empty tube detected during aspiration
                print('ZEUS ERROR: Empty tube during aspiration. Dispensing and trying again.')
                time.sleep(2)
                move_z(ZeusTraversePosition_1000ul)
                time.sleep(2)
                dispense_liquid(container, volume)
                time.sleep(2)
                continue

    print(f'Tried {n_retries} but zeus error is still there')
    raise Exception


def dispense_liquid(container, volume, liquidClassTableIndex, liquidSurface=manual_vial_surface,
                    liquid_surface_margin=50, deckGeometryTableIndex=1):

    if zm.pos > ZeusTraversePosition_1000ul:
        move_z(ZeusTraversePosition_1000ul)
        # wait_until_zeus_reaches_traverse_height()
    move_xy(container['xy'])

    # check if container is full.
    if container['volume'] >= container["volume_max"]:
        print("The target container is full. Dispensing is aborted.")
        return
    #print(f'Volume for zeus {int(round(volume_for_zeus(volume)*10))}') # this is to offset the difference between water and the organic solvent, e.g. BMF

    # this is used for organic solvents, e.g.BMF
    # zm.dispensing(dispensingVolume=int(round(volume_for_zeus(volume)*10)),
    #               containerGeometryTableIndex=container['containerGeometryTableIndex'],
    #               deckGeometryTableIndex=deckGeometryTableIndex, liquidClassTableIndex=liquidClassTableIndex,
    #               lld=0, lldSearchPosition=lld_search_position(container),
    #               liquidSurface=liquid_surface_in_container(container) - liquid_surface_margin,
    #               searchBottomMode=0, mixVolume=0, mixFlowRate=0, mixCycles=0)
    #

    # this is used for testing water
    zm.dispensing(dispensingVolume=int(round(volume*10)),
                  containerGeometryTableIndex=container['containerGeometryTableIndex'],
                  deckGeometryTableIndex=deckGeometryTableIndex, liquidClassTableIndex=liquidClassTableIndex,
                  lld=0, lldSearchPosition=lld_search_position(container),
                  liquidSurface=liquid_surface_in_container(container) - liquid_surface_margin,
                  searchBottomMode=0, mixVolume=0, mixFlowRate=0, mixCycles=0)

    time.sleep(1.5)
    # wait_until_zeus_reaches_traverse_height()
    wait_until_zeus_responds_with_string('GDid')
    container['volume'] += volume


def dispense_to_balance(volume, container=balance_vial, liquidClassTableIndex=2, liquidSurface=manual_vial_surface,
                    liquid_surface_margin=50, deckGeometryTableIndex=1):

    print(f" balance_ vial volume is now : { container['volume']}")
    if zm.pos > balance_traverse_height:
        move_z(balance_traverse_height)
        # wait_until_zeus_reaches_traverse_height(traverse_height=balance_traverse_height)
    move_to_balance(balance_vial)
    zm.dispensing(dispensingVolume=int(round(volume*10)),
                  containerGeometryTableIndex=container['containerGeometryTableIndex'],
                  deckGeometryTableIndex=deckGeometryTableIndex,
                  liquidClassTableIndex=liquidClassTableIndex,
                  lld=0, lldSearchPosition=lld_search_position(container),
                  liquidSurface=liquid_surface_in_container(container) - liquid_surface_margin,
                  searchBottomMode=0, mixVolume=0, mixFlowRate=0, mixCycles=0)
    time.sleep(1.5)
    # wait_until_zeus_reaches_traverse_height(traverse_height=balance_traverse_height)
    wait_until_zeus_responds_with_string('GDid')
    move_xy(xy_idle)
    container['volume'] += volume
    print(f" balance_ vial volume is now : { container['volume']}")


def transfer_liquid(source, destination, volume_here, lld, liquidClassTableIndex, max_volume=900):

    # check if container is full.
    if destination['volume'] >= destination["volume_max"]:
        print("The target container is full. Dispensing is aborted.")
        return

    # if it exceeds max_volume, then do several pipettings
    N_max_vol_pipettings = int(volume_here // max_volume)

    for i in range(N_max_vol_pipettings):
        draw_liquid(source, lld, volume = max_volume)
        dispense_liquid(destination, volume=max_volume)

    volume_of_last_pipetting = volume_here % max_volume
    draw_liquid(source, lld, liquidClassTableIndex, volume = volume_of_last_pipetting)
    dispense_liquid(destination, liquidClassTableIndex, volume = volume_of_last_pipetting)


def transfer_liquid_simple(source, destination, volume, lld, liquidClassTableIndex):

    # check if container is full.
    if destination['volume'] >= destination["volume_max"]:
        print("The target container is full. Dispensing is aborted.")
        return
    draw_liquid(container = source, lld =lld, liquidClassTableIndex = liquidClassTableIndex, volume = volume)
    dispense_liquid(container = destination, liquidClassTableIndex = liquidClassTableIndex, volume = volume)


def empty_plate_vials():
    global plate1
    global plate2
    well1['volume'] = 0
    plate1 = create_well_plate(template_well=well1,
                               Nwells=(6, 9),
                               topleft=(-7, -255.5),
                               topright=(-111.5, -255.5),
                               bottomleft=(-7, -321),
                               bottomright=(-111.5, -321))
    plate2 = create_well_plate(template_well=well1,
                               Nwells=(6, 9),
                               topleft=(-156.5, -255.5),
                               topright=(-261, -255.5),
                               bottomleft=(-156.5, -321),
                               bottomright=(-261, -321))




# container_having_substance = {'Isocyano':bottle6,
#                               'amine':bottle5,
#                               'aldehyde':bottle2,
#                               'pTSA':bottle3,
#                               'DMF': jar1}
#
# excel_filename = 'C:\\Users\\Chemiluminescence\\Desktop\\roborea_data\\' \
#                  '2022-12-14-run01\\input_compositions\\compositions.xlsx'
# df = pd.read_excel(excel_filename,
#                    sheet_name='Sheet1', usecols='I,J,K,L,M')
#
# xy1 = plate1['wells'][0]['xy'] # coord of the first 2ml vial




## the following is for typing lazines
def dis():
    discard_tip()

def request_zeus():
    pass

def pick():
    pick_tip(tips_rack_1000ul)

def draw():
    draw_liquid(jar2, 200)

def disp():
    dispense_liquid(plate1['wells'][0], 800)

def dispb():
    dispense_liquid(balance_vial, 100)

def weight():
    dispense_to_balance_and_weight(bottle8, 100, timedelay=5)

def weight_n(volume):
    dispense_to_balance_and_weight_n_times(jar2, volume, ntimes=10, timedelay=5)

def test_sd():
    pick()
    for i in range(1, 10):
        weight_n(i*100)
    dis()
    json.dump(weighted_values, open("weighted_values.txt",'w'))

def reaction():
    for i in range(0, 5):
        transfer_liquid_simple(source=bottle1,
                               destination=plate1['wells'][i],
                               volume=500, lld = 0,
                               liquidClassTableIndex=14)
        time.sleep(0.5)
    dis()
    pick()
    for i in range(3, 6):
        transfer_liquid_simple(source=bottle7,
                               destination= plate1['wells'][i],
                               volume=100, lld = 0,
                               liquidClassTableIndex= 14)
        time.sleep(0.5)
    dis()
    pick()
    for i in range(3, 6):
        transfer_liquid_simple(source=bottle8,
                               destination=plate1['wells'][i],
                               volume=100, lld = 0,
                               liquidClassTableIndex= 14)
        time.sleep(0.5)
    dis()
    move_xy(xy_idle)
    print(f'Pipetting done!')



def test_bv():
    n_times = 5
    for i in range(n_times):
        print(f'n = {i} / {n_times} cycles')
        draw_liquid(container=bottle6, volume=100, liquidClassTableIndex= 14, lld = 0)
        # time.sleep(0.5)
        dispense_to_balance(volume=100, liquidClassTableIndex=14)
        # time.sleep(0.5)

# zm.sendString('GAid0000ai01000ge01go01lq14gq1lb1zp1667cf1707ma00000mb00000dn00')

avg = []
std = []
def ast(weighted_values= weighted_values):
    global avg
    global std
    keys = [key for key in weighted_values]
    for i in keys:
        print(i)
        avg.append(np.mean(weighted_values[i]))
        std.append(np.std(weighted_values[i]))
    xx = [i for i in range(1, 10)]
    plt.errorbar(xx, avg[:9], std[:9], linestyle = 'None', marker = '^',  capsize=4, elinewidth=2, markersize = 6)
    plt.plot(xx,[x*100 for x in xx], marker = '.', markersize = 6)
    # plt.ylim(190, 210)
    plt.show()
    return [avg, std]


time.sleep(1)
home_xy()

# import json
# json.dump(weighted_values, open("weighted_values.txt",'w'))

# # df_one_plate = df.head(54)  # plate #1
# df_one_plate = df.iloc[54:] # plate #2
#
# addition_sequence = ['DMF', 'aldehyde', 'pTSA', 'amine', 'Isocyano']
# # addition_sequence = ['pTSA', 'amine', 'Isocyano']
# for substance in addition_sequence:
#     if not (substance == addition_sequence[0]):
#         change_tip(tips_rack)
#         time.sleep(6)
#     t0 = time.time()
#     for well_id, volume in enumerate(df_one_plate[substance + '.1']):
#         if substance == 'DMF' and well_id < 26:
#             print(f'Skipping substance {substance}, well {well_id}')
#             continue
#         print('Substance {0}, well {1}, volume {2}'.format(substance, well_id, volume))
#         if volume == 0:
#             print('Target volume is zero. Skipping operation.')
#             continue
#         transfer_liquid(container_having_substance[substance],
#                         plate['wells'][well_id],
#                         volume)
#     print('Time_elapsed: {0:.1f} min'.format((time.time() - t0) / 60))


# # motion tests
# for i in range(10):
#     move_xy((400, -100), block_until_motion_is_completed=True, use_time_estimates=True)
#     move_xy((300, -200), block_until_motion_is_completed=True, use_time_estimates=True)


##TODO
# 1 change dispensing height for 2ml vials