# Importing Libraries
import serial
import time

def led_blink():

    """Check the serial communication by blinking the LED on Zeus LT"""

    sm = "00SMid1234sm1\r\n".encode()
    sg = "00SLid1234sg1\r\n".encode()
    for i in range(3):
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

def send_one_cmd(msg):
    zeus.write(msg.encode("utf-8"))
    value = zeus.readline()
    print("Respond: ", value)  # printing the value
    time.sleep(1)


def init():
    aa = "00DIid0815\r\n"
    zeus.write(aa.encode("utf-8"))
    value = zeus.readline()
    print("Respond: ", value)  # printing the value
    time.sleep(1)

def tip_pick_up():
    zeus.write("00TPid0815tt02\r\n".encode())
    value = zeus.readline()
    print("Respond: ", value)  # printing the value
    time.sleep(1)

def tip_request():
    zeus.write("00RTid0815\r\n".encode())
    value = zeus.readline()
    print("Respond: ", value)  # printing the value
    time.sleep(1)

def tip_discard():
    zeus.write("00TDid0815\r\n".encode())
    value = zeus.readline()
    print("Respond: ", value)  # printing the value
    time.sleep(1)

def plld_adj():
    zeus.write("00PAid0815\r\n".encode())
    value = zeus.readline()
    print("Respond for auto adjust pLLD: ", value)  # printing the value
    time.sleep(1)

def plld_start():
    zeus.write("00PLid0815pr0ps4\r\n".encode())
    value = zeus.readline()
    print("Respond for auto adjust pLLD: ", value)  # printing the value
    time.sleep(1)


zeus = serial.Serial(port='COM5',
                     baudrate=38400,
                     timeout=0.1,
                     parity= serial.PARITY_EVEN,
                     stopbits= serial.STOPBITS_ONE,
                     bytesize= serial.EIGHTBITS)
firmware_version()
# led_blink()
print(1)


# aa = "00RTid0815"
# send_one_cmd(aa)