import time

import winsound

def beep_normal():
    for i in range(2):
        winsound.Beep(800, 400)
        time.sleep(0.2)

def beep_error():
    for i in range(4):
        winsound.Beep(1800, 400)
        time.sleep(0.2)

if __name__ == "__main__":
    beep_normal()
    beep_error()