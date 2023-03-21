
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

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'

def initiate_hardware() -> (zeus.ZeusModule, pipetter.Gantry, pipetter.Pipetter):
    # initiate zeus
    zm = zeus.ZeusModule(id=1)
    time.sleep(3)
    logger.info("zeus is loaded as: zm")

    # initiate gantry
    gt = pipetter.Gantry(zeus=zm)
    time.sleep(3)
    logger.info("gantry is loaded as: gt")
    # gt.configure_grbl() # This only need to be done once.
    gt.home_xy()
    if gt.xy_position == (0, 0):
        logger.info("gantry is homed")

    # initiate pipetter
    pt = pipetter.Pipetter(zeus=zm, gantry=gt)
    time.sleep(2)
    logger.info("pipetter is loaded as: pt")

    return zm, gt, pt

## initiate hardware
zm, gt, pt = initiate_hardware()
time.sleep(1)

# do_dilution()
##  generate_dilution_events()
# step1: dilution original reactions, adding volume: 1400ul
# step2: transfer liquid from original reaction to new vial, transfer volume: 20ul
# step3: dilution new vial, adding volume: 480ul

def generate_dilution_event(source_container: object = None,
                            destination_container: object = None,
                            volume: float = 1.1,
                            asp_liquid_surface: int = 0,
                            disp_liquid_surface: int = 0):
    # load template event
    with open('multicomponent_reaction\\dilution_template.pickle', 'rb') as f:
        event_template = pickle.load(f)
    # always creat a copy of the template event
    event = copy.deepcopy(event_template)
    # asign new parameters to the event
    event.source_container = source_container
    event.destination_container = destination_container
    event.aspirationVolume = volume
    event.dispensingVolume = volume
    event.event_label = f'transfer from {source_container.container_id} to {destination_container.container_id}'

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
event_list_dilute_old_vial = []
def dilute_old_vial(): # diluting volume 1400ul
    global event_list_dilute_old_vial

    for i in [0, 18, 36]:
        for vial_index in range(i, i+9):
            source_container = copy.deepcopy(brb.plate_list[6].containers[0])
            destination_container = copy.deepcopy(brb.plate_list[0].containers[vial_index])
            event_temp = generate_dilution_event(source_container=source_container,
                                                destination_container=destination_container,
                                                volume=1400,
                                                asp_liquid_surface = 1800,
                                                disp_liquid_surface = 2100)
            event_list_dilute_old_vial.append(event_temp)

    time.sleep(2)
    pln.run_events_chem(zm=zm, pt=pt, logger=module_logger,
                        event_list= event_list_dilute_old_vial, start_event_id=0)

dilute_old_vial()


# step2: transfer liquid from original reaction to new vial, transfer volume: 20ul
event_list_dilution_old_to_new = []
def transfer_liquid_from_old_vial_to_new(): # transfer volume 20ul
    global event_list_dilution_old_to_new

    for i in [0, 18, 36]:
        for vial_index in range(i, i + 9):
            source_container = copy.deepcopy(brb.plate_list[0].containers[vial_index])
            destination_container = copy.deepcopy(brb.plate_list[0].containers[vial_index+9])
            event_temp = generate_dilution_event(source_container=source_container,
                                                 destination_container=destination_container,
                                                 volume=22.5,
                                                 asp_liquid_surface=1800,
                                                 disp_liquid_surface=2100)
            event_list_dilution_old_to_new.append(event_temp)

    time.sleep(1)
    pln.run_events_chem(zm=zm, pt=pt, logger=module_logger,
                        event_list=event_list_dilution_old_to_new, start_event_id=0,
                        change_tip_after_every_pipetting = True)

transfer_liquid_from_old_vial_to_new()


# step3: dilution new vial, adding volume: 480ul
event_list_dilute_new_vial = []
def dilute_new_vial(): # diluting volume 480ul
    global event_list_dilute_new_vial

    for i in [9, 27, 45]:
        for vial_index in range(i, i + 9):
            source_container = copy.deepcopy(brb.plate_list[6].containers[0])
            destination_container = copy.deepcopy(brb.plate_list[0].containers[vial_index])
            event_temp = generate_dilution_event(source_container=source_container,
                                                 destination_container=destination_container,
                                                 volume=477.5,
                                                 asp_liquid_surface=1800,
                                                 disp_liquid_surface=2100)
            event_list_dilute_new_vial.append(event_temp)

    time.sleep(2)
    pln.run_events_chem(zm=zm, pt=pt, logger=module_logger,
                        event_list=event_list_dilute_new_vial, start_event_id=0)

dilute_new_vial()

