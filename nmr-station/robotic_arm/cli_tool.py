"""
CLI app for simpler testing nmr-station objects position and 
corresponding MECA500 moving configurations


King Lam Kwong
"""

import click
from pynput import keyboard

import threading
import time

from meca_movements import (
    change_vertical_height,
    change_radial_distance,
    change_azimuth,
    change_gripper_state,
    invert_gripper,
    zero,
    rotate_one_joint,
    reset_robot
)
from meca import get_robot, connect_robot, config_robot


# @click.command()
@click.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    )
)
@click.argument("function_name")
@click.argument("args", nargs=-1, type=float)
def cli(function_name, args):
    # Get the method from the instance
    func = globals().get(function_name)
    # Check if it's callable (i.e., a method)
    if callable(func):
        func(args)


class KeyReader:
    def __init__(self, mode: str = "safe"):
        self.listener = None
        if mode == "safe":
            self.listener = keyboard.Listener(on_release=self.mark_last_key)
        elif mode == "smooth":
            self.listener = keyboard.Listener(on_press=self.mark_last_key)
        self.listener.start()
        self.last_key = ""

    def mark_last_key(self, key: keyboard.Key):
        try:
            self.last_key = key.char
        except AttributeError:
            self.last_key = str(key).split(".")[-1]

    def listener_off(self):
        self.listener.stop()


# add new functions as testing tool below


def check_health(args):
    print("healthy", args)


def vert_move(args):
    r = get_robot()
    connect_robot(r)
    config_robot(r)

    unit_distance = int(args[0])
    tilted_angle = 0 if len(args) < 2 else int(args[1])
    print(
        f"move vertically by unit distance {unit_distance} mm with joint-6 {tilted_angle}° tilted"
    )

    kr = KeyReader()

    while kr.last_key != "x":
        threading.Event().wait(0.2)

        if kr.last_key in ["up", "down"]:
            change_vertical_height(r, kr.last_key, unit_distance, tilted_angle)
            kr.last_key = ""

    kr.listener_off()

def args_update(factor, args:list):

    """For scaling up or scaling down the joystick steps by a factor."""

    return [round(factor*arg,3) for arg in args]


def joystick(args):
    r = get_robot()
    connect_robot(r)
    config_robot(r)

    # vertical_height_change_unit
    # horizontal_movement_change_unit
    # joint1_rotation_change_unit
    # joint6_tilted_angle
    delta_h = 5
    delta_z = 5
    delta_jx = 0.25
    tilted_angle = 0
    which_joint_to_rotate = 6

    if len(args) in [1, 2]:
        print("Invalid number of arguments. Expected 3 or 4 arguments.")
        exit()
    elif len(args) == 3:
        delta_h, delta_z, delta_jx = args
    elif len(args) >= 4:
        delta_h, delta_z, delta_jx, tilted_angle, which_joint_to_rotate = args[0:5]

    kr = KeyReader(("smooth" if len(args) == 0 else "safe"))

    print(f'Current joystick args {delta_h, delta_z, delta_jx, tilted_angle}')

    time_out_threshold = 10*60 # unit in second
    cur_time = time.time()

    while True:
        threading.Event().wait(0.1)

        if kr.last_key == "x":
            break
        elif kr.last_key in ["up", "down"]:
            change_vertical_height(r, kr.last_key, delta_h, tilted_angle)
        elif kr.last_key in ["w", "s"]:
            change_radial_distance(r, (delta_z if kr.last_key == "w" else -delta_z))
        elif kr.last_key in ["left", "right", 'a', 'd']:
            change_azimuth(r, (-delta_jx if kr.last_key in ["left",'a'] else delta_jx))
        elif kr.last_key == "g":
            change_gripper_state(r)
        elif kr.last_key == "r":
            invert_gripper(r, tilted_angle)
        elif kr.last_key in ['[',']']:
            rotate_one_joint(r,which_joint_to_rotate,(delta_z if kr.last_key == "[" else -delta_z))
        elif kr.last_key == 'f12':
            zero(r)
        elif kr.last_key == ',': # this is the '<' key. Decrease steps by a factor 1.2.
            delta_h, delta_z, delta_jx, tilted_angle = (
                args_update(factor=1/1.5, args=[delta_h, delta_z, delta_jx, tilted_angle]))
            print(f'Agrs updated to {delta_h, delta_z, delta_jx, tilted_angle}')
        elif kr.last_key == '.':  # this is the '>' key. Increase steps by a factor 1.2.
            delta_h, delta_z, delta_jx, tilted_angle = (
                args_update(factor=1.5, args=[delta_h, delta_z, delta_jx, tilted_angle]))
            print(f'Agrs updated to {delta_h, delta_z, delta_jx, tilted_angle}')

        elif kr.last_key == 'q':
            print("Joystick is terminated by 'q' key.")
            exit()
        elif kr.last_key == 'f1':
            if input('Reset robot?') in ['y','Y']:
                reset_robot()

        if kr.last_key !='':
            cur_time = time.time()
        # if no key pressed in long time, terminate joystick for safety.
        if time.time()-cur_time > time_out_threshold:
            print(f"Joystick terminated due to timeout of {round(time_out_threshold/60,2)} min.")
            exit()

        kr.last_key = ""

    kr.listener_off()

# the following is only for shorter typing.
def js(args):
    joystick(args)
def vm(args):
    vert_move(args)



if __name__ == "__main__":

    cli()

