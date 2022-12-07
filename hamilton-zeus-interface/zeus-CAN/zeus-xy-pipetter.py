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

matplotlib.use('TkAgg')
import serial

# plt.ion()

ZeusTraversePosition = 650
floor_z = 2317
manual_vial_surface = 2152

# # ZEUS
zm = zeus.ZeusModule(id=1)
time.sleep(3)

deckgeom = zeus.DeckGeometry(index=0, endTraversePosition=ZeusTraversePosition,
                             beginningofTipPickingPosition=1230,
                             positionofTipDepositProcess=1250)
zm.setDeckGeometryParameters(deckGeometryParameters=deckgeom)
print('Zeus deck geometry loaded')

# Container loading
# TODO: In the object-oriented version this will be depend on target container dictionaries passed by
#  the module's user
container_2mL_vial = zeus.ContainerGeometry(index=0, diameter=98, bottomHeight=0, bottomSection=10000,
                 bottomPosition=2292, immersionDepth=50, leavingHeight=130, jetHeight=130,
                 startOfHeightBottomSearch=50, dispenseHeightAfterBottomSearch=50,
                 )
zm.setContainerGeometryParameters(containerGeometryParameters=container_2mL_vial)
print('2ml vial container loaded')

container_20mL_bottle = zeus.ContainerGeometry(index=1, diameter=255, bottomHeight=0, bottomSection=10000,
                 bottomPosition=2285, immersionDepth=20, leavingHeight=50, jetHeight=130,
                 startOfHeightBottomSearch=20, dispenseHeightAfterBottomSearch=50,
                 )
zm.setContainerGeometryParameters(containerGeometryParameters=container_20mL_bottle)
print('20 ml bottle container loaded')

container_bottle_large = zeus.ContainerGeometry(index=2, diameter=520, bottomHeight=0, bottomSection=10000,
                 bottomPosition=2217, immersionDepth=50, leavingHeight=130, jetHeight=130,
                 startOfHeightBottomSearch=50, dispenseHeightAfterBottomSearch=50,
                 )
zm.setContainerGeometryParameters(containerGeometryParameters=container_bottle_large)
print('Large bottle container loaded')


def wait_until_zeus_reaches_traverse_height(n_retries=70):
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
        if position <= ZeusTraversePosition:
            print('Traverse height is reached.')
            return True
    print(f'Traverse height was not reached after {n_retries} retries. This is dangerous, so we do emergency stop')
    raise Exception
    return False


def move_z(z):
    zm.moveZDrive(z, 'fast')


move_z(650)

horiz_speed = 200 * 60 # horizontal speed in mm / min
xy_offset = (-0.3, 7) # offsets in x and y that are automatically added to each move_xy()
trash_xy = (157, -207) # can for discarding the pipette tips into
xy_position = (500, -100)

ser = serial.Serial('COM6', 115200, timeout=0.2)
time.sleep(1)
t0 = time.time()
while time.time() - t0 < 8:
    line = ser.readline()
    print(line)

def send_to_xy_stage(ser, command, wait_for_ok=True, verbose=False, read_all=False):
    # start_time = datetime.now()
    ser.write(str.encode(command + '\r\n'))
    # ser.write(str.encode(command))
    if verbose:
        print('SENT: {0}'.format(command))
    # time.sleep(1)

    if wait_for_ok:
        while True:
            line = ser.readline()
            if verbose:
                print(line)
            if b'ok' in line:
                break

    if read_all:
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
            use_time_estimates=True):
    global xy_position
    if ensure_traverse_height:
        if zm.pos > ZeusTraversePosition:
            print(f'ERROR: ZEUS was not in traverse height before motion, but instead at {zm.pos}')
            return
    # if np.linalg.norm(np.array((x, y))) <= R:
    send_to_xy_stage(ser, 'G0 X{0:.3f} Y{1:.3f}'.format(xy[0] + xy_offset[0], xy[1] + xy_offset[1]),
                     read_all=False)
    if block_until_motion_is_completed:
        if use_time_estimates:
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


def home_xy():
    send_to_xy_stage(ser, '$H', read_all=True, verbose=True)
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
         'volume_max': 1500,
         'area': 75.56,  # container's horizontal cross-section area is in square mm
         'min_z': 1.2,  # location of container's # bottom above the floor
         'top_z': 32,  # height of container
         'containerGeometryTableIndex': 0,
         'lldSearchPosition': 2020
         }

tip_300ul = {'tip_vol': 300,
             'xy': (300, -100),
             'tipTypeTableIndex': 4,
             'exists': True
             }

bottle_20ml = {'volume': 20000,
               'xy': (-51.0, -6.0),
               'volume_max': 20000,
               'area': 510.7,  # container's horizontal cross-section area is in square mm
               'min_z': 5,  # location of container's # bottom above the floor
               'top_z': 62,  # height of container
               'containerGeometryTableIndex': 1,
               'lldSearchPosition': 1890
               }

bottle1 = bottle_20ml.copy()
bottle2 = bottle_20ml.copy()
bottle3 = bottle_20ml.copy()
bottle4 = bottle_20ml.copy()
bottle5 = bottle_20ml.copy()
bottle6 = bottle_20ml.copy()

bottle1['xy'] = (527.5, -190)
bottle2['xy'] = (496.0, -190)
bottle3['xy'] = (464.5, -190)
bottle4['xy'] = (526.5, -221)
bottle5['xy'] = (496.0, -221)
bottle6['xy'] = (465.0, -221)

