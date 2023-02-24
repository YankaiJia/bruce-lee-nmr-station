import logging
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

# create logger with 'spam_application'
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

import time
import zeus
import gantry
import pipetter
import planner as pln

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
    logger.info("gantry is homed")

# initiate pipetter
pt = pipetter.Pipetter(zeus=zm, gantry=gt)
time.sleep(2)
logger.info("pipetter is loaded as: pt")

def do_calibration():
    calibration_event_dataframe, calibration_event_list = \
        pln.generate_event_object(pln=pln, logger=logger,
                                  txt_path_for_substance='calibration_for_pipetting/pipetting_calibration_settings.txt',
                                  excel_to_generate_dataframe='calibration_for_pipetting/pipetting_calibration_substances.xlsx',
                                  sheet_name='80MUAa', usecols='B:F',
                                  is_pipeting_to_balance = True)

    weighing_result = pln.do_calibration_on_events(zm=zm, pt=pt, logger=logger,
                                                   calibration_event_list=calibration_event_list)
    return calibration_event_list, weighing_result

# calibration_event_list, weighing_result = do_calibration()

def do_reaction_bio():
    event_dataframe, event_list = \
        pln.generate_event_object(pln = pln, logger = logger,
                                  txt_path_for_substance='protein_screen/20230221_reaction_settings.txt',
                                  excel_to_generate_dataframe='protein_screen/20230221_robot_protein.xlsx',
                                  sheet_name='80MUAa', usecols='C:O',
                                  is_pipeting_to_balance=False)
    pln.run_events_bio(zm=zm, pt=pt, logger=logger, event_list=event_list)
    return event_list

event_list = do_reaction_bio()
