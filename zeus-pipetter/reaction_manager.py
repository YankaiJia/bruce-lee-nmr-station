import logging

logging.root.handlers = []
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("reaction_manager.log"),
        logging.StreamHandler()
    ],
)

import time
import copy
import pandas as pd

import zeus
import gantry
import pipetter
import planner as pln
import breadboard as brb
import importlib

# initiate zeus
zm = zeus.ZeusModule(id=1)
time.sleep(5)

# initiate gantry
gt = gantry.Gantry(zeus=zm)
time.sleep(5)
# gt.configure_grbl() # This only need to be done once.
gt.home_xy()

#initiate pipetter
pt = pipetter.Pipetter(zeus=zm, gantry=gt)

# load containers for source substances
pln.source_substance_containers = \
    pln.add_all_substance_to_stock_containers(txt_path =
                                              'multicomponent_reaction_input/reaction_settings.txt')

# generate event dataframes
event_dataframe = \
    pln.interprete_events_from_excel_to_dataframe(dataframe_filename =
                                                  'multicomponent_reaction_input\\composition_input_20230110RF029_adj.xlsx')

# generate event list
event_list = pln.generate_event_list(event_dataframe = event_dataframe)


def run_events():

    # logging.info("A tip 300ul is to be taken.")
    if not zm.getTipPresenceStatus():
        pt.pick_tip('50ul')

    starting_index = 0
    for event_index in range(starting_index, len(event_list)):
        pt.transfer_liquid(event_list[event_index])
        logging.info(f"Performed one event: {event_list[event_index].event_label}")

        # check tip type and change tip if needed
        if event_index != len(event_list)-1: # check if this is the last event.
            if event_list[event_index].substance_name!= event_list[event_index+1].substance_name:
                pt.change_tip(event_list[event_index+1].tip_type)
        time.sleep(0.5)
    pt.discard_tip()

def bio_settings():
    for i in event_list:
        i.tip_type = '50ul'
        i.asp_liquidClassTableIndex = 21
        i.disp_liquidClassTableIndex = 21
        i.disp_liquidSurface = 1900
        i.dispensingVolume = 3
        i.aspirationVolume = 3


bio_settings()
run_events()