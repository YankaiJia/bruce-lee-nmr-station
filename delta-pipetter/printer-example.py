import serial
import time

horiz_speed = 50000*60
vert_speed = 200*60
vert_hop_pos = 5
vert_zero_pos = 1.6
x0 = -30
y0 = -30

def send_to_printer(ser, command, wait_for_ok=True):
    # start_time = datetime.now()
    ser.write(str.encode(command + '\r\n'))
    print(f'SENT: {command}')
    # time.sleep(1)

    if wait_for_ok:
        while True:
            line = ser.readline()
            print(line)
            # time.sleep()

            # if line == b'ok\n':
            if b'ok' in line:
                break

# def lower_the_pen():
#     send_to_printer(ser, f'G1 F{vert_speed:.0f} Z{vert_zero_pos:.1f}')
#
# def raise_the_pen():
#     send_to_printer(ser, f'G1 F{vert_speed:.0f} Z{vert_hop_pos:.1f}')

def move_z(z):
    send_to_printer(ser, f'G1 F{vert_speed:.0f} Z{z:.1f}')

def move_to_coords(x, y):
    send_to_printer(ser, f'G0 F{horiz_speed:.0f} X{x:.3f} Y{y:.3f}')
    # send_to_printer(ser, f'G0 X{x:.3f} Y{y:.3f}')

def home_the_axes():
    send_to_printer(ser, f'G28')
    time.sleep(4)


ser = serial.Serial('COM4', 115200, timeout=2)
def close_the_printer():
    time.sleep(2)
    ser.close()
time.sleep(1)
t0 = time.time()
while time.time()-t0 < 8:
    line = ser.readline()
    print(line)
print('Printer initiated.')

home_the_axes()

move_z(1)

time.sleep(3)

horiz_speed = 50000*60
waitdelay = 0.5
amplitude = 50
for i in range(10):
    move_to_coords(amplitude, -amplitude)
    time.sleep(waitdelay)
    move_to_coords(amplitude, amplitude)
    time.sleep(waitdelay)
    move_to_coords(-amplitude, amplitude)
    time.sleep(waitdelay)
    move_to_coords(-amplitude, -amplitude)
    time.sleep(waitdelay)


close_the_printer()


# python linedraw.py -i images/papin2.png -o output.svg --contour_simplify 2 -nh --hatch_size 16

# export_path = 'images/output.svg'
# resolution = 1024
# draw_hatch = not True
# draw_contours = True
# hatch_size = 16
# contour_simplify = 2
# show_bitmap = False
# no_cv = False


def home_the_printer():
    initiation_commands = '''M140 S27
    M105
    M190 S29
    M104 S26
    M105
    M109 S26
    M82
    G21
    G90
    M82
    M107
    G28
    G29
    G1 Z15.0 F9000
    G92 E0
    G1 F200 E5
    G92 E0
    G1 F9000
    G92 E0
    G92 E0
    G1 F1500 E-6.5
    M107
    G1 F12000 Z5.3
    G0 F2400 X2.324 Y1.154 Z5.3
    G1 F12000 Z0.3
    G1 F1500 E0
    G0 F2400 X0 Y0 Z2'''.split('\n')

    # initial_commands = initiation_commands.split('\n')
    for command in initiation_commands:
        send_to_printer(ser, command) # rapid motion but does not extrude material ender 5 plus is 350 x 350
    time.sleep(2)



# XY movement:
# G0 F2400 X2.25 Y3.417

# Z movement:
# G1 F12000 Z5.3
# G0 F2400 X4.628 Y4.123 Z5.3
# G1 F12000 Z0.3



# home_the_printer()