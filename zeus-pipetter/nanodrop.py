##  connect to arduino and send commands "1" and "0"
import serial, time

# make a class for nanodrop
class Nanodrop:
    def __init__(self):
        try:
            self.serial = serial.Serial('COM4', 9600, timeout=1)
        except:
            print("Arduino not connected")

        self.flush_time = 4
        self.dry_time = 8

    def open_lid(self):
        self.close_vacumm()
        time.sleep(0.2)
        self.open_air()
        time.sleep(0.2)
        self.serial.write(b'1')

    def close_lid(self):
        self.close_vacumm()
        time.sleep(0.2)
        self.open_air()
        time.sleep(0.2)
        self.serial.write(b'0')

    def open_liquid(self):
        self.serial.write(b'40')
    def close_liquid(self):
        self.serial.write(b'41')

    def open_air(self):
        self.serial.write(b'30')
    def close_air(self):
        self.serial.write(b'31')

    def open_vacumm(self):
        self.serial.write(b'20')

    def close_vacumm(self):
        self.serial.write(b'21')

    def close_all(self):
        self.close_vacumm()
        time.sleep(0.2)
        self.close_liquid()
        time.sleep(0.2)
        self.close_air()


    def flush_pedestal(self):
        time_stamp = time.time()
        self.open_vacumm()
        time.sleep(0.2)
        self.close_air()
        time.sleep(0.2)
        while time.time() - time_stamp < self.flush_time:
            self.open_liquid()
            time.sleep(0.2)
        self.close_liquid()
        time.sleep(0.2)
        self.close_vacumm()
        time.sleep(0.2)
        return True

    def dry_pedestal(self):
        time_stamp = time.time()
        self.open_vacumm()
        time.sleep(0.2)
        self.close_liquid()
        time.sleep(0.2)
        while time.time() - time_stamp < self.dry_time:
            self.open_air()
            time.sleep(0.2)
        self.close_vacumm()
        time.sleep(0.2)
        self.open_air()
        time.sleep(0.2)
        return True


if __name__ ==  '__main__':
    nd = Nanodrop()
    print(1)