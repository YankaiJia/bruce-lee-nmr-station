"""
workflow:
1. initiate hardware
2. generate event list for detecting surface height of stock solutions
3. run events for surface detection, get liquid surface heights and write to excel
4. generate event list for pipetting
"""

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


# specify Excel path for reactions and stock solutions
def load_excel_path_by_pysimplegui():
    sg.theme('BrightColors')  # Add a touch of color
    working_directory = os.getcwd()
    # All the stuff inside your window.
    layout = [[sg.Text('Select Excel file for reactions')],
              [sg.InputText(key="-FILE_PATH-"),
               sg.FileBrowse(initial_folder=working_directory,
                             file_types=(("Excel Files", "*.xlsx"), ("All Files", "*.*")))],
              [sg.Submit(), sg.Cancel()]]

    # Create the Window
    window = sg.Window('Select Excel file for reactions',
                       layout,
                       size=(600, 200),
                       font=('Helvetica', 14), )

    # Event Loop to process "events" and get the "values" of the inputs
    event, values = window.read()
    # print(event, values[0])
    window.close()
    logger.info(f"Excel file for reactions is selected: {values['-FILE_PATH-']}")
    return values['-FILE_PATH-']

# path_for_reactions = 'NPs\\2023_03_15-reaction_template_for_robot_Yankai.xlsx'
path_for_reactions = load_excel_path_by_pysimplegui()


def load_stock_solutions_from_excel(path: str = path_for_reactions) -> list:

    stock_solution_list = []
    wb_excel = load_workbook(path, data_only=True)
    ws = wb_excel[[x for x in wb_excel.sheetnames if 'Stock_solutions' in x][0]]

    for row in tuple(ws.rows)[1:]:  # exclude the header
        if row[0].value is not None:
            substance_name = row[0].value,
            index = row[1].value,
            container = row[2].value,
            solvent = row[3].value,
            density = row[4].value,
            volume = row[5].value,
            liquid_surface_height = row[6].value,
            pipetting_mode = row[7].value,
            stock_solution_list.append(
                [substance_name, index, container, solvent, density, volume, liquid_surface_height, pipetting_mode])

    # remove the tuple in the list
    for i in range(len(stock_solution_list)):
        for j in range(len(stock_solution_list[i])):
            stock_solution_list[i][j] = stock_solution_list[i][j][0]

    logger.info(f"stock solutions are loaded from Excel file: {stock_solution_list}" )

    # stock_solution_list example: ['p-BrPhOTf', 'Substance_A', ' plate_4_container0', 'ethanol', 0.789, 4.5, 1979, None]

    return stock_solution_list


def generate_event_list_for_surface_detection(path_for_stock_solution: str = path_for_reactions):
    event_list_surface_detection = []

    # load object from pickle.
    # This pickle object is a template for generating events for surface detection
    pickle_path = 'calibration_for_pipetting\\transfer_object_for_liquid_surface_detection.pickle'
    with open(pickle_path, 'rb') as f:
        event_for_surface_detection = pickle.load(f)

    stock_solution_list = load_stock_solutions_from_excel(path_for_stock_solution)

    # generate one event for each stock solution
    for solution in stock_solution_list:
        event_temp = copy.deepcopy(event_for_surface_detection)  # deepcopy to avoid changing the original object
        plate_id = re.findall(r'\d+', solution[2])[0]  # get the first number in the string
        container_id = re.findall(r'\d+', solution[2])[1]  # get the second number in the string
        event_temp.substance_name = solution[0]
        event_temp.source_container = copy.deepcopy(brb.plate_list[int(plate_id)].containers[int(container_id)])
        event_temp.destination_container = copy.deepcopy(event_temp.source_container)
        event_temp.asp_lld = 1  # liquidClassTableIndex =13, so pLLD will be used.
        event_temp.disp_lld = 0
        event_temp.asp_liquidClassTableIndex = 13  # use pLLD for surface detection
        event_temp.disp_liquidClassTableIndex = 13
        event_temp.asp_liquidSurface = 1750
        event_temp.asp_lldSearchPosition = 1800
        event_temp.disp_liquidSurface = 1750
        event_temp.aspirationVolume = 100
        event_list_surface_detection.append(event_temp)

    return event_list_surface_detection


event_list_surface_detection = generate_event_list_for_surface_detection()


## run detection events and get liquid surface heights
## liquid_info_in_stock example:
## {'p-BrPhOTf_height': 1986, 'p-BrPhOTf_volume': 9.7, 'm-BrPhOTf_height': 2091, 'm-BrPhOTf_volume': 4.3}
liquid_info_in_stock, *rest = pln.run_events_chem(zm=zm, pt=pt, logger=logger,
                                           event_list=event_list_surface_detection)

logger.info(f"liquid_surface_heights: {liquid_info_in_stock}")

# liquid_info_in_stock = liquid_info_in_stock[0]

## This update will rely on the exact naming and order of the file header, so keep them the same as the template.
def update_excel_with_liquid_heights_and_volume(path_for_reaction: str = path_for_reactions,
                                             liquid_info_in_stock: dict = liquid_info_in_stock):
    liquid_surface_heights_in_stock = {k[:-7]: v for k, v in liquid_info_in_stock.items() if 'height' in k}
    liquid_volume_in_stock = {k[:-7]: v for k, v in liquid_info_in_stock.items() if 'volume' in k}

    wb = load_workbook(filename=path_for_reaction)
    sheet = wb[[x for x in wb.sheetnames if 'Stock_solutions' in x][0]]

    for i in sheet.iter_rows(min_row=2, min_col=1, max_col=1):
        substance_name = i[0].value
        if substance_name in liquid_surface_heights_in_stock.keys():
            sheet[f'G{i[0].row}'] = liquid_surface_heights_in_stock[substance_name]
            sheet[f'I{i[0].row}'] = liquid_volume_in_stock[substance_name]

            logger.info(f'Stock solution {substance_name} has been updated with liquid surface height: '
                        f'{liquid_surface_heights_in_stock[substance_name]}')

    wb.save(path_for_reaction)

update_excel_with_liquid_heights_and_volume(liquid_info_in_stock=liquid_info_in_stock)

# TODO: add a function to update the Excel file with the liquid surface heights and volumes
def add_stock_solutions_to_brb_containers(reaction_excel_path: str):

    # this loading should be done after the liquid surface heights are updated in the Excel file
    stock_solution_list = load_stock_solutions_from_excel(reaction_excel_path)
    # stock_solution_list example: ['p-BrPhOTf', 'Substance_A', ' plate_4_container0', 'ethanol', 0.789, 4.5, 1979, None]

    for solution in stock_solution_list:

        container:str = solution[2]
        plate_id = int(re.findall(r'\d+', container)[0])
        container_id = int(re.findall(r'\d+', container)[1])

        substance_name = solution[0]
        substance_index = solution[1]
        substance_solvent = solution[3]
        substance_density = solution[4]
        liquid_surface_height = solution[6]


        brb.plate_list[plate_id].add_substance_to_container(substance_name=substance_name,
                                                        container_id=container_id,
                                                        solvent=substance_solvent,
                                                        substance_density=substance_density,
                                                        liquid_surface_height=liquid_surface_height)

        brb.source_substance_containers.append(brb.plate_list[plate_id].containers[container_id])

    return brb.source_substance_containers

add_stock_solutions_to_brb_containers(reaction_excel_path=path_for_reactions)


# multicomponent reactions
event_dataframe_chem, event_list_chem = \
    pln.generate_event_object(logger=logger,
                              excel_to_generate_dataframe= path_for_reactions,
                              sheet_name='Reactions_0315', usecols='B:G',
                              is_pipeting_to_balance=False, is_for_bio=False)

liquid_surface, event_crashed = pln.run_events_chem(zm=zm, pt=pt, logger=logger, event_list=event_list_chem)

#

# TODO: think about updating the stock solutions when they run out.




# TODO: update volume after surface detection
# TODO: move staff relating to IO to dropbox
# TODO: learn database









# calibration_event_dataframe, calibration_event_list = \
#     pln.generate_event_object(logger=logger,
#                               txt_path_for_substance='calibration_for_pipetting\\pipetting_calibration_settings_ALL.txt',
#                               excel_to_generate_dataframe='calibration_for_pipetting\\pipetting_calibration_substances_ALL.xlsx',
#                               sheet_name='Solvents', usecols='E',
#                               is_pipeting_to_balance=True, is_for_bio=False)
#
#
#
# for event in event_list_surface_detection:
#     # print(event.aspirationVolume)
#
#     event.source_container = brb.plate_list[4].containers[7]
#     event.destination_container = brb.plate_list[4].containers[7]
# # # generate_calibration_event_list
# # calibration_event_dataframe, calibration_event_list = \
# #     pln.generate_event_object(logger=logger,
# #                               txt_path_for_substance='calibration_for_pipetting\\pipetting_calibration_settings_ALL.txt',
# #                               excel_to_generate_dataframe='calibration_for_pipetting\\pipetting_calibration_substances_ALL.xlsx',
# #                               sheet_name='Solvents', usecols='E',
# #                               is_pipeting_to_balance=True, is_for_bio=False)
# # # time.sleep(1)
# # calibration_event_list = calibration_event_list[::-1] # reverse the list
# #
# # # specify tip and liquidClassIndex for calibration
# # def specify_tip_and_liquidClassIndex_for_calibration():
# #     for event in calibration_event_list:
# #         event.tip_type = '300ul'
# #         event.asp_liquidClassTableIndex = 22
# #         event.disp_liquidClassTableIndex = 22
# #
# # specify_tip_and_liquidClassIndex_for_calibration()
# #
# # #
# # # do_calibration
# # weighing_result = pln.do_calibration_on_events(zm=zm, pt=pt, logger=logger,
# #                                                    calibration_event_list= calibration_event_list)
# #
#
# # event_dataframe_bio, event_list_bio = \
# #     pln.generate_event_object(logger=logger,
# #                               txt_path_for_substance='protein_screen\\03072023_Plate_reader_UvVis_Yankai_test.txt',
# #                               excel_to_generate_dataframe='protein_screen\\03072023_Plate_reader_UvVis_Yankai_test.xlsx',
# #                               sheet_name='Treated_Yankai', usecols='C:G',
# #                               is_pipeting_to_balance=False, is_for_bio=True)
# #
# # pln.run_events_bio(zm=zm, pt=pt, logger=logger, event_list=event_list_bio[93:])
#
# # new_event_list = [event for i, event in enumerate(event_list_bio) if i % 5 == 0]
#
# # pln.run_events_bio(zm=zm, pt=pt, logger=logger, event_list=new_event_list)
# #
#
#



# # # for event in event_list_chem:
# #
# #     event.asp_liquidClassTableIndex = 22
# #     event.disp_liquidClassTableIndex = 22
# #     event.tip_type = '300ul'
#
#
# event_dataframe_chem, event_list_chem = \
#     pln.generate_event_object(logger=logger,
#                               txt_path_for_substance='NPs\\nps_03082023.txt',
#                               excel_to_generate_dataframe='NPs\\2023_03_15-reaction_template_for_robot_Yankai.xlsx',
#                               sheet_name='0315', usecols='B:G',
#                               is_pipeting_to_balance=False, is_for_bio=False)
# #
# for event in event_list_chem:
#     # print(event.aspirationVolume)
#     event.asp_lld = 1
#     event.disp_lld = 0
#     event.source_container = brb.plate_list[4].containers[7]
#     event.destination_container = brb.plate_list[4].containers[7]
#     event.disp_liquidSurface = 1800
#
#     # print(event.asp_liquidSurface)
# #     event.asp_liquidClassTableIndex = 1
# #     event.aspirationVolume = 300
# #     event.dispensingVolume = 300
#
# # pln.run_events_chem(zm=zm, pt=pt, logger=logger, event_list=event_list_chem)
#
#
# # def cloud_logging_test():
# #     i = 0
# #     while True:
# #         logger.info(f"{i * 10} minutes passed")
# #         i += 1
# #         time.sleep(10)
# #
# # with open(f'calibration_for_pipetting/weights_for_calibration_{datetime.now().strftime("%Y_%m_%d_%H_%M")}.json',
# #           'w', encoding='utf-8') as f:
# #     json.dump(weighing_result, f, ensure_ascii=False)
#
# # # avg = []
# # # for result in weighing_result:
# # #     for key, value in result.items():
# # #         avg.append(sum(value['weight'])/len(value['weight']))
# #
# # for event in event_list_bio:
# #     print(f'LiquidIndex: {event.asp_liquidClassTableIndex}, '
# #           f'asp_vol: {event.aspirationVolume}, '
# #           f'tiptype: {event.tip_type},'
# #           f'substance: {event.substance_name}')
#
# # event_list_chem[0].source_container.container_id
#
#
