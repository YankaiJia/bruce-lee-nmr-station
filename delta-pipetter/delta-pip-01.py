# -*- coding: utf-8 -*-
"""
Script for operating an ad-hoc pipetter robot
based on Kossel Anycubic delta-robot 3D printer and
Gilson Microman positive displacement pipette attached
to Thorlabs MTS50/M linear translation stage.

Author: Yaroslav I. Sobolev
Date: 26 Oct 2022
"""
# import configparser
import time
# from datetime import datetime
import numpy as np
import thorlabs_apt as apt
# import os
import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import serial

# plt.ion()

# horiz_speed = 50000*60
horiz_speed = 200 * 60
vert_speed = 200 * 60
floor_z = 26
# offsets in x and y
xy_offset = (1.5, 0.5)


def send_to_printer(ser, command, wait_for_ok=True, verbose=False):
    # start_time = datetime.now()
    ser.write(str.encode(command + '\r\n'))
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


def move_z(z):
    send_to_printer(ser, 'G1 F{0:.0f} Z{1:.1f}'.format(vert_speed, z + floor_z))


def move_xy(x, y, R=85):
    if np.linalg.norm(np.array((x, y))) <= R:
        send_to_printer(ser, 'G0 F{0:.0f} X{1:.3f} Y{2:.3f}'.format(horiz_speed, x + xy_offset[0], y + xy_offset[1]))
    else:
        print('MOTION ABORTED: target XY point outside of the allowed circle with R = {0}'.format(R))
        raise Exception
    # send_to_printer(ser, f'G0 X{x:.3f} Y{y:.3f}')


def home_the_axes():
    send_to_printer(ser, 'G28')
    time.sleep(4)


# Printer initialization
ser = serial.Serial('COM9', 115200, timeout=2)


def close_the_printer():
    time.sleep(2)
    ser.close()


time.sleep(1)
t0 = time.time()
while time.time() - t0 < 8:
    line = ser.readline()
    print(line)

print('Printer initiated.')
#
# config = configparser.RawConfigParser()
# config.read('scanner_params.cfg')

# start_pos_z = config.getfloat('Starting_position', 'start_pos_z')

# Initialize Thorlabs stage moving the pipette piston
apt.list_available_devices()
z_stage = apt.Motor(83855315)

# making z-stage faster
z_stage.acceleration = 5
time.sleep(3)
z_stage.backlash = 0
time.sleep(3)

# Pipetter parameters:
pipette_z_offset = 0
pipette_top_z = 37.8309
pipette_bottom_z = 8.67
pipette_top_v = 100

# world parameters
ceiling_z = 70

home_the_axes()
# This command tells printer will disengage the motors after 10 hours (36000 seconds) of inactivity.
# Without this command it will disengage after a minute or so
send_to_printer(ser, 'M84 S0')
move_z(ceiling_z)
time.sleep(2)
pos = np.array((0, 0, ceiling_z))


def pipette_move_z(z):
    z_stage.move_to(z)


def pipette_move(volume):
    target_z = pipette_bottom_z + volume / pipette_top_v * (pipette_top_z - pipette_bottom_z) + pipette_z_offset
    z_stage.move_to(target_z, blocking=True)


# pipette_move_z(pipette_top_z)

def wasd_control(pos):
    move_z(pos[2])
    move_xy(pos[0], pos[1])
    k = 'n'
    amplitude = 1
    while k != 'q':
        k = input('wasd control:')
        if k == 'd':
            pos += np.array((amplitude, 0, 0))
        if k == 'a':
            pos += np.array((-amplitude, 0, 0))
        if k == 'w':
            pos += np.array((0, amplitude, 0))
        if k == 's':
            pos += np.array((0, -amplitude, 0))
        if k == 'r':
            pos += np.array((0, 0, amplitude))
        if k == 'f':
            pos += np.array((0, 0, -amplitude))
        if k == 'u':
            amplitude += 1
            print('Amplitude = {0}'.format(amplitude))
        if k == 'j':
            amplitude -= 1
            print('Amplitude = {0}'.format(amplitude))
        print('pos = {0}'.format(pos))
        move_z(pos[2])
        move_xy(pos[0], pos[1])
    print('Finished wasd')
    return pos


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


