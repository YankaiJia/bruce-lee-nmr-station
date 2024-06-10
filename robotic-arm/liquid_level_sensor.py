import serial, time
import winsound

def pump_liquid(duration:float = 1):
    for i in range(3):
        print(f'The pump is wokred for {duration}s.')
        time.sleep(1)


if __name__ == '__main__':

    lls = serial.Serial('COM3', 115200, timeout=3)

    winsound.Beep(500, 500)

    pumping_timestamp = [0]

    while True:
        flag = 0
        this_line = None

        while True:
            lls.reset_input_buffer() # this is to flush the serial buffer.
            this_line = lls.readline()

            if this_line == b'0\r\n':
                flag = 0
            elif this_line == b'1\r\n':
                winsound.Beep(500, 100)
                flag += 1
                print(flag)

            if flag > 20: # check continues positive(no liquid) cycle.
                timestamp_here = time.time()
                if timestamp_here - pumping_timestamp[-1] < 20: # check if the time gap bewteen two pumping is too small.
                    print('Just pumped less than 10s ago! Will not pump this time!')
                    continue
                pump_liquid(duration=1)
                pumping_timestamp.append(timestamp_here)
                break


