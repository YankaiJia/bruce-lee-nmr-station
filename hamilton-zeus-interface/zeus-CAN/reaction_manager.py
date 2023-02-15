import time
import copy
import logging
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

gt = gantry.Gantry(zeus = zm)
time.sleep(5)
# gt.configure_grbl() # This only need to be done once.
gt.home_xy()

pt = pipetter.Pipetter(zeus = zm, gantry = gt)



def interpretor():
    reaction = pln.EventInterpreter(dataframe_filename='multicomponent_reaction_input'
                                                    '\\composition_input_20230110RF029_adj.xlsx')
    reaction.creat_events()
    event_dataframe = reaction.pd_output

    event_dataframe.to_json('multicomponent_reaction_input\\event_dataframe.json', orient='records', lines=True)
    df_read = pd.read_json('multicomponent_reaction_input\\event_dataframe.json' , lines=True)

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


pt.pick_tip(300)

for event in event_list[18:20]:
    pt.transfer_liquid(event)
    # logging.info(f"Performed one event: {event.event_label}")
    logging.info(f"Performed one event")

    time.sleep(1)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    # filename="basic.log",
)
for i in range(1):
    logging.debug("This is a debug message.")
    logging.info("This is an info message.")
    logging.warning("This is a warning message.")
    logging.error("This is an error message.")
    logging.critical("This is a critical message.")
