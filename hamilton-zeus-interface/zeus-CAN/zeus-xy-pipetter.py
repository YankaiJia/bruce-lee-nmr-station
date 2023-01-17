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
import statistics

# statistics.stdev()
# plt.ion()

class ZeusError(Exception):
    pass

# ZeusTraversePosition_300ul = 650
ZeusTraversePosition_1000ul = 880
xy_idle = (-345, -187)

balance_traverse_height = 880
floor_z = 2300
manual_vial_surface = 2152

weighted_values = {}


# # ZEUS
zm = zeus.ZeusModule(id=1)
time.sleep(3)

## Declarations

# Deck loading
deckgeom_300ul = zeus.DeckGeometry(index=0, endTraversePosition=ZeusTraversePosition_1000ul,
                             beginningofTipPickingPosition=1530,
                             positionofTipDepositProcess=1817)
zm.setDeckGeometryParameters(deckGeometryParameters=deckgeom_300ul)
print('Zeus deck geometry loaded')
time.sleep(1)

deckgeom_1000ul= zeus.DeckGeometry(index=1, endTraversePosition=ZeusTraversePosition_1000ul,
                                   beginningofTipPickingPosition=1210,
                                   positionofTipDepositProcess=1600)
zm.setDeckGeometryParameters(deckGeometryParameters=deckgeom_1000ul)
print('Zeus deck geometry loaded')
time.sleep(1)

deckgeom_balance = zeus.DeckGeometry(index=2, endTraversePosition=balance_traverse_height,
                             beginningofTipPickingPosition=1530,
                             positionofTipDepositProcess=2217)
zm.setDeckGeometryParameters(deckGeometryParameters=deckgeom_balance)
print('Zeus deck geometry loaded')
time.sleep(1)

# Declarations
# TODO: In the object-oriented version this will be depend on target container dictionaries passed by
#  the module's user
container_2mL_vial = zeus.ContainerGeometry(index=0, diameter=98, bottomHeight=0, bottomSection=10000,
                 bottomPosition=2172, immersionDepth=20, leavingHeight=20, jetHeight=130,
                 startOfHeightBottomSearch=30, dispenseHeightAfterBottomSearch=80)
zm.setContainerGeometryParameters(containerGeometryParameters=container_2mL_vial)
print('2ml vial container loaded')
time.sleep(1)

container_20mL_bottle = zeus.ContainerGeometry(index=1, diameter=255, bottomHeight=0, bottomSection=10000,
                 bottomPosition=2135, immersionDepth=20, leavingHeight=30, jetHeight=130,
                 startOfHeightBottomSearch=20, dispenseHeightAfterBottomSearch=50)
zm.setContainerGeometryParameters(containerGeometryParameters=container_20mL_bottle)
print('20 ml bottle container loaded')
time.sleep(1)

container_jar = zeus.ContainerGeometry(index=2, diameter=520, bottomHeight=0, bottomSection=10000,
                                       bottomPosition=2070, immersionDepth=40, leavingHeight=40, jetHeight=130,
                                       startOfHeightBottomSearch=50, dispenseHeightAfterBottomSearch=50,
                                       )
zm.setContainerGeometryParameters(containerGeometryParameters=container_jar)
print('Jar container loaded')
time.sleep(1)

container_balance_vial = zeus.ContainerGeometry(index=3, diameter=400, bottomHeight=0, bottomSection=10000,
                 bottomPosition=1590, immersionDepth=20, leavingHeight=20, jetHeight=100,
                 startOfHeightBottomSearch=30, dispenseHeightAfterBottomSearch=100)
zm.setContainerGeometryParameters(containerGeometryParameters=container_balance_vial)
print('Balance container loaded')
time.sleep(1)

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
        plate['wells'][-1]['xy'] = list(well_positions[well_index, :])
    return plate

