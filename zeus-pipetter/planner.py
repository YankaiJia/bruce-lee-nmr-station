import logging
import pickle
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
                 sheet_name: str,
                 usecols: str,
                 is_for_bio=False
                 ):
        self.dataframe_filename = dataframe_filename
        self.sheet_name = sheet_name
        self.usecols = usecols

        self.logger = logging.getLogger('main.planner.EventInterpreter')
        self.logger.info(f'Interpretating dataframe_filename from {self.dataframe_filename}')

        self.reaction_df = pd.read_excel(io=self.dataframe_filename,
                                         sheet_name=self.sheet_name,
                                         usecols=self.usecols)

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

    def __init__(self, event_dataframe: pd.DataFrame, pipeting_to_balance: bool = False):

        self.substance_name: str = event_dataframe['substance']
        self.event_label: str = ' event_id:' + str(event_dataframe['event_id']) + '   ' + \
                                'substance:' + str(event_dataframe['substance']) + '   ' + \
                                'transfer_volume:' + str(event_dataframe['transfer_volume']) + " " +\
                                'plate_number_barcode:' + str(event_dataframe['plate_number_barcode'])

        # print(f'solvent: {solvent}')
        # print(event_dataframe['substance'])
        self.source_container: object = self.get_source_container(event_dataframe['substance'])
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
            self.get_liquid_class_index(solvent=self.source_container.solvent.split('_')[0],
                                        mode=self.source_container.solvent.split('_')[-1],
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
            'DMF_empty_1000ul_clld': 23
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
        if transfer_volume > 50 and transfer_volume <= 600:
            return "300ul"
        if transfer_volume > 600 and transfer_volume < 3000:
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


def interprete_events_from_excel_to_dataframe(dataframe_filename: str, sheet_name: str, usecols: str,
                                              is_for_bio: bool) -> pd.DataFrame:
    # generate empty dataframes
    event_dataframes = EventInterpreter(dataframe_filename=dataframe_filename,
                                        sheet_name=sheet_name,
                                        usecols=usecols,
                                        is_for_bio=is_for_bio)

    # add all events to the dataframe
    event_dataframes.add_events_to_df()

    module_logger.info(f'event_dataframe is generated with {len(event_dataframes.pd_output.index)} events.')
    event_dataframes.pd_output.to_json(
        f'event_dataframes\\event_dataframe_{datetime.now().strftime("%Y_%m_%d_%H_%M")}.json',
        orient='records', lines=True)
    module_logger.info(f'event_dataframe is saved as event_dataframe_{datetime.now().strftime("%Y_%m_%d_%H_%M")}.json')

    return event_dataframes.pd_output


def generate_event_list(event_dataframe: pd.DataFrame, pipeting_to_balance: bool = False) -> list:
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
                                         pipeting_to_balance=pipeting_to_balance)
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


def generate_event_object(logger: object, excel_to_generate_dataframe: str,
                          sheet_name: str, usecols: str, is_pipeting_to_balance: bool = False,
                          is_for_bio: bool = False) -> tuple:
    # load containers for source substances
    source_substance_containers = brb.source_substance_containers

    # generate event dataframes from excel
    event_dataframe = \
        interprete_events_from_excel_to_dataframe(dataframe_filename=excel_to_generate_dataframe,
                                                  sheet_name=sheet_name,
                                                  usecols=usecols, is_for_bio=is_for_bio)

    logger.info(f"All events are generated to dataframes from excel here: {excel_to_generate_dataframe}")

    # generate event list
    event_list = generate_event_list(event_dataframe=event_dataframe,
                                     pipeting_to_balance=is_pipeting_to_balance)

    logger.info("All event objects are generated from dataframes.")

    return event_dataframe, event_list


def do_calibration_on_events(zm: object, pt: object, logger: object, calibration_event_list: list[object]) -> list:
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
                                                            n_times=1)
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


