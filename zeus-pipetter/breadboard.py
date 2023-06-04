"""
container: vial_2ml, well_bio, bottle_20ml, jar_100ml, tube_1.5ml

plates plate0: vial_2ml, 54 vials
       plate1: vial_2ml, 54 vials
       plate2: vial_2ml, 54 vials
       plate3: well_bio, 96 wells
       plate4: bottle_20ml, 8 bottles
       palte5, bottle_20ml, 8 bottles
       plate6, jar_100ml, 2 jars
       plate7, tube_1500ul, 20 tubes

"""
import logging
# create logger
module_logger = logging.getLogger('pipette_calibration.breadboard')

from dataclasses import dataclass
import numpy as np
import copy
import json
import re

floor_z = 2220
ZeusTraversePosition = 880
balance_traverse_height = ZeusTraversePosition

bottom_z_of_vial_2ml = 2210
bottom_z_of_well_bio = 2190
bottom_z_of_bottle_20ml = 2175
bottom_z_of_jar_100ml = 2120
bottom_z_of_tube_1500ul = 2190
bottom_z_of_balance_cuvette = 1930

source_substance_containers: list = []

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
    liquid_surface_height = 0


vial_2ml = Container(
    name='vial_2ml',
    containerGeometryTableIndex=0,
    container_shape="cylindrical",
    # diameter = 98, ## old value 20230322
    diameter= 118, ## new value, 20230322
    bottomHeight=0,
    bottomSection=10000,
    bottomPosition=bottom_z_of_vial_2ml,
    immersionDepth=5,
    leavingHeight= 20,
    jetHeight=130,
    startOfHeightBottomSearch=0,
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
    container_id='')

well_bio = Container(
    name='well_bio',
    containerGeometryTableIndex=4,
    container_shape='cylindrical',
    diameter=68,
    bottomHeight=0,
    bottomSection=10000,
    bottomPosition=bottom_z_of_well_bio,
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
    container_id='')

bottle_20ml = Container(
    name='bottle_20ml',
    containerGeometryTableIndex=1,
    container_shape='cylindrical',
    diameter=255,
    bottomHeight=0,
    bottomSection=10000,
    bottomPosition=bottom_z_of_bottle_20ml,
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
    container_id='')

jar_100ml = Container(
    name='jar_100ml',
    containerGeometryTableIndex=2,
    container_shape='cylindrical',
    diameter=520,  # ID of tube
    bottomHeight=0,
    bottomSection=10000,
    bottomPosition=bottom_z_of_jar_100ml,
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
    container_id='')

tube_1500ul = Container(
    name='tube_1500ul',
    containerGeometryTableIndex=5,
    container_shape='conical_1500ul',
    diameter=88,
    bottomHeight=195,
    bottomSection=0,
    bottomPosition=bottom_z_of_tube_1500ul,
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
    container_id='')

