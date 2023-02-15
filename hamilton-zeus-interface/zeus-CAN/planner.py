import time
import copy
from dataclasses import dataclass
import pandas as pd
from pprint import pprint

import breadboard as brb

import zeus
import gantry

# zm = zeus.ZeusModule(id=1)
# gt = gantry.Gantry(zeus=zm)

# add substance to containers
def add_one_substance_to_stock_containers(line_str: str) -> None:
    substance_name, source_container, stock_volume = line_str.split()
    print([substance_name,source_container, stock_volume])
    stock_volume_int = int(stock_volume[:-2])
    if 'bottle' in source_container:
        plate_id = 4 + int(source_container[-1]) // 8
        print(f'plate_id : {plate_id}')
        container_id = int(source_container[-1]) % 8
        print(f'container_id: {container_id}')
        print([plate_id, container_id])
    elif 'jar' in source_container:
        plate_id = 6 + int(source_container[-1]) // 2
        container_id = int(source_container[-1]) % 2
        print([plate_id, container_id])

    brb.plate_list[plate_id].add_substance_to_container(substance_name=substance_name,
                                                        container_id=container_id, liquid_volume= stock_volume_int)

def add_all_substance_to_stock_containers(txt_path: str =
                                          'multicomponent_reaction_input/reaction_settings.txt') -> None:
    with open(txt_path) as file:
        lines_without_header = file.readlines()[1:]
        for this_line in lines_without_header:
            print(this_line)
            add_one_substance_to_stock_containers(this_line)

add_all_substance_to_stock_containers()

print(1)
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
    print(f'source_container.liquid_volume: {source_container.liquid_volume}')
    source_container.liquid_volume = source_container.liquid_volume -transfer_volume
    print(f'source_container.liquid_volume: {source_container.liquid_volume}')

    print(f'destination_container.liquid_volume: {destination_container.liquid_volume}')
    destination_container.liquid_volume = destination_container.liquid_volume+ transfer_volume
    print(f'destination_container.liquid_volume: {destination_container.liquid_volume}')

    # print("Volume updated for containers!")


class TransferEventConstructor:

    def __init__(self, event_dataframe, solvent: str = 'DMF'):

        self.substance_name = event_dataframe['substance']
        self.event_label = 'event_id:'+str(event_dataframe['event_id'])+\
                        'substance:'+str(event_dataframe['substance'])+\
                        'transfer_volume:'+str(event_dataframe['transfer_volume'])

        self.solvent = solvent
        # print(f'solvent: {solvent}')
        # print(event_dataframe['substance'])
        self.source_container = self._get_source_container(event_dataframe['substance'])[0]
        # print(f'source_container: {self.source_container}')
        self.source_container_xy = self.source_container.xy
        # print(f'source_container_xy: {self.source_container_xy}')
        self.source_container_id = self._get_source_container(event_dataframe['substance'])[1]

        self.destination_container = brb.plate_list[event_dataframe['plate_id_on_breadboard']].containers[
            event_dataframe['container_id']]
        # print(f'destination_container: {self.destination_container}')
        self.destination_container_xy = self.destination_container.xy
        # print(f'destination_container_xy: {self.destination_container_xy}')
        destination_plate_id = event_dataframe['plate_id_on_breadboard']
        destination_container_id = event_dataframe['container_id']
        self.destination_container_id = f'destination_plate_id:{destination_plate_id} destination_container_id:{destination_container_id}'

        # for aspiration
        self.aspirationVolume: int = event_dataframe['transfer_volume']
        # print(f'aspirationVolume: {self.aspirationVolume}')
        self.tip_type: str = self._choose_tip_type(self.aspirationVolume)
        # print(f'tip_type: {self.tip_type}')
        self.asp_containerGeometryTableIndex = self.source_container.containerGeometryTableIndex
        # print(f'asp_containerGeometryTableIndex: {self.asp_containerGeometryTableIndex}')
        self.asp_deckGeometryTableIndex: int = self._get_deck_index(self.tip_type)
        # print(f'asp_deckGeometryTableIndex: {self.asp_deckGeometryTableIndex}')
        self.asp_liquidClassTableIndex: int = 22
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
        self.disp_liquidClassTableIndex: int = 22
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

    def _get_source_container(self, substance_name: str):
        # print(f'Looking for : {substance_name}')
        for plate_index, plate in enumerate([brb.plate4, brb.plate5, brb.plate6, brb.plate7]):
            for container_index, container in enumerate(plate.containers):
                # print(f'substance: {container.substance} is in {container}')
                if container.substance == substance_name:
                    # print(f'{substance_name} is found!')
                    return [container, f'source_plate_id:{4+plate_index} source_container_id: {container_index}']
        print('Subtance not found in the stock container!')

    def _get_deck_index(self, tip_type: str):
        if '50' in tip_type:
            return 3
        elif '300' in tip_type:
            return 0
        elif '1000' in tip_type:
            return 1

    def _get_liquid_class_index(self, liquid_name: str):

        liquid_class_dict = {
            'water_empty_50ul_clld': 0,
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
        }
        return liquid_class_dict[liquid_name]

    def _choose_tip_type(self, transfer_volume: int):
        if transfer_volume < 10:
            return "50ul_tip"
        if transfer_volume >= 10 and transfer_volume <= 600:
            return "300ul_tip"
        if transfer_volume > 600 and transfer_volume < 3000:
            return "1000ul_tip"

    def get_liquid_surface(self, container: object = brb.plate0.containers[0]):

        liquid_height = container.bottomPosition - container.liquid_volume / container.area

        return 1500



