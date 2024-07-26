import logging

# create logger
module_logger = logging.getLogger('pipette_calibration.breadboard')

from dataclasses import dataclass
import numpy as np, copy, json, os

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'

CONFIG_PATH = 'config//miniPi//'

# load config file from json
with open(CONFIG_PATH + 'brb_lt.json', 'r') as config_file:
    config_brb = json.load(config_file)

ZeusTraversePosition = config_brb['ZeusTraversePosition']


floor_z = -117.5
bottom_z_of_vial_2ml = -116

source_substance_containers: list = []

@dataclass
class Container:

    asp_height:float
    xy: tuple = (0, 0)
    asp_height = 0


vial_2ml = Container(asp_height=-112)

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
                                                            topleft=config_brb['plate0'][0],
                                                            topright= config_brb['plate0'][1],
                                                            bottomleft= config_brb['plate0'][2],
                                                            bottomright= config_brb['plate0'][3])

def container_list(container_geom: object, container_coordinates) -> list:
    # input exp:vial_2ml, plate0_vial_2mL_coordinates
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
        liquid_volume_in_container = (self.containers[container_id].bottomPosition - liquid_surface_height) / 10 \
                                     * self.containers[container_id].area  # in ul. 1 mm^3 is 1 ul.
        self.containers[container_id].substance = substance_name
        self.containers[container_id].liquid_surface_height = liquid_surface_height
        self.containers[container_id].liquid_volume = round(liquid_volume_in_container, 1)
        self.containers[container_id].solvent = solvent
        self.containers[container_id].substance_density = float(substance_density)
        self.logger.info(f'Container {container_id} is filled with {substance_name} in {solvent} solvent. ')

    def assign_container_id(self, plate_id: int):
        for container_index in range(len(self.containers)):
            # print(f'brb.plate_list[{plate_id}].containers[{container_index}]')
            self.containers[container_index].id = {'plate_id': plate_id, 'container_id': container_index}


def plate_on_breadboard():
    plate0_containers = container_list(vial_2ml, plate0_vial_2mL_coordinates)
    plate0 = Plate(plate_id='plate0', containers=plate0_containers)
    plate0.assign_container_id(plate_id=0)

    module_logger.info('All plates in breadboard are created.')
    print('All plates in breadboard are created.')

    return plate0

plate0 = plate_on_breadboard()
# plate_list = [plate0]

@dataclass
class Tube:
    xy: tuple
    disp_height: float

class Tube_rack:
    def __init__(self):
        self.tubes = list()
        tube1 = Tube(xy = (-320, -20), disp_height = -100)
        tube2 = Tube(xy = (-320, -30), disp_height = -100)
        tube3 = Tube(xy = (-320, -40), disp_height = -100)
        tube4 = Tube(xy = (-320, -50), disp_height = -100)
        self.tubes.append(tube1)
        self.tubes.append(tube2)
        self.tubes.append(tube3)
        self.tubes.append(tube4)

tube_rack = Tube_rack()

@dataclass
class Deck:
    beginningofTipPickPosition: int


deckgeom_1000ul = Deck(beginningofTipPickPosition=config_brb['beginningofTipPickPosition'],)

deckgeom_trash_can = Deck(beginningofTipPickPosition=config_brb['beginningofTipPickPosition'],)

deckGeometryTableIndex = {'1000ul': 1}

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
    with open(CONFIG_PATH + 'tip_rack.json') as json_file:
        tip_rack = json.load(json_file)

    tip = {'1000ul': {'tip_vol': 1000,
                      'xy': (-163.5, -108.5), # dummy coordinates
                      'tipTypeTableIndex': 6,
                      'deckGeometryTableIndex': 1,
                      'ZeusTraversePosition': ZeusTraversePosition,
                      'exists': True,
                      'substance': 'None'
                      }
           }

    if rack_reload == '1000ul':
        print(f"the1000ul rack corner coords: {config_brb['rack_1000ul'][0]},{config_brb['rack_1000ul'][1]},{config_brb['rack_1000ul'][2]},{config_brb['rack_1000ul'][3]}")

        tip_rack['1000ul'] = create_deck(template_well=tip['1000ul'],
                                         Nwells=(8, 12),
                                         topleft=config_brb['rack_1000ul'][0],
                                         topright= config_brb['rack_1000ul'][1],
                                         bottomleft=config_brb['rack_1000ul'][2],
                                         bottomright=config_brb['rack_1000ul'][3],
                                         )

    with open(CONFIG_PATH + 'tip_rack.json', 'w', encoding='utf-8') as f:
        json.dump(tip_rack, f, ensure_ascii=False, indent=4)
        print("tip_rack.json is updated.")

    return tip_rack

def mark_next_n_tip_as_used(tip_type, n):
    with open(CONFIG_PATH + 'tip_rack.json') as json_file:
        tip_rack = json.load(json_file)
    i = 0

    while i < n:
        for tip in tip_rack[tip_type]['tips']:
            if tip['exists'] == True:
                tip['exists'] = False
                break
        i+=1

    # save the revised tip_rack to json
    with open(CONFIG_PATH + 'tip_rack.json', 'w', encoding='utf-8') as f:
        json.dump(tip_rack, f, ensure_ascii=False, indent=4)


with open(CONFIG_PATH + 'tip_rack.json') as json_file:
    tip_rack = json.load(json_file)

tip_rack_1000ul = tip_rack['1000ul']



if __name__ == "__main__":

    print('This is main.')

    load_new_tip_rack(rack_reload ='1000ul')
    module_logger.info('New tip rack: 1000ul is loaded.')
