"""
Controller part of the testing kit
Integrates the View and Model part in the testing kit

King Lam Kwong
"""

import curses

from testing_kit_model import change_vertical_height
from testing_kit_view import View
from meca import (get_robot, connect_robot, config_robot)


class Controller:
    def __init__(self, stdscr: curses.window):
        self.view = View(stdscr)

        self.robo = get_robot()
        connect_robot(self.robo)
        config_robot(self.robo)

        self.moving_distance_in_mm = 10
        self.tilted_angle = 0

    def change_moving_distance(self):
        self.view.display_message("Set the moving distance (in mm): ")
        new_dist = int(self.view.get_user_input(1, 0))
        self.moving_distance_in_mm = new_dist

    def vert_movement_mode(self):
        # init moving dist per step
        self.change_moving_distance()

        while True:
            # self.view.display_z_value(self.model.get_z())

            # read user input
            key = self.view.wait_for_key()
            direction_str = ""

            if key == ord("x"):
                break
            elif key == ord("c"):
                self.change_moving_distance()
            elif key == curses.KEY_UP:
                direction_str = "u"
            elif key == curses.KEY_DOWN:
                direction_str = "d"

            change_vertical_height(
                direction_str, self.moving_distance_in_mm, self.tilted_angle
            )

    def run(self):
        self.view.clear_screen()

        while True:
            self.view.display_message(
                "Enter function name (e.g., 'vheight') or 'exit' to quit:", 0, 0
            )
            user_input = self.view.get_user_input(1, 0)

            if user_input == "exit":
                break
            elif user_input == "vheight":
                self.vert_height_moving_mode()
                self.view.clear_screen()
            else:
                self.view.display_message("Unknown command. Please try again.", 2, 0)
                self.view.wait_for_key()
                self.view.clear_screen()
