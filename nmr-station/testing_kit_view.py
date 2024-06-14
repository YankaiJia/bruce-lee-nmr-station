"""
View part of the testing kit
Only deals with the user interaction in the command line interface (CLI) 

King Lam Kwong
"""

import curses

class View:
    def __init__(self, stdscr: curses.window):
        self.stdscr = stdscr

    def display_message(self, message: str, y=0, x=0):
        self.stdscr.addstr(y, x, message)
        self.stdscr.refresh()

    def get_user_input(self, y, x):
        self.stdscr.move(y, x)
        return self.stdscr.getstr().decode('utf-8').strip()

    def clear_screen(self):
        self.stdscr.clear()
        self.stdscr.refresh()

    def wait_for_key(self):
        return self.stdscr.getch()

    # def display_z_value(self, z):
    #     self.clear_screen()
    #     self.display_message("Change z mode. Use Up/Down arrows to adjust z. Press 'x' to exit.")
    #     self.display_message(f"Current z value: {z}", 1, 0)