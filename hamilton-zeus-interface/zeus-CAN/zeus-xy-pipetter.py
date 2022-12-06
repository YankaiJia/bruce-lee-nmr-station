# -*- coding: utf-8 -*-
"""
Script for operating an ad-hoc pipetter robot based on:
1) Hamilton ZEUS automatic pipette with embedded vertical Z axis and
2) Ad-hoc XY stage controlled by Arduino running GRBL firmware.

ZEUS is mounted on the XY stage.

Author: Yaroslav I. Sobolev, Yankai Jia
Date: 6 Dec 2022
"""
# import configparser
import zeus
import time
# from datetime import datetime
import numpy as np
# import os
import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
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
                 bottomPosition=2291, immersionDepth=50, leavingHeight=130, jetHeight=130,
                 startOfHeightBottomSearch=50, dispenseHeightAfterBottomSearch=50,
                 )
zm.setContainerGeometryParameters(containerGeometryParameters=container_20mL_bottle)
print('20 ml bottle container loaded')

container_bottle_large = zeus.ContainerGeometry(index=2, diameter=520, bottomHeight=0, bottomSection=10000,
                 bottomPosition=2217, immersionDepth=50, leavingHeight=130, jetHeight=130,
                 startOfHeightBottomSearch=50, dispenseHeightAfterBottomSearch=50,
                 )
zm.setContainerGeometryParameters(containerGeometryParameters=container_bottle_large)
print('Large bottle container loaded')

#
def move_z(z):
    zm.moveZDrive(z, 'fast')


# horiz_speed = 50000*60
horiz_speed = 200 * 60
# vert_speed = 200 * 60
# floor_z = 26
# offsets in x and y
xy_offset = (0, 0)
trash_xy = (157, -205)

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


# def move_z(z):
#     send_to_xy_stage(ser, 'G1 F{0:.0f} Z{1:.1f}'.format(vert_speed, z + floor_z))

def xy_pos():
    send_to_xy_stage(ser, '?', read_all=True, verbose=True)


# def move_xy(x, y):
def move_xy(xy, verbose=False, ensure_traverse_height=True):
    if ensure_traverse_height:
        if zm.pos > ZeusTraversePosition:
            print(f'ERROR: ZEUS was not in traverse height before motion, but instead at {zm.pos}')
            return
    # if np.linalg.norm(np.array((x, y))) <= R:
    send_to_xy_stage(ser, 'G0 X{0:.3f} Y{1:.3f}'.format(xy[0] + xy_offset[0], xy[1] + xy_offset[1]),
                     read_all=False)
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
    if verbose:
        print('Finished moving')
    # else:
    #     print('MOTION ABORTED: target XY point outside of the allowed circle with R = {0}'.format(R))
    #     raise Exception
    # # send_to_xy_stage(ser, f'G0 X{x:.3f} Y{y:.3f}')


def home_the_xy_stage():
    send_to_xy_stage(ser, '$H', read_all=True, verbose=True)
    xy_pos()


def close_the_xy_stage():
    time.sleep(2)
    ser.close()
#
# #
# # config = configparser.RawConfigParser()
# # config.read('scanner_params.cfg')
#
# # start_pos_z = config.getfloat('Starting_position', 'start_pos_z')
#
#
# # Pipetter parameters:
# pipette_z_offset = 0
# pipette_top_z = 37.8309
# pipette_bottom_z = 8.67
# pipette_top_v = 100
#
# # world parameters
# ceiling_z = 70
#
# home_the_xy_stage()
# # This command tells printer will disengage the motors after 10 hours (36000 seconds) of inactivity.
# # Without this command it will disengage after a minute or so
# send_to_xy_stage(ser, 'M84 S0')
# move_z(ceiling_z)
# time.sleep(2)
# pos = np.array((0, 0, ceiling_z))
#
#
# def pipette_move_z(z):
#     z_stage.move_to(z)
#
#
# def pipette_move(volume):
#     target_z = pipette_bottom_z + volume / pipette_top_v * (pipette_top_z - pipette_bottom_z) + pipette_z_offset
#     z_stage.move_to(target_z, blocking=True)
#
#
# # pipette_move_z(pipette_top_z)
#
# def wasd_control(pos):
#     move_z(pos[2])
#     move_xy(pos[0], pos[1])
#     k = 'n'
#     amplitude = 1
#     while k != 'q':
#         k = input('wasd control:')
#         if k == 'd':
#             pos += np.array((amplitude, 0, 0))
#         if k == 'a':
#             pos += np.array((-amplitude, 0, 0))
#         if k == 'w':
#             pos += np.array((0, amplitude, 0))
#         if k == 's':
#             pos += np.array((0, -amplitude, 0))
#         if k == 'r':
#             pos += np.array((0, 0, amplitude))
#         if k == 'f':
#             pos += np.array((0, 0, -amplitude))
#         if k == 'u':
#             amplitude += 1
#             print('Amplitude = {0}'.format(amplitude))
#         if k == 'j':
#             amplitude -= 1
#             print('Amplitude = {0}'.format(amplitude))
#         print('pos = {0}'.format(pos))
#         move_z(pos[2])
#         move_xy(pos[0], pos[1])
#     print('Finished wasd')
#     return pos
#

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
         'containerGeometryTableIndex': 0
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
               'containerGeometryTableIndex': 1
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
bottle6['xy'] = (464.5, -221)

