"""
This file defines a facility on the NMR-station platform, and 
describes the tube handling behaviour for each facility
Settings of the facilities are stored in facility_config.json
Here we provide a function to load the facility_config.json data 

KingLam Kwong
"""
# Third-party imports

# Standard library imports
from collections import namedtuple
import json
from typing import Callable

# current codespace imports


CartPos = namedtuple(
    "CartPos", ["x", "y", "z", "alpha", "beta", "gamma"]
)

class Facility:
    def __init__(self, pos: dict, tube_handling_strategy: Callable):
        self.pos = pos
        self.handle_tube = tube_handling_strategy

def load_facilities() -> dict:
    facilities = {}

    with open('facility_config.json') as file:
        config_data = json.load(file)
    
    for name, details in config_data.items():
        position_map = {key: CartPos(*value) for key, value in details["pos"].itmes()}
        tube_handling_strategy = getattr(globals(), details["handle_tube"])
        facilities[name] = Facility(position_map, tube_handling_strategy)
    
    return facilities