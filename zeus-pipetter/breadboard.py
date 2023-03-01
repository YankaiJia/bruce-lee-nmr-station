"""
container: vial_2ml, well_bio, bottle_20ml, jar_100ml

plate: plate0, plate1, plate2, plate3, plate4, palte5, plate6, plate7
       plate0: vial_2mL
       plate1: vial_2mL
       plate2: vial_2mL
       plate3: well_bio
       plate4: bottle_20ml
       plate5: bottle_20ml
       plate6: jar_100ml
       plate7: jar_100ml
"""
import logging

# create logger
module_logger = logging.getLogger('pipette_calibration.breadboard')


def some_function():
    module_logger.error('received a call to "some_function"')


from dataclasses import dataclass
import numpy as np
import copy
import json

floor_z = 2210


@dataclass
class DeckGeometry:
    index: int
    endTraversePosition: int
    beginningofTipPickingPosition: int
    positionofTipDepositProcess: int


@dataclass
class Container:
    name: str
    container_id: str
    # contaniner geometry table for zeus
    containerGeometryTableIndex: int
    container_shape: str
    diameter: int
    bottomHeight: int
    bottomSection: int
    bottomPosition: int
    immersionDepth: int
    leavingHeight: int
    jetHeight: int
    startOfHeightBottomSearch: int
    dispenseHeightAfterBottomSearch: int
    # for liquid transfer
    liquid_volume: float
    volume_max: float
    area: float  # container's horizontal cross-section area is in square mm
    min_z: float  # location of container's bottom above the floor in mm
    top_z: float  # height of container
    safety_margin_for_lldsearch_position: int
    solvent: str
    # coordinate
    xy: tuple = (0, 0)

    substance: str = ' '
    substance_density: float = 1.0


vial_2ml = Container(
    name='vial_2ml',
    containerGeometryTableIndex=0,
    container_shape = 'cylindrical',
    diameter=98,
    bottomHeight=0,
    bottomSection=10000,
    bottomPosition=2191,
    immersionDepth=10,
    leavingHeight=20,
    jetHeight=130,
    startOfHeightBottomSearch=30,
    dispenseHeightAfterBottomSearch=80,

    liquid_volume=0,
    volume_max=2000,
    area=75.7,  # wall thickness=0.88mm, OD=11.58, ID = 11.58-0.88*2
    min_z=floor_z - 2172,
    top_z=32,
    safety_margin_for_lldsearch_position=40,
    solvent='',
    xy=(0, 0),  # coordinate
    substance='',
    substance_density=1.0,
    container_id=''
)

well_bio = Container(
    name='well_bio',
    containerGeometryTableIndex=4,
    container_shape='cylindrical',
    diameter=68,
    bottomHeight=0,
    bottomSection=10000,
    bottomPosition=2180,
    immersionDepth=20,
    leavingHeight=20,
    jetHeight=60,
    startOfHeightBottomSearch=30,
    dispenseHeightAfterBottomSearch=80,

    liquid_volume=0,
    volume_max=200,
    area=6.8 * 6.8 * 3.14 / 4,  # container's horizontal cross-section area is in square mm
    min_z=3.4,  # location of container's bottom above the floor in mm
    top_z=12,
    safety_margin_for_lldsearch_position=40,
    solvent='',
    xy=(0, 0),  # coordinate
    substance='',
    substance_density=1.0,
    container_id=''

)