def create_well_plate(template_well, Nwells, topleft, topright, bottomleft, bottomright, delete_well_45=True):
    well_positions = generate_well_coordinates(Nwells, topleft, topright, bottomleft, bottomright)
    if delete_well_45:
        well_positions = np.delete(well_positions, 45, 0)
    plate = {'wells': list()}
    for well_index in range(well_positions.shape[0]):
        plate['wells'].append(template_well.copy())
        plate['wells'][-1]['xy'] = well_positions[well_index, :]
    return plate

bottle6 = {'volume': 20000,
           'xy': (-51, -6),
           'volume_max': 20000,
           'area': 510.7,  # container's horizontal cross-section area is in square mm
           'min_z': 5,  # location of container's # bottom above the floor
           'top_z': 62  # height of container
           }

well1 = {'volume': 0,
         'xy': (-37, -52),
         'volume_max': 1500,
         'area': 75.56,  # container's horizontal cross-section area is in square mm
         'min_z': 1.2,  # location of container's # bottom above the floor
         'top_z': 32  # height of container
         }

# generate coordinates for all wells of a well plate from coordinates of corner wells.
plate = create_well_plate(template_well=well1,
                          Nwells=(6, 9),
                          topleft=(-37, -52),
                          topright=(8, 43),
                          # bottomleft = (9, -76)
                          bottomleft=(20.5, -82),
                          bottomright=(65.5, 15))

wells = generate_well_coordinates(Nwells=(6, 9),
                                  topleft=(-37, -52),
                                  topright=(8, 43),
                                  # bottomleft = (9, -76)
                                  bottomleft=(20.5, -82),
                                  bottomright=(65.5, 15))


def move_through_wells(wells,
                       z_above_well=80 - 26,
                       z_in_well=50 - 26):
    move_z(z_above_well)
    for i, well in enumerate(wells):
        if i == 45:
            continue
        move_xy(well[0], well[1])
        move_z(z_in_well)
        move_z(z_above_well)


def draw_liquid(container, volume, dip_to_depth=5):
    pipette_move(0)
    move_z(ceiling_z)
    move_xy(container['xy'][0], container['xy'][1])
    level_of_liquid_in_container_after_drawing = (container['volume'] - volume) / container['area']
    if level_of_liquid_in_container_after_drawing - dip_to_depth < 0:
        target_z = container['min_z']
    else:
        target_z = container['min_z'] + level_of_liquid_in_container_after_drawing - dip_to_depth
    move_z(target_z)
    pipette_move(volume)
    container['volume'] -= volume
    move_z(ceiling_z)


def dispense_liquid(container, volume='all', height_from_top=0):
    move_z(ceiling_z)
    move_xy(container['xy'][0], container['xy'][1])
    move_z(container['top_z'] + height_from_top)

    assert volume == 'all'
    pipette_move(0)
    # partial dispensing not implemented yet

    # maybe also make a fast down-up move to throw the hanging droplet down
    move_z(ceiling_z)


def transfer_liquid(source, destination, volume, dip_into_source_to_depth=5, dispense_from_height=0):
    draw_liquid(source, volume, dip_to_depth=dip_into_source_to_depth)
    dispense_liquid(destination, volume='all', height_from_top=dispense_from_height)


# # draw from bottle then span 5 wells
# draw_liquid(bottle6, volume=20)
# move_to_coords(-37, -52)
# first_vial_pos = (-37, -52)
# last_vial_pos = (9, -76)
# Nwells = 5
# z_above_well = 65
# z_in_well = 50
# xs = np.linspace(first_vial_pos[0], last_vial_pos[0], Nwells)
# ys = np.linspace(first_vial_pos[1], last_vial_pos[1], Nwells)
# move_z(z_above_well)
# for i in range(Nwells):
#     move_to_coords(xs[i], ys[i])
#     move_z(z_in_well)
#     move_z(z_above_well)

