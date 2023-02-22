import time
import copy
import math
import re
from typing import Dict, Any, List

import pandas as pd
from pprint import pprint

import breadboard as brb
import logging

source_substance_containers: list = []


class EventInterpreter:
    def __init__(self,
                 dataframe_filename: str,
                 sheet_name: str,
                 usecols: str,
                 is_for_bio=False
                 ):
        self.dataframe_filename = dataframe_filename
        self.sheet_name = sheet_name
        self.usecols = usecols
        print(f'dataframe_filename: {self.dataframe_filename}')
        self.reaction_df = pd.read_excel(io = self.dataframe_filename,
                                         sheet_name=self.sheet_name,
                                         usecols=self.usecols)
        self.pd_output = pd.DataFrame(columns=['reaction_id',
                                               'event_id',
                                               'plate_number',
                                               'plate_id_on_breadboard',
                                               'container_id',
                                               'substance',
                                               'transfer_volume',
                                               ])
        self.reaction_plates = pd.DataFrame()
        self.is_for_bio = is_for_bio
        if self.is_for_bio:
            self.containers_per_plate = 96
        else:
            self.containers_per_plate = 54


    def correct_order(self):
        pass

    def _yield_plates(self):
        _df = self.reaction_df.copy()
        yield _df[:self.containers_per_plate]
        _df = _df[self.containers_per_plate:]

    def creat_events(self):
        # print('plate_id')
        event_id = 0
        if self.reaction_df.shape[0] // self.containers_per_plate == 0:
            plate_list = [0]
        else:
            plate_list = list(range(self.reaction_df.shape[0] // self.containers_per_plate))

        for plate_id in plate_list:
            # print(plate_id)
            this_plate = list(self._yield_plates())
            # print(this_plate)
            for enum, substance in enumerate(this_plate[0].columns):
                # print(this_plate[0].columns)
                for container_id in this_plate[0][substance].index:
                    transfer_volume = this_plate[0][substance][container_id]
                    # print(f'transfer_volume: {transfer_volume}')
                    if transfer_volume < 0.5 or math.isnan(transfer_volume):
                        continue
                    # event_id = container_id + \
                    #            enum * len(this_plate[0][substance]) + \
                    #            plate_id * self.containers_per_plate * this_plate[0].shape[1]
                    event_id += 1
                    plate_id_on_breadboard = plate_id % 3  # why devided by 3 ?
                    if self.is_for_bio:
                        plate_id_on_breadboard = 3
                    _dict = {'event_id': event_id,
                             "reaction_id": container_id + plate_id * self.containers_per_plate,
                             "plate_number": plate_id,
                             'plate_id_on_breadboard': plate_id_on_breadboard,
                             'container_id': container_id,
                             'substance': substance,
                             'transfer_volume': transfer_volume,
                             }
                    # self.volume_update(volume = transfer_volume, source_container = source_container, destination_container = destination_container)
                    # print(_dict)
                    self.pd_output = pd.concat([self.pd_output, pd.DataFrame(_dict, index=[event_id])],
                                               ignore_index=True)


# add substance to containers
def add_one_substance_to_stock_containers(line_str: str) -> dict[Any, dict[str, int]]:
    """
    line example: DMF plate_4_container_2 20ml
    """
    substance_name, source_container_name, stock_volume, substance_solvent, substance_density = line_str.split()
    # print([substance_name,source_container_name, stock_volume])
    stock_volume_int = int(float(stock_volume[:-2]) * 1000)  # volume in ml change to ul

    # source_container_name exp: 'plate_7_container_12'
    plate_id = int(re.findall(r'\d+', source_container_name)[0])
    container_id = int(re.findall(r'\d+', source_container_name)[-1])

    brb.plate_list[plate_id].add_substance_to_container(substance_name=substance_name,
                                                        container_id=container_id,
                                                        liquid_volume=stock_volume_int,
                                                        solvent = substance_solvent,
                                                        substance_density = substance_density)

    # return exp {'DMF': {'plate_id': 4, 'container_id': 2}}
    print(f'One substance added: {substance_name}:: "plate_id": {plate_id}, "container_id": {container_id}')
    substance_container = {substance_name: {'plate_id': plate_id, 'container_id': container_id}}

    return substance_container


def add_all_substance_to_stock_containers(txt_path: str ) -> list[
    dict[Any, dict[str, int]]]:
    source_substance_containers = []
    with open(txt_path) as file:
        lines_without_header = file.readlines()[1:]
        for this_line in lines_without_header:
            # print(this_line)
            one_substance = add_one_substance_to_stock_containers(this_line)
            source_substance_containers.append(one_substance)
    return source_substance_containers


# load container geometry parameters
# def setContainerGeometryparameters(containers=None):
#     if containers is None:
#         containers = brb.containers
#     for container in containers:
#         zm.setContainerGeometryParameters(container)
#         time.sleep(2)
#         print(f"Zeus loaded: {container.name}")

def volume_update(transfer_volume: int, source_container: object, destination_container: object):
    # print(f'source_container: {source_container}')

    # print(f'destination_container: {destination_container}')
    # print(f'source_container.liquid_volume: {source_container.liquid_volume}')
    source_container.liquid_volume = source_container.liquid_volume - transfer_volume
    # print(f'source_container.liquid_volume: {source_container.liquid_volume}')

    # print(f'destination_container.liquid_volume: {destination_container.liquid_volume}')
    destination_container.liquid_volume = destination_container.liquid_volume + transfer_volume
    # print(f'destination_container.liquid_volume: {destination_container.liquid_volume}')

    # print("Volume updated for containers!")


class TransferEventConstructor:

    def __init__(self, event_dataframe, pipeting_to_balance = False):

        self.substance_name = event_dataframe['substance']
        self.event_label = ' event_id:' + str(event_dataframe['event_id']) + '   ' + \
                           'substance:' + str(event_dataframe['substance']) + '   ' + \
                           'transfer_volume:' + str(event_dataframe['transfer_volume'])

        # print(f'solvent: {solvent}')
        # print(event_dataframe['substance'])
        self.source_container = self._get_source_container(event_dataframe['substance'])
        # print(f'source_container: {self.source_container}')
        self.source_container_xy = self.source_container.xy
        # print(f'source_container_xy: {self.source_container_xy}')
        # self.source_container_id = self.source_container.container_id

        if pipeting_to_balance:
            self.destination_container = brb.balance_cuvette
        else:
            self.destination_container = brb.plate_list[event_dataframe['plate_id_on_breadboard']].containers[
            event_dataframe['container_id']]
        # print(f'destination_container: {self.destination_container}')
        self.destination_container_xy = self.destination_container.xy
        # print(f'destination_container_xy: {self.destination_container_xy}')
        destination_plate_id = event_dataframe['plate_id_on_breadboard']
        destination_container_id = event_dataframe['container_id']
        # self.destination_container_id = f'destination_plate_id:{destination_plate_id} destination_container_id:{destination_container_id}'

        # for aspiration
        self.aspirationVolume: int = event_dataframe['transfer_volume']
        # print(f'aspirationVolume: {self.aspirationVolume}')
        self.tip_type: str = self._choose_tip_type(self.aspirationVolume)
        # print(f'tip_type: {self.tip_type}')
        self.asp_containerGeometryTableIndex = self.source_container.containerGeometryTableIndex
        # print(f'asp_containerGeometryTableIndex: {self.asp_containerGeometryTableIndex}')
        self.asp_deckGeometryTableIndex: int = self._get_deck_index(self.tip_type)
        # print(f'asp_deckGeometryTableIndex: {self.asp_deckGeometryTableIndex}')
        self.asp_liquidClassTableIndex: int = self._get_liquid_class_index(solvent = self.source_container.solvent.split('_')[0],
                                                                           mode = self.source_container.solvent.split('_')[-1],
                                                                           tip_type= self.tip_type)
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
        self.disp_deckGeometryTableIndex: int = self._get_deck_index(self.tip_type)
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

    def _get_source_container(self, substance_name: str, source_containers=None):

        '''
        source_substance_containers exp:  {'DMF': {'plate_id': 4, 'container_id': 2}, 'amine': {'plate_id': 7, 'container_id': 15}}
        '''
        # print(substance_name)
        if source_containers is None:
            source_containers = source_substance_containers
        for this_substance in source_containers:  # iterate through keys
            # print(this_substance)
            # print(substance_name)
            # print(list(this_substance.keys())[0])
            if substance_name == list(this_substance.keys())[0]:
                plate_id = this_substance[substance_name]['plate_id']
                container_id = this_substance[substance_name]['container_id']
                # print(f'substance is found in container::: brb.plate_list[{plate_id}].containers[{container_id}]')
                return brb.plate_list[plate_id].containers[container_id]

        print(f'Subtance:: {substance_name} is not found in the stock container!')

    def _get_deck_index(self, tip_type: str):
        # print(f'tipe_type: {tip_type}')

        tip_index_dict = {'50ul': 3, '300ul': 0, '1000ul': 1}

        return tip_index_dict[tip_type]

    def _get_liquid_class_index(self, solvent: str, mode: str, tip_type: int):
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
            'DMF_empty_300ul_clld':  22,
            'DMF_empty_1000ul_clld': 23
        }
        solvent_para = {solvent, mode, tip_type} # define a set
        for liquid_class, index in liquid_class_dict.items():
            solvent_para_here = set(liquid_class.split('_'))
            # print(f'solvent_para_here: {solvent_para_here}')
            if solvent_para.issubset(solvent_para_here):
                return index


    def _choose_tip_type(self, transfer_volume: int):
        if transfer_volume <= 30:
            return "50ul"
        if transfer_volume > 30 and transfer_volume <= 600:
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


def interprete_events_from_excel_to_dataframe(dataframe_filename, sheet_name, usecols):
    reaction = EventInterpreter(dataframe_filename=dataframe_filename,
                                sheet_name = sheet_name,
                                usecols= usecols,
                                is_for_bio= False)
    reaction.creat_events()
    event_dataframe = reaction.pd_output

    event_dataframe.to_json('multicomponent_reaction_input\\event_dataframe.json', orient='records', lines=True)
    df_read = pd.read_json('multicomponent_reaction_input\\event_dataframe.json', lines=True)

    return df_read


def generate_event_list(event_dataframe, pipeting_to_balance = False):
    event_list = []

    for i in range(len(event_dataframe.index)):
        # print(i)
        event = TransferEventConstructor(event_dataframe=event_dataframe.iloc[i], pipeting_to_balance = pipeting_to_balance)
        # print(event.source_container.container_id, event.destination_container.container_id)
        # print(f'event_substance: {event.substance_name}')
        volume_update(transfer_volume=event.aspirationVolume,
                      source_container=event.source_container,
                      destination_container=event.destination_container)
        # pprint(vars(event))
        event_list.append(copy.deepcopy(event))

    logging.info(f'Event_list is generated with {len(event_list)} events.')

    return event_list


if __name__ == '__main__':

    import zeus
    import gantry

    # zm = zeus.ZeusModule(id=1)
    # gt = gantry.Gantry(zeus=zm)

    # load containers for source substances
    source_substance_containers = \
        add_all_substance_to_stock_containers(txt_path=
                                                  'protein_screen/20230221_reaction_settings.txt')
    print("all substances are loaded to the corresponding containers.")

    # generate event dataframes
    # event_dataframe = \
    #     pln.interprete_events_from_excel_to_dataframe(dataframe_filename =
    #                                                   'multicomponent_reaction_input\\'
    #                                                   'composition_input_20230110RF029_adj.xlsx',
    #                                                   sheet_name = '80MUAa',
    #                                                   usecols = 'C:O')
    event_dataframe = \
        interprete_events_from_excel_to_dataframe(dataframe_filename='protein_screen/20230221_robot_protein.xlsx',
                                                  sheet_name='80MUAa',
                                                  usecols='C:O')
    print("all events are generated to dataframes from excel.")

    # generate event list
    event_list = generate_event_list(event_dataframe=event_dataframe)
    print("all event objects are generated from dataframes.")


