import click
from pynput import keyboard

import threading

from testing_kit_model import change_vertical_height
from meca import (get_robot, connect_robot, config_robot)

@click.command()
@click.argument("function_name")
@click.argument("params", nargs=-1)
def cli(function_name, params):
    # Get the method from the instance
    func = globals().get(function_name)
    # Check if it's callable (i.e., a method)
    if callable(func):
        func(params)


class KeyReader:
    def __init__(self):
        self.listener = keyboard.Listener(on_release=self.on_release)
        self.listener.start()
        self.last_key = ""

    def on_release(self, key: keyboard.Key):
        try:
            self.last_key = key.char
        except AttributeError:
            self.last_key = str(key).split(".")[-1]

    def listener_off(self):
        self.listener.stop()


# add new functions as testing tool below


def check_health(params):
    print("healthy", params)


def vert_move(params):
    unit_distance = int(params[0])
    tilted_angle = (
        0 if len(params) < 2 else (0 if params[1].isdigit() == False else int(params[1])) 
    )
    print(f"move vertically by unit distance {unit_distance} mm")

    kr = KeyReader()

    while kr.last_key != "x":
        threading.Event().wait(0.2)

        if kr.last_key in ["up", "down"]:
            change_vertical_height(r, kr.last_key, unit_distance, tilted_angle)
            kr.last_key = ""

    kr.listener_off()


if __name__ == "__main__":
    r = get_robot()
    connect_robot(r)
    config_robot(r)

    cli()
