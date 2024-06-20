"""
CLI app for simpler testing nmr-station objects position and 
corresponding MECA500 moving configurations


King Lam Kwong
"""

import click
from pynput import keyboard

import threading

from meca_movements import (
    change_vertical_height,
    change_z_value,
    change_joint1_deg,
    change_gripper_state,
    invert_gripper,
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


def reset(args):
    pass


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
    delta_j1 = 0.25
    tilted_angle = 0

    if len(args) in [1, 2]:
        print("Invalid number of arguments. Expected 3 or 4 arguments.")
        exit()
    elif len(args) == 3:
        delta_h, delta_z, delta_j1 = args
    elif len(args) >= 4:
        delta_h, delta_z, delta_j1, tilted_angle = args[0:4]

    kr = KeyReader(("smooth" if len(args) == 0 else "safe"))
    while True:
        threading.Event().wait(0.2)

        if kr.last_key == "x":
            break
        elif kr.last_key in ["up", "down"]:
            change_vertical_height(r, kr.last_key, delta_h, tilted_angle)
        elif kr.last_key in ["w", "s"]:
            change_z_value(r, (delta_z if kr.last_key == "w" else -delta_z))
        elif kr.last_key in ["a", "d"]:
            change_joint1_deg(r, (-delta_j1 if kr.last_key == "a" else delta_j1))
        elif kr.last_key == "g":
            change_gripper_state(r)
        elif kr.last_key == "r":
            invert_gripper(r, tilted_angle)

        kr.last_key = ""

    kr.listener_off()


if __name__ == "__main__":

    cli()