def generate_wellplates():
    well1 = {'volume': 0,
             'xy': (-37, -52),
             'volume_max': 1800,
             'area': 75.56,  # container's horizontal cross-section area is in square mm
             'min_z': (floor_z - container_2mL_vial.bottomPosition) / 10 ,  # location of container's bottom above the floor in mm
             'top_z': 32,  # height of container
             'containerGeometryTableIndex': 0,
             'lldSearchPosition': 'auto',
             'safety_margin_for_lldsearch_position': 40
             }
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
    return plate1, plate2
plate1, plate2 = generate_wellplates()

plate = (plate1, plate2)

def generate_balance_container():
    # This is for the 2-ml vial on balance
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
    balance_cup = {'volume': 0,
             'xy': (-715, -187),
             'volume_max': 15000,
             'area': 40*40,  # container's horizontal cross-section area is in square mm
             'min_z': (floor_z - container_balance_vial.bottomPosition) / 10,  # location of container's bottom above the floor in mm
             'top_z': 73 + 40,  # height of container
             'containerGeometryTableIndex': 3,
             'lldSearchPosition': 1410,
             'safety_margin_for_lldsearch_position': 40
             }
    return balance_cup
balance_cup = generate_balance_container()

def generate_bottle_container():
    bottle = {}
    bottle_20ml = {'volume': 0,
                   'xy': (-51.0, -6.0),
                   'volume_max': 20000,
                   # container's horizontal cross-section area is in square mm
                   'area': 510.7,
                   # location of container's # bottom above the floor
                   'min_z': (floor_z - container_20mL_bottle.bottomPosition) / 10,
                   'top_z': 62,  # height of container
                   'containerGeometryTableIndex': 1,
                   'lldSearchPosition': 'auto',
                   'safety_margin_for_lldsearch_position': 40
                   }

    for i in range(8):
        bottle[str(i)] = bottle_20ml.copy()

    bottle['0']['xy'] = (-13, -172)  # upper left
    bottle['1']['xy'] = (-42, -172)
    bottle['2']['xy'] = (-71, -172)
    bottle['3']['xy'] = (-100, -172)  # upper right
    bottle['4']['xy'] = (-13, -202)  # bottom left
    bottle['5']['xy'] = (-42, -202)
    bottle['6']['xy'] = (-71, -202)
    bottle['7']['xy'] = (-100, -202)

    bottle['0']['volume'] = 20000  # volume in ul. 15000 means 15 mL
    bottle['1']['volume'] = 20000
    bottle['2']['volume'] = 20000
    bottle['3']['volume'] = 20000
    bottle['4']['volume'] = 20000
    bottle['5']['volume'] = 20000
    bottle['6']['volume'] = 12000
    bottle['7']['volume'] = 20000
    print('Bottle container generated!')
    return bottle
bottle = generate_bottle_container()

def generated_jar_container():
    jar = {'0': {'volume': 91500,
                    'xy': ((-177, -187)),
                    'volume_max': 100000,
                    'area': 2123.7,  # container's horizontal cross-section area is in square mm
                    'min_z': (floor_z - container_jar.bottomPosition) / 10,  # location of container's # bottom above the floor in mm
                    'top_z': 70,  # height of container in mm
                    'neck_r': 3,  # inner radius of the neck in mm
                    'containerGeometryTableIndex': 2,
                    'lldSearchPosition': 1700},
           '1' : {'volume': 91500,
                    'xy': (-238.5, -187),
                    'volume_max': 100000,
                    'area': 2123.7,  # container's horizontal cross-section area is in square mm
                    'min_z': (floor_z - container_jar.bottomPosition) / 10,  # location of container's # bottom above the floor in mm
                    'top_z': 70,  # height of container in mm
                    'neck_r': 3,  # inner radius of the neck in mm
                    'containerGeometryTableIndex': 2,
                    'lldSearchPosition': 1700}
           }
    print('Jar container generated!')
    return jar
jar = generated_jar_container()

