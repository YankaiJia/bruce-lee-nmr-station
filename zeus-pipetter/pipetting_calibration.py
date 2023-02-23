import time
import json
from datetime import datetime


import zeus
import gantry
import pipetter
import planner as pln
import breadboard as brb

import logging

logger = logging.getLogger("pipetting_calibration")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

file_handler = logging.FileHandler('calibration_for_pipetting\\pipetting_calibration.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# initiate zeus
zm = zeus.ZeusModule(id=1)
time.sleep(3)
logger.info("zeus is loaded as: zm")

# initiate gantry
gt = gantry.Gantry(zeus=zm)
time.sleep(3)
logger.info("gantry is loaded as: gt")
# gt.configure_grbl() # This only need to be done once.
gt.home_xy()
if gt.xy_position == (0, 0):
    logger.info("gantry is now homed")

#initiate pipetter
pt = pipetter.Pipetter(zeus=zm, gantry=gt)
time.sleep(2)
logger.info("pipetter is loaded as: pt")

def generate_events():

    # load containers for source substances
    txt_path_for_substance = 'calibration_for_pipetting/pipetting_calibration_settings.txt'
    pln.source_substance_containers = pln.add_all_substance_to_stock_containers(txt_path=txt_path_for_substance)
    logger.info("All substances are loaded to the corresponding containers.")

    # generate event dataframes from excel
    excel_path_to_generate_dataframe = 'calibration_for_pipetting/pipetting_calibration_substances.xlsx'
    event_dataframe_calibration = \
        pln.interprete_events_from_excel_to_dataframe(dataframe_filename=excel_path_to_generate_dataframe,
                                                      sheet_name='80MUAa',
                                                      usecols='B:F')
    logger.info(f"All events are generated to dataframes from excel here: {excel_path_to_generate_dataframe}")

    # generate event list
    event_list_for_calibration = pln.generate_event_list(event_dataframe= event_dataframe_calibration,
                                         pipeting_to_balance= True)
    logger.info("All event objects are generated from dataframes.")

    return event_dataframe_calibration, event_list_for_calibration

calibration_event_dataframe, calibration_event_list = generate_events()

def calibrate_pipetting_of_substances():
    '''This function is used to calibrate the pipetting of substances.'''
    results_for_calibration = []
    if zm.tip_on_zeus:
        pt.discard_tip()
    starting_index = 16
    ending_index = len(calibration_event_list)
    # ending_index = 3
    for event_index in range(starting_index, ending_index):
        if zm.tip_on_zeus != calibration_event_list[event_index].tip_type:
            pt.change_tip(calibration_event_list[event_index].tip_type)
            logging.info(f'The tip is changed to : {calibration_event_list[event_index].tip_type}')

        result = pt.pipetting_to_balance_and_weight_n_times(transfer_event=calibration_event_list[event_index], n_times=10)
        results_for_calibration.append(result)

        time.sleep(1)
        logger.info(f"Performed one measurement: {calibration_event_list[event_index].event_label}")
        logger.info(f'Result: {result}')
        # check tip type and change the tip if needed
        if event_index != len(calibration_event_list) - 1:  # check if this is the last event.
            if calibration_event_list[event_index].substance_name != calibration_event_list[event_index + 1].substance_name:
                pt.discard_tip()
        time.sleep(0.5)
    pt.discard_tip()
    return results_for_calibration


for index in range(15):
    calibration_event_list[index].tip_type = '300ul'
    calibration_event_list[index].asp_liquidClassTableIndex = 1

weighing_result = calibrate_pipetting_of_substances()

with open(f'calibration_for_pipetting//weights_for_calibration_{datetime.now().strftime("%Y_%m_%d_%H_%M")}.json',
          'w', encoding='utf-8') as f:
    json.dump(weighing_result, f, ensure_ascii=False, indent=4)

