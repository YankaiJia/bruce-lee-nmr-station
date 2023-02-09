from dataclasses import dataclass

import breadboard

plate0, plate1, plate2, plate3, plate4, plate5, plate6, plate7 = breadboard.plate_on_breadboard()

@dataclass
class TransferEvent:

    source: dict
    destination: dict
    tip_type: str

    # for aspiration
    aspirationVolume: int
    asp_containerGeometryTableIndex: int
    asp_deckGeometryTableIndex: int
    asp_liquidClassTableIndex: int
    asp_qpm: int
    asp_lld: int
    asp_lldSearchPosition: int
    asp_liquidSurface: int

    # for dispensing
    dispensingVolume: int
    disp_containerGeometryTableIndex: int
    disp_deckGeometryTableIndex: int
    disp_liquidClassTableIndex: int
    disp_lld: int
    disp_lldSearchPosition: int
    disp_liquidSurface: int
    searchBottomMode: int

    #default values
    asp_mixVolume: int = 0
    asp_mixFlowRate: int = 0
    asp_mixCycles:int = 0
    disp_mixVolume: int = 0
    disp_mixFlowRate: int = 0
    disp_mixCycles: int = 0
