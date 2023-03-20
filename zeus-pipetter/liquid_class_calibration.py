import logging


def setup_logger():
    # better logging format in console
    class CustomFormatter(logging.Formatter):
        grey = "\x1b[38;20m"
        yellow = "\x1b[33;20m"
        red = "\x1b[31;20m"
        bold_red = "\x1b[31;1m"
        reset = "\x1b[0m"
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

        FORMATS = {
            logging.DEBUG: grey + format + reset,
            logging.INFO: yellow + format + reset,
            logging.WARNING: yellow + format + reset,
            logging.ERROR: red + format + reset,
            logging.CRITICAL: bold_red + format + reset
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    # create logger with 'main'
    logger = logging.getLogger('main')
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler('logs\\main.log')
    fh.setLevel(logging.INFO)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(CustomFormatter())
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


logger = setup_logger()

import copy, time, pickle, re, importlib, json, os
from datetime import datetime
from typing import List
from openpyxl import Workbook
from openpyxl import load_workbook
import PySimpleGUI as sg
import pandas as pd
# import arrow

import zeus
import pipetter
import planner as pln
import breadboard as brb


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

zm, gt, pt = initiate_hardware()
time.sleep(1)


# calibration for 50ul tips.
calibration_event_dataframe, calibration_event_list = \
    pln.generate_event_object(logger=logger,
                              txt_path_for_substance='calibration_for_pipetting\\pipetting_calibration_settings_ALL.txt',
                              excel_to_generate_dataframe='calibration_for_pipetting\\pipetting_calibration_substances_ALL.xlsx',
                              sheet_name='Solvents', usecols='F',
                              is_pipeting_to_balance=True, is_for_bio=False)
time.sleep(1)

calibration_event_list = calibration_event_list[::-1] # reverse the list
#
# specify tip and liquidClassIndex for calibration
def specify_tip_and_liquidClassIndex_for_calibration():
    for event in calibration_event_list:
        event.tip_type = '50ul'
        event.asp_liquidClassTableIndex = 22
        event.disp_liquidClassTableIndex = 22
#
# specify_tip_and_liquidClassIndex_for_calibration()
#
# #



