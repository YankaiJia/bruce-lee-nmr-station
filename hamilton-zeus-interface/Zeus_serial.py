# Importing Libraries
import serial
import time

def led_blink():

    """Check the serial communication by blinking the LED on Zeus LT"""

    sm = "00SMid1234sm1\r\n".encode()
    sg = "00SLid1234sg1\r\n".encode()
    for i in range(5):
        print("LED blinking\r")
        zeus.write(sg)
        time.sleep(0.5)
        zeus.write(sm)
        time.sleep(0.5)


def firmware_version():

    """Check firmware version"""

    msg = '00RFid0815\r\n'
    zeus.write(msg.encode("utf-8"))
    value = zeus.readline()
    print("Firmware version: \r\n", value)  # printing the value
    time.sleep(1)


zeus = serial.Serial(port='COM5',
                     baudrate=19200,
                     timeout=0.1,
                     parity= serial.PARITY_EVEN,
                     stopbits= serial.STOPBITS_ONE,
                     bytesize= serial.EIGHTBITS)
firmware_version()
led_blink()
print(1)