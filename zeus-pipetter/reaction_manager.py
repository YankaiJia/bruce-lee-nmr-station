import logging

logger_here = logging.getLogger(__name__)
logger_here.setLevel(logging.DEBUG)

formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

file_handler = logging.FileHandler('logs\\reaction_manager.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# stream_handler = logging.StreamHandler()
# stream_handler.setFormatter(formatter)
# stream_handler.setLevel(logging.DEBUG)

logger_here.addHandler(file_handler)
# logger_here.addHandler(stream_handler)

import pprint
import time
import copy
import pandas as pd
import importlib

import zeus
import gantry
import pipetter
import planner as pln
import breadboard as brb

# initiate zeus
zm = zeus.ZeusModule(id=1)
time.sleep(3)
logger_here.info("zeus is loaded as: zm.")

# initiate gantry
gt = gantry.Gantry(zeus=zm)
time.sleep(3)
logger_here.info("gantry is loaded as: gt.")
# gt.configure_grbl() # This only need to be done once.
gt.home_xy()
if gt.xy_position == (0, 0):
    logger_here.info("gantry is now homed.")

# initiate pipetter
pt = pipetter.Pipetter(zeus=zm, gantry=gt)
time.sleep(2)
logger_here.info("pipetter is loaded as: pt.")

# load containers for source substances
txt_path_for_substance = 'protein_screen/20230221_reaction_settings.txt'
pln.source_substance_containers = \
    pln.add_all_substance_to_stock_containers(txt_path=txt_path_for_substance)
logger_here.info("all substances are loaded to the corresponding containers.")

# generate event dataframes from excel
excel_path_to_generate_dataframe = 'protein_screen/20230221_robot_protein.xlsx'
event_dataframe = pln.interprete_events_from_excel_to_dataframe(dataframe_filename=excel_path_to_generate_dataframe,
                                                                sheet_name='80MUAa',
                                                                usecols='C:O')
logger_here.info("all events are generated to dataframes from excel.")

# generate event list
event_list = pln.generate_event_list(event_dataframe=event_dataframe)
logger_here.info("all event objects are generated from dataframes.")


def run_events():
    if zm.tip_on_zeus:
        pt.discard_tip()
    starting_index = 169
    for event_index in range(starting_index, len(event_list)):
        if zm.tip_on_zeus != event_list[event_index].tip_type:
            pt.change_tip(event_list[event_index].tip_type)
            logging.info(f'The tip is changed to : {event_list[event_index].tip_type}')
        pt.transfer_liquid(event_list[event_index])
        time.sleep(0.5)
        logger_here.info(f"Performed one event: {event_list[event_index].event_label}")

        # check tip type and change tip if needed
        if event_index != len(event_list) - 1:  # check if this is the last event.
            if event_list[event_index].substance_name != event_list[event_index + 1].substance_name:
                pt.change_tip(event_list[event_index + 1].tip_type)
        time.sleep(0.5)
    pt.discard_tip()


#
# def run_events1():
#
#     # logging.info("A tip 300ul is to be taken.")
#     if not zm.getTipPresenceStatus():
#         pt.pick_tip('50ul')
#
#     starting_index = 0
#     for event_index in range(40):
#         pt.transfer_liquid(event_list[0])
#         time.sleep(0.5)
#         # logger_here.info(f"Performed one event: {event_list[event_index].event_label}")
#         print(f'transfer time: {event_index}')
#         # check tip type and change tip if needed
#         # if event_index != len(event_list)-1: # check if this is the last event.
#         #     if event_list[event_index].substance_name!= event_list[event_index+1].substance_name:
#         #         pt.change_tip(event_list[event_index+1].tip_type)
#         time.sleep(0.5)
#     pt.discard_tip()

def bio_settings():
    for event_index in range(0, 87):
        event_list[event_index].asp_liquidClassTableIndex = 1
        event_list[event_index].disp_liquidClassTableIndex = 1

# bio_settings()
# run_events()
