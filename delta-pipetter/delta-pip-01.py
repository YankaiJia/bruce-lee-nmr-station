# -*- coding: utf-8 -*-
"""
Script for operating an ad-hoc pipetter robot
based on Kossel Anycubic delta-robot 3D printer and
Gilson Microman positive displacement pipette attached
to Thorlabs MTS50/M linear translation stage.

Author: Yaroslav I. Sobolev
Date: 26 Oct 2022
"""
import configparser
import time
# from datetime import datetime
import numpy as np
import thorlabs_apt as apt
# import os
# import matplotlib
# #matplotlib.use('TkAgg')
# import matplotlib.pyplot as plt
import serial
#plt.ion()


# horiz_speed = 50000*60
horiz_speed = 200*60
vert_speed = 200*60

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
    send_to_printer(ser, 'G1 F{0:.0f} Z{1:.1f}'.format(vert_speed, z))

def move_to_coords(x, y):
    send_to_printer(ser, 'G0 F{0:.0f} X{1:.3f} Y{2:.3f}'.format(horiz_speed, x, y))
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
while time.time()-t0 < 8:
    line = ser.readline()
    print(line)

print('Printer initiated.')
#
#config = configparser.RawConfigParser()
#config.read('scanner_params.cfg')

#start_pos_z = config.getfloat('Starting_position', 'start_pos_z')

# Initialize Thorlabs stage moving the pipette piston
apt.list_available_devices()
z_stage = apt.Motor(83855315)

# making z-stage faster
z_stage.acceleration = 5
time.sleep(3)
z_stage.backlash = 0
time.sleep(3)

# Pipetter parameters:
pipette_top_z = 39
pipette_bottom_z = 10
pipette_top_v = 100

# world parameters
ceiling_z = 95
floor_z = 25

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
    target_z = pipette_bottom_z + volume/pipette_top_v * pipette_top_z
    z_stage.move_to(target_z, blocking=True)

# pipette_move_z(pipette_top_z)

def wasd_control(pos):
    move_z(pos[2])
    move_to_coords(pos[0], pos[1])
    k = 'n'
    amplitude=1
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
        move_to_coords(pos[0], pos[1])
    print('Finished wasd')

bottle6 = {'volume': 20000,
           'xy'   : (-51, -6),
           'volume_max':20000,
           'area' :510.7, # container's horizontal cross-section area is in square mm
           'min_z':5} # location of container's # bottom above the floor

well1 = {'volume': 1500,
           'xy'   : (-37, -52),
           'volume_max':1500,
           'area' :75.56, # container's horizontal cross-section area is in square mm
           'min_z':1.2} # location of container's # bottom above the floor

plate1 = {'wells':[well1]}


def draw_liquid(container, volume, dip_to_depth=5):
    pipette_move(0)
    move_z(ceiling_z)
    move_to_coords(container['xy'][0], container['xy'][1])
    level_of_liquid_in_container_after_drawing = (container['volume'] - volume)/container['area']
    if level_of_liquid_in_container_after_drawing - dip_to_depth < 0:
        target_z = floor_z + container['min_z']
    else:
        target_z = floor_z + container['min_z'] + level_of_liquid_in_container_after_drawing - dip_to_depth
    move_z(target_z)
    pipette_move(volume)
    move_z(ceiling_z)


def transfer_liquid(source, destination, volume):
    '''NOT INVENTED HERE'''
    print(1)

draw_liquid(bottle6, volume=50)

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