def load_new_tip_tack(rack_reload ):
    # tip_rack = {}
    with open('data/tip_rack.json') as json_file:
        tip_rack = json.load(json_file)

    tip = {'300ul': {'tip_vol': 300,
                     'xy': (300, -100),
                     'tipTypeTableIndex': 4,
                     'deckGeometryTableIndex': 0,
                     'ZeusTraversePosition': 650,
                     'exists': True,
                     'substance': 'None'
                     },
           '1000ul': {'tip_vol': 1000,
                      'xy': (-296.5, -32.5),
                      'tipTypeTableIndex': 6,
                      'deckGeometryTableIndex': 1,
                      'ZeusTraversePosition': 880,
                      'exists': True,
                      'substance': 'None'
                      }
           }
    if rack_reload == '300ul':
        tip_rack['300ul'] = create_well_plate(template_well=tip['300ul'],
                                        Nwells=(8, 12),
                                        topleft=(-158.5, -44.5),
                                        topright=(-257.5, -44.5),
                                        bottomleft=(-158.5, -107),
                                        bottomright=(-257.5, -107))
    if rack_reload == '1000ul':
        tip_rack['1000ul'] = create_well_plate(template_well=tip['1000ul'],
                                        Nwells=(8, 12),
                                        topleft=(-296.5, -32.5),
                                        topright=(-396, -32.5),
                                        bottomleft=(-296.5, -95),
                                        bottomright=(-396, -95))

    with open('data/tip_rack.json', 'w', encoding='utf-8') as f:
        json.dump(tip_rack, f, ensure_ascii=False, indent=4)

    return tip_rack
## run this ONLY when changing new tip rack.
# load_new_tip_tack(rack_reload = '300ul')
# load_new_tip_tack(rack_reload = '1000ul')


# Zeus
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

def zeus_is_at_traverese_height():
    if zm.pos <= ZeusTraversePosition_1000ul:
        return True
    else:
        print(f'ERROR: ZEUS was not in traverse height before motion, but instead at {zm.pos}')
        return False

def pos_z():
    print(zm.getAbsoluteZPosition())

move_z(880)


# XY stage
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
def configure_grbl():
    with open('grbl_settings.txt', 'r') as grbl_config_file:
        for line in grbl_config_file:
            # extract command before the comments
            send_to_xy_stage(ser, command=line.split('    (')[0], read_all=True, verbose=True)
    print('XY stage configured.')

configure_grbl()

def xy_pos():
    send_to_xy_stage(ser, '?', read_all=True, verbose=True)
def pos_xy():
    xy_pos()

# def move_xy(x, y):
def time_that_xy_motion_takes(dx, dy, acceleration=2000, max_speed=333.33333):

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



# LIQUID
def liquid_surface_in_container(container, verbose=True):
    height_of_liquid_from_floor = container['min_z'] + container['volume'] / container['area']
    if verbose:
        print(f'Height of liquid from the floor = {height_of_liquid_from_floor:.2f}')
    height  = int(round(floor_z - height_of_liquid_from_floor * 10))
    print(f'liquid height in container is : {height}')
    return height

def lld_search_position(container):
    if container['lldSearchPosition'] == 'auto':
        return int(round(liquid_surface_in_container(container) - container['safety_margin_for_lldsearch_position']))
    else:
        return container['lldSearchPosition']


def pick_tip(tip_type):

    with open('data/tip_rack.json') as json_file:
        tip_rack = json.load(json_file)

    move_z(tip_rack[str(tip_type)+'ul']['wells'][0]['ZeusTraversePosition'])
    # wait_until_zeus_reaches_traverse_height()
    # In the rack, find the first tip that exists
    for item in tip_rack[str(tip_type)+'ul']['wells']:
        if item['exists']:
            # pick up tip
            move_xy(item['xy'], ensure_traverse_height= True)
            zm.pickUpTip(tipTypeTableIndex=item['tipTypeTableIndex'], deckGeometryTableIndex=item['deckGeometryTableIndex'])
            item['exists'] = False
            # wait_until_zeus_reaches_traverse_height()
            wait_until_zeus_responds_with_string('GTid')
            # update json file
            with open('data/tip_rack.json', 'w', encoding='utf-8') as f:
                json.dump(tip_rack, f, ensure_ascii=False, indent=4)
            return True
    print('ERROR: No tips in rack.')
    raise Exception

