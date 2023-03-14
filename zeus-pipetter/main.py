from datetime import datetime
import json
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

import time
import importlib
import zeus
import pipetter
import planner as pln
import breadboard as brb

def initiate_hardware():
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

# generate_calibration_event_list
calibration_event_dataframe, calibration_event_list = \
    pln.generate_event_object(logger=logger,
                              txt_path_for_substance='calibration_for_pipetting\\pipetting_calibration_settings_ALL.txt',
                              excel_to_generate_dataframe='calibration_for_pipetting\\pipetting_calibration_substances_ALL.xlsx',
                              sheet_name='Solvents', usecols='E',
                              is_pipeting_to_balance=True, is_for_bio=False)
# time.sleep(1)
calibration_event_list = calibration_event_list[::-1] # reverse the list

# specify tip and liquidClassIndex for calibration
def specify_tip_and_liquidClassIndex_for_calibration():
    for event in calibration_event_list:
        event.tip_type = '300ul'
        event.asp_liquidClassTableIndex = 22
        event.disp_liquidClassTableIndex = 22
#
specify_tip_and_liquidClassIndex_for_calibration()

# calibration_event_list[0].aspirationVolume = 150
# calibration_event_list[0].dispensingVolume = 150
#
# calibration_event_list[0].aspirationVolume = 170
# calibration_event_list[1].dispensingVolume = 170



# do_calibration
weighing_result = pln.do_calibration_on_events(zm=zm, pt=pt, logger=logger,
                                                   calibration_event_list= calibration_event_list[1:])


# event_dataframe_bio, event_list_bio = \
#     pln.generate_event_object(logger=logger,
#                               txt_path_for_substance='protein_screen\\03072023_Plate_reader_UvVis_Yankai_test.txt',
#                               excel_to_generate_dataframe='protein_screen\\03072023_Plate_reader_UvVis_Yankai_test_supplementary.xlsx',
#                               sheet_name='Treated_Yankai', usecols='C:G',
#                               is_pipeting_to_balance=False, is_for_bio=True)

# pln.run_events_bio(zm=zm, pt=pt, logger=logger, event_list=event_list_bio[:114])
# pln.run_events_bio(zm=zm, pt=pt, logger=logger, event_list=event_list_bio[:114])

# new_event_list = [event for i, event in enumerate(event_list_bio) if i % 5 == 0]

# pln.run_events_bio(zm=zm, pt=pt, logger=logger, event_list=new_event_list)
#
# event_dataframe_chem, event_list_chem = \
#     pln.generate_event_object(logger=logger,
#                               txt_path_for_substance='multicomponent_reaction_input\\reaction_settings.txt',
#                               excel_to_generate_dataframe='multicomponent_reaction_input\\'
#                                                           'composition_input_20230110RF029_adj.xlsx',
#                               sheet_name='reactions', usecols='A:E',
#                               is_pipeting_to_balance=False, is_for_bio=False)

# pln.run_events_chem(zm=zm, pt=pt, logger=logger, event_list=event_list)

# event_dataframe_chem, event_list_chem = \
#     pln.generate_event_object(logger=logger,
#                               txt_path_for_substance='NPs\\nps_03082023.txt',
#                               excel_to_generate_dataframe='NPs\\reaction_template_for_robot_test_for_ethanol.xlsx',
#                               sheet_name='reactions', usecols='H',
#                               is_pipeting_to_balance=False, is_for_bio=False)
#
# for event in event_list_chem:
#     # if event.substance_name == 'Substance_E':
#     #     event.asp_liquidSurface = 1700
#     #     event.asp_lldsearchPosition = 1700
#     #     event.asp_lldSearchPosition = 1700
#     event.asp_liquidClassTableIndex = 1
#     event.aspirationVolume = 300
#     event.dispensingVolume = 300

# pln.run_events_chem(zm=zm, pt=pt, logger=logger, event_list=event_list_chem)


# def cloud_logging_test():
#     i = 0
#     while True:
#         logger.info(f"{i * 10} minutes passed")
#         i += 1
#         time.sleep(10)
#
with open(f'calibration_for_pipetting/weights_for_calibration_{datetime.now().strftime("%Y_%m_%d_%H_%M")}.json',
          'w', encoding='utf-8') as f:
    json.dump(weighing_result, f, ensure_ascii=False)

# # avg = []
# # for result in weighing_result:
# #     for key, value in result.items():
# #         avg.append(sum(value['weight'])/len(value['weight']))
#
# for event in event_list_bio:
#     print(f'LiquidIndex: {event.asp_liquidClassTableIndex}, '
#           f'asp_vol: {event.aspirationVolume}, '
#           f'tiptype: {event.tip_type},'
#           f'substance: {event.substance_name}')

# event_list_chem[0].source_container.container_id