bottle_20ml = Container(
    name='bottle_20ml',
    containerGeometryTableIndex=1,
    container_shape='cylindrical',
    diameter=255,
    bottomHeight=0,
    bottomSection=10000,
    bottomPosition=2165,
    immersionDepth=10,
    leavingHeight=30,
    jetHeight=130,
    startOfHeightBottomSearch=20,
    dispenseHeightAfterBottomSearch=50,

    liquid_volume=0,
    volume_max=20000,
    area=510.7,
    min_z=(floor_z - 2165) / 10,
    top_z=62,
    safety_margin_for_lldsearch_position=40,
    solvent='',
    xy=(0, 0),  # coordinate
    substance='',
    substance_density=1.0,
    container_id=''

)
jar_100ml = Container(
    name='jar_100ml',
    containerGeometryTableIndex=2,
    container_shape='cylindrical',
    diameter=520,  # ID of tube
    bottomHeight=0,
    bottomSection=10000,
    bottomPosition=2070,
    immersionDepth=40,
    leavingHeight=40,
    jetHeight=130,
    startOfHeightBottomSearch=50,
    dispenseHeightAfterBottomSearch=50,

    liquid_volume=0,
    volume_max=100000,
    area=2123.7,
    min_z=(floor_z - 2070) / 10,
    top_z=70,
    safety_margin_for_lldsearch_position=40,
    solvent='',
    xy=(0, 0),  # coordinate
    substance='',
    substance_density=1.0,
    container_id=''
)

tube_1500ul = Container(
    name='tube_1500ul',
    containerGeometryTableIndex=5,
    container_shape='conical_1500ul',
    diameter=88,
    bottomHeight=195,
    bottomSection=0,
    bottomPosition=2175,
    immersionDepth=20,
    leavingHeight=20,
    jetHeight=80,
    startOfHeightBottomSearch=30,
    dispenseHeightAfterBottomSearch=80,

    liquid_volume=0,
    volume_max=2000,
    area=8.8 * 8.8 * 3.14 / 4,
    min_z=floor_z - 2172,
    top_z=32,
    safety_margin_for_lldsearch_position=40,
    solvent='',
    xy=(0, 0),  # coordinate
    substance='',
    substance_density= 1.0,
    container_id=''
)

balance_cuvette = Container(
    name='balance_cuvette',
    containerGeometryTableIndex=3,
    container_shape='cylindrical',
    diameter=400,  # ID of tube
    bottomHeight=0,
    bottomSection=10000,
    bottomPosition=1590,
    immersionDepth=20,
    leavingHeight=20,
    jetHeight=100,
    startOfHeightBottomSearch=30,
    dispenseHeightAfterBottomSearch=100,

    liquid_volume=0,
    volume_max=80000,
    area=40*40, # in mm^2
    min_z=(floor_z - 1590) / 10,
    top_z=70,
    safety_margin_for_lldsearch_position=40,
    solvent='water',
    xy=(-810, -200),  # coordinate
    substance='water',
    substance_density= 1.0,
    container_id='balance_cuvette'
)

def generate_container_coordinates(Nwells, topleft, topright, bottomleft, bottomright):
    '''generate coordinates for all wells of a  plate from coordinates of corner wells.'''
    # left_side_wells

    coordinates = []
    xs = np.linspace(topleft[0], bottomleft[0], Nwells[0])
    ys = np.linspace(topleft[1], bottomleft[1], Nwells[0])
    left_side_wells = np.stack((xs, ys)).T

    # right side wells
    xs = np.linspace(topright[0], bottomright[0], Nwells[0])
    ys = np.linspace(topright[1], bottomright[1], Nwells[0])
    right_side_wells = np.stack((xs, ys)).T

    wells = []
    for i in range(Nwells[0]):
        xs = np.linspace(left_side_wells[i, 0], right_side_wells[i, 0], Nwells[1])
        ys = np.linspace(left_side_wells[i, 1], right_side_wells[i, 1], Nwells[1])
        wells.append(np.stack((xs, ys)).T)
    well_positions = np.vstack(wells)

    for well_index in range(well_positions.shape[0]):
        coordinates.append(tuple(well_positions[well_index, :]))

    return coordinates


x_length_vial_2ml = 103
y_length_vial_2ml = 65
plate0_vial_2mL_coordinates = generate_container_coordinates(Nwells=(6, 9),
                                                             topleft=(-7, -255),
                                                             topright=(-7 - x_length_vial_2ml, -255),
                                                             bottomleft=(-7, -255 - y_length_vial_2ml),
                                                             bottomright=(
                                                             -7 - x_length_vial_2ml, -255 - y_length_vial_2ml))
plate1_vial_2mL_coordinates = generate_container_coordinates(Nwells=(6, 9),
                                                             topleft=(-157, -256),
                                                             topright=(-157 - x_length_vial_2ml, -256),
                                                             bottomleft=(-157, -256 - y_length_vial_2ml),
                                                             bottomright=(
                                                             -157 - x_length_vial_2ml, -256 - y_length_vial_2ml))
plate2_vial_2mL_coordinates = generate_container_coordinates(Nwells=(6, 9),
                                                             topleft=(-307, -256),
                                                             topright=(-307 - x_length_vial_2ml, -256),
                                                             bottomleft=(-307, -256 - y_length_vial_2ml),
                                                             bottomright=(
                                                             -307 - x_length_vial_2ml, -256 - y_length_vial_2ml))
# plate7_vial_2ml_coordinates = generate_container_coordinates(Nwells=(6, 9),
#                                                              topleft=(-458, -157),
#                                                              topright=(-458 - x_length_vial_2ml, -157),
#                                                              bottomleft=(-458, -157- y_length_vial_2ml),
#                                                              bottomright=(-458 - x_length_vial_2ml, -157 - y_length_vial_2ml))
x_length_tube_1500ul = 88.5
y_length_tube_1500ul = 56
plate7_tube_1500ul_coordinates = generate_container_coordinates(Nwells=(4, 5),
                                                                topleft=(-465, -161),
                                                                topright=(-465 - x_length_tube_1500ul, -161),
                                                                bottomleft=(-465, -161 - y_length_tube_1500ul),
                                                                bottomright=(-465 - x_length_tube_1500ul,
                                                                             -161 - y_length_tube_1500ul))

x_length_well_bio = 99
y_length_well_bio = 63
plate3_well_bio_coordinates = generate_container_coordinates(Nwells=(8, 12),
                                                             topleft=(-457, -258),
                                                             topright=(-457 - x_length_well_bio, -258),
                                                             bottomleft=(-457, -258 - y_length_well_bio),
                                                             bottomright=(
                                                             -457 - x_length_well_bio, -258 - y_length_well_bio))
x_length_bottle_20ml = 85
y_length_bottle_20ml = 28
plate4_bottle_20ml_coordinates = generate_container_coordinates(Nwells=(2, 4),
                                                                topleft=(-15, -175),
                                                                topright=(-15 - x_length_bottle_20ml, -175),
                                                                bottomleft=(-15, -175 - y_length_bottle_20ml),
                                                                bottomright=(-15 - x_length_bottle_20ml,
                                                                             -175 - y_length_bottle_20ml))
plate5_bottle_20ml_coordinates = generate_container_coordinates(Nwells=(2, 4),
                                                                topleft=(-164, -175),
                                                                topright=(-164 - x_length_bottle_20ml, -175),
                                                                bottomleft=(-164, -175 - y_length_bottle_20ml),
                                                                bottomright=(-164 - x_length_bottle_20ml,
                                                                             -175 - y_length_bottle_20ml))
plate6_jar_100ml_coordinates = [(-325, -189), (-388, -189)]


# return a list of container(object) in one plate.
# this function puts container geometry and container coordinate together for one specific plate
def container_list(container_geom: object, container_coordinates) -> list:
    # input exp: vial_2ml, plate0_vial_2mL_coordinates
    container_list = []
    for container_index in range(len(container_coordinates)):
        container_geom.xy = container_coordinates[container_index]
        container_temp = copy.copy(container_geom)
        container_list.append(container_temp)
    return container_list