bottle_large = {'volume': 80000,
                'xy': (338, -282),
                'volume_max': 100000,
                'area': 2123.7,  # container's horizontal cross-section area is in square mm
                'min_z': 5,  # location of container's # bottom above the floor in mm
                'top_z': 70,  # height of container in mm
                'neck_r': 3,  # inner radius of the neck in mm
                'containerGeometryTableIndex': 2
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
    # In the rack, find the first tip that exists
    for tip in tips_rack['wells']:
        if tip['exists']:
            # pick up tip
            move_xy(tip['xy'])
            zm.pickUpTip(tipTypeTableIndex=tip['tipTypeTableIndex'], deckGeometryTableIndex=0)
            tip['exists'] = False
            return True
    print('ERROR: No tips in rack.')
    raise Exception

def discard_tip():
    move_z(ZeusTraversePosition)
    move_xy(trash_xy)
    zm.discardTip(deckGeometryTableIndex=0)

def change_tip(tips_rack):
    discard_tip()
    pick_tip(tips_rack)


# generate coordinates for all wells of a well plate from coordinates of corner wells.
plate = create_well_plate(template_well=well1,
                          Nwells=(6, 9),
                          topleft=(555.5, -277.5),
                          topright=(443.5, -277.5),
                          # bottomleft = (9, -76)
                          bottomleft=(555.5, -347),
                          bottomright=(443.5, -347))
#
# wells = generate_well_coordinates(Nwells=(6, 9),
#                                   topleft=(-37, -52),
#                                   topright=(8, 43),
#                                   # bottomleft = (9, -76)
#                                   bottomleft=(20.5, -82),
#                                   bottomright=(65.5, 15))
#

def move_through_wells(plate, dwell_time=1):
    for well in plate['wells']:
        move_xy(well['xy'])
        time.sleep(dwell_time)



#
def draw_liquid(container, volume, dip_to_depth=5):

    container['volume'] -= volume
    move_z(ceiling_z)
#
#
# def dispense_liquid(container, volume='all', height_from_top=0, brush_walls=True, brush_mag=0.3,
#                     brush_delay=0.5):
#     move_z(ceiling_z)
#     move_xy(container['xy'][0], container['xy'][1])
#     move_z(container['top_z'] + height_from_top)
#     time.sleep(1)
#
#     assert volume == 'all'
#     pipette_move(0)
#     # partial dispensing not implemented yet
#
#     if brush_walls:
#         brushing_distance = container['neck_r'] - pipette_tip_radius + brush_mag
#         move_xy(container['xy'][0] - brushing_distance, container['xy'][1])
#         time.sleep(brush_delay)
#         move_xy(container['xy'][0] + brushing_distance, container['xy'][1])
#         time.sleep(brush_delay)
#         move_xy(container['xy'][0], container['xy'][1])
#         move_xy(container['xy'][0], container['xy'][1] - brushing_distance)
#         time.sleep(brush_delay)
#         move_xy(container['xy'][0], container['xy'][1] + brushing_distance)
#         time.sleep(brush_delay)
#         # move_xy(container['xy'][0], container['xy'][1])
#
#     # maybe also make a fast down-up move to throw the hanging droplet down
#     move_z(ceiling_z)
#
#
# def transfer_liquid(source, destination, volume, dip_into_source_to_depth=10,
#                     dispense_from_height=-1, max_volume=1000):
#     # if it exceeds max_volume, then do several pipettings
#     N_max_vol_pipettings = int(volume // max_volume)
#     for i in range(N_max_vol_pipettings):
#         draw_liquid(source, max_volume, dip_to_depth=dip_into_source_to_depth)
#         dispense_liquid(destination, volume='all', height_from_top=dispense_from_height)
#     volume_of_last_pipetting = volume % max_volume
#     draw_liquid(source, volume_of_last_pipetting, dip_to_depth=dip_into_source_to_depth)
#     dispense_liquid(destination, volume='all', height_from_top=dispense_from_height)
#
# # N = 50
# # volumes = np.linspace(10, 100, N)
# # for i in range(N):
# #     transfer_liquid(source=bottle6, destination=plate['wells'][i], volume=volumes[i])
#
# container_having_substance = {'Isocyano':bottle6,
#                               'amine':bottle6,
#                               'aldehyde':bottle6,
#                               'pTSA':bottle6,
#                               'DMF': bottle_large}
#
# df = pd.read_excel('delta-pipetter/runs/2022-11-26-run01/input_compositions/compositions.xlsx',
#                    sheetname='Sheet1', parse_cols='I,J,K,L,M')
#
# # df_one_plate = df.head(53)  # plate #1
# df_one_plate = df.iloc[53:] # plate #2
#
# substance = 'DMF'
# # substance = 'aldehyde'
# # substance = 'pTSA'
# # substance = 'amine'
# # substance = 'Isocyano'
# #
# t0 = time.time()
# for well_id, volume in enumerate(df_one_plate[substance]):
#     print('Substance {0}, well {1}, volume {2}'.format(substance, well_id, volume))
#     transfer_liquid(container_having_substance[substance],
#                     plate['wells'][well_id],
#                     volume)
# print('Time_elapsed: {0:.1f} min'.format((time.time() - t0)/60))