balance_cuvette = Container(
    name='balance_cuvette',
    containerGeometryTableIndex=3,
    container_shape='cylindrical',
    diameter=400,  # ID of tube
    bottomHeight=0,
    bottomSection=10000,
    bottomPosition=bottom_z_of_balance_cuvette,
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
    xy=(-820, -240),  # coordinate
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

plate0_vial_2mL_coordinates = generate_container_coordinates(Nwells=(6, 9),
                                                             topleft=(-3, -232),
                                                             topright=(-107, -231),
                                                             bottomleft=(-3.0, -297.0),
                                                             bottomright=(-107.5, -296))

plate1_vial_2mL_coordinates = generate_container_coordinates(Nwells=(6, 9),
                                                             topleft=(-153, -232),
                                                             topright= (-257, -231),
                                                             bottomleft=(-153.5, -296.5),
                                                             bottomright=(-258.0, -297))

plate2_vial_2mL_coordinates = generate_container_coordinates(Nwells=(6, 9),
                                                             topleft=(-303.5, -232),
                                                             topright=(-408.5, -232.0),
                                                             bottomleft=(-303.5, -296.5),
                                                             bottomright=(-408.5, -297.0))
x_length_well_bio = 99
y_length_well_bio = 63
xy_topleft_well_bio_plate3 = (-453.5, -233)
plate3_well_bio_coordinates = generate_container_coordinates(Nwells=(8, 12),
                                                             topleft=(xy_topleft_well_bio_plate3 [0], xy_topleft_well_bio_plate3 [1]),
                                                             topright=(xy_topleft_well_bio_plate3 [0] - x_length_well_bio, xy_topleft_well_bio_plate3 [1]),
                                                             bottomleft=(xy_topleft_well_bio_plate3 [0], xy_topleft_well_bio_plate3 [1] - y_length_well_bio),
                                                             bottomright=(xy_topleft_well_bio_plate3 [0] - x_length_well_bio, xy_topleft_well_bio_plate3 [1] - y_length_well_bio))
x_length_bottle_20ml = 85
y_length_bottle_20ml = 28
xy_topleft_bottle_20ml_plate4 = (-10, -151)
plate4_bottle_20ml_coordinates = generate_container_coordinates(Nwells=(2, 4),
                                                                topleft=(xy_topleft_bottle_20ml_plate4[0], xy_topleft_bottle_20ml_plate4[1]),
                                                                topright=(xy_topleft_bottle_20ml_plate4[0] - x_length_bottle_20ml, xy_topleft_bottle_20ml_plate4[1]),
                                                                bottomleft=(xy_topleft_bottle_20ml_plate4[0], xy_topleft_bottle_20ml_plate4[1] - y_length_bottle_20ml),
                                                                bottomright=(xy_topleft_bottle_20ml_plate4[0] - x_length_bottle_20ml, xy_topleft_bottle_20ml_plate4[1] - y_length_bottle_20ml))
xy_topleft_bottle_20ml_plate5 = (-161, -152) # (x,y)
plate5_bottle_20ml_coordinates = generate_container_coordinates(Nwells=(2, 4),
                                                                topleft=(xy_topleft_bottle_20ml_plate5[0], xy_topleft_bottle_20ml_plate5[1]),
                                                                topright=(xy_topleft_bottle_20ml_plate5[0] - x_length_bottle_20ml, xy_topleft_bottle_20ml_plate5[1]),
                                                                bottomleft=(xy_topleft_bottle_20ml_plate5[0], xy_topleft_bottle_20ml_plate5[1] - y_length_bottle_20ml),
                                                                bottomright=(xy_topleft_bottle_20ml_plate5[0] - x_length_bottle_20ml, xy_topleft_bottle_20ml_plate5[1] - y_length_bottle_20ml))
plate6_jar_100ml_coordinates = [(-322, -165), (-385, -165)]

x_length_tube_1500ul = 88.5
y_length_tube_1500ul = 56
xy_topleft_tube_1500ul_plate7 = (-461.0, -137)
plate7_tube_1500ul_coordinates = generate_container_coordinates(Nwells=(4, 5),
                                                                topleft=(xy_topleft_tube_1500ul_plate7[0], xy_topleft_tube_1500ul_plate7[1]),
                                                                topright=(xy_topleft_tube_1500ul_plate7[0]- x_length_tube_1500ul, xy_topleft_tube_1500ul_plate7[1]),
                                                                bottomleft=(xy_topleft_tube_1500ul_plate7[0], xy_topleft_tube_1500ul_plate7[1] - y_length_tube_1500ul),
                                                                bottomright=(xy_topleft_tube_1500ul_plate7[0] - x_length_tube_1500ul, xy_topleft_tube_1500ul_plate7[1] - y_length_tube_1500ul))


# return a list of container(object) in one plate.
# this function puts geometry and coordinate of containers together into one specific plate
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

        self.containers = containers if containers is not None else []
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
                                   # liquid_volume: int, # calculate from liquid_surface_height not from user input
                                   solvent: str,
                                   substance_density: float,
                                   liquid_surface_height: int):
        liquid_volume_in_container = (self.containers[container_id].bottomPosition - liquid_surface_height)/10 \
                                     * self.containers[container_id].area # in ul. 1 mm^3 is 1 ul.
        self.containers[container_id].substance = substance_name
        self.containers[container_id].liquid_surface_height = liquid_surface_height
        self.containers[container_id].liquid_volume = round(liquid_volume_in_container, 1)
        self.containers[container_id].solvent = solvent
        self.containers[container_id].substance_density = float(substance_density)
        self.logger.info(f'Container {container_id} is filled with {substance_name} in {solvent} solvent. ')


    def assign_container_id(self, plate_id: int):
        for container_index in range(len(self.containers)):
            # print(f'brb.plate_list[{plate_id}].containers[{container_index}]')
            self.containers[container_index].id = {'plate_id':plate_id, 'container_id': container_index}