def align_floor(higher_z=45, R=100, N=11, target_file_prefix='floor_alignment/2022-11-04/', do_from_scratch=False):
    '''Go through a grid of points. Use keys to go up and down. The "accept floor" key remembers the z here and
    goes to the next point in the xy grid.
    There must be a point for restoring the xy position. Because near the edge
    of the plate the pipette will not actually reach the position it should. In that case I should go with WASD keys
    to check whether the point is reacheable or not. If it's not reachable, there should be a key that marks this point
    as unreacheable and moves on.'''
    move_z(higher_z)
    if do_from_scratch:
        grid_x = np.linspace(-R, R, N)
        grid_y = np.linspace(-R, R, N)
        xs = []
        ys = []
        for i in range(N):
            for j in range(N):
                x = grid_x[i]
                y = grid_y[j]
                if np.linalg.norm(np.array((x, y))) <= R:
                    xs.append(x)
                    ys.append(y)
        xs = np.array(xs)
        ys = np.array(ys)
        np.save(target_file_prefix + 'xs.npy', xs)
        np.save(target_file_prefix + 'ys.npy', ys)
        # plt.scatter(xs, ys)
        # plt.show()

        zs = np.zeros_like(xs)
        np.save(target_file_prefix + 'zs.npy', zs)
    else:
        xs = np.load(target_file_prefix + 'xs.npy')
        ys = np.load(target_file_prefix + 'ys.npy')
        zs = np.load(target_file_prefix + 'zs.npy')

    for i, x in enumerate(xs):
        if zs[i] != 0:
            continue
        # if i == 7:
        #     zs[i] = -1000
        #     np.save(target_file_prefix + 'zs.npy', zs)
        #     print('Z location accepted for subsequent removal due to z obstacle at this xy')
        #     continue
        y = ys[i]
        move_z(higher_z)
        pos = np.array([x, y, higher_z])
        print('Calibrating at index {0} position {1}'.format(i, pos))
        move_xy(pos[0], pos[1])
        k = 'n'
        amplitude = 1
        while k != 'q' or k == ' ':
            k = input('wasd control:')
            if k == 'd':
                pos += np.array((amplitude, 0, 0))
            if k == 'a':
                pos += np.array((-amplitude, 0, 0))
            if k == 'w':
                pos += np.array((0, amplitude, 0))
            if k == 's':
                pos += np.array((0, -amplitude, 0))
            if k == 'r':
                pos += np.array((0, 0, amplitude))
            if k == 'f':
                pos += np.array((0, 0, -amplitude))
            if k == 'g':
                pos += np.array((0, 0, -16))
            if k == 'u':
                amplitude += 1
                print('Amplitude = {0}'.format(amplitude))
            if k == 'j':
                amplitude -= 1
                print('Amplitude = {0}'.format(amplitude))
            if k == ' ':
                zs[i] = pos[2]
                np.save(target_file_prefix + 'zs.npy', zs)
                print('Z location accepted.')
                break
            if k == ' S':
                zs[i] = -1000
                np.save(target_file_prefix + 'zs.npy', zs)
                print('Z location accepted for subsequent removal due to z obstacle at this xy')
                break
            print('pos = {0}'.format(pos))
            move_z(pos[2])
            move_xy(pos[0], pos[1])
        if k == 'q':
            break
    print('Finished aligning to floor.')

# align_floor(higher_z = 41, R = 85, N = 11, target_file_prefix='floor_alignment/2022-11-04/', do_from_scratch=True)

# x = np.linspace(0, 4, 13)
# y = np.array([0, 2, 3, 3.5, 3.75, 3.875, 3.9375, 4])
# X, Y = np.meshgrid(x, y)
# Z = np.sin(np.pi*X/2) * np.exp(Y/2)
#
# x2 = np.linspace(0, 4, 65)
# y2 = np.linspace(0, 4, 65)
# f = interp2d(x, y, Z, kind='cubic')
# Z2 = f(x2, y2)

# move_to_coords(-34, 0)
# move_z(40)
# pipette_move(20)
# time.sleep(5)
# move_z(65)
# move_to_coords(0, 0)
# move_z(40)
# pipette_move(10)
# time.sleep(5)
# move_z(65)