## making z-stage faster
#z_stage.acceleration = 5
#time.sleep(3)
#z_stage.backlash = 0
#time.sleep(3)
#y_stage.acceleration = 5
#time.sleep(3)
#
#print('Homing complete. Press ENTER to go to starting position.\n')
#
#time_of_delamination = datetime.now()# "{:%d-%m-%Y_%H-%M}__".format()
#
#a = input('Do you want to skip the manual alignment and use last coordinates instead? (y/n):')
#
#this_is_first_alignment_run = True
#topright_x = start_pos_x + scan_range/12
#topright_y = start_pos_y + scan_range/12*11
#topleft_x = start_pos_x + scan_range*11/12
#topleft_y = start_pos_y + scan_range*11/12
#bottomright_x = start_pos_x + scan_range/12
#bottomright_y = start_pos_y + scan_range/12
#bottomleft_x = start_pos_x + scan_range*11/12
#bottomleft_y = start_pos_y + scan_range/12
#
#while a != 'y':
#    # =================== MANUAL ALIGNMENT PROCEDURE ============
#    def keys_stuff(start_pos_x, start_pos_y, start_pos_z):
#        inkey = _Getch()
#        k = inkey()
#        br = 0
#        if k == b'a':
#            start_pos_y += 0.1
#        elif k == b'd':
#            start_pos_y -= 0.1
#        elif k == b's':
#            start_pos_x += 0.1
#        elif k == b'w':
#            start_pos_x -= 0.1
#        elif k == b'f':
#            start_pos_z += 0.05
#        elif k == b'r':
#            start_pos_z -= 0.05
#        elif k == b't':
#            start_pos_z -= 0.01
#        elif k == b'g':
#            start_pos_z += 0.01
#        elif k == b'\r':
#            br = 1
#        elif k == b'\x08':
#            br = 2
#        print('New position at this point is: X={0:0.4f}, Y={1:0.4f}, Z={2:0.4f}'.format(start_pos_x,
#            start_pos_y,
#            start_pos_z))
#        return br, start_pos_x, start_pos_y, start_pos_z
#    
#    print('This is a procedure for manual horizontal alignment of the stamp and for selecting the scan window.')
#    
#    print('Corner #1. Use WASD for XY-plane positioning, R and F for Z-axis, T and G for small Z-axis steps.'
#          'Press ENTER to go to bottom left corner.\n')
#    # Top right corner
##    print('Do the same. Press ENTER to go to another corner.\n')
#    z_stage.move_to(start_pos_z - z_elevation_during_alignment)
#    while(z_stage.is_in_motion):
#        continue
#    move_to(topright_x,
#                topright_y,
#                start_pos_z - z_elevation_during_alignment)
#    while(y_stage.is_in_motion or x_stage.is_in_motion or z_stage.is_in_motion):
#        continue
#    z_stage.move_to(start_pos_z)
#    while(z_stage.is_in_motion):
#        continue
#    while (True):
#        move_to(topright_x,
#                topright_y,
#                start_pos_z)
#        br, topright_x, topright_y, start_pos_z = keys_stuff(topright_x, topright_y, start_pos_z)
#        if br:
#            break
#    start_pos_x = topright_x - scan_range/12
#    start_pos_y = topright_y - scan_range*11/12
#    
#    # Search for starting position, topleft corner
#    print('Corner #2. Do the same. Press ENTER to go to top right corner.\n')
#    z_stage.move_to(start_pos_z - z_elevation_during_alignment)
#    while(z_stage.is_in_motion):
#        continue
#    move_to(topleft_x,
#                topleft_y,
#                start_pos_z - z_elevation_during_alignment)
#    while(y_stage.is_in_motion or x_stage.is_in_motion or z_stage.is_in_motion):
#        continue
#    move_to(topleft_x,
#                topleft_y,
#                start_pos_z)
#    while(y_stage.is_in_motion or x_stage.is_in_motion or z_stage.is_in_motion):
#        continue
#    while (True):
#        move_to(topleft_x,
#                topleft_y,
#                start_pos_z)
#        br, topleft_x, topleft_y, start_pos_z = keys_stuff(topleft_x, topleft_y, start_pos_z)
#        if br:
#            break
#    start_pos_x = (topleft_x + topright_x)/2 - scan_range/2
#    start_pos_y = (topleft_y + topright_y)/2 - scan_range*11/12
#
#    # bottom_right corner
#    print('Corner #3. Do the same. Press ENTER to go to bottom right corner.\n')
#    z_stage.move_to(start_pos_z - z_elevation_during_alignment)
#    while(z_stage.is_in_motion):
#        continue
#    move_to(bottomright_x,
#                bottomright_y,
#                start_pos_z - z_elevation_during_alignment)
#    while(y_stage.is_in_motion or x_stage.is_in_motion or z_stage.is_in_motion):
#        continue
#    z_stage.move_to(start_pos_z)
#    while(z_stage.is_in_motion):
#        continue
#    while (True):
#        move_to(bottomright_x,
#                bottomright_y,
#                start_pos_z)
#        br, bottomright_x, bottomright_y, start_pos_z = keys_stuff(bottomright_x, bottomright_y, start_pos_z)
#        if br:
#            break
#    start_pos_x = (topleft_x + (topright_x + bottomright_x)/2)/2 - scan_range/2
#    start_pos_y = ((topleft_y + topright_y)/2 + bottomright_y)/2 - scan_range/2
#    # bottom_left corner
#    print('Corner #4. Press ENTER when this corner is fine.\n')
#    z_stage.move_to(start_pos_z - z_elevation_during_alignment)
#    while(z_stage.is_in_motion):
#        continue
#    move_to(bottomleft_x,
#                bottomleft_y,
#                start_pos_z - z_elevation_during_alignment)
#    while(y_stage.is_in_motion or x_stage.is_in_motion or z_stage.is_in_motion):
#        continue
#    z_stage.move_to(start_pos_z)
#    while(z_stage.is_in_motion):
#        continue
#    while (True):
#        move_to(bottomleft_x,
#                bottomleft_y,
#                start_pos_z)
#        br, bottomleft_x, bottomleft_y, start_pos_z = keys_stuff(bottomleft_x, bottomleft_y, start_pos_z)
#        if br:
#            break
#    start_pos_x = (topleft_x + topright_x + bottomright_x + bottomleft_x)/4 - scan_range/2
#    start_pos_y = (topleft_y + topright_y + bottomright_y + bottomleft_y)/4 - scan_range/2
#    
#    config.set('Starting_position', 'start_pos_x', '{0}'.format(start_pos_x))
#    config.set('Starting_position', 'start_pos_y', '{0}'.format(start_pos_y))
#    config.set('Starting_position', 'start_pos_z', '{0}'.format(start_pos_z))
#    
#    with open('scanner_params.cfg', 'w+') as configfile:
#        config.write(configfile)
#    
#    this_is_first_alignment_run = False
#    a = input('Did you finish the alignment? (y/n):')
#
#
## Ask if this is triangle or the rectangle
#
#a = input('Is this a triangle or rectangle? (If it is a triangle, I will ignore the point #4) [3/4]:')
#if a == '4':
#    start_pos_x = (topleft_x + topright_x + bottomright_x + bottomleft_x)/4 - scan_range/2
#    start_pos_y = (topleft_y + topright_y + bottomright_y + bottomleft_y)/4 - scan_range/2
#else:
#    start_pos_x = (topleft_x + 2*topright_x + bottomleft_x)/4 - scan_range/2
#    start_pos_y = (topleft_y + topright_y + 2*bottomleft_y)/4 - scan_range/2
#
#config.set('Starting_position', 'start_pos_x', '{0}'.format(start_pos_x))
#config.set('Starting_position', 'start_pos_y', '{0}'.format(start_pos_y))
#config.set('Starting_position', 'start_pos_z', '{0}'.format(start_pos_z))
#
#with open('scanner_params.cfg', 'w+') as configfile:
#    config.write(configfile)
#
### going over four corners and aligning
##print('Sweeping 100% of ranges. Use WASD for XY-plane positioning, '
##          'R and F for Z-axis. Press ENTER to go to raise the stage.')
##while (True):
###    time.sleep(1)
##    move_to(start_pos_x + 1*scan_range,
##            start_pos_y + 0*scan_range,
##            start_pos_z)
###    time.sleep(1)
##    move_to(start_pos_x + 1*scan_range,
##            start_pos_y + 1*scan_range,
##            start_pos_z)
###    time.sleep(1)
##    move_to(start_pos_x + 0*scan_range,
##            start_pos_y + 1*scan_range,
##            start_pos_z)
###    time.sleep(1)
##    move_to(start_pos_x + 0*scan_range,
##            start_pos_y + 0*scan_range,
##            start_pos_z)
##    br, start_pos_x, start_pos_y, start_pos_z = keys_stuff(start_pos_x, start_pos_y, start_pos_z)
##    if br:
##        break
#    
## Raise the stage for whatever reason
##z_stage.move_to(5)
##while(z_stage.is_in_motion):
##    continue
##a = input('Press ENTER to go to start position and begin square-sweeping 100% of ranges.')
#
#print('Moving to starting position...')
#z_stage.move_to(start_pos_z - z_elevation_during_alignment)
#while(z_stage.is_in_motion):
#    continue
#move_to(start_pos_x,
#        start_pos_y,
#        start_pos_z - z_elevation_during_alignment)
#while(y_stage.is_in_motion or x_stage.is_in_motion or z_stage.is_in_motion):
#    continue
#z_stage.move_to(start_pos_z)
#while(z_stage.is_in_motion):
#    continue
#
#number_of_scans = int(input('How many consecutive full scans should I make?:\n'))
##
#data_for_plot = np.zeros((num_steps, num_steps))
#fig,ax = plt.subplots(1,1)
#image = ax.imshow(data_for_plot, cmap='bwr', interpolation='nearest', animated=True)
#plt.colorbar(image)
#fig.canvas.draw()
#plt.show()
#
## text file for the entire scan sequence
#scan_times_text_file = open(directory + '/' + save_to_filename +'_scantimes.txt', 'w+')
#scan_times_text_file.write('This file is for marking the times of each scan in sequence {0}\n'.format(
#        exp_name))
#scan_times_text_file.write('''PARAMETERS:\n
#                Starting position X: {0} mm\n
#                Starting position Y: {1} mm\n
#                Starting position Z: {2} mm\n
#                Delta Z: {3} mm\n
#                Time to wait at each point: {4} sec\n
#                Scan range: {5} mm\n
#                Scanning step: {6} mm\n
#                Time of delamination by wall clock: {7:%d-%m-%Y_%H-%M}\n\n'''.format(start_pos_x, start_pos_y, 
#                start_pos_z, delta_z, time_to_wait_at_position, scan_range, scan_step,
#                time_of_delamination))
#scan_times_text_file.write('ScanID\tScanStartTime\n')
## beginning of the actual scanning
#for scan_id in range(number_of_scans):
## =================== Beginning to scan ==============
#    scan_times_text_file.write('{0}\t{1:%d-%m-%Y_%H-%M}\n'.format(scan_id, datetime.now()))
#    scan_times_text_file.flush()
#    os.fsync(scan_times_text_file)
#    print('Moving to starting position...')
#    
#    move_to(start_pos_x,
#            start_pos_y,
#            start_pos_z)
#    while(y_stage.is_in_motion or x_stage.is_in_motion or z_stage.is_in_motion):
#        continue
#    print("Beginning to scan...")
#    
#    #for i in range(30):
#    #    z_stage.move_to(15.1)
#    #    while(z_stage.is_in_motion):
#    #        time.sleep(0.1)
#    #    z_stage.move_to(15.0)
#    #    while(z_stage.is_in_motion):
#    #        time.sleep(0.1)
#    
#    # make header in the text file
#    #            main header  
#
#    xyz_top_file = create_xyz_file_and_make_header(
#            directory + '/' + save_to_filename +'_scan{0}'.format(scan_id) + '__top_layer.xyz')
#    xyz_bottom_file = create_xyz_file_and_make_header(
#            directory + '/' + save_to_filename +'_scan{0}'.format(scan_id) + '__bottom_layer.xyz')
#    xyz_diff_file = create_xyz_file_and_make_header(
#            directory + '/' + save_to_filename +'_scan{0}'.format(scan_id) + '__diff.xyz')
#    
#    text_file = open(directory + '/' + save_to_filename +'_scan{0}'.format(scan_id) + '.txt', 'w+')
#    text_file.write('Greetings! This is a humble account of an experiment {0}\n'.format(
#            exp_name))
#    text_file.write('This is consecutive scan number {0}.\n'.format(scan_id))
#    text_file.write('''PARAMETERS:\n
#                    Starting position X: {0} mm\n
#                    Starting position Y: {1} mm\n
#                    Starting position Z: {2} mm\n
#                    Delta Z: {3} mm\n
#                    Time to wait at each point: {4} sec\n
#                    Scan range: {5} mm\n
#                    Scanning step: {6} mm\n
#                    Time of delamination by wall clock: {7:%d-%m-%Y_%H-%M}\n
#                    Beginning of this scan by wall clock: {8:%d-%m-%Y_%H-%M}\n\n'''.format(start_pos_x, start_pos_y, 
#                    start_pos_z, delta_z, time_to_wait_at_position, scan_range, scan_step,
#                    time_of_delamination, datetime.now()))
#    #            columns names
#    text_file.write("X,mm\tY,mm\tTop_charge,nC\tBottom_charge,nC\tCharge_diff,nC\tTime\tDate\tReadingID\r\n")
#    
#    start_time = time.time()
#    top_line = np.zeros(shape=(num_steps))
#    bottom_line = np.zeros(shape=(num_steps))
#    x_stage.move_to(start_pos_x)
#    z_stage.move_to(start_pos_z - delta_z)
#    for i,y in enumerate(np.linspace(start_pos_y, start_pos_y + scan_range, num_steps)):
#        if i>0:
#            time_spent_on_one_line = (time.time() - start_time)/i
#            print('I\'m scanning line {0}. There are {1} more lines, and I\'ll finish in about {2:.01f} minutes'.format(
#                    i, 
#                    num_steps - i,
#                    (num_steps - i)*time_spent_on_one_line/60))
#        else:
#            print('I\'m scanning line {0}. There are {1} more lines.'.format(i, num_steps - i))
#        y_stage.move_to(y)
#        time.sleep(1)
#        while(y_stage.is_in_motion or x_stage.is_in_motion or z_stage.is_in_motion):
#            continue
#        # Get values at top line
#        for j,x in enumerate(np.linspace(start_pos_x, start_pos_x + scan_range, num_steps)):
#            x_stage.move_to(x)
#            value_at_top_plane, date_time = get_coulombs_from_keithley(
#                                get_volts_instead = use_volts_instead_of_coulombs)
#            top_line[j] = value_at_top_plane
#        x_stage.move_to(start_pos_x)
#        z_stage.move_to(start_pos_z)
#        while(z_stage.is_in_motion):
#            time.sleep(0.01)
#        for j,x in enumerate(np.linspace(start_pos_x, start_pos_x + scan_range, num_steps)):  
#            x_stage.move_to(x)
#            value_at_bottom_plane, date_time = get_coulombs_from_keithley(
#                                get_volts_instead = use_volts_instead_of_coulombs)
#            bottom_line[j] = value_at_bottom_plane
#        x_stage.move_to(start_pos_x)
#        z_stage.move_to(start_pos_z - delta_z)
#        #subtract lines and add to file
#        line_diff = bottom_line - top_line
#        #write line to file and to plotting dataset
#        for j,x in enumerate(np.linspace(start_pos_x, start_pos_x + scan_range, num_steps)): 
#            text_file.write("{0}\t{1}\t{2}\t{3}\t{4}\t{5}".format(
#                    x,
#                    y,
#                    top_line[j],
#                    bottom_line[j],
#                    line_diff[j],
#                    date_time))
#            data_for_plot[i,j] = line_diff[j]
#            xyz_top_file.write("{0:.7e}\t{1:.7e}\t{2:.7e}\n".format(
#                    x,y,top_line[j]))
#            xyz_bottom_file.write("{0:.7e}\t{1:.7e}\t{2:.7e}\n".format(
#                    x,y,bottom_line[j]))
#            xyz_diff_file.write("{0:.7e}\t{1:.7e}\t{2:.7e}\n".format(
#                    x,y,line_diff[j]))
#        text_file.flush()
#        os.fsync(text_file)
#        xyz_top_file.flush()
#        os.fsync(xyz_top_file)
#        xyz_bottom_file.flush()
#        os.fsync(xyz_bottom_file)
#        xyz_diff_file.flush()
#        os.fsync(xyz_diff_file)
#        image.set_data(data_for_plot)
#        image.set_clim(vmin=-1*np.abs(data_for_plot).max())
#        image.set_clim(vmax=np.abs(data_for_plot).max())
#        fig.canvas.draw()
#        plt.draw()
#        plt.pause(0.001)
#        
#    text_file.close()
#    xyz_top_file.close()
#    xyz_bottom_file.close()
#    xyz_diff_file.close()
#    fig.savefig(directory + '/' + save_to_filename +'_scan{0}'.format(scan_id)+'.png', dpi = 600)
#    np.save(directory + '/' + save_to_filename +'_scan{0}'.format(scan_id)+'.npy', data_for_plot)
#    # saving for ImageJ
#    import scipy.misc as immisc
#    data_for_save = (data_for_plot - data_for_plot.min())/(data_for_plot.max()-data_for_plot.min())*255
#    immisc.imsave(directory + '/' + save_to_filename +'_scan{0}'.format(scan_id) +'_raw.png', data_for_save)
#    
#    
#    print('There you go! This scan only took me {0:.01f} minutes, darling!'.format(
#            (time.time() - start_time)/60))
#
#scan_times_text_file.close()
#keithley.close()
#z_stage.move_to(5)
#a = input('Press ENTER to shut me down.')

