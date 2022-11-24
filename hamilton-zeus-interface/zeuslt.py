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
        self.zeus_serial.flushInput()
        self.zeus_serial.flushOutput()
        self.zeus_serial.write((msg + '\r\n').encode("utf-8"))
        print("Command sent: ", (msg + '\r\n').encode("utf-8"))
        time.sleep(.1)
        response = self.zeus_serial.readline()
        print("Serial response: ", response)  # printing the response
        # if there is error code in reply, then display the error description
        if 'er' in response.decode():
            error_code = response.decode().split('er')[-1][:2]
            if error_code == '00':
                print("No error during the command")
            if error_code != '00':
                print('Error {0}: {1}'.format(error_code, self.errorTable[error_code]))
        time.sleep(timeout_after_completion)
        return response


    def led_blink(self, time_interval=0.5):
        """Check the serial communication by blinking the LED on Zeus LT five times on and off."""
        sm = f"00SMid{self.id:04d}sm1"
        sg = f"00SLid{self.id:04d}sg1"
        for i in range(3):
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

    def clld_start(self, cr = 0, cs = 1):
        self.send_command(f"00CLid{self.id:04d}cr{cr:01d}cs{cs:01d}")

    def clld_stop(self):
        self.send_command(f"00CPid{self.id:04d}")

    def clld_re(self):
        self.send_command(f"00RNid{self.id:04d}")

    def plld_adj(self):
        self.send_command(f"00PAid{self.id:04d}")

    def plld_start(self):
        self.send_command(f"00PLid{self.id:04d}pr1ps4")

    def plld_stop(self):
        self.send_command(f"00PPid{self.id:04d}")

    def plld_re(self):
        """request plld status"""
        self.send_command(f"00RPid{self.id:04d}")

    def plld_blow_out(self, flow_rate=10):
        self.send_command(f"00PBid{self.id:04d}fr{flow_rate:05d}")

    def mixting_asp(self, mixing_volume = 10, flow_rate = 10):
        self.send_command(f"00MAid{self.id:04d}ma{mixing_volume:05d}fr{flow_rate:05d}")

    def mixing_disp(self, flow_rate = 10):
        self.send_command(f"00MDid{self.id: 04d}fr{flow_rate: 05d}")

    def asp_liquid(self,asp_volume = 10,
                   overasp = 10,
                   flow_rate = 10,
                   stop_speed = 10,
                   qpm = 0,
                   pressure_sensor = 1,
                   qpm_clot = 500,
                   qpm_foam = 500,
                   qpm_empty = 500,
                   time_after_asp = 10):
        self.send_command(f"00ALid{self.id:04d}av{asp_volume:05d}oa{overasp:05d}"
                          f"fr{flow_rate:05d}ss{stop_speed:05d}qm{qpm:01d}"
                          f"bi{pressure_sensor:01d}qc{qpm_clot:04d}qf{qpm_foam:04d}"
                          f"qe{qpm_empty:04d}to{time_after_asp:03d}")

    def asp_transport_air_volume(self, asp_transport_air_volume = 10, flow_rate = 10):
        self.send_command(f"00ATid{self.id:04d}tv{asp_transport_air_volume:05d}fr{flow_rate:05d}")

    def start_adc(self):
        self.send_command(f"00AXid{self.id:04d}")
    def stop_adc(self):
        self.send_command(f"00AYid{self.id:04d}")

    def dis_transport_air_volume(self, flow_rate = 10):
        self.send_command(f"00DTid{self.id:04d}fr{flow_rate:05d}")

    def disp_liquid(self, disp_volume = 10,
                    stop_back_volume = 10,
                    flow_rate=10,
                    stop_speed=10,
                    pressure_sensor=1,
                    qpm=0,
                    qpm_clot=500,
                    qpm_foam=500,
                    time_after_disp=10):
        self.send_command(f"00DLid{self.id:04d}dv{disp_volume:05d}sv{stop_back_volume:03d}"
                          f"fr{flow_rate:05d}ss{stop_speed:05d}bi{pressure_sensor:01d}"
                          f"qm{qpm:01d}qc{qpm_clot:04d}qf{qpm_foam:04d}to{time_after_disp:03d}")

    def empty_tip(self,
                    flow_rate=10,
                    stop_speed=10,
                    pressure_sensor=1,
                    qpm=0,
                    qpm_clot=500,
                    qpm_foam=500,
                    time_after_disp=10):
        self.send_command(f"00DEid{self.id:04d}fr{flow_rate:05d}ss{stop_speed:05d}bi{pressure_sensor:01d}"
                          f"qm{qpm:01d}qc{qpm_clot:04d}qf{qpm_foam:04d}to{time_after_disp:03d}")

    def re_number_of_pressure_data_recorded(self):
        self.send_command(f"00QHid{self.id:04d}")

    def re_pressue_data(self, start_index = 0, number_of_values_requested = 1):
        self.send_command(f"00QIid{self.id:04d}li{start_index:04d}ln{number_of_values_requested:04d}")

    """
    Additional commands and parameters
    """

    def switch_dispensing_drive_power_off(self):
        self.send_command(f"00DOid{self.id:04d}")

    def re_number_of_lld_data_recorded(self, lld_channel = 0):
        self.send_command(f"00RBid{self.id:04d}lc{lld_channel}")

    def re_lld_data(self, start_index = 0, number_of_values = 0, lld_channel = 0):
        self.send_command(f"00RLid{self.id:04d}li{start_index:04d}ln{number_of_values:02d}lc{lld_channel}")

    """
       Status request
    """

    def re_instrument_status(self):
        self.send_command(f"00RQid{self.id:04d}")

    def re_error_code(self):
        self.send_command(f"00REid{self.id:04d}")

    def re_parameter_value(self, parameter_name = "ai"):
        self.send_command(f"00RAid{self.id:04d}ra"+parameter_name)

    def re_instrument_init_status(self):
        self.send_command(f"00QWid{self.id:04d}")

    def re_name_of_last_faulty_parameter(self):
        self.send_command(f"00VPid{self.id:04d}")

    def re_cycle_counter(self):
        self.send_command(f"00RVid{self.id:04d}")

    def re_lifetime_counter(self):
        self.send_command(f"00RYid{self.id:04d}")

    def re_technical_status(self):
        self.send_command(f"00QTid{self.id:04d}")

    """tip status"""

    def re_tips_pressure_status(self):
        self.send_command(f"00RTid{self.id:04d}")

    def re_monitoring_of_volume_in_tip(self):
        self.send_command(f"00VTid{self.id:04d}")

    """special commends"""

    def emergency_stop_on(self):
        self.send_command(f"00ESid{self.id:04d}")

    def emergency_stop_off(self):
        self.send_command(f"00SRid{self.id:04d}")

    def test_mode_status(self, on_off = 0):
        self.send_command(f"00TMid{self.id:04d}at{on_off}")

    def reset_tip_counter_after_change_of_adapter(self):
        self.send_command(f"00SCid{self.id:04d}")

    def save_counters_before_power_off(self):
        self.send_command(f"00AVid{self.id:04d}")

    def switch_leds_manually(self, blue= 0, red = 0, green = 0):
        self.send_command(f"00AVid{self.id:04d}sb{blue}sr{red}sg{green}")

    def master_switch_led(self, master_switch = 0):
        self.send_command(f"00AVid{self.id:04d}sm{master_switch}")


if __name__ == "__main__":
    # Any variable (instance) name can be used instead of zeus_pipette_one
    zeus_pipette_one = ZeusLTModule(id=815, COMport='COM5', COM_timeout=0.1, baudrate=38400)
    zeus_pipette_one.firmware_version()
    zeus_pipette_one.led_blink()