bottle_large = {'volume': 80000,
                'xy': (338, -282),
                'volume_max': 100000,
                'area': 2123.7,  # container's horizontal cross-section area is in square mm
                'min_z': 5,  # location of container's # bottom above the floor in mm
                'top_z': 70,  # height of container in mm
                'neck_r': 3,  # inner radius of the neck in mm
                'containerGeometryTableIndex': 2,
                'lldSearchPosition': 1700
               }


# generate plate with tips
# generate coordinates for all wells of a well plate from coordinates of corner wells.
tips_rack = create_well_plate(template_well=tip_300ul,
                          Nwells=(8, 12),
                          topleft=(366.5, -104),
                          topright=(260.5, -104.5),
                          bottomleft=(367, -171.5),
                          bottomright=(261, -171.5))

def pick_tip(tips_rack):
    move_z(ZeusTraversePosition)
    wait_until_zeus_reaches_traverse_height()
    # In the rack, find the first tip that exists
    for tip in tips_rack['wells']:
        if tip['exists']:
            # pick up tip
            move_xy(tip['xy'])
            zm.pickUpTip(tipTypeTableIndex=tip['tipTypeTableIndex'], deckGeometryTableIndex=0)
            tip['exists'] = False
            wait_until_zeus_reaches_traverse_height()
            return True
    print('ERROR: No tips in rack.')
    raise Exception

def discard_tip():
    move_z(ZeusTraversePosition)
    wait_until_zeus_reaches_traverse_height()
    move_xy(trash_xy)
    zm.discardTip(deckGeometryTableIndex=0)
    wait_until_zeus_reaches_traverse_height()

def change_tip(tips_rack):
    discard_tip()
    pick_tip(tips_rack)


# generate coordinates for all wells of a well plate from coordinates of corner wells.
plate = create_well_plate(template_well=well1,
                          Nwells=(6, 9),
                          topleft=(556, -275.5),
                          topright=(444, -275.5),
                          bottomleft=(556, -345),
                          bottomright=(444, -345))


def move_through_wells(plate, dwell_time=1):
    for well in plate['wells']:
        move_xy(well['xy'])
        time.sleep(dwell_time)



#
def draw_liquid(container, volume, liquidClassTableIndex=1, liquidSurface=manual_vial_surface):
    container['volume'] -= volume
    if zm.pos > ZeusTraversePosition:
        move_z(ZeusTraversePosition)
        wait_until_zeus_reaches_traverse_height()
    move_xy(container['xy'])
    zm.aspiration(aspirationVolume=int(round(volume*10)),
                  containerGeometryTableIndex=container['containerGeometryTableIndex'],
                  deckGeometryTableIndex=0, liquidClassTableIndex=liquidClassTableIndex,
                  qpm=1, lld=1, lldSearchPosition=container['lldSearchPosition'],
                  liquidSurface=liquidSurface,
                  mixVolume=0, mixFlowRate=0, mixCycles=0)
    time.sleep(1.5)
    wait_until_zeus_reaches_traverse_height()

#
#
def dispense_liquid(container, volume, liquidClassTableIndex=1, liquidSurface=manual_vial_surface):
    if zm.pos > ZeusTraversePosition:
        move_z(ZeusTraversePosition)
        wait_until_zeus_reaches_traverse_height()
    move_xy(container['xy'])
    zm.dispensing(dispensingVolume=int(round(volume*10)),
                  containerGeometryTableIndex=container['containerGeometryTableIndex'],
                  deckGeometryTableIndex=0, liquidClassTableIndex=liquidClassTableIndex,
                  lld=0, lldSearchPosition=container['lldSearchPosition'],
                  liquidSurface=liquidSurface,
                  searchBottomMode=0, mixVolume=0, mixFlowRate=0, mixCycles=0)
    time.sleep(1.5)
    wait_until_zeus_reaches_traverse_height()
    container['volume'] += volume


def transfer_liquid(source, destination, volume, max_volume=250):
    # if it exceeds max_volume, then do several pipettings
    N_max_vol_pipettings = int(volume // max_volume)
    for i in range(N_max_vol_pipettings):
        draw_liquid(source, volume=max_volume)
        dispense_liquid(destination, volume=max_volume)
    volume_of_last_pipetting = volume % max_volume
    draw_liquid(source, volume=volume_of_last_pipetting)
    dispense_liquid(destination, volume=volume_of_last_pipetting)

container_having_substance = {'Isocyano':bottle6,
                              'amine':bottle5,
                              'aldehyde':bottle2,
                              'pTSA':bottle3,
                              'DMF': bottle_large}

excel_filename = 'C:\\Users\\Chemiluminescence\\Desktop\\roborea_data\\2022-12-07-run01\\input_compositions\\compositions.xlsx'
df = pd.read_excel(excel_filename,
                   sheet_name='Sheet1', usecols='I,J,K,L,M')

# df_one_plate = df.head(54)  # plate #1
df_one_plate = df.iloc[54:] # plate #2

addition_sequence = ['DMF', 'aldehyde', 'pTSA', 'amine', 'Isocyano']
for substance in addition_sequence:
    change_tip(tips_rack)
    time.sleep(6)
    t0 = time.time()
    for well_id, volume in enumerate(df_one_plate[substance + '.1']):
        print('Substance {0}, well {1}, volume {2}'.format(substance, well_id, volume))
        transfer_liquid(container_having_substance[substance],
                        plate['wells'][well_id],
                        volume)
    print('Time_elapsed: {0:.1f} min'.format((time.time() - t0) / 60))


# # motion tests
# for i in range(10):
#     move_xy((400, -100), block_until_motion_is_completed=True, use_time_estimates=True)
#     move_xy((300, -200), block_until_motion_is_completed=True, use_time_estimates=True)