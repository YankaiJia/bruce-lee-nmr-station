# Importing Libraries
import serial
import time

def send_one_cmd(msg):
    zeus.write(msg.encode("utf-8"))
    value = zeus.readline()
    print("Respond: ", value)  # printing the value
    for i in range(5):
        zeus.readline()
        time.sleep(0.1)
def led_blink():

    """Check the serial communication by blinking the LED on Zeus LT"""

    sm = "00SMid1234sm1\r\n"
    sg = "00SLid1234sg1\r\n"
    for i in range(3):
        print("LED blinking\r")
        send_one_cmd(sm)
        time.sleep(0.5)
        send_one_cmd(sg)
        time.sleep(0.5)

def fm():

    """Check firmware version"""

    send_one_cmd('00RFid0815\r\n')

def init():
    send_one_cmd("00DIid0815\r\n")

def tip_pick_up():
    send_one_cmd("00TPid0815tt02\r\n")


def tip_re():
    send_one_cmd("00RTid0815\r\n")

def tip_discard():
   send_one_cmd("00TDid0815\r\n")

def plld_adj():
    send_one_cmd("00PAid0815\r\n")

def plld_start():
    send_one_cmd("00PLid0815pr1ps4\r\n")

def plld_stop():
    send_one_cmd("00PPid0815\r\n")

def plld_re():

    """request plld status"""

    send_one_cmd("0RPLid0815\r\n")


def plld_blow_out():
    send_one_cmd("00PBid0815fr10000\r\n")


zeus = serial.Serial(port='COM5',
                     baudrate=38400,
                     timeout=0.1,
                     parity= serial.PARITY_EVEN,
                     stopbits= serial.STOPBITS_ONE,
                     bytesize= serial.EIGHTBITS)
fm()
# led_blink()
print(1)


# aa = "00RTid0815"
# send_one_cmd(aa)