class Plate:
    def __init__(self, plate_id: str, containers=None):

        if containers == None:
            self.containers = []
        else:
            self.containers = containers

        self.plate_id = plate_id
        self.logger = logging.getLogger('pipette_calibration.breadboard.Plate')
        self.logger.debug(f'A Plate object is created with plate_id: {plate_id}.')

    def add_container(self, container_list: list):
        for container in container_list:
            if container not in self.containers:
                self.containers.append(container)

    def add_substance_to_container(self,
                                   substance_name: str,
                                   container_id: int,
                                   liquid_volume: int,
                                   solvent: str,
                                   substance_density: float):
        self.containers[container_id].substance = substance_name
        self.containers[container_id].liquid_volume = liquid_volume
        self.containers[container_id].solvent = solvent
        self.containers[container_id].substance_density = float(substance_density)


    def assign_container_id(self, plate_id: int):
        for container_index in range(len(self.containers)):
            # print(f'brb.plate_list[{plate_id}].containers[{container_index}]')
            self.containers[container_index].container_id = f'brb.plate_list[{plate_id}].containers[{container_index}]'


def plate_on_breadboard():
    plate0 = Plate(plate_id='plate0')
    plate0.add_container(container_list(vial_2ml, plate0_vial_2mL_coordinates))
    plate0.assign_container_id(plate_id=0)

    plate1 = Plate(plate_id='plate1')
    plate1.add_container(container_list(vial_2ml, plate1_vial_2mL_coordinates))
    plate1.assign_container_id(plate_id=1)

    plate2 = Plate(plate_id='plate2')
    plate2.add_container(container_list(vial_2ml, plate2_vial_2mL_coordinates))
    plate2.assign_container_id(plate_id=2)

    plate3 = Plate(plate_id='plate3')
    plate3.add_container(container_list(well_bio, plate3_well_bio_coordinates))
    plate3.assign_container_id(plate_id=3)

    plate4 = Plate(plate_id='plate4')
    plate4.add_container(container_list(bottle_20ml, plate4_bottle_20ml_coordinates))
    plate4.assign_container_id(plate_id=4)

    plate5 = Plate(plate_id='plate5')
    plate5.add_container(container_list(bottle_20ml, plate5_bottle_20ml_coordinates))
    plate5.assign_container_id(plate_id=5)

    plate6 = Plate(plate_id='plate6')
    plate6.add_container(container_list(jar_100ml, plate6_jar_100ml_coordinates))
    plate6.assign_container_id(plate_id=6)

    plate7 = Plate(plate_id='plate7')
    plate7.add_container(container_list(tube_1500ul, plate7_tube_1500ul_coordinates))
    plate7.assign_container_id(plate_id=7)

    module_logger.info('All plates in breadboard are created.')

    return plate0, plate1, plate2, plate3, plate4, plate5, plate6, plate7


plate0, plate1, plate2, plate3, plate4, plate5, plate6, plate7 = plate_on_breadboard()
plate_list = [plate0, plate1, plate2, plate3, plate4, plate5, plate6, plate7]

container_vial_2ml = plate0.containers[0]
container_well_bio = plate3.containers[0]
container_bottle_20ml = plate4.containers[0]
container_jar_100ml = plate6.containers[0]

containers: list = [container_vial_2ml, container_well_bio, container_bottle_20ml, container_jar_100ml]

bottle0 = plate4.containers[0]
bottle1 = plate4.containers[1]
bottle2 = plate4.containers[2]
bottle3 = plate4.containers[3]
bottle4 = plate4.containers[4]
bottle5 = plate4.containers[5]
bottle6 = plate4.containers[6]
bottle7 = plate4.containers[7]
bottle8 = plate5.containers[0]
bottle9 = plate5.containers[1]
bottle10 = plate5.containers[2]
bottle11 = plate5.containers[3]
bottle12 = plate5.containers[4]
bottle13 = plate5.containers[5]
bottle14 = plate5.containers[6]
bottle15 = plate5.containers[7]
jar0 = plate6.containers[0]
jar1 = plate6.containers[1]