def run_events_chem(zm: object, pt: object, logger: object, start_event_id: int,
                    event_list_path=None, event_list=None,
                    change_tip_after_every_pipetting: bool = False) -> dict[Any, Any]:

    # for event list either specify a path or a list. Only speficify one of them.
    if event_list_path is not None:
        with open(event_list_path, 'rb') as f:
            event_list = pickle.load(f)

    ## adjust lc index ## this is for 0320_run
    for event in event_list:
        if event.aspirationVolume <= 50:
            event.asp_liquidClassTableIndex = 24
            event.disp_liquidClassTableIndex = 24
            event.tip_type = '50ul'
        else:
            event.asp_liquidClassTableIndex = 22
            event.disp_liquidClassTableIndex = 22
            event.tip_type = '300ul'

    liquid_surface_height_from_zeus = {}

    if zm.tip_on_zeus:
        pt.discard_tip()

    for event_index in range(start_event_id, len(event_list)):

        if zm.tip_on_zeus != event_list[event_index].tip_type:
            pt.change_tip(event_list[event_index].tip_type)
            logger.info(f'The tip is changed to : {event_list[event_index].tip_type}')
        # record start time
        event_start_time = int(time.time())  # unix time
        event_start_time_datetime = datetime.fromtimestamp(event_start_time)
        event_list[event_index].event_start_time_utc = event_start_time
        event_list[event_index].event_start_time_datetime = str(event_start_time_datetime)
        try:
            liquid_surface_height_from_zeus_here = pt.transfer_liquid(event_list[event_index])

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
                pt.change_tip(event_list[event_index + 1].tip_type)

        time.sleep(0.5)

        with open('multicomponent_reaction\\event_list_chem.pickle', 'wb') as f:
            pickle.dump(event_list, f)

        if change_tip_after_every_pipetting:
            pt.discard_tip()
            time.sleep(0.5)

    pt.discard_tip()

    return liquid_surface_height_from_zeus



def run_events_chem_dilution(zm: object, pt: object, logger: object,
                             start_event_id: int, event_list_path=None, event_list=None,
                             change_tip_after_every_pipetting: bool = False):

    # for event list, specify either a path or a list. Only specify one of them.
    if event_list_path is not None:
        with open(event_list_path, 'rb') as f:
            event_list = pickle.load(f)


    if zm.tip_on_zeus:
        pt.discard_tip()

    for event_index in range(start_event_id, len(event_list)):

        if zm.tip_on_zeus != event_list[event_index].tip_type:
            pt.change_tip(event_list[event_index].tip_type)
            logger.info(f'The tip is changed to : {event_list[event_index].tip_type}')

        try:
            pt.transfer_liquid(event_list[event_index])

        except Exception as e:
            print(f'Error in transfer liquid.\n '
                  f'\t\t\t\t\t\tConsider adding more liquid to source container: '
                  f'{event_list[event_index].source_container.container_id}\n'
                  f'\t\t\t\t\t\tNext, proceed with: {event_list[event_index].event_label}')

            with open(f'multicomponent_reaction\\event_list_chem_id_{event_index}.pickle', 'wb') as f:
                pickle.dump(event_list, f)

            pt.discard_tip() # discard the tip to trash bin if there is an error
            raise e # raise the error to stop the program

        time.sleep(0.05)
        logger.info(f"Performed one event: event_number {event_index}, "
                    f"{event_list[event_index].event_label}")
        print(f"Performed one event: event_number {event_index}, "
              f"{event_list[event_index].event_label}")

        # check tip type and change tip if needed
        if event_index != len(event_list) - 1:  # check if this is the last event.
            if event_list[event_index].substance_name != event_list[event_index + 1].substance_name:
                pt.change_tip(event_list[event_index + 1].tip_type)

        time.sleep(0.1)

        with open('multicomponent_reaction\\event_list_chem.pickle', 'wb') as f:
            pickle.dump(event_list, f)

        if change_tip_after_every_pipetting:
            pt.discard_tip()
            time.sleep(0.1)

    if zm.tip_on_zeus:
        pt.discard_tip()



if __name__ == "__main__":
    print('You are runing the module: ', __name__)
