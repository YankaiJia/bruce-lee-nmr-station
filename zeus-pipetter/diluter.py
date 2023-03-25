
import logging

module_logger = logging.getLogger('main.diluter')


import copy, time, pickle, re, importlib, json, os
from datetime import datetime
from typing import List
from openpyxl import Workbook
from openpyxl import load_workbook
import PySimpleGUI as sg
import pandas as pd

import zeus
import pipetter
import planner as pln
import breadboard as brb


## TODO 2023-03-21:
# 1. module_logger is not working;
# 2. dispensing height is not adjustable, no idea what is wrong.
# 3. coordinates need to be further optimized.


data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'

def initiate_hardware() -> (zeus.ZeusModule, pipetter.Gantry, pipetter.Pipetter):
    # initiate zeus
    zm = zeus.ZeusModule(id=1)
    time.sleep(3)
    module_logger.info("zeus is loaded as: zm")

    # initiate gantry
    gt = pipetter.Gantry(zeus=zm)
    time.sleep(3)
    module_logger.info("gantry is loaded as: gt")
    # gt.configure_grbl() # This only need to be done once.
    gt.home_xy()
    if gt.xy_position == (0, 0):
        module_logger.info("gantry is homed")

    # initiate pipetter
    pt = pipetter.Pipetter(zeus=zm, gantry=gt)
    time.sleep(2)
    module_logger.info("pipetter is loaded as: pt")

    return zm, gt, pt

## initiate hardware
zm, gt, pt = initiate_hardware()
time.sleep(1)

## note: sometimes the arduino port fails to initiate, restart the computer to fix it.
## better way need to be found.

##  generate_dilution_events()
# step1: dilution original reactions, adding volume: 1400ul
# step2: transfer liquid from original reaction to new vial, transfer volume: 20ul
# step3: dilution new vial, adding volume: 480ul

# volume setting versions:
# 1. 200ul, 1600ul, 22.5ul, 477.5ul
# 2. 200ul, 1400ul, 20ul, 480ul
# 3. 200ul, 1000ul, 15ul, 485ul ## this one is now used, 2023-03-22 14:23

# specify volumes for dilution
volume_added_to_old_vial = 1000
volume_transfered_from_old_to_new_vial = 15
volume_added_to_new_vial = 485

event_list_dilute_old_vial = []
event_list_dilution_old_to_new = []
event_list_dilute_new_vial = []

def generate_dilution_event(source_container: object = None,
                            destination_container: object = None,
                            volume: float = 0,
                            asp_liquid_surface: int = 0,
                            disp_liquid_surface: int = 0):
    # load template event
    with open('multicomponent_reaction\\template\\dilution_template.pickle', 'rb') as f:
        event_template = pickle.load(f)
    # always creat a copy of the template event
    event = copy.deepcopy(event_template)
    # asign new parameters to the event
    event.source_container = source_container
    event.destination_container = destination_container
    event.aspirationVolume = volume
    event.dispensingVolume = volume
    event.event_label = f'transfer from {source_container.container_id} to {destination_container.container_id}'

    print(f'volume: {volume}')
    if volume <= 50:
        event.tip_type = '50ul'
        event.asp_liquidClassTableIndex = 24
        event.disp_liquidClassTableIndex = 24

    elif volume <= 300 and volume > 50:
        event.tip_type = '300ul'
        event.asp_liquidClassTableIndex = 22
        event.disp_liquidClassTableIndex = 22

    else:
        event.tip_type = '1000ul'
        event.asp_liquidClassTableIndex = 23
        event.disp_liquidClassTableIndex = 23

    event.asp_liquidSurface = asp_liquid_surface
    event.asp_lld = 1
    event.asp_lldSearchPosition = asp_liquid_surface - 50

    event.disp_liquidSurface = disp_liquid_surface
    event.disp_lld = 0

    return event


# step1: dilution original reactions, adding volume: 1400ul

def dilute_old_vial(): # diluting volume 1400ul
    global event_list_dilute_old_vial

    # generate dilution events
    for i in [0, 18, 36]:
        for vial_index in range(i, i+9):
            source_container = copy.deepcopy(brb.plate_list[6].containers[0])
            destination_container = copy.deepcopy(brb.plate_list[2].containers[vial_index])
            event_temp = generate_dilution_event(source_container=source_container,
                                                destination_container=destination_container,
                                                volume=volume_added_to_old_vial,
                                                asp_liquid_surface = 1800,
                                                disp_liquid_surface = 2100)
            event_list_dilute_old_vial.append(event_temp)
    # time.sleep(2)

    ## run dilution events
    pln.run_events_chem_dilution(zm=zm, pt=pt, logger=module_logger,
                        event_list= event_list_dilute_old_vial, start_event_id=0)

# dilute_old_vial()


# step2: transfer liquid from original reaction to new vial, transfer volume: 15ul

def transfer_liquid_from_old_vial_to_new(): # transfer volume 20ul
    global event_list_dilution_old_to_new

    for i in [0, 18, 36]:
        for vial_index in range(i, i + 9):
            source_container = copy.deepcopy(brb.plate_list[2].containers[vial_index])
            destination_container = copy.deepcopy(brb.plate_list[2].containers[vial_index+9])
            event_temp = generate_dilution_event(source_container=source_container,
                                                 destination_container=destination_container,
                                                 volume=volume_transfered_from_old_to_new_vial,
                                                 asp_liquid_surface=1900,
                                                 disp_liquid_surface=2100)
            event_list_dilution_old_to_new.append(event_temp)

    # time.sleep(1)
    pln.run_events_chem_dilution(zm=zm, pt=pt, logger=module_logger,
                        event_list=event_list_dilution_old_to_new, start_event_id=0,
                        change_tip_after_every_pipetting = True)





# step3: dilution new vial, adding volume: 485ul

def dilute_new_vial(skip_vials=[]): # diluting volume 485ul
    global event_list_dilute_new_vial

    for i in [9, 27, 45]:
        for vial_index in range(i, i + 9):
            if vial_index in skip_vials:
                print(f'skipping vial with index {vial_index}')
                continue
            source_container = copy.deepcopy(brb.plate_list[6].containers[0])
            destination_container = copy.deepcopy(brb.plate_list[2].containers[vial_index])
            event_temp = generate_dilution_event(source_container=source_container,
                                                 destination_container=destination_container,
                                                 volume=volume_added_to_new_vial,
                                                 asp_liquid_surface=1900,
                                                 disp_liquid_surface=2100)
            event_list_dilute_new_vial.append(event_temp)

    # time.sleep(2)
    pln.run_events_chem_dilution(zm=zm, pt=pt, logger=module_logger,
                        event_list=event_list_dilute_new_vial, start_event_id=0)

if __name__ == '__main__':
    dilute_old_vial()
    transfer_liquid_from_old_vial_to_new()
    dilute_new_vial()