def generate_deck_coordinates(Nwells, topleft, topright, bottomleft, bottomright):
    '''generate coordinates for all wells of a well plate from coordinates of corner wells.'''
    # left_side_wells
    xs = np.linspace(topleft[0], bottomleft[0], Nwells[0])
    ys = np.linspace(topleft[1], bottomleft[1], Nwells[0])
    left_side_wells = np.stack((xs, ys)).T

    # right side wells
    xs = np.linspace(topright[0], bottomright[0], Nwells[0])
    ys = np.linspace(topright[1], bottomright[1], Nwells[0])
    right_side_wells = np.stack((xs, ys)).T

    wells = []
    for i in range(Nwells[0]):
        xs = np.linspace(left_side_wells[i, 0], right_side_wells[i, 0], Nwells[1])
        ys = np.linspace(left_side_wells[i, 1], right_side_wells[i, 1], Nwells[1])
        wells.append(np.stack((xs, ys)).T)
    return np.vstack(wells)


def create_deck(template_well, Nwells, topleft, topright, bottomleft, bottomright):
    well_positions = generate_deck_coordinates(Nwells, topleft, topright, bottomleft, bottomright)
    plate = {'wells': list()}
    for well_index in range(well_positions.shape[0]):
        plate['wells'].append(template_well.copy())
        plate['wells'][-1]['xy'] = list(well_positions[well_index, :])
    return plate


def load_new_tip_tack(rack_reload):
    # tip_rack = {}
    with open('data/tip_rack.json') as json_file:
        tip_rack = json.load(json_file)

    tip = {'300ul': {'tip_vol': 300,
                     'xy': (300, -100),
                     'tipTypeTableIndex': 4,
                     'deckGeometryTableIndex': 0,
                     'ZeusTraversePosition': 880,
                     'exists': True,
                     'substance': 'None'
                     },
           '1000ul': {'tip_vol': 1000,
                      'xy': (-296.5, -32.5),
                      'tipTypeTableIndex': 6,
                      'deckGeometryTableIndex': 1,
                      'ZeusTraversePosition': 880,
                      'exists': True,
                      'substance': 'None'
                      },
           '50ul': {'tip_vol': 50,
                    'xy': (300, -100),
                    'tipTypeTableIndex': 2,
                    'deckGeometryTableIndex': 0,
                    'ZeusTraversePosition': 880,
                    'exists': True,
                    'substance': 'None'
                    },
           }
    if rack_reload == '300ul':
        tip_rack['300ul'] = create_deck(template_well=tip['300ul'],
                                        Nwells=(8, 12),
                                        topleft=(-158.5, -44.5),
                                        topright=(-257.5, -44.5),
                                        bottomleft=(-158.5, -107),
                                        bottomright=(-257.5, -107))
    if rack_reload == '1000ul':
        tip_rack['1000ul'] = create_deck(template_well=tip['1000ul'],
                                         Nwells=(8, 12),
                                         topleft=(-296.5, -32.5),
                                         topright=(-396, -32.5),
                                         bottomleft=(-296.5, -95),
                                         bottomright=(-396, -95))
    if rack_reload == '50ul':
        tip_rack['50ul'] = create_deck(template_well=tip['50ul'],
                                       Nwells=(8, 12),
                                       topleft=(-33.5, -44.5),
                                       topright=(-132.5, -44.5),
                                       bottomleft=(-33.5, -107),
                                       bottomright=(-132.5, -107))

    with open('data/tip_rack.json', 'w', encoding='utf-8') as f:
        json.dump(tip_rack, f, ensure_ascii=False, indent=4)

    return tip_rack


## run this ONLY when changing new tip rack.
# load_new_tip_tack(rack_reload = '300ul')
# load_new_tip_tack(rack_reload = '1000ul')
# load_new_tip_tack(rack_reload = '50ul')


def main():
    print("This is main.")

    ## run this ONLY when changing new tip rack.
    load_new_tip_tack(rack_reload = '300ul')
    load_new_tip_tack(rack_reload = '1000ul')
    load_new_tip_tack(rack_reload = '50ul')


if __name__ == "__main__":
    main()
