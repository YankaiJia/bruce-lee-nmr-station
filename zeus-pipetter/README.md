# An automatic liquid transfer system by mounting a Zeus pipetter onto a XY gantry

## Introduction ##
This project is a  liquid transfer system that uses a Zeus pipetter and a XY 
gantry to transfer liquid between specified containers.

## Modules explanation ##

#### Zeus.py ####
Communication between the Zeus and the computer is done through a CAN bus. This module includes
Zeus initialization, CAN bus initialization, and class to change the liquid class parameters.

#### gantry.py ####  
The XY gantry is placed on a breadboard. The gantry is controlled by an Arduino running GRBL firmware.
The gantry is controlled by sending G-code commands to the Arduino. The Zeus is mounted on the gantry.

#### breadboard.py #### 
objects on the breadboard:
* **plates**, inside which there are different containers including vials (2mL), 
wells (200 uL), tubes (1.5 mL), bottles (20 mL) and jars (100 mL).
* **racks** for tips
* **balance**
* **trash bin**

#### pipetter.py #### 
Combination of Zeus and the gantry. 

#### planner.py #### 
The planner is responsible for planning the liquid transfer. It takes an excel file as input and generates 
dataframes for each transfer. The transfer events are then interpreted to objects. Later, the objects are sent to 
pipetter.py to execute the transfer.

#### main.py ####
The main program controls the whole system. 