def discard_tip():
    move_z(ZeusTraversePosition_1000ul)
    # wait_until_zeus_reaches_traverse_height()
    move_xy(trash_xy)
    zm.discardTip(deckGeometryTableIndex=1)
    wait_until_zeus_responds_with_string('GUid')

def change_tip(tip_rack):
    discard_tip()
    pick_tip(tip_rack)

def move_through_wells(plate, dwell_time=1):
    for well in plate['wells']:
        move_xy(well['xy'])
        time.sleep(dwell_time)

def draw_liquid(container, volume, lld,  liquidClassTableIndex, tip_type = '300ul', liquidSurface=manual_vial_surface,
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

            tip_dict = {'300ul':0, '1000ul':1}
            print(f'Aspiration volume: {int(round(volume * 10))}')
            zm.aspiration(aspirationVolume=int(round(volume * 10)),
                          containerGeometryTableIndex=container['containerGeometryTableIndex'],
                          deckGeometryTableIndex=tip_dict[tip_type], liquidClassTableIndex=liquidClassTableIndex,
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



# BALANCE
balance_port = serial.Serial('COM7', 19200, stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE,
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

def balance_zero(verbose = True):
    balance_port.write(str.encode('Z\n'))
    zeroing_complete = False
    while True:
        line = balance_port.readline()
        if b'Z' in line:
            zeroing_complete = True
        if verbose:
            print(f'Tare in progress. Response from balance. {line}')
        if line == b'':
            if zeroing_complete:
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

def move_to_balance(container):
    open_balance_door()
    move_z(balance_traverse_height)
    move_xy(container['xy'])

def dispense_to_balance_and_weight(source_container, volume, lld, liquid_class_index, timedelay=5):
    global xy_position
    global weighted_values
    # if xy_position[0] < -80:
    #     move_xy((-80, -195))
    close_balance_door()
    time.sleep(timedelay)
    # balance_tare()
    balance_zero(verbose=True)
    draw_liquid(container=source_container, volume=volume, lld = lld, liquidClassTableIndex= liquid_class_index)
    weight_before = balance_value()
    print(f'weight_before: {weight_before} g')
    dispense_to_balance(volume=volume, liquidClassTableIndex= liquid_class_index, container= balance_cup)
    close_balance_door()
    time.sleep(timedelay)
    weight_after = balance_value()
    print(f'weight_after: {weight_after} g')
    print(f'Weight of aliquot: {(weight_after - weight_before)*1000} mg')
    print(f'Volume of aliquot: {volume}')
    return round((weight_after - weight_before)*1000, 1)

def dispense_to_balance_and_weight_n_times(source_container, volume,lld, liquid_class_index,  ntimes, timedelay=3):
    result = []
    t0 = time.time()
    for i in range(ntimes):
        print(f'Dispensing to balance and weighting: iteration {i} out of {ntimes}')
        weight_here = dispense_to_balance_and_weight(source_container=source_container,
                                                     volume=volume, timedelay=timedelay, lld = lld, liquid_class_index = liquid_class_index)
        result.append(weight_here)
        time.sleep(timedelay)
        print(f'Dispensing to balance and weighting took {time.time()-t0:.2f} seconds')
    return result

# dispense_to_balance_and_weight_n_times(source_container = jar['0'], volume = 500,lld = 1, liquid_class_index = 23,  ntimes = 3, timedelay=3)

def get_calibration_values21(index, liquid):

    weighted_values = {}
    density_dict = {'DMF': 0.944, "THF": 0.888, }
    liquid_density = density_dict[liquid]
    if index == 2:
        # volumes_list = [100, 200, 300, 400, 500, 700, 800, 1000]
        volumes_list = [ 800, 1000]

        # volumes = [750, 1000]
        # volumes = [10, 750]
    for i in volumes_list[::-1]:
        values = dispense_to_balance_and_weight_n_times(source_container = jar['0'], volume = i, lld = 1, liquid_class_index = index, ntimes = 5, timedelay=5)
        print(f'values: {values}')
        weighted_values[str(i)+'ul'] = {}
        weighted_values[str(i)+'ul']['data'] = values
        weighted_values[str(i) + 'ul']['volume'] = [x / liquid_density for x in values]
        weighted_values[str(i) + 'ul']['avg'] = ( sum(values) / len(values) ) / liquid_density
        weighted_values[str(i) + 'ul']['std'] = statistics.stdev([x / liquid_density for x in values])

        with open('data/Weighted_values_for_calibration_index2_should_work.json', 'w', encoding='utf-8') as f:
            json.dump(weighted_values, f, ensure_ascii=False, indent=4)

    print('done and data save!!!')

    return weighted_values

# get_calibration_values21(index = 2, liquid = 'DMF')


def get_calibration_values22(index = 22, liquid = 'DMF', tip = 300):

    if not zm.getTipPresenceStatus():
        time.sleep(0.5)
        pick_tip(300)

    weighted_values = {}
    density_dict = {'DMF': 0.944, "THF": 0.888, }
    liquid_density = density_dict[liquid]
    if index == 22:
        # volumes = [10, 20, 50, 100, 200, 500, 750, 1000]
        # volumes = [1, 5, 10, 25, 50, 100, 200, 300]

        volumes = [1, 5]
        # volumes = [1, 5, 10, 25]
        # volumes = [750, 1000]
        # volumes = [10, 750]
    for i in volumes[::-1]:
        values = dispense_to_balance_and_weight_n_times(source_container = bottle['6'], volume = i, lld = 1, liquid_class_index = index, ntimes = 10, timedelay=5)
        print(f'values: {values}')
        weighted_values[str(i)+'ul'] = {}
        weighted_values[str(i)+'ul']['data'] = values
        weighted_values[str(i) + 'ul']['volume'] = [x / liquid_density for x in values]
        weighted_values[str(i) + 'ul']['avg'] = ( sum(values) / len(values) ) / liquid_density
        weighted_values[str(i) + 'ul']['std'] = statistics.stdev([x / liquid_density for x in values])

        with open('data/Weighted_values_for_calibration_index22_fresh_liquid_lld1_1830.json', 'w', encoding='utf-8') as f:
            json.dump(weighted_values, f, ensure_ascii=False, indent=4)

    print('done and data save!!!')

    return weighted_values

# bbb = get_calibration_values22(index = 22, liquid = 'DMF')


# weighted_values = get_calibration_values(index = 21)


# Calibration
def dispense_to_balance(volume, liquidClassTableIndex, container=balance_cup, liquidSurface=manual_vial_surface,
                    liquid_surface_margin=50, deckGeometryTableIndex=0):

    print(f" balance_ vial volume is now : { container['volume']}")
    if zm.pos > balance_traverse_height:
        move_z(balance_traverse_height)
        # wait_until_zeus_reaches_traverse_height(traverse_height=balance_traverse_height)
    move_to_balance(container)
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


def transfer_liquid(source, destination, volume, lld, liquidClassTableIndex, max_volume=280):

    # check if container is full.
    if destination['volume'] >= destination["volume_max"]:
        print("The target container is full. Dispensing is aborted.")
        return

    # if it exceeds max_volume, then do several pipettings
    N_max_vol_pipettings = int(volume // max_volume)

    for i in range(N_max_vol_pipettings):
        draw_liquid(container = source,volume = max_volume,  lld = lld, liquidClassTableIndex = liquidClassTableIndex)
        dispense_liquid(container = destination, volume = max_volume, liquidClassTableIndex= liquidClassTableIndex)

    volume_of_last_pipetting = volume % max_volume
    if volume_of_last_pipetting:
        draw_liquid(container = source, volume = volume_of_last_pipetting, lld = lld, liquidClassTableIndex = liquidClassTableIndex, )
        dispense_liquid(container = destination, volume = volume_of_last_pipetting, liquidClassTableIndex= liquidClassTableIndex)


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

# def load_calibration_dict_from_file(calibration_file):
#     if os.path.exists(calibration_file):
#         with open(calibration_file, 'rb') as handle:
#             calibration_dictionary = pickle.load(handle)
#             print('Calibration file loaded.')
#     return calibration_dictionary
#
# calibration_dict = load_calibration_dict_from_file(
#     calibration_file='calibration/calibration_DMF_300ul_lld_qpm__empty_jet.pickle')

#
# def volume_for_zeus(real_volume, calibration_dict=calibration_dict):
#     zeus_volumes = [0]
#     real_volumes = [0]
#     sigmas = []
#     for zeus_volume in sorted(calibration_dict.keys()):
#         zeus_volumes.append(zeus_volume)
#         real_volumes.append(calibration_dict[zeus_volume][0])
#         sigmas.append(calibration_dict[zeus_volume][1])
#     zeus_volumes = np.array(zeus_volumes)
#     real_volumes = np.array(real_volumes)
#     sigmas = np.array(sigmas)
#     calibration_interpolator = interpolate.interp1d(x=real_volumes, y=zeus_volumes, fill_value='extrapolate')
#     result = calibration_interpolator(real_volume)
#     if not result.shape:
#         result = result.tolist()
#     return result


time.sleep(1)
home_xy()
print('init finished.')


###########################################################################
#################### Run reactions ########################################

t0 = time.time()
indicator = 0 # Indicator from which plate the pipetting is going to. 0: plate['0']. 1: plate['1']
container_having_substance = {'Isocyano': bottle['4'],
                              'amine':bottle['5'],
                              'aldehyde':bottle['6'],
                              'pTSA':bottle['7'],
                              'DMF': jar['0']}
addition_sequence = ('DMF', 'aldehyde', 'pTSA', 'amine', 'Isocyano')
# addition_sequence = ( 'aldehyde', 'pTSA', 'amine', 'Isocyano')

excel_filename = 'multicompnent_reaction_input\\composition_input_20230110RF029.xlsx'
df1 = pd.read_excel(excel_filename, sheet_name='Robot', usecols='R:V')
df = df1.copy()
# df.columns = [i[:-2] if '.2' in i else i for i in df.columns]
df.columns = [col_name.split('.')[0] for col_name in df.columns]

def devide_data_frame(data_frame, n):
    """A generator to divide the reactions into chunks of n units. Each chunk is one reaction_plate"""
    while len(data_frame):
        yield data_frame.iloc[:n]
        data_frame = data_frame.iloc[n:]

def generate_n_reaction_plate():
    reaction_plate_n = tuple(devide_data_frame(df, 53)) # The volume will not change after devision,
                                                        # so use tuple for protection
    for i in range(len(reaction_plate_n)):
        index = reaction_plate_n[i].index[0]
        print(f'reaction range in {i}th plate: {index} --- {index + len(reaction_plate_n[i])-1}')
    return reaction_plate_n
reaction_plate_n = generate_n_reaction_plate()


def pipette_one_plate(reaction_plate_number ):
    global indicator
    for substance in addition_sequence:
        for well_id, volume in enumerate(reaction_plate_n[reaction_plate_number][substance]):
            print(f'substance: {substance}, index: {well_id}, tranfer volume: {volume}')
            indicator = reaction_plate_number % 2 ## even or odd
            # move_xy(container_having_substance[substance]['xy'])
            # time.sleep(0.1)
            # move_xy(plate[indicator]['wells'][well_id]['xy'])
            # time.sleep(0.1)
            transfer_liquid(source = container_having_substance[substance],
                            destination = plate[indicator]['wells'][well_id],
                                volume = volume, lld = 1, liquidClassTableIndex=1)
            print(f'well_plate0 or well_plate1: {str(indicator)}')
            # print('Time_elapsed: {0:.1f} min'.format((time.time() - t0) / 60))

def pipette_n_plate():
    for i in range(len(reaction_plate_n)):
        if input('Ready for next reaction_plate: ') in ['yes', 'Yes', 'Y', '1', 'True', 'true']:
            print(f"OKAY, I will pipette the: {i}th reaction_plate! Starting...")
            pipette_one_plate(reaction_plate_number=i)
        else:
            print(f"The pipetting is stopped! Next you should do the {i}th reaciton_plate")
            return

# pipette_n_plate()








#






## the following is for typing lazines. No more info presented below
def home():
    home_xy()

def z(z):
    move_z(z)

def z_pos(z):
    pos_z(z)

def xy(pos):
    move_xy(pos)

def dis():
    discard_tip()

def pick( tip ):
    pick_tip(tip)

def draw():
    draw_liquid(jar['1'], 200)

def disp():
    dispense_liquid(container = bottle['6'], volume = 200, liquidClassTableIndex = 21, liquidSurface=manual_vial_surface,
                    liquid_surface_margin=50, deckGeometryTableIndex=1)

def reaction():
    pick()
    for i in range(0, 6):
        transfer_liquid(source=bottle['0'],
                               destination=plate1['wells'][i],
                               volume=500, lld = 0,
                               liquidClassTableIndex=21)
        time.sleep(0.5)
    dis()
    pick()
    for i in range(0, 6):
        # transfer_liquid(source, destination, volume, lld, liquidClassTableIndex, max_volume=900)

        transfer_liquid(source=bottle['1'],
                               destination= plate1['wells'][i],
                               volume=500, lld = 0,
                               liquidClassTableIndex= 21)
        time.sleep(0.5)
    dis()
    pick()
    for i in range(0, 6):
        transfer_liquid(source=bottle['2'],
                               destination=plate1['wells'][i],
                               volume=500, lld = 0,
                               liquidClassTableIndex= 21)
        time.sleep(0.5)
    dis()
    move_xy(xy_idle)
    print(f'Pipetting for reations done!')

def height(container):
    liquid_surface_in_container(container = container, verbose=True)










def dr(container, volume, lld,  liquidClassTableIndex, tip_type = '300ul', liquidSurface=manual_vial_surface,
                n_retries=3):

    container['volume'] -= volume
    if zm.pos > ZeusTraversePosition_1000ul:
        move_z(ZeusTraversePosition_1000ul)
    #     wait_until_zeus_reaches_traverse_height()
    move_xy(container['xy'])

    tip_dict = {'300ul':0, '1000ul':1}
    print(f'Aspiration volume: {int(round(volume * 10))}')
    zm.aspiration(aspirationVolume=int(round(volume * 10)),
                  containerGeometryTableIndex=container['containerGeometryTableIndex'],
                  deckGeometryTableIndex=tip_dict[tip_type], liquidClassTableIndex=liquidClassTableIndex,
                  qpm=1, lld= lld, lldSearchPosition=lld_search_position(container),
                  liquidSurface=liquid_surface_in_container(container),
                  mixVolume=0, mixFlowRate=0, mixCycles=0)

    #         # time.sleep(1.5)
    #         time.sleep(2)
    #         wait_until_zeus_responds_with_string('GAid')
    #         return True
    #     except ZeusError:
    #         if zeus_error_code(zm.r.received_msg) == '81':
    #             # Empty tube detected during aspiration
    #             print('ZEUS ERROR: Empty tube during aspiration. Dispensing and trying again.')
    #             time.sleep(2)
    #             move_z(ZeusTraversePosition_1000ul)
    #             time.sleep(2)
    #             dispense_liquid(container, volume)
    #             time.sleep(2)
    #             continue
    #
    # print(f'Tried {n_retries} but zeus error is still there')
    # raise Exception


def ds(container, volume, liquidClassTableIndex, liquidSurface=manual_vial_surface,
                    liquid_surface_margin=50, deckGeometryTableIndex=1):

    if zm.pos > ZeusTraversePosition_1000ul:
        move_z(ZeusTraversePosition_1000ul)
        # wait_until_zeus_reaches_traverse_height()
    move_xy(container['xy'])

    # check if container is full.
    if container['volume'] >= container["volume_max"]:
        print("The target container is full. Dispensing is aborted.")
        return

    # this is used for testing water
    zm.dispensing(dispensingVolume=int(round(volume*10)),
                  containerGeometryTableIndex=container['containerGeometryTableIndex'],
                  deckGeometryTableIndex=deckGeometryTableIndex, liquidClassTableIndex=liquidClassTableIndex,
                  lld=0, lldSearchPosition=lld_search_position(container),
                  liquidSurface=liquid_surface_in_container(container) - liquid_surface_margin,
                  searchBottomMode=0, mixVolume=0, mixFlowRate=0, mixCycles=0)


calibration_dict = {}
def measure_qpm_asp():
    global calibration_dict
    # volumes = [5, 10, 25, 50, 75, 125, 200, 300]
    volumes = [5, 10, 25]

    for volume in volumes:
        dr(container = jar['0'], volume = volume, lld = 1,
           liquidClassTableIndex = 1, tip_type = '300ul',liquidSurface=manual_vial_surface, n_retries=3)
        time.sleep(8)
        # plot_pressure_curve()
        data = get_pressure_curve()
        calibration_dict[str(volume) + 'ul'] = data
        with open('calibration_data/qpm_asp_second.json', 'w', encoding='utf-8') as json_file:
            json.dump(calibration_dict, json_file, ensure_ascii=False, indent=4)

        ds(container = jar['0'], volume = volume,  liquidClassTableIndex = 1, liquidSurface=manual_vial_surface,
                    liquid_surface_margin=50, deckGeometryTableIndex=1)
        time.sleep(8)
    return calibration_dict

abc = measure_qpm_asp()

def devide_index():
    index = list(range(4361, 5000))
    while len(index):
        yield index[:50]
        index = index[50:]

def get_pressure_curve():
    data = []
    chunk_list = list(devide_index())
    for i in range(len(chunk_list)):
        string = str(chunk_list[i][0])
        zm.sendCommand('QIid0001li'+string+'ln50')
        string_temp = zm.r.received_msg
        time.sleep(0.5)
        zm.sendCommand('QIid0001li' + string + 'ln50')
        string = zm.r.received_msg
        data_str = string[10:].split()
        data_here = [int(i) for i in data_str]
        data.append(data_here)
        data_flatten = [item for sublist in data for item in sublist ]
        time.sleep(0.5)
    return data_flatten

# data = get_pressure_curve()

def plot_pressure_curve(aa):
    # data = get_pressure_curve()
    for key, value in aa.items():
        xx= list(range(len(value)))
        plt.plot(xx, value, 'o-', color='firebrick', label='No mask')
    plt.show()

plot_pressure_curve(aa = calibration_dict)

# plot_pressure_curve()

# jar0 = jar['0']['xy']

# plt.show()

# container_having_substance = {'Isocyano':bottle6,
#                               'amine':bottle5,
#                               'aldehyde':bottle2,
#                               'pTSA':bottle3,
#                               'DMF': jar1}
#
# excel_filename = 'composition_input_20230110RF029.xlsx'
# df = pd.read_excel(excel_filename ,
#                    sheet_name='Sheet1', usecols='I,J,K,L,M')
#
# xy1 = plate1['wells'][0]['xy'] # coord of the first 2ml vial

# addition_sequence = ['DMF', 'aldehyde', 'pTSA', 'amine', 'Isocyano']
# # addition_sequence = ['pTSA', 'amine', 'Isocyano']
# for substance in addition_sequence:
#     if not (substance == addition_sequence[0]):
#         change_tip(tip_rack)
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

# dispense_to_balance_and_weight(source_container = bottle['6'], volume = 200, lld = 0, liquid_class_index = 21, timedelay=3)
