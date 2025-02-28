import click
from queue import Queue
import threading, time, re, logging, PySimpleGUI as sg, json, os, pandas as pd

from settings import (
            T_WASTE_COLLECTOR, T_WASHER1, T_WASHER2, T_DRYER,
            MAX_SAMPLE_COUNT_AFTER_SHIMMING, REGULAR_SHIM_XML,
            ROBOT_ARM_LOG_PATH, MEASUREMENT_DATA_GUI_PATH
            )
from shared_state import SharedState

# if __name__ != "__main__":
from robotic_arm import RobotArm
from pipetter import PipetterControl
from spectrometer import SpectrometerRemoteControl

from tests.dummy_robotarm import DummyRobotArmControl
from tests.dummy_pipetter import DummyPipetterControl
from tests.dummy_spectrometer import DummySpectrometerRemoteControl

measurement_info = None

def setup_logger(name = 'Scheduler'):
    # better logging format in console
    class CustomFormatter(logging.Formatter):
        grey, yellow, red, bold_red, reset = [
            "\x1b[38;20m",
            "\x1b[33;20m",
            "\x1b[31;20m",
            "\x1b[31;1m",
            "\x1b[0m",
        ]
        format = (
            "%(asctime)s-%(name)s-%(levelname)s-%(message)s (%(filename)s:%(lineno)d)"
        )
        FORMATS = {
            logging.DEBUG: grey + format + reset,
            logging.INFO: yellow + format + reset,
            logging.WARNING: yellow + format + reset,
            logging.ERROR: red + format + reset,
            logging.CRITICAL: bold_red + format + reset,
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    # create logger with 'main'
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(ROBOT_ARM_LOG_PATH + "Scheduler.log")
    fh.setLevel(logging.INFO)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    # create formatter and add it to the handlers
    formatter = logging.Formatter("%(asctime)s-%(name)s-%(levelname)s-%(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(CustomFormatter())
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

logger = setup_logger()

class Scheduler:
    # dependency injection here
    def __init__(self, robot_arm, NMR_spectrometer, pipetter) -> None:
        self.shared_state = SharedState()
        self.robot_arm = robot_arm
        self.NMR_spectrometer = NMR_spectrometer
        self.pipetter = pipetter
    
    def start(self):
        threads = [
            threading.Thread(target=self.robot_arm.run, args=(self.shared_state,)),
            threading.Thread(target=self.NMR_spectrometer.run, args=(self.shared_state,)),
            threading.Thread(target=self.pipetter.run, args=(self.shared_state,)),
        ]

        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()


class RobotArmDecision:
    # def __init__(self, robot_arm_control: RobotArm):
    def __init__(self, robot_arm_control):
        self.robot_arm = robot_arm_control
        self.target_tube_id = -1
        self.asked_return_tube = False

        self.sample_count_after_shimming = MAX_SAMPLE_COUNT_AFTER_SHIMMING
        self.logger = setup_logger(name = 'RobotArmDecision')

        self.init_timestamp = time.time()
        # print(f"RobotArmDecision initiated")
    
    def cur_time(self) -> float:
        return round(time.time() - self.init_timestamp, 2)

    def run(self, shared_state: SharedState):
        tube_state = shared_state.tube 
        producer_mq = shared_state.producer_message_queue
        consumer_mq = shared_state.consumer_message_queue

        
        while True:
            time.sleep(0.5)

            # print("\033[94m === Robot Arm === \033[0m")
            # tube_state.print_status()
            # print(self.robot_arm.get_cart_pos())
            # print(f"\x1b[38;5;190m Producer Channel: {producer_mq.q.queue} \033[0m")
            # print(f"\x1b[38;5;214m Consumer Channel: {consumer_mq.q.queue}\033[0m")
            # print()
            
            # get message from the consumer_mq
            spectrometer_msg = ""
            if not consumer_mq.no_message():
                spectrometer_msg = consumer_mq.get_front_message()
            

            """
            Regular Shimming
            """
            if self.sample_count_after_shimming >= MAX_SAMPLE_COUNT_AFTER_SHIMMING:
                if spectrometer_msg == "":
                    self.robot_arm.pick_tube(self.robot_arm.facilities["reference_slot"])
                    self.robot_arm.place_tube_to_spinsolve()
                    consumer_mq.add_new_message("ShimReference")

                    continue
                          
                elif spectrometer_msg == "RemoveReference":
                    self.robot_arm.pick_tube_from_spinsolve()
                    self.robot_arm.place_tube(self.robot_arm.facilities["reference_slot"])

                    consumer_mq.finish_front_message()

                    self.sample_count_after_shimming = 0
                else:
                    continue
                

            """
            Priority 1: Take analyzed tube from spinsolve to waste collector
            """
            
            if spectrometer_msg == "DitchSample":
                self.robot_arm.pick_tube_from_spinsolve()
                consumer_mq.finish_front_message()

                target_tube_id = tube_state.find("spectrometer")
                tube_state.transferring_tube(target_tube_id)
                self.robot_arm.flip_tube(location='flip_stand_waste',
                                            is_pick=False)
                tube_state.in_waste_collector(target_tube_id)
                tube_state.set_time_finished(target_tube_id, self.cur_time() + T_WASTE_COLLECTOR)

                self.sample_count_after_shimming += 1

            """
            Priority 2: Take the tube of next unanalyzed sample from tube rack to spinsolve for analysis
            """
            pipetter_msg = ""
            if not producer_mq.no_message():
                pipetter_msg = producer_mq.get_front_message()

            # only run this block when no tube is in the spectrometer
            if tube_state.find("analyzing") == -1 and tube_state.find("spectrometer") == -1:
                if pipetter_msg == "":
                    producer_mq.add_new_message("NextSample?")
                elif pipetter_msg.startswith("TubeId="):
                    new_target = re.search(r'TubeId=(\d+)', pipetter_msg)
                    producer_mq.add_new_message("PauseRefill")
                    producer_mq.finish_front_message()
                elif pipetter_msg == "PauseRefillOkay":
                    target_tube_id = tube_state.find_next_filled_tube()
                    self.robot_arm.pick_tube(self.robot_arm.facilities[f"tube{target_tube_id + 1}"])
                    producer_mq.finish_front_message()

                    tube_state.transferring_tube(target_tube_id)
                    self.robot_arm.place_tube_to_spinsolve()
                    producer_mq.add_new_message("ResumeRefill")
                    tube_state.in_spectrometer(target_tube_id)
                    consumer_mq.add_new_message("NewSampleReady")


            """
            Priority 3: Reversely iterate each cleaning-related tube_state: each transit to next state
                i.e 
                    tube at "dryer" transit to "empty"
                    tube at "washer2" transit to "dryer"
                    tube at "washer1" transit to "washer2"
                    tube at "waste_collector" transit to "washer1"
                why reversely iterate?
                    prevent tube moving from washer1 to washer2 and still there is tube at washer2
            """
            for state in ["dryer", "washer2", "washer1", "waste_collector"]:
                tube_id = tube_state.find(state)
                # print(f"=> current state: {state}, tube_id: {tube_id}")

                if tube_id == -1: continue 
                
                cur_time = self.cur_time()
                end_time = tube_state.time_finished[tube_id]

                # print(f"==> cur_time: {cur_time}, end_time: {end_time}")

                if cur_time <= end_time: continue

                # print(f"===> okay")


                if state == "dryer":
                    # move the tube back to its tube rack
                    if pipetter_msg != "ReadyToReturnTube":
                        if not self.asked_return_tube:
                            producer_mq.add_new_message("ReturnTube")
                            self.asked_return_tube = True
                        
                    else:
                        producer_mq.finish_front_message()
                        self.robot_arm.pick_tube(self.robot_arm.facilities["dryer"])
                        self.robot_arm.flip_tube(location = 'flip_stand_clean')
                        self.robot_arm.place_tube(self.robot_arm.facilities[f"tube{tube_id+1}"])

                        ## for real run
                        time.sleep(30)# this time is for cooling of tube after drying
                        ## for testing or taking video
                        time.sleep(1)# this time is for cooling of tube after drying

                        tube_state.empty_tube(tube_id)
                        # self.robot_arm.go_to_safe("auto")
                        self.robot_arm.retract_to_carousel()
                        producer_mq.add_new_message("ResumeRefill")
                        self.asked_return_tube = False
                
                elif state == "washer2":
                    # move the tube from washer2 to dryer
                    if tube_state.find("dryer") == -1:
                        self.robot_arm.pick_tube(self.robot_arm.facilities['washer2'])
                        self.robot_arm.place_tube(self.robot_arm.facilities["dryer"])
                        tube_state.in_dryer(tube_id)
                        tube_state.set_time_finished(tube_id, cur_time + T_DRYER)

                elif state == "washer1":
                    # move the tube from washer1 to washer2
                    if tube_state.find("washer2") == -1:
                        self.robot_arm.pick_tube(self.robot_arm.facilities['washer1'])
                        self.robot_arm.place_tube(self.robot_arm.facilities["washer2"])
                        tube_state.in_washer2(tube_id)
                        tube_state.set_time_finished(tube_id, cur_time + T_WASHER2)
                
                elif state == "waste_collector":
                    # move the tube from waste_collector to washer1
                    if tube_state.find("washer1") == -1:
                        self.robot_arm.pick_tube(
                            self.robot_arm.facilities['flip_stand_waste_gripper_upright'])
                        self.robot_arm.place_tube(self.robot_arm.facilities["washer1"])
                        tube_state.in_washer1(tube_id)
                        tube_state.set_time_finished(tube_id, cur_time + T_WASHER1)

            """
            Block 4: Terminate this thread if ended
            """
            if pipetter_msg == "Terminate":
                consumer_mq.add_new_message("Terminate")
                break
        
class NMR_SpectrometerDecision:
    # def __init__(self, remote_control: SpectrometerRemoteControl, message: list[str]) -> None:
    def __init__(self, remote_control,
                 spectrum_storage_dir: str,
                 message: list[str],
                 measurement_info: dict) -> None:
        self.remote_control = remote_control
        self.spectrum_storage_dir = spectrum_storage_dir
        self.request_xml_messages = message
        self.measurement_info = measurement_info
        # print("Spectrometer initiated!")
        # print(f"\t with NMR requests {self.request_xml_messages}")
        self.container_uuid_dict = self.measurement_info['container_uuid_dict']

        if measurement_info['reaction_excel_path']:
            excel_name = measurement_info['reaction_excel_path'].split('/')[-1].split('.')[0]
        else:
            excel_name = 'dummy_reactions'
        self.measurement_name = excel_name
        self.measurement_log_file_name = excel_name + '_plate_'+ self.measurement_info['well_plate_number'] + '.csv'

        self.measurement_info.pop('container_uuid_dict')

    def run(self, shared_state: SharedState):
        tube_state = shared_state.tube
        consumer_mq = shared_state.consumer_message_queue

        while True:
            time.sleep(1)

            # print(" === Spectrometer === ")

            if consumer_mq.no_message():
                continue
            # print(f"\x1b[38;5;214m Consumer Channel: {consumer_mq.q.queue}\033[0m")

            message = consumer_mq.get_front_message()

            if message == "Terminate":
                break
            
            if message == "NewSampleReady":
                tube_id = tube_state.find("spectrometer")
                sample_well_id = tube_state.sample_in_tube[tube_id]
                # print(f"Analyzing sample {sample_well_id} in tube {tube_id}")
                tube_state.analyzing_tube(tube_id)

                """
                # TODO: Update the folder path
                folder_path = self.spectrum_storage_dir + "\\" + str(tube_id)
                """
                measurement_start_time = time.time()
                # for each sample, send the sequence of xml message
                # OLD: each sequence has four msg: 'sample', 'solvent', 'custom', '1d-proton', '1d-wet-sup'
                for num, message in enumerate(self.request_xml_messages):

                    if num == 0: # this msg specifies the sample id
                        message = message.replace('######', str(sample_well_id))

                    self.remote_control.send_request_to_spinsolve80(message)
                    time.sleep(1)

                measurement_end_time = time.time()

                ## collect measurement info
                measurement_info = {
                    **self.measurement_info,
                    'sample_well_id': sample_well_id,
                    'measurement_start_time': measurement_start_time,
                    'measurement_end_time': measurement_end_time,
                    'data_folder': self.remote_control.data_folder,
                    'reaction_uuid': self.container_uuid_dict[sample_well_id]
                }

                df_here = pd.DataFrame([measurement_info])
                log_file_path = ROBOT_ARM_LOG_PATH + '//measurement_log//' + self.measurement_log_file_name
                # If file doesn't exist, create it with headers
                if not os.path.exists(log_file_path ):
                    df_here.to_csv(log_file_path, mode='w', header=True, index=False)
                    logger.warning(f"###### Finished first measurement ######")
                else:
                    # Append to existing file without writing the header again
                    df_here.to_csv(log_file_path, mode='a', header=False, index=False)
                    logger.warning(f"###### Finished one measurement ######")

                logger.warning(measurement_info)
                tube_state.in_spectrometer(tube_id)
                consumer_mq.finish_front_message()
                consumer_mq.add_new_message("DitchSample")
            
            elif message == "ShimReference":
                # print("Shimming Reference")

                """
                # TODO: Update the folder path  
                folder_path = self.spectrum_storage_dir + "\\" + "RegularShim"
                """
                self.remote_control.send_request_to_spinsolve80(REGULAR_SHIM_XML)
                consumer_mq.finish_front_message()
                consumer_mq.add_new_message("RemoveReference")


class PipetterDecision:
    # def __init__(self, pipetter_control: PipetterControl, process_order: list[int]) -> None:
    def __init__(self, pipetter_control, process_order: list[int]) -> None:
        self.pipettor = pipetter_control
        self.process_order = process_order
        
        self.standby = False

        self.prev_log_msg = ""

        logger.info("Pipetter initiated")
        logger.info(f"\t with process order {self.process_order}")
    def run(self, shared_state: SharedState):
        tube_state = shared_state.tube
        producer_mq = shared_state.producer_message_queue

        while True:
            time.sleep(1)
            
            # print(" === Pipetter === ")
            # print(f"\x1b[38;5;190m Producer Channel: {producer_mq.q.queue} \033[0m")
            tube_state.print_status()

            next_sample_id = (-1 if self.process_order == [] else self.process_order[0])
            next_refill_tube_id = tube_state.find_next_empty_tube()

            # print(f"  --> next_sample {next_sample_id}\n  --> next_refill {next_refill_tube_id}\n  --> is_standby? {self.standby}")

            if next_sample_id != -1 and next_refill_tube_id != -1 and not self.standby:
                self.pipettor.aspirate(next_sample_id)
                self.pipettor.refill(next_refill_tube_id)
                tube_state.filled_tube(next_refill_tube_id, next_sample_id)
                self.process_order.pop(0)
            

            if producer_mq.no_message(): continue

            message = producer_mq.get_front_message()

            if message == "NextSample?":
                next_available_tube = tube_state.find_next_filled_tube()
                if next_available_tube != -1:
                    # print(f"Next available tube is at rack id {next_available_tube}")
                    producer_mq.add_new_message(f"TubeId={next_available_tube}, SampleId={tube_state.sample_in_tube[next_available_tube]}")
                
                # elif next_available_tube == -1 and next_sample_id == -1:
                #     producer_mq.add_new_message("NoSampleLeft")
                
                producer_mq.finish_front_message()
            
            elif message == "PauseRefill":
                self.pipettor.standby()
                self.standby = True
                producer_mq.add_new_message("PauseRefillOkay")
                producer_mq.finish_front_message()
            
            elif message == "ResumeRefill":
                self.standby = False
                producer_mq.finish_front_message()
            
            elif message == "ReturnTube":
                self.pipettor.standby()
                self.standby = True
                producer_mq.add_new_message("ReadyToReturnTube")
                producer_mq.finish_front_message()

            if tube_state.is_all_empty() and self.process_order == []:
                producer_mq.add_new_message("Terminate")
                break

def get_measurement_info():

    # File to store the last used input values: MEASUREMENT_DATA_GUI_PATH

    def load_previous_data():
        """Load the last entered values from a JSON file, handling empty or missing files."""
        if os.path.exists(MEASUREMENT_DATA_GUI_PATH):
            try:
                with open(MEASUREMENT_DATA_GUI_PATH, "r") as file:
                    data = json.load(file)
                    return data if isinstance(data, dict) else {}  # Ensure it returns a dictionary
            except (json.JSONDecodeError, ValueError):  # Handle empty or corrupted JSON
                return {}
        return {}  # Return an empty dictionary if the file doesn't exist

    def save_data(data):
        """Save the input values to a JSON file."""
        with open(MEASUREMENT_DATA_GUI_PATH, "w") as file:
            json.dump(data, file)

    def parse_vial_list(input_text):
        """Convert mixed range and discrete input into a sorted list of vial numbers."""
        vials = set()  # Use a set to avoid duplicates
        parts = input_text.split(',')

        for part in parts:
            part = part.strip()
            if '-' in part:  # Range case
                start, end = map(int, part.split('-'))
                vials.update(range(start, end + 1))
            elif part.isdigit():  # Single number case
                vials.add(int(part))

        return sorted(vials)  # Return as a sorted list

    sg.theme("DarkBlue")  # Choose a modern theme

    # Load previous data
    previous_data = load_previous_data()

    layout = [
        [sg.Text("Input Measurement Info", font=("Arial", 18, "bold"), justification="center", expand_x=True)],

        [sg.Text("Reaction Name:", size=(20, 1), font=("Arial", 14)),
         sg.InputText(previous_data.get("reaction_name", ""), key="reaction_name", font=("Arial", 14), size=(30, 1))],

        [sg.Text("User Name:", size=(20, 1), font=("Arial", 14)),
         sg.InputText(previous_data.get("user_name", ""), key="user_name", font=("Arial", 14), size=(30, 1))],

        [sg.Text("Well Plate Number:", size=(20, 1), font=("Arial", 14)),
         sg.InputText(previous_data.get("well_plate_number", ""), key="well_plate_number", font=("Arial", 14),
                      size=(30, 1))],

        [sg.Text("Reaction Solvent:", size=(20, 1), font=("Arial", 14)),
         sg.InputText(previous_data.get("reaction_solvent", ""), key="reaction_solvent", font=("Arial", 14),
                      size=(30, 1))],

        [sg.Text("Reaction Excel Path:", size=(20, 1), font=("Arial", 14)),
         sg.InputText(previous_data.get("reaction_excel_path", ""), key="reaction_excel_path", font=("Arial", 14),
                      size=(25, 1)),
         sg.FileBrowse(font=("Arial", 12))],

        [sg.Text("\t\tVials to Measure \n(e.g. 0-5, 7, 10-12 (both left and right are included)):", size=(40, 2), font=("Arial", 16))],
        [sg.InputText(previous_data.get("vials_to_measure", ""), key="vials_to_measure", font=("Arial", 14),
                      size=(30, 1))],

        [sg.Button("Submit", font=("Arial", 14), size=(10, 1)), sg.Button("Cancel", font=("Arial", 14), size=(10, 1))]
    ]

    window = sg.Window("Measurement Input", layout, size=(650, 400), element_justification='center',
                       finalize=True)

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == "Cancel":
            window.close()
            return None  # User canceled

        if event == "Submit":

            measurement_info = {
                "reaction_name": values["reaction_name"],
                "user_name": values["user_name"],
                "well_plate_number": values["well_plate_number"],
                "reaction_solvent": values["reaction_solvent"],
                "reaction_excel_path": values["reaction_excel_path"],
                "vials_to_measure": values["vials_to_measure"]  # Store as final list of numbers
            }
            save_data(measurement_info)  # Save input for next time
            vials_to_measure = parse_vial_list(values["vials_to_measure"])  # Convert input to final list
            measurement_info["vials_to_measure"] = vials_to_measure  # Store as final list of numbers
            window.close()

            # collection info
            vials_to_measure = measurement_info['vials_to_measure']
            measurement_info.pop('vials_to_measure')

            return measurement_info, vials_to_measure  # Return collected data

def extract_uuid_container_mapping(file_path):
    """Reads an Excel file and extracts container_id as keys and uuid as values into a dictionary."""
    try:
        # Load Excel file
        df = pd.read_excel(file_path, usecols=["uuid", "container_id"], engine="openpyxl")

        # Convert to dictionary (container_id as key, uuid as value)
        container_uuid_dict = dict(zip(df["container_id"], df["uuid"]))

        return container_uuid_dict

    except Exception as e:
        print(f"Error reading file: {e}")
        return {}

# @click.command()
# @click.option('--test', is_flag=True, required=True, help='Use dummy components')
def main(use_gui=True, vials_to_measure=None):

    if use_gui:
        measurement_info, vials_to_measure = get_measurement_info()
        print(measurement_info)
        print(vials_to_measure)
    # example: measurement_info
    # {'reaction_name': 'bromination',
    #  'user_name': 'YJ',
    #  'well_plate_number': '85',
    #  'reaction_solvent': 'Ethanol',
    #  'reaction_excel_path': 'D:/dropbox/Dropbox/robochem/data/DPE_bromination/2025-01-23-run01/2025-01-23-run01.xlsx',
    #  }
    else:
        measurement_info = {'reaction_name': 'bromination',
                            'user_name': 'YJ',
                            'well_plate_number': '78',
                            'reaction_solvent': 'DCE',
                            'reaction_excel_path': 'D:/dropbox/Dropbox/brucelee/data/DPE_bromination/2025-02-19-run01_time_varied/2025-02-19-run01.xlsx'}
    print(measurement_info)
    print(vials_to_measure)


    container_uuid_dict = extract_uuid_container_mapping(file_path=measurement_info['reaction_excel_path'])
    measurement_info['container_uuid_dict']=container_uuid_dict

    logger.warning(measurement_info)

    # raise KeyError

    pipetter_decision = PipetterDecision(PipetterControl(), vials_to_measure)

    robot_here = RobotArm()
    robot_arm_decision = RobotArmDecision(robot_here)

    xml_sample = [f"""<?xml version="1.0" encoding="utf-8"?>
                <Message>
                    <Set>
                        <Sample> ###### </Sample>
                    </Set>
                </Message>"""]
    # #########Following is not used due it is slow.############
    # solvent = 'DCE'
    # xml_solvent = [f""" <?xml version="1.0" encoding="utf-8"?>
    #                 <Message>
    #                     <Set>
    #                         <Solvent> {solvent} </Solvent>
    #                     </Set>
    #                 </Message>"""]
    # custom_msg = 'DPE_bromination'
    # xml_custom = [f"""<?xml version="1.0" encoding="utf-8"?>
    #             <Message>
    #                 <Set>
    #                     <Custom> {custom_msg} </Custom>
    #                 </Set>
    #             </Message>"""]
    # ##########################################################
    xml_1dproton = ["""<?xml version="1.0" encoding="utf-8"?>
                            <Message>
                                    <Start protocol="1D PROTON">
                                            <Option name="Scan" value="QuickScan" />
                                    </Start>
                            </Message>"""]

    ### this is for Yanqiu's exp.
    # xml_1dwetsup = ["""<?xml version="1.0" encoding="utf-8"?>
    #                         <Message>
    #                             <Start protocol="1D WET SUP">
    #                                 <Option name="Mode" value="Auto 2 Peaks" />
    #                                 <Option name="autoStart" value="1.3" />
    #                                 <Option name="autoEnd" value="2.7" />
    #                                 <Option name="autoStart2" value="2.8" />
    #                                 <Option name="autoEnd2" value="4.5" />
    #                                 <Option name="CorrectionFactor" value="0.9" />
    #                                 <Option name="Dummy" value="2" />
    #                                 <Option name="Number" value="32" />
    #                                 <Option name="AcquisitionTime" value="3.2" />
    #                                 <Option name="RepetitionTime" value="10" />
    #                                 <Option name="DecoupleAcq" value="Off" />
    #                                 <Option name="DecoupleSat" value="Off" />
    #                             </Start>
    #                         </Message>"""]

    ### for bromination exp
    xml_1dproton_plus = ["""
                        <?xml version="1.0" encoding="utf-8"?>
                            <Message>
                                <Start protocol="1D EXTENDED+">
                                    <Option name="Number" value="32" />
                                    <Option name="AcquisitionTime" value="6.4" />
                                    <Option name="RepetitionTime" value="10" />
                                    <Option name="PulseAngle" value="30" />
                                </Start>
                            </Message>
                        """]

    #"Number" value="32" or "16"
    # "RepetitionTime" value="10"
    # spectrometer_decision = NMR_SpectrometerDecision(DummySpectrometerRemoteControl(), "", xml_request_message)

    # xml_msg_list = ['sample', 'solvent', 'custom', '1dproton', '1dwetsup']

    ## Yanqiu exp
    # spectrometer_decision = NMR_SpectrometerDecision(SpectrometerRemoteControl(),
    #                                                  "",
    #                                                  xml_sample+
    #                                                  # xml_solvent+
    #                                                  # xml_custom+
    #                                                  xml_1dproton+
    #                                                  xml_1dwetsup)
    ## bromination exp
    spectrometer_decision = NMR_SpectrometerDecision(SpectrometerRemoteControl(),
                                                     "",
                                                     xml_sample + xml_1dproton_plus,
                                                     measurement_info=measurement_info,
                                                     )
    # # for taking demo
    # spectrometer_decision = NMR_SpectrometerDecision(SpectrometerRemoteControl(),
    #                                                  "",
    #                                                  xml_sample+
    #                                                  # xml_solvent+
    #                                                  # xml_custom+
    #                                                  xml_1dproton)

    scheduler = Scheduler(robot_arm_decision, spectrometer_decision, pipetter_decision)
    scheduler.start()


if __name__ == "__main__":

    main()

