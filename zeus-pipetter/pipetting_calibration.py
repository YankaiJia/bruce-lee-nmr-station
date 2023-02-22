import time

import zeus
import gantry
import pipetter
import planner as pln
import breadboard as brb

import logging

logger_here = logging.getLogger(__name__)
logger_here.setLevel(logging.DEBUG)

formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

file_handler = logging.FileHandler('calibration_for_pipetting\\pipetting_calibration.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# initiate zeus
zm = zeus.ZeusModule(id=1)
time.sleep(3)
print("zeus is loaded as: zm.")

# initiate gantry
gt = gantry.Gantry(zeus=zm)
time.sleep(3)
print("gantry is loaded as: gt.")
# gt.configure_grbl() # This only need to be done once.
gt.home_xy()
if gt.xy_position == (0, 0):
    print("gantry is now homed.")

#initiate pipetter
pt = pipetter.Pipetter(zeus=zm, gantry=gt)
time.sleep(2)
print("pipetter is loaded as: pt.")

def generate_event():

    # load containers for source substances
    txt_path_for_substance = 'calibration_for_pipetting/pipetting_calibration_settings.txt'
    pln.source_substance_containers = pln.add_all_substance_to_stock_containers(txt_path=txt_path_for_substance)
    logger_here.info("all substances are loaded to the corresponding containers.")

    # generate event dataframes from excel
    excel_path_to_generate_dataframe = 'calibration_for_pipetting/pipetting_calibration_substances.xlsx'
    calibration_event_dataframe = pln.interprete_events_from_excel_to_dataframe(dataframe_filename=excel_path_to_generate_dataframe,
                                                                    sheet_name='80MUAa',
                                                                    usecols='B:D')
    logger_here.info("all events are generated to dataframes from excel.")

    # generate event list
    calibration_event_list = pln.generate_event_list(event_dataframe= calibration_event_dataframe,
                                         pipeting_to_balance= True)
    logger_here.info("all event objects are generated from dataframes.")

    return calibration_event_dataframe, calibration_event_list

calibration_event_dataframe, calibration_event_list = generate_event()

def calibrate_pipetting_of_substances():
    if zm.tip_on_zeus:
        pt.discard_tip()
    starting_index = 6
    ending_index = len(calibration_event_list)
    # ending_index = 5
    for event_index in range(starting_index, ending_index):
        if zm.tip_on_zeus != calibration_event_list[event_index].tip_type:
            pt.change_tip(calibration_event_list[event_index].tip_type)
            logging.info(f'The tip is changed to : {calibration_event_list[event_index].tip_type}')

        pt.dispense_to_balance_and_weight(transfer_event=calibration_event_list[event_index])

        time.sleep(1)
        logger_here.info(f"Performed one measurement: {calibration_event_list[event_index].event_label}")

        # check tip type and change the tip if needed
        if event_index != len(calibration_event_list) - 1:  # check if this is the last event.
            if calibration_event_list[event_index].substance_name != calibration_event_list[event_index + 1].substance_name:
                pt.change_tip(calibration_event_list[event_index + 1].tip_type)
        time.sleep(0.5)
    pt.discard_tip()


calibrate_pipetting_of_substances()