class EventInterpreter:
    def __init__(self,
                 dataframe_filename: str,
                 solvent: str = 'DMF',
                 substance_container_volume=None,
                 containers_per_plate=54,
                 ):
        self.solvent = solvent
        if substance_container_volume is None:
            substance_container_volume = [['Isocyano.2', 'bottle0', '10ml'],
                                          ['amine.2', 'bottle1', '20ml'],
                                          ['aldehyde.2', 'bottle2', '30ml'],
                                          ['pTSA.2', 'bottle3', '80ml'],
                                          ['DMF', 'jar0', '150ml']]
        self.substance_container_volume = substance_container_volume
        # print(self.substance_container_volume)
        self.dataframe_filename = dataframe_filename
        self.reaction_df = pd.read_excel(self.dataframe_filename, sheet_name='Robot', usecols='R:V')
        self.pd_output = pd.DataFrame(columns=['reaction_id',
                                               'event_id',
                                               'plate_number',
                                               'plate_id_on_breadboard',
                                               'container_id',
                                               'substance',
                                               'transfer_volume',
                                               ])
        self.reaction_plates = pd.DataFrame()
        self.containers_per_plate = containers_per_plate

    def correct_order(self):
        pass

    def _yield_plates(self):
        _df = self.reaction_df.copy()
        yield _df[:self.containers_per_plate]
        _df = _df[self.containers_per_plate:]

    def creat_events(self):
        # print('plate_id')
        for plate_id in range(self.reaction_df.shape[0] // self.containers_per_plate):
            # print(plate_id)
            this_plate = tuple(self._yield_plates())
            # print(this_plate)
            for enum, substance in enumerate(this_plate[0].columns):
                # print(this_plate[0].columns)
                for container_id in this_plate[0][substance].index:
                    event_id = container_id + \
                               enum * self.containers_per_plate + \
                               plate_id * self.containers_per_plate * this_plate[0].shape[1]

                    transfer_volume = this_plate[0][substance][container_id]
                    _dict = {'event_id': event_id,
                            "reaction_id": container_id + plate_id * self.containers_per_plate,

                             "plate_number": plate_id,
                             'plate_id_on_breadboard': plate_id % 3,
                             'container_id': container_id,
                             'substance': substance,
                             'transfer_volume': transfer_volume,
                             }
                    # self.volume_update(volume = transfer_volume, source_container = source_container, destination_container = destination_container)
                    # print(_dict)
                    self.pd_output = pd.concat([self.pd_output, pd.DataFrame(_dict, index=[event_id])],
                                               ignore_index=True)


reaction1 = EventInterpreter(dataframe_filename='multicomponent_reaction_input'
                                                '\\composition_input_20230110RF029_adj.xlsx')
reaction1.creat_events()

pd_output = reaction1.pd_output



