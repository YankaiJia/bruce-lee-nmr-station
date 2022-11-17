import serial
import time

class ZeusLTModule(object):
    # CANBus = None
    # transmission_retries = 5
    # remote_timeout = 1
    # serial_timeout = 0.1
    errorTable = {
        "20": "No communication to EEPROM.",
            "30": "Undefined command.",
            "31": "Undefined parameter.",
            "32": "Parameter out of range.",
            "35": "Voltage outside the permitted range.",
            "36": "Emergency stop is active or was sent during action.",
            "38": "Empty liquid class.",
            "39": "Liquid class write protected.",
            "40": "Parallel processes not permitted.",
            "50": "Initialization failed.",
            "51": "Pipetting drive not initialized.",
            "52": "Movement error on pipetting drive.",
            "53": "Maximum volume of the tip reached.",
            "54": "Maximum volume in pipetting drive reached.",
            "55": "Volume check failed.",
            "56": "Conductivity check failed.",
            "57": "Filter check failed.",
            "60": "Initialization failed.",
            "61": "Z-drive is not initialized.",
            "62": "Movement error on the z-drive.",
            "63": "Container bottom search failed.",
            "64": "Z-position not possible.",
            "65": "Z-position not possible.",
            "66": "Z-position not possible.",
            "67": "Z-position not possible.",
            "68": "Z-position not possible.",
            "69": "Z-position not possible.",
            "70": "Liquid level not detected.",
            "71": "Not enough liquid present.",
            "72": "Auto calibration of the pressure sensor not possible.",
            "73": "cLLD adjust error. Check if adapter is touching conductive things during initialization. Also the grounding should be checked.",
            "74": "Early liquid level detection.",
            "75": "No tip picked up or no tip present.",
            "76": "Tip already picked up.",
            "77": "Tip not discarded.",
            "80": "Clot detected during aspiration.",
            "81": "Empty tube detected during aspiration.",
            "82": "Foam detected during aspiration.",
            "83": "Clot detected during dispensing.",
            "84": "Foam detected during dispensing.",
            "85": "No communication to the digital potentiometer.",
    }

    def __init__(self, id=1234, COMport='COM5', COM_timeout=0.1, baudrate=38400):
        self.zeus_serial = serial.Serial(port=COMport,
                                    baudrate=baudrate,
                                    timeout=COM_timeout,
                                    parity=serial.PARITY_EVEN,
                                    stopbits=serial.STOPBITS_ONE,
                                    bytesize=serial.EIGHTBITS)
        self.id = id

    def send_command(self, msg, timeout_after_completion=0.2):
        self.zeus_serial.write((msg + '\r\n').encode("utf-8"))
        response = self.zeus_serial.readline()
        print("Serial response: \r\n", response)  # printing the response
        # if there is error code in reply, then display the error description
        if 'er' in response.decode():
            error_code = response.split('er')[-1][:2]
            print('Error {0}: {1}'.format(error_code, self.errorTable[error_code]))
        time.sleep(timeout_after_completion)
        return response


    def led_blink(self, time_interval=0.5):
        """Check the serial communication by blinking the LED on Zeus LT five times on and off."""
        sm = f"00SMid{self.id:04d}sm1"
        sg = f"00SLid{self.id:04d}sg1"
        for i in range(5):
            print("LED blinking\r")
            self.send_command(sg)
            time.sleep(time_interval)
            self.send_command(sm)
            time.sleep(time_interval)


    def firmware_version(self):
        """Request Firmware version"""
        self.send_command(f'00RFid{self.id:04d}')

    def init(self):
        self.send_command(f'00DIid{self.id:04d}')

    def tip_pick_up(self, tt=2):
        self.send_command(f"00TPid{self.id:04d}tt{tt:02d}")

    def tip_re(self):
        self.send_command(f"00RTid{self.id:04d}")

    def tip_discard(self):
        self.send_command(f"00TDid{self.id:04d}")

    def plld_adj(self):
        self.send_command(f"00PAid{self.id:04d}")

    def plld_start(self):
        self.send_command(f"00PLid{self.id:04d}pr1ps4")

    def plld_stop(self):
        self.send_command(f"00PPid{self.id:04d}")

    def plld_re(self):
        """request plld status"""
        self.send_command(f"00RPid{self.id:04d}")

    def plld_blow_out(self, flow_rate=10000):
        self.send_command(f"00PBid{self.id:04d}fr{flow_rate:05d}")

if __name__ == "__main__":
    # Any variable (instance) name can be used instead of zeus_pipette_one
    zeus_pipette_one = ZeusLTModule(id=815, COMport='COM5', COM_timeout=0.1, baudrate=38400)
    zeus_pipette_one.firmware_version()
    zeus_pipette_one.led_blink()

