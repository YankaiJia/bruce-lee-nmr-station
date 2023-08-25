import logging, copy
import pyautogui
import pydirectinput

# create logger
module_logger = logging.getLogger('pipette_calibration.breadboard')

import zeus, pipetter, planner as pln, breadboard as brb, prepare_reaction as prep, nanodrop
import time, os, pickle

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'

def initiate_hardware() -> (zeus.ZeusModule, pipetter.Gantry, pipetter.Pipetter):
    # initiate zeus
    zm = zeus.ZeusModule(id=1)
    time.sleep(3)
    module_logger.info("zeus is loaded as: zm")

    # initiate gantry
    gt = pipetter.Gantry(zeus=zm)
    time.sleep(3)
    module_logger.info("gantry is loaded as: gt")
    # gt.configure_grbl() # This only need to be done once.
    gt.home_xy()
    if gt.xy_position == (0, 0):
        module_logger.info("gantry is homed")

    # initiate pipetter
    pt = pipetter.Pipetter(zeus=zm, gantry=gt)
    time.sleep(2)
    module_logger.info("pipetter is loaded as: pt")

    return zm, gt, pt

def construct_liquid_transfer_events_for_measurement():
    # mn.data_folder
    with open(data_folder + 'pipetter_files\\event_template.pickle', 'rb') as f:
        event = pickle.load(f)

    event_list = []
    source_plate = brb.plate1

    for container in source_plate.containers:
        container.liquid_surface_height = 2180
        container.liquid_volume = 1000

        event_here = copy.deepcopy(event)
        event_here.source_container = container
        event_here.destination_container = brb.nanodrop_pedestal
        event_here.transfer_volume = 8
        event_here.lld = 0
        event_here.tip_type = '50ul'
        event_here.liquidClassTableIndex = 40 ## 40 is for nanodrop based 27 (dioxane)
        event_here.asp_containerGeometryTableIndex = 0 # this is for 2-ml vial
        event_here.disp_containerGeometryTableIndex = 6 # this is for nanodrop pedestal

        event_list.append(event_here)

    return event_list


def run_one_event_chem(pt: object, event=None):

    nd.open_lid()
    time.sleep(0.5)

    if zm.tip_on_zeus=='':
        pt.pick_tip('50ul')
    else:
        pt.discard_tip()
        pt.pick_tip('50ul')
    pt.transfer_liquid(event)
    time.sleep(0.1)
    pt.discard_tip()


    # event.execute_event()
    # beep()
def measure_one_spectrum_by_pyautogui(sample_name: str):

    ## activate nanodrop software window
    pydirectinput.moveTo(2700, 510)  # Find where button.png appears on the screen and click it.
    pydirectinput.click()
    time.sleep(0.1)

    # input sample name
    pydirectinput.moveTo(4943, 168)
    pydirectinput.click()
    time.sleep(0.1)
    pydirectinput.press('backspace', presses=5)
    time.sleep(0.1)
    pydirectinput.write(sample_name, interval=0.1)
    time.sleep(0.1)

    # start measurement
    pydirectinput.moveTo(2604, 111)  # Find where button.png appears on the screen and click it.
    time.sleep(0.1)
    pydirectinput.click()

    return True

def measure_spectra(events_for_measurement, pass_event_list):
    for index, event in enumerate(events_for_measurement):
        if index in pass_event_list:
            print(f'event {index} is passed')
            continue
        print(f'event {index} is being measured...')
        nd.open_lid()
        time.sleep(1)
        run_one_event_chem(pt=pt, event=event)
        nd.close_lid()
        time.sleep(0.5)
        measure_one_spectrum_by_pyautogui(sample_name= str(index))
        time.sleep(6) ## wait for 6 seconds for the measurement to finish
        nd.flush_pedestal()
        time.sleep(0.2)
        nd.dry_pedestal()
        time.sleep(0.2)
        # nd.flush_pedestal()
        # time.sleep(0.2)
        # nd.dry_pedestal()
        # time.sleep(0.2)
        print(f'event {index} is done.')



if __name__ == '__main__':

    nd = nanodrop.Nanodrop()
    zm, gt, pt = initiate_hardware()

    events_for_measurement = construct_liquid_transfer_events_for_measurement()
    # nd.open_lid()
    # run_one_event_chem(pt=pt, event= events_for_measurement[0])
    measure_spectra(events_for_measurement=events_for_measurement,
                    pass_event_list= [])



