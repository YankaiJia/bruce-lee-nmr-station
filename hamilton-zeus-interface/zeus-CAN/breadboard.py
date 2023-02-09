"""
container: vial_2ml, bottle_20ml

plate: plate0, plate1, plate2, plate3, plate4, palte5, plate6, plate7

"""

from dataclasses import dataclass
import numpy as np
import copy

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
    # contaniner geometry table for zeus
    index: int
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
    containerGeometryTableIndex: int
    lldSearchPosition: str
    safety_margin_for_lldsearch_position: int
    has_liquid: str
    # coordinate
    xy: tuple = (0, 0)


vial_2ml = Container(
    name='vial_2ml',
    index=0,
    diameter=98,
    bottomHeight=0,
    bottomSection=10000,
    bottomPosition=2172,
    immersionDepth=10,
    leavingHeight=20,
    jetHeight=130,
    startOfHeightBottomSearch=30,
    dispenseHeightAfterBottomSearch=80,

    liquid_volume=0,
    volume_max=2000,
    area=75.56,
    min_z=floor_z - 2172,
    top_z=32,
    containerGeometryTableIndex=0,
    lldSearchPosition='auto',
    safety_margin_for_lldsearch_position=40,
    has_liquid='water',
    # coordinate
    xy=(0, 0)
)

well_bio = Container(
    name='well_bio',
    index=0,
    diameter=98,
    bottomHeight=0,
    bottomSection=10000,
    bottomPosition=2172,
    immersionDepth=10,
    leavingHeight=20,
    jetHeight=130,
    startOfHeightBottomSearch=30,
    dispenseHeightAfterBottomSearch=80,

    liquid_volume=0,
    volume_max=2000,
    area=75.56,
    min_z=floor_z - 2172,
    top_z=32,
    containerGeometryTableIndex=0,
    lldSearchPosition='auto',
    safety_margin_for_lldsearch_position=40,
    has_liquid='water',
    # coordinate
    xy=(0, 0)
)

bottle_20ml = Container(
    name='bottle_20ml',
    index=0,
    diameter=98,
    bottomHeight=0,
    bottomSection=10000,
    bottomPosition=2172,
    immersionDepth=10,
    leavingHeight=20,
    jetHeight=130,
    startOfHeightBottomSearch=30,
    dispenseHeightAfterBottomSearch=80,

    liquid_volume=0,
    volume_max=2000,
    area=75.56,
    min_z=floor_z - 2172,
    top_z=32,
    containerGeometryTableIndex=0,
    lldSearchPosition='auto',
    safety_margin_for_lldsearch_position=40,
    has_liquid='water',
    # coordinate
    xy=(0, 0)
)
jar_100ml = Container(
    name = 'jar_100ml',
    index=0,
    diameter=98,
    bottomHeight=0,
    bottomSection=10000,
    bottomPosition=2172,
    immersionDepth=10,
    leavingHeight=20,
    jetHeight=130,
    startOfHeightBottomSearch=30,
    dispenseHeightAfterBottomSearch=80,

    liquid_volume=0,
    volume_max=2000,
    area=75.56,
    min_z=floor_z - 2172,
    top_z=32,
    containerGeometryTableIndex=0,
    lldSearchPosition='auto',
    safety_margin_for_lldsearch_position=40,
    has_liquid='water',
    # coordinate
    xy=(0, 0)
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
                                                             topleft=(-7, -255.5),
                                                             topright=(-111.5, -255.5),
                                                             bottomleft=(-7, -321),
                                                             bottomright=(-111.5, -321))
plate1_vial_2mL_coordinates = generate_container_coordinates(Nwells=(6, 9),
                                                             topleft=(-7, -255.5),
                                                             topright=(-111.5, -255.5),
                                                             bottomleft=(-7, -321),
                                                             bottomright=(-111.5, -321))
plate2_vial_2mL_coordinates = generate_container_coordinates(Nwells=(6, 9),
                                                             topleft=(-7, -255.5),
                                                             topright=(-111.5, -255.5),
                                                             bottomleft=(-7, -321),
                                                             bottomright=(-111.5, -321))
plate3_vial_2mL_coordinates = generate_container_coordinates(Nwells=(6, 9),
                                                             topleft=(-7, -255.5),
                                                             topright=(-111.5, -255.5),
                                                             bottomleft=(-7, -321),
                                                             bottomright=(-111.5, -321))
plate4_vial_2mL_coordinates = generate_container_coordinates(Nwells=(6, 9),
                                                             topleft=(-7, -255.5),
                                                             topright=(-111.5, -255.5),
                                                             bottomleft=(-7, -321),
                                                             bottomright=(-111.5, -321))
plate1_well_bio_coordinates = generate_container_coordinates(Nwells=(6, 9),
                                                             topleft=(-7, -255.5),
                                                             topright=(-111.5, -255.5),
                                                             bottomleft=(-7, -321),
                                                             bottomright=(-111.5, -321))
plate5_bottle_20ml_coordinates = generate_container_coordinates(Nwells=(6, 9),
                                                                topleft=(-7, -255.5),
                                                                topright=(-111.5, -255.5),
                                                                bottomleft=(-7, -321),
                                                                bottomright=(-111.5, -321))
plate6_bottle_20ml_coordinates = generate_container_coordinates(Nwells=(6, 9),
                                                                topleft=(-7, -255.5),
                                                                topright=(-111.5, -255.5),
                                                                bottomleft=(-7, -321),
                                                                bottomright=(-111.5, -321))
plate7_jar_100ml_coordinates = generate_container_coordinates(Nwells=(6, 9),
                                                              topleft=(-7, -255.5),
                                                              topright=(-111.5, -255.5),
                                                              bottomleft=(-7, -321),
                                                              bottomright=(-111.5, -321))

# return a list of container(object) in one plate.
# this function puts container geometry and container coordinate together for one specific plate
def container_list(container_geom, container_coordinates) -> list:
    container_list = []
    for i in range(len(container_coordinates)):
        container_geom.xy = container_coordinates[i]
        container_temp = copy.copy(container_geom)
        container_list.append(container_temp)
    return container_list

class Plate:
    def __init__(self, containers=None):
        if containers == None:
            self.containers = []
        else:
            self.containers = containers

    def add_container(self, container_list: list):
        for container in container_list:
            if container not in self.containers:
                self.containers.append(container)

def plate_on_breadboard():
    plate0 = Plate()
    plate0.add_container(container_list(vial_2ml, plate0_vial_2mL_coordinates))
    plate1 = Plate()
    plate1.add_container(container_list(vial_2ml, plate1_vial_2mL_coordinates))
    plate2 = Plate()
    plate2.add_container(container_list(vial_2ml, plate2_vial_2mL_coordinates))
    plate3 = Plate()
    plate3.add_container(container_list(well_bio, plate1_well_bio_coordinates))
    plate4 = Plate()
    plate4.add_container(container_list(bottle_20ml, plate4_vial_2mL_coordinates))
    plate5 = Plate()
    plate5.add_container(container_list(bottle_20ml, plate5_bottle_20ml_coordinates))
    plate6 = Plate()
    plate6.add_container(container_list(bottle_20ml, plate6_bottle_20ml_coordinates))
    plate7 = Plate()
    plate7.add_container(container_list(jar_100ml, plate7_jar_100ml_coordinates))

    return plate0, plate1, plate2, plate3, plate4, plate5, plate6, plate7


def main():
    pass


if __name__ == "__main__":
    main()
