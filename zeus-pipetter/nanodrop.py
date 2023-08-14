##  connect to arduino and send commands "1" and "0"
import serial, time

# make a class for nanodrop
class Nanodrop:
    def __init__(self):
        try:
            self.serial = serial.Serial('COM6', 9600, timeout=1)
        except:
            print("Arduino not connected")

    def lid_open(self):
        self.serial.write(b'1')

    def lid_close(self):
        self.serial.write(b'0')



if '__name__' ==  '__main__':
    nd = Nanodrop()