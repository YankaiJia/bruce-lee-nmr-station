import logging
import os
import pickle
import json

import numpy as np
import winsound
from typing import Dict, Any

module_logger = logging.getLogger('main.planner')

import time
from datetime import datetime
import copy
import math
import re
import pandas as pd
from pprint import pprint
import breadboard as brb


class EventInterpreter:
    '''This class is used to interpret the MS Excel file to a list of pipetting df.
    **How to use:
        1, upon calling __init__, the MS Excel file will be read into a
    pandas dataframe called self.reaction_df. Also, an empty dataframe called self.pd_output
    will be created.
        2, call add_events_to_df() to add events to self.pd_output.
    '''
    def __init__(self,
                 dataframe_filename: str,
                 is_for_bio=False
                 ):
        self.dataframe_filename = dataframe_filename

        self.logger = logging.getLogger('main.planner.EventInterpreter')
        self.logger.info(f'Interpretating dataframe_filename from {self.dataframe_filename}')

        self.reaction_df = pd.read_excel(io=self.dataframe_filename,
                                         sheet_name= 'reactions')

        # remove the first column from df
        self.reaction_df = self.reaction_df.iloc[:, 1:]

        self.pd_output = pd.DataFrame(columns=['reaction_id',
                                               'event_id',
                                               'plate_number',
                                               'plate_number_barcode',
                                               'plate_id_on_breadboard',
                                               'container_id',
                                               'substance',
                                               'transfer_volume',
                                               ])
        self.reaction_plates = pd.DataFrame()
        self.is_for_bio = is_for_bio
        if self.is_for_bio:
            self.containers_per_plate: int = 96
        else:
            self.containers_per_plate: int = 54

    def correct_order(self):  # TODO: use this function to correct the order of the adding substances
        pass

    def add_events_to_df(self):
        # print('plate_id')
        event_id = 0

        # generate a list of plates to accommodate all the reactions
        if self.reaction_df.shape[0] // self.containers_per_plate == 0:
            plate_list = [0]  # note: list(range(0)) = []
        else:
            plate_list = list(range(self.reaction_df.shape[0] // self.containers_per_plate))
        #
        for plate_id in plate_list:
            # print(plate_id)
            df_here = self.reaction_df.copy()
            dataframes_for_this_plate = df_here[plate_id * self.containers_per_plate: (
                                                                                                  plate_id + 1) * self.containers_per_plate]
            # print(this_plate)
            for enum, substance in enumerate(dataframes_for_this_plate.columns):
                # print(this_plate[0].columns)
                for reaction_id in dataframes_for_this_plate[substance].index:
                    transfer_volume = dataframes_for_this_plate[substance][reaction_id]
                    if transfer_volume < 0.5 or math.isnan(transfer_volume):
                        continue
                    plate_id_on_breadboard = plate_id % 3  # The breadboard has 3 plates for chemical reactions using
                    # 2_mL vials, so the plate_id_on_breadboard is the remainder of plate_id divided by 3
                    if self.is_for_bio:
                        plate_id_on_breadboard = 3  # for bio, the 96 wells are only on plate_id = 3
                    dict_here = {
                        # event_id is the index of pipetting events
                        'event_id': event_id,
                        # reaction_id is the index of reactions, this is also the index of the MS excel file
                        "reaction_id": reaction_id,
                        # plate_number is the index of the plate indicated by the barcode on the physical plate
                        "plate_number": plate_id,
                        # plate bar code
                        'plate_number_barcode': str(plate_id).zfill(2),
                        # this is the index of the plate on the breadboard
                        'plate_id_on_breadboard': plate_id_on_breadboard,
                        # container_id is the index of the container on the plate
                        'container_id': reaction_id % self.containers_per_plate,  # output: 0-53
                        # what substance is going to be pipetted in this event
                        'substance': substance,
                        # how much volume is going to be pipetted in this event
                        'transfer_volume': transfer_volume
                    }
                    # self.volume_update(volume = transfer_volume, source_container = source_container, destination_container = destination_container)
                    # print(_dict)
                    self.pd_output = pd.concat([self.pd_output, pd.DataFrame(dict_here, index=[event_id])],
                                               ignore_index=True)
                    event_id += 1


class TransferEventConstructor:

    def __init__(self, event_dataframe: pd.DataFrame, containers_for_stock, pipeting_to_balance: bool = False):

        self.substance_name: str = event_dataframe['substance']
        # show event_dataframe
        # print(event_dataframe)

        self.event_label: str = ' event_id:' + str(event_dataframe['event_id']) + '   ' + \
                                'substance:' + str(event_dataframe['substance']) + '   ' + \
                                'transfer_volume:' + str(event_dataframe['transfer_volume'])
                                # + " " + 'plate_number_barcode:' + str(event_dataframe['plate_number_barcode'])

        # print(f'solvent: {solvent}')
        # print(event_dataframe['substance'])
        # self.source_container: object = self.get_source_container(event_dataframe['substance'])
        self.source_container: object = [container for container in containers_for_stock if container.substance == self.substance_name][0]

        # print(f'source_container: {self.source_container}')
        # self.source_container_xy = self.source_container.xy
        # print(f'source_container_xy: {self.source_container_xy}')
        # self.source_container_id = self.source_container.container_id

        if pipeting_to_balance:
            self.destination_container: object = brb.balance_cuvette
        else:
            # print(f'event_dataframe: {event_dataframe["plate_id_on_breadboard"]}___{event_dataframe["container_id"]}')
            self.destination_container: object = brb.plate_list[event_dataframe['plate_id_on_breadboard']].containers[
                event_dataframe['container_id']]
        # print(f'destination_container: {self.destination_container}')
        # self.destination_container_xy = self.destination_container.xy
        # print(f'destination_container_xy: {self.destination_container_xy}')
        # destination_plate_id = event_dataframe['plate_id_on_breadboard']
        # destination_container_id = event_dataframe['container_id']
        # self.destination_container_id = f'destination_plate_id:{destination_plate_id} destination_container_id:{destination_container_id}'

        # for aspiration
        self.aspirationVolume: int = event_dataframe['transfer_volume']
        # print(f'aspirationVolume: {self.aspirationVolume}')
        self.tip_type: str = self.choose_tip_type(self.aspirationVolume)
        # print(f'tip_type: {self.tip_type}')
        self.asp_containerGeometryTableIndex = self.source_container.containerGeometryTableIndex
        # print(f'asp_containerGeometryTableIndex: {self.asp_containerGeometryTableIndex}')
        self.asp_deckGeometryTableIndex: int = self.get_deck_index(self.tip_type)
        # print(f'asp_deckGeometryTableIndex: {self.asp_deckGeometryTableIndex}')
        self.asp_liquidClassTableIndex: int = \
            self.get_liquid_class_index(solvent=self.source_container.solvent,
                                        mode=self.source_container.solvent,
                                        tip_type=self.tip_type)

        # print(f'asp_liquidClassTableIndex: {self.asp_liquidClassTableIndex}')
        self.asp_liquidSurface: int = self.get_liquid_surface(self.source_container)
        # print(f'asp_liquidSurface: {self.asp_liquidSurface}')
        self.asp_lldSearchPosition: int = self.asp_liquidSurface - 50
        # print(f'asp_lldSearchPosition: {self.asp_lldSearchPosition}')

        # for dispensing
        self.dispensingVolume: int = event_dataframe['transfer_volume']
        # print(f'dispensingVolume: {self.dispensingVolume}')
        self.disp_containerGeometryTableIndex: int = self.destination_container.containerGeometryTableIndex
        # print(f'disp_containerGeometryTableIndex: {self.disp_containerGeometryTableIndex}')
        self.disp_deckGeometryTableIndex: int = self.get_deck_index(self.tip_type)
        # print(f'disp_deckGeometryTableIndex: {self.disp_deckGeometryTableIndex}')
        self.disp_liquidClassTableIndex: int = self.asp_liquidClassTableIndex
        # print(f'disp_liquidClassTableIndex: {self.disp_liquidClassTableIndex}')
        self.disp_liquidSurface: int = self.get_liquid_surface(self.destination_container)
        # print(f'disp_liquidSurface: {self.disp_liquidSurface}')
        self.disp_lldSearchPosition: int = self.disp_liquidSurface - 50
        # print(f'disp_lldSearchPosition: {self.disp_lldSearchPosition}')

        # default values
        self.asp_qpm: int = 1
        self.asp_lld: int = 1
        self.disp_lld: int = 0
        self.asp_mixVolume: int = 0
        self.asp_mixFlowRate: int = 0
        self.asp_mixCycles: int = 0
        self.disp_mixVolume: int = 0
        self.disp_mixFlowRate: int = 0
        self.disp_mixCycles: int = 0
        self.searchBottomMode: int = 0

        # event conducting status
        self.is_event_conducted: bool = False
        self.event_start_time: str = None  # time: (UTC time, local time)
        self.event_finish_time: str = None  # time: (UTC time, local time)

    def get_source_container(self, substance_name: str, source_containers=None):

        """
        source_substance_containers exp:
        {'DMF': {'plate_id': 4, 'container_id': 2}, 'amine': {'plate_id': 7, 'container_id': 15}}
        """
        # print(substance_name)
        source_containers = brb.source_substance_containers  # global variable, mutable object (list),
        # so it should not be used directly as a default argument
        for container in source_containers:  # iterate through keys
            # print(this_substance)
            # print(substance_name)
            # print(list(this_substance.keys())[0])
            if substance_name == container.substance:
                return container
                # plate_id = this_substance[substance_name]['plate_id']
                # container_id = this_substance[substance_name]['container_id']
                # # print(f'substance is found in container: brb.plate_list[{plate_id}].containers[{container_id}]')
                # return brb.plate_list[plate_id].containers[container_id]

        print(f'Subtance:: {substance_name} is not found in the stock container!')

    def get_deck_index(self, tip_type: str):
        # print(f'tipe_type: {tip_type}')

        tip_index_dict = {'50ul': 3, '300ul': 0, '1000ul': 1}

        return tip_index_dict[tip_type]

    def get_liquid_class_index(self, solvent: str, mode: str, tip_type: str):
        liquid_class_dict = {
            'water_empty_50ul_clld': 21,
            'water_empty_300ul_clld': 1,
            'water_empty_1000ul_clld': 2,
            'water_part_50ul_clld': 3,
            'water_part_300ul_clld': 4,
            'water_part_1000ul_clld': 5,
            'serum_empty_50ul_clld': 6,
            'serum_empty_300ul_clld': 7,
            'serum_empty_1000ul_clld': 8,
            'serum_part_50ul_clld': 9,
            'serum_part_300ul_clld': 10,
            'serum_part_1000ul_clld': 11,
            'ethanol_empty_50ul_plld': 12,
            'ethanol_empty_300ul_plld': 13,
            'ethanol_empty_1000ul_plld': 14,
            'glycerin_empty_50ul_plld': 15,
            'glycerin_empty_300ul_plld': 16,
            'glycerin_empty_1000ul_plld': 17,
            'DMF_empty_300ul_clld': 22,
            'DMF_empty_1000ul_clld': 23,
            'DMF_empty_50ul_clld': 24
        }
        solvent_para = {solvent, mode, tip_type}  # define a set of paras
        for liquid_class, index in liquid_class_dict.items():
            solvent_para_here = set(liquid_class.split('_'))
            # print(f'solvent_para_here: {solvent_para_here}')
            # print(f'solvent_para: {solvent_para}')
            if solvent_para.issubset(solvent_para_here):
                return index

    def choose_tip_type(self, transfer_volume: int):
        if transfer_volume <= 50:
            return "50ul"
        if transfer_volume > 50 and transfer_volume <= 300:
            return "300ul"
        if transfer_volume > 300 and transfer_volume < 2000:
            return "1000ul"

    def get_liquid_surface(self, container: object) -> int:

        # container.liquid_volume. This is in uL
        # container.area This is in mm^2
        # container.liquid_volume / container.area This is in mm
        if container.container_shape == 'cylindrical':
            liquid_height = ((container.liquid_volume / container.area) * 10)

        elif container.container_shape == 'conical_1500ul':
            if container.liquid_volume <= 500:
                liquid_height = 17 * 10
            else:
                liquid_height = 17 * 10 + ((container.liquid_volume - 500) / container.area) * 10
        else:
            print('Container shape is not defined!')

        return round(container.bottomPosition - liquid_height)


def interprete_events_from_excel_to_dataframe(dataframe_filename: str,
                                              is_for_bio: bool) -> pd.DataFrame:
    # generate empty dataframes
    event_dataframes = EventInterpreter(dataframe_filename=dataframe_filename,
                                        is_for_bio=is_for_bio)

    # add all events to the dataframe
    event_dataframes.add_events_to_df()

    module_logger.info(f'event_dataframe is generated with {len(event_dataframes.pd_output.index)} events.')
    event_dataframes.pd_output.to_json(
        f'event_dataframes\\event_dataframe_{datetime.now().strftime("%Y_%m_%d_%H_%M")}.json',
        orient='records', lines=True)
    module_logger.info(f'event_dataframe is saved as event_dataframe_{datetime.now().strftime("%Y_%m_%d_%H_%M")}.json')

    return event_dataframes.pd_output


def generate_event_list(event_dataframe: pd.DataFrame,containers_for_stock, pipeting_to_balance: bool = False) -> list:
    """
    IMPORTANT: The source and destination containers in the event_list are not copied, but referenced to the brb.plate_list.
    So, change the liquid_volume in the event_list will also change the liquid_volume in the brb.plate_list, and vice versa.
    You can check their by the following example code:
    >> id(event_list[0].source_container) == id(brb.plate_list[x].containers[y]) # x, y correspond to the brb container index.
    True
    >> id(event_list[0].destination_container) == id(brb.plate_list[x].containers[y])
    True
    """

    event_list = []
    for i in range(len(event_dataframe.index)):
        # print(i)
        event = TransferEventConstructor(event_dataframe=event_dataframe.iloc[i],
                                         pipeting_to_balance=pipeting_to_balance,
                                         containers_for_stock=containers_for_stock)
        # print(event.source_container.container_id, event.destination_container.container_id)
        # print(f'event_substance: {event.substance_name}')
        # event_list.append(copy.deepcopy(event))  # use deepcopy to avoid the reference problem
        event_list.append(event)

        # volume update
        event.source_container.liquid_volume = event.source_container.liquid_volume - event.aspirationVolume
        event.destination_container.liquid_volume = event.destination_container.liquid_volume + event.dispensingVolume
        # pprint(vars(event))

    module_logger.info(f'Event_list is generated with {len(event_list)} events.')

    return event_list


def generate_event_object(logger: object, excel_to_generate_dataframe: str,containers_for_stock,
                          is_pipeting_to_balance: bool = False,
                          is_for_bio: bool = False) -> tuple:

    # generate event dataframes from excel
    event_dataframe = \
        interprete_events_from_excel_to_dataframe(dataframe_filename=excel_to_generate_dataframe,
                                                  is_for_bio=is_for_bio)

    logger.info(f"All events are generated to dataframes from excel here: {excel_to_generate_dataframe}")

    # generate event list
    event_list = generate_event_list(event_dataframe=event_dataframe,
                                     pipeting_to_balance=is_pipeting_to_balance,
                                     containers_for_stock=containers_for_stock)

    logger.info("All event objects are generated from dataframes.")

    return event_dataframe, event_list


def do_calibration_on_events(zm: object, pt: object, logger: object,
                             calibration_event_list: list[object],
                             change_tip_after_every_pipetting: bool,
                             repeat_n_times: int) -> list:
    '''This function is used to calibrate the pipetting of substances.'''
    results_for_calibration = []
    if zm.tip_on_zeus:
        pt.discard_tip()
    starting_index = 0
    ending_index = len(calibration_event_list)
    # ending_index = 3
    for event_index in range(starting_index, ending_index):
        if zm.tip_on_zeus != calibration_event_list[event_index].tip_type:
            pt.change_tip(calibration_event_list[event_index].tip_type)
            logger.info(f'The tip is changed to : {calibration_event_list[event_index].tip_type}')
            time.sleep(0.5)

        result = pt.pipetting_to_balance_and_weight_n_times(transfer_event=calibration_event_list[event_index],
                                                            n_times=repeat_n_times,
                                                            change_tip_after_every_pipetting= change_tip_after_every_pipetting)
        results_for_calibration.append(result)

        time.sleep(1)
        logger.info(f"Performed one measurement: {calibration_event_list[event_index].event_label}")
        logger.info(f'Result: {result}')
        # check tip type and change the tip if needed
        if event_index != len(calibration_event_list) - 1:  # check if this is the last event.
            if calibration_event_list[event_index].substance_name != \
                    calibration_event_list[event_index + 1].substance_name:
                pt.discard_tip()
        time.sleep(0.5)

        result_dict = {calibration_event_list[event_index].event_label: results_for_calibration}

        # save result_dict to jason file
        with open(f'calibration_for_pipetting\\calibration_results\\'
                  f'calibration_results_{datetime.now().strftime("%m_%d_%H_%M")}_1000ul_tips.json', 'w') as f:
            json.dump(result_dict, f, indent=4)

    pt.discard_tip()



    return results_for_calibration


def run_events_bio(zm: object, pt: object, logger: object, event_list: list[object]) -> None:
    liquid_surface_height_from_zeus = {}

    if zm.tip_on_zeus:
        pt.discard_tip()

    starting_index = 0
    ending_index = len(event_list)
    for event_index in range(starting_index, ending_index):
        if zm.tip_on_zeus != event_list[event_index].tip_type:
            pt.change_tip(event_list[event_index].tip_type)
            logger.info(f'The tip is changed to : {event_list[event_index].tip_type}')

        liquid_surface_height_from_zeus_here = pt.transfer_liquid(event_list[event_index])

        liquid_surface_height_from_zeus[event_list[event_index].substance_name + '_height'] = \
            liquid_surface_height_from_zeus_here
        liquid_surface_height_from_zeus[event_list[event_index].substance_name + 'volume'] = \
            (-liquid_surface_height_from_zeus_here + event_list[event_index].source_container.bottomPosition) \
            * event_list[event_index].source_container.area / 10000

        time.sleep(0.5)
        logger.info(f"Performed one event: {event_list[event_index].event_label}")

        # check tip type and change tip if needed
        if event_index != len(event_list) - 1:  # check if this is the last event.
            if event_list[event_index].substance_name != event_list[event_index + 1].substance_name:
                pt.change_tip(event_list[event_index + 1].tip_type)
        time.sleep(0.5)
    pt.discard_tip()

    return liquid_surface_height_from_zeus

def prewet_new_tip( zm: object, pt: object, logger: object, pipetting_event: object ):

    event_adjusted = copy.deepcopy(pipetting_event)

    max_volume = int(re.findall(r'\d+', zm.tip_on_zeus)[0])
    event_adjusted.aspirationVolume = max_volume
    event_adjusted.destination_container = event_adjusted.source_container
    event_adjusted.disp_liquidSurface = 1650

    logger.info(f'Prewetting tip with {max_volume}ul of {event_adjusted.substance_name}')
    pt.transfer_liquid(event_adjusted)
    logger.info('Prewet done! Continue with pipetting...')


def beep():

    duration = 600  # milliseconds
    freq = 1000  # Hz
    # time.sleep(0.2)
    winsound.Beep(freq, duration)

def beep_n():

    duration = 600  # milliseconds
    freq = 1000  # Hz
    # time.sleep(0.2)
    for i in range(10):
        winsound.Beep(freq, duration)

def run_events_chem(zm: object, pt: object, logger: object,
                    excel_path, plate_code_list,
                    event_list=None,
                    change_tip_after_every_pipetting: bool = False,
                    prewet_tip: bool = True,
                    ):

    liquid_surface_height_from_zeus = {}
    excel_file_name = excel_path.split('/')[-1].split('.')[0]  # get the excel file name

    if zm.tip_on_zeus: # tip_on_zeus: '' or '50ul' or '300ul' or '1000ul'
        pt.discard_tip()

    split_index = []
    for index in range(1, len(event_list)):
        if event_list[index].destination_container.id['plate_id'] != \
                event_list[index - 1].destination_container.id['plate_id']:
            split_index.append(index)
    # group event by mask
    events_grouped_by_plate_id = np.split(event_list, split_index)

    for plate_index, events_in_one_plate in enumerate(events_grouped_by_plate_id):

        start_time_unix = int(time.time())
        start_time_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for event_index in range(len(events_in_one_plate)):

            if zm.tip_on_zeus != events_in_one_plate[event_index].tip_type:
                pt.change_tip(events_in_one_plate[event_index].tip_type)
                logger.info(f'The tip is changed to : {events_in_one_plate[event_index].tip_type}')
                time.sleep(0.5)

                # do prewet every time a new tip is taken
                if prewet_tip:
                    prewet_new_tip(zm=zm, pt=pt, logger=logger, pipetting_event=events_in_one_plate[event_index])


            try:
                liquid_surface_height_from_zeus_here = pt.transfer_liquid(events_in_one_plate[event_index])
                beep()

            except Exception as e:
                logger.error(f'Error in transfer liquid.\n')
                pt.discard_tip()

                return liquid_surface_height_from_zeus

            # calculate volume and liquid height
            liquid_surface_height_from_zeus[events_in_one_plate[event_index].substance_name + '_height'] = \
                liquid_surface_height_from_zeus_here
            volume_here = (-liquid_surface_height_from_zeus_here + events_in_one_plate[event_index].source_container.bottomPosition) \
                          * events_in_one_plate[event_index].source_container.area / 10  # in uL
            liquid_surface_height_from_zeus[events_in_one_plate[event_index].substance_name + '_volume'] = round(volume_here, 1)

            time.sleep(0.05)

            logger.info(f"Performed one event: event_number {event_index}, "
                        f"{events_in_one_plate[event_index].event_label},"
                        f'{events_in_one_plate[event_index].destination_container.id},'
                        f'plate_code: {plate_code_list[plate_index]}')

            # save this event to local pickle file
            pickle_folder = os.path.dirname(excel_path) + '\\pipetter_io\\run_log\\'
            # build a new folder if not exist
            if not os.path.exists(pickle_folder):
                os.makedirs(pickle_folder)
            # pickle_folder  = 'C:\\Users\\Chemiluminescence\\Dropbox\\robochem\\pipetter_files\\pickle_files\\'
            with open(pickle_folder + f'{datetime.now().strftime("%m_%d_%H_%M_%S")}'
                                      f'_id_{event_index}'
                                      f'_{events_in_one_plate[event_index].substance_name}'
                                      f'_{events_in_one_plate[event_index].aspirationVolume}_ul'
                                      f'_barcode_{plate_code_list[plate_index]}.pickle', 'wb') as f:
                pickle.dump(events_in_one_plate[event_index], f)

            # check tip when the next event is different substance
            if event_index != len(events_in_one_plate) - 1:  # check if this is the last event.
                if events_in_one_plate[event_index].substance_name != events_in_one_plate[event_index + 1].substance_name:
                    # pt.change_tip(event_list[event_index + 1].tip_type)
                    pt.discard_tip()
            time.sleep(0.5)
            #  change tip after every pipetting if specified
            if change_tip_after_every_pipetting:
                pt.discard_tip()
                time.sleep(0.5)


        finish_time_unix = int(time.time())
        finish_time_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # record the events in this plate
        pipetter_io_info = os.path.dirname(excel_path) + '\\pipetter_io\\'
        if not os.path.exists(pipetter_io_info):
            os.makedirs(pipetter_io_info)

        run_info = f"{plate_code_list[plate_index]}, " \
                   f"{excel_file_name}, " \
                   f"{start_time_unix}, " \
                   f"{start_time_datetime}, " \
                   f"{finish_time_unix}, " \
                   f"{finish_time_datetime}, " \
                   f"\n"
        with open(pipetter_io_info + 'run_info.csv', 'a') as f:
            f.write(run_info)

        #plate_code, experiment_name, start_time_unix, start_time_datetime, finish_time_unix, finish_time_datetime, pipetting_event_id, reaction_id, excel_path, note
        #17, 2023_04_12_run01, 1681309257, 2023-04-12 23:20:57, 1681310983, 2023-04-12 23:49:43, '0-134', 0-26,"""

        pt.discard_tip()

        ## play some sound to notify the user
        beep_n()

    return liquid_surface_height_from_zeus


def run_events_chem_nps(zm: object, pt: object, logger: object, start_event_id: int,
                    event_list_path=None, event_list=None,
                    change_tip_after_every_pipetting: bool = False,
                    prewet_tip: bool = True) -> dict[Any, Any]:

    # for event list either specify a path or a list. Only speficify one of them.
    if event_list_path is not None:
        with open(event_list_path, 'rb') as f:
            event_list = pickle.load(f)

    liquid_surface_height_from_zeus = {}

    if zm.tip_on_zeus:
        pt.discard_tip()
    #
    # for event in event_list:
    #     event.asp_lld = 1

    for event_index in range(start_event_id, len(event_list)):

        if zm.tip_on_zeus != event_list[event_index].tip_type:
            pt.change_tip(event_list[event_index].tip_type)
            logger.info(f'The tip is changed to : {event_list[event_index].tip_type}')
            # do prewet every time a new tip is taken
            time.sleep(0.5)
            if prewet_tip:
                prewet_new_tip(zm=zm, pt=pt, logger=logger, pipetting_event=event_list[event_index])

        # record start time
        event_start_time = int(time.time())  # unix time
        event_start_time_datetime = datetime.fromtimestamp(event_start_time)
        event_list[event_index].event_start_time_utc = event_start_time
        event_list[event_index].event_start_time_datetime = str(event_start_time_datetime)
        try:
            liquid_surface_height_from_zeus_here = pt.transfer_liquid(event_list[event_index])
            beep()

        except Exception as e:
            logger.error(f'Error in transfer liquid.\n '
                         f'\t\t\t\t\t\tConsider adding more liquid to source container: '
                         f'{event_list[event_index].source_container.container_id}\n'
                         f'\t\t\t\t\t\tNext, proceed with: event_number{event_index+1}, {event_list[event_index].event_label}')

            with open(f'multicomponent_reaction\\event_list_chem_id_finished_at_{event_index-1}.pickle', 'wb') as f:
                pickle.dump(event_list, f)

            pt.discard_tip()

            return liquid_surface_height_from_zeus

        # record finish time
        event_finish_time = int(time.time())  # UTC time
        event_finish_time_datetime = datetime.fromtimestamp(event_finish_time)
        event_list[event_index].event_finish_time = event_finish_time
        event_list[event_index].event_finish_time_datetime = str(event_finish_time_datetime)
        event_list[event_index].is_event_conducted = True

        # calculate volume and liquid height
        liquid_surface_height_from_zeus[event_list[event_index].substance_name + '_height'] = \
            liquid_surface_height_from_zeus_here
        volume_here = (-liquid_surface_height_from_zeus_here + event_list[event_index].source_container.bottomPosition) \
                      * event_list[event_index].source_container.area / 10  # in uL
        liquid_surface_height_from_zeus[event_list[event_index].substance_name + '_volume'] = round(volume_here, 1)

        time.sleep(0.05)
        logger.info(f"Performed one event: event_number {event_index}, "
                    f"{event_list[event_index].event_label}")

        # check tip type and change tip if needed
        if event_index != len(event_list) - 1:  # check if this is the last event.
            if event_list[event_index].substance_name != event_list[event_index + 1].substance_name:
                # pt.change_tip(event_list[event_index + 1].tip_type)
                pt.discard_tip()

        time.sleep(0.5)

        # with open(f'multicomponent_reaction\\event_list_chem_{datetime.now().strftime("%Y_%m_%d_%H_%M")}.pickle', 'wb') as f:
        #     pickle.dump(event_list, f)

        if change_tip_after_every_pipetting:
            pt.discard_tip()
            time.sleep(0.5)

    pt.discard_tip()

    return liquid_surface_height_from_zeus


def run_events_chem_dilution(zm: object, pt: object, logger: object,
                             start_event_id: int, skip_vial_id: tuple = (),
                             event_list_path=None, event_list=None,
                             change_tip_after_every_pipetting: bool = False):

    # for event list, specify either a path or a list. Only specify one of them.
    if event_list_path is not None:
        with open(event_list_path, 'rb') as f:
            event_list = pickle.load(f)


    if zm.tip_on_zeus:
        pt.discard_tip()

    for event_index in range(start_event_id, len(event_list)):

        if event_index in skip_vial_id:
            print(f"Skip event {event_index}.\n")
            logger.info(f"Skip event {event_index}.\n")
            continue

        if zm.tip_on_zeus != event_list[event_index].tip_type:
            pt.change_tip(event_list[event_index].tip_type)
            logger.info(f'The tip is changed to : {event_list[event_index].tip_type}')

        try:
            pt.transfer_liquid(event_list[event_index])
            beep()

        except Exception as e:
            print(f"Error in transfer liquid.\n")

            # with open(f'multicomponent_reaction\\event_list_chem_id_{event_index}.pickle', 'wb') as f:
            #     pickle.dump(event_list, f)

            pt.discard_tip() # discard the tip to trash bin if there is an error
            raise e # raise the error to stop the program

        # time.sleep(0.05)

        logger.info(f"Performed one pipetting for dilution: event_number {event_index}, "
                    f"volume: {event_list[event_index].aspirationVolume},"
                    f"from {event_list[event_index].source_container.id},"
                    f"to {event_list[event_index].destination_container.id},")

        print(f"Performed one pipetting for dilution: event_number {event_index}, "
                    f"volume: {event_list[event_index].aspirationVolume},"
                    f"from {event_list[event_index].source_container.id},"
                    f"to {event_list[event_index].destination_container.id},")

        # check tip type and change tip if needed
        if event_index != len(event_list) - 1:  # check if this is the last event.
            if event_list[event_index].substance_name != event_list[event_index + 1].substance_name:
                pt.change_tip(event_list[event_index + 1].tip_type)

        # time.sleep(0.1)

        # with open(f'multicomponent_reaction\\event_list_chem_dilution_\\pickle_output\\'
        #           f'{datetime.now().strftime("%Y_%m_%d_%H_%M")}.pickle', 'wb') as f:
        #     pickle.dump(event_list, f)

        if change_tip_after_every_pipetting:
            pt.discard_tip()
            # time.sleep(0.1)

    if zm.tip_on_zeus:
        pt.discard_tip()



if __name__ == "__main__":
    print('You are runing the module: ', __name__)
