import curses

from testing_kit_controller import Controller

def main(stdscr: curses.window):
    curses.curs_set(0)

    # print(type(stdscr))
    controller = Controller(stdscr)
    controller.run()

if __name__ == "__main__":
    curses.wrapper(main)