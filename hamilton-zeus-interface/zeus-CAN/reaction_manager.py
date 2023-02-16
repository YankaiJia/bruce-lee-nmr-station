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

# initiate hardware
zm = zeus.ZeusModule(id=1)
time.sleep(5)

gt = gantry.Gantry(zeus=zm)
time.sleep(5)
# gt.configure_grbl() # This only need to be done once.
gt.home_xy()

pt = pipetter.Pipetter(zeus=zm, gantry=gt)


def interpretor():
    reaction = pln.EventInterpreter(dataframe_filename='multicomponent_reaction_input'
                                                       '\\composition_input_20230110RF029_adj.xlsx')
    reaction.creat_events()
    event_dataframe = reaction.pd_output

    event_dataframe.to_json('multicomponent_reaction_input\\event_dataframe.json', orient='records', lines=True)
    df_read = pd.read_json('multicomponent_reaction_input\\event_dataframe.json', lines=True)

    return df_read

event_dataframe = interpretor()

def generate_event_object():
    event_list = []

    for i in range(len(event_dataframe.index)):
        # print(i)
        event = pln.TransferEventConstructor(event_dataframe=event_dataframe.iloc[i])
        print(event.source_container_id, event.destination_container_id)
        print(f'event_substance: {event.substance_name}')
        pln.volume_update(transfer_volume=event.aspirationVolume,
                          source_container=event.source_container,
                          destination_container=event.destination_container)
        # pprint(vars(event))
        event_list.append(copy.deepcopy(event))

    return event_list

event_list = generate_event_object()


def run_events():
    logging.info("A tip 300ul is to be taken.")
    pt.pick_tip('300ul')

    starting_index = 0
    for event_index in range(starting_index, len(event_list)-5):
        pt.transfer_liquid(event_list[event_index])
        logging.info(f"Performed one event::: {event_list[event_index].event_label}")

        # check tip type and change tip if need
        if event_index != len(event_list)-1: # check if this is the last event.
            if event_list[event_index].substance_name!= event_list[event_index+1].substance_name:
                pt.change_tip(event_list[event_index+1].tip_type[:-4])
                logging.info(f'Tip is changed and its type is {event_list[event_index+1].tip_type[:-4]}')
        time.sleep(0.5)