def plate_on_breadboard():
    plate0_containers = container_list(vial_2ml, plate0_vial_2mL_coordinates)
    plate0 = Plate(plate_id='plate0', containers=plate0_containers)
    plate0.assign_container_id(plate_id=0)

    plate1_containers = container_list(vial_2ml, plate1_vial_2mL_coordinates)
    plate1 = Plate(plate_id='plate1', containers=plate1_containers)
    plate1.assign_container_id(plate_id=1)

    plate2_containers = container_list(vial_2ml, plate2_vial_2mL_coordinates)
    plate2 = Plate(plate_id='plate2', containers=plate2_containers)
    plate2.assign_container_id(plate_id=2)

    plate3_containers = container_list(well_bio, plate3_well_bio_coordinates)
    plate3 = Plate(plate_id='plate3', containers=plate3_containers)
    plate3.assign_container_id(plate_id=3)

    plate4_containers = container_list(bottle_20ml, plate4_bottle_20ml_coordinates)
    plate4 = Plate(plate_id='plate4', containers=plate4_containers)
    plate4.assign_container_id(plate_id=4)

    plate5_containers = container_list(bottle_20ml, plate5_bottle_20ml_coordinates)
    plate5 = Plate(plate_id='plate5', containers=plate5_containers)
    plate5.assign_container_id(plate_id=5)

    plate6_containers = container_list(jar_100ml, plate6_jar_100ml_coordinates)
    plate6 = Plate(plate_id='plate6', containers=plate6_containers)
    plate6.assign_container_id(plate_id=6)

    plate7_containers = container_list(tube_1500ul, plate7_tube_1500ul_coordinates)
    plate7 = Plate(plate_id='plate7', containers=plate7_containers)
    plate7.assign_container_id(plate_id=7)

    module_logger.info('All plates in breadboard are created.')

    return plate0, plate1, plate2, plate3, plate4, plate5, plate6, plate7

plate0, plate1, plate2, plate3, plate4, plate5, plate6, plate7 = plate_on_breadboard()
plate_list = [plate0, plate1, plate2, plate3, plate4, plate5, plate6, plate7]



@dataclass
class Deck_para:
    index: int
    endTraversePosition: int
    beginningofTipPickingPosition: int
    positionofTipDepositProcess: int

deckgeom_300ul = Deck_para(index=0, endTraversePosition=ZeusTraversePosition,
                      beginningofTipPickingPosition=1500, positionofTipDepositProcess=1650)

deckgeom_1000ul = Deck_para(index=1, endTraversePosition=ZeusTraversePosition,
                       beginningofTipPickingPosition=1500, positionofTipDepositProcess=1650)

deckgeom_balance = Deck_para(index=2, endTraversePosition=balance_traverse_height,
                        beginningofTipPickingPosition=1530, positionofTipDepositProcess=2217)

deckgeom_50ul = Deck_para(index=3, endTraversePosition=ZeusTraversePosition,
                     beginningofTipPickingPosition=1500,positionofTipDepositProcess=1650)  # this is the same as 300ul tips


# decks are for pipetting tips
def generate_deck_coordinates(Nwells, topleft, topright, bottomleft, bottomright):

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
    deck = {'tips': list()}
    for well_index in range(well_positions.shape[0]):
        deck['tips'].append(template_well.copy())
        deck['tips'][-1]['xy'] = list(well_positions[well_index, :])
    return deck


def load_new_tip_rack(rack_reload):
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
    if rack_reload == '50ul':

        tip_rack['50ul'] = create_deck(template_well=tip['50ul'],
                                       Nwells=(8, 12),
                                       topleft=(-29, -21),
                                       topright=(-128, -21),
                                       bottomleft=(-29, -84),
                                       bottomright=(-128.5, -83.5)
                                       )

    if rack_reload == '300ul':

        tip_rack['300ul'] = create_deck(template_well=tip['300ul'],
                                        Nwells=(8, 12),
                                        topleft=(-154.5, -21.5),
                                        topright=(-253.5, -20.5),
                                        bottomleft=(-154.5, -84.5),
                                        bottomright=(-253.5, -83.5)
                                        )
    if rack_reload == '1000ul':
        x_gap_1000ul = 99.5
        y_gap_1000ul = 62.5
        xy_topleft_1000ul = (-293, -9)
        tip_rack['1000ul'] = create_deck(template_well=tip['1000ul'],
                                         Nwells=(8, 12),
                                         topleft=(-293.0, -9.0),
                                         topright=(-392, -9.0),
                                         bottomleft=(-292.5, -71.5),
                                         bottomright=(-391.5, -71.5)
                                         )

    with open('data/tip_rack.json', 'w', encoding='utf-8') as f:
        json.dump(tip_rack, f, ensure_ascii=False, indent=4)

    return tip_rack

with open('data/tip_rack.json') as json_file:
    tip_rack = json.load(json_file)

tip_rack_50ul = tip_rack['50ul']
tip_rack_300ul = tip_rack['300ul']
tip_rack_1000ul = tip_rack['1000ul']

@dataclass
class Liquid:
    name: str
    liquid_class_index: int
    density: float

    def __post_init__(self):
      pass

    def __repr__(self):
        return f'liquid_name: {self.name}, liquid_class_index: {self.liquid_class_index}'

if __name__ == "__main__":

    print('This is main.')

    ##run this ONLY when changing new tip rack.
    # load_new_tip_rack(rack_reload ='300ul')
    # module_logger.info('New tip rack: 300ul is loaded.')

    # load_new_tip_rack(rack_reload ='1000ul')
    # module_logger.info('New tip rack: 1000ul is loaded.')

    # load_new_tip_rack(rack_reload ='50ul')
    # module_logger.info('New tip rack: 50ul is loaded.')
