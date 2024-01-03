import csv
import logging, copy, asyncio
import pyautogui, json
pyautogui.FAILSAFE = False

# create logger
module_logger = logging.getLogger('pipette_calibration.breadboard')

import zeus, pipetter, planner as pln, sound, breadboard as brb, prepare_reaction as prep, nanodrop
import time, os, pickle

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'
time_for_measuring_one_spectrum = 5

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

        event_here.transfer_volume = 2 # volume 4 ul generally,including ethanol, water
        # event_here.transfer_volume = 6 # volume 6 ul for DCM
        # event_here.transfer_volume = 2 # volume 3 ul for 1,2-DCE
        # event_here.transfer_volume = 30 # volume 30 ul for 1,2-DCE with O-ring



        event_here.lld = 0
        event_here.tip_type = '50ul'
        event_here.liquidClassTableIndex = 40 ## LC 40 is only for nanodrop, it is based on 27 (dioxane)
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
    gt.move_to_idle_position()
    time.sleep(0.2)
    nd.close_lid()
    time.sleep(0.1)
    pt.discard_tip()
    gt.move_to_idle_position()
    time.sleep(0.2)


class ZeusError(Exception):
    pass

async def pick_tip():

    print("picking up tips...")

    if zm.tip_on_zeus=='':
        pt.pick_tip('50ul')
    elif zm.tip_on_zeus != '':
        pt.discard_tip()
        time.sleep(2)
        pt.pick_tip('50ul')

    await asyncio.sleep(0.1)

async def aspirate_next_sample(event=None):

    assert event != None, "Event for asp is incorrect!!"

    print('gt moving to the vial')

    zm.move_z(880)
    gt.move_xy(event.source_container.xy)

    await asyncio.sleep(0.1)

    print(f'aspirating liquid... {event.source_container.id}')

    try:
        # print(f'Aspiration volume for zeus: {int(round(transfer_event.aspirationVolume * 10))}')
        zm.aspiration(aspirationVolume=int(round(event.transfer_volume*5*10)),  # volume in 0.1 ul,## transfer_volume is doubled, this is to avoid bubbles.
                             containerGeometryTableIndex=event.asp_containerGeometryTableIndex,
                             deckGeometryTableIndex=event.asp_deckGeometryTableIndex,
                             liquidClassTableIndex=event.liquidClassTableIndex,
                             qpm=event.asp_qpm,
                             lld=event.asp_lld,
                             liquidSurface=event.source_container.liquid_surface_height,
                             lldSearchPosition=event.source_container.liquid_surface_height - 50,
                             mixVolume=event.asp_mixVolume,
                             mixFlowRate=event.asp_mixFlowRate,
                             mixCycles=event.asp_mixCycles)
        print(
            f'DEBUG:liquid surface height in source container: {event.source_container.liquid_surface_height} ')

        # Replace this sleep with a proper check. Why do you even need a sleep if next function is zeus.wait_until...???
        # time.sleep(2)
        zm.wait_until_zeus_responds_with_string('GAid')

    except ZeusError:
        if zm.zeus_error_code(zm.r.received_msg) == '81':
            # Empty tube detected during aspiration
            gt.logger.info('ZEUS ERROR: Empty tube during aspiration. Dispensing and trying again.')
            time.sleep(2)
            exit()

    await asyncio.sleep(0.1)

    gt.move_to_idle_position()

    await asyncio.sleep(0.1)

def dispense_sample(event=None):
    try:
        pt.dispense_liquid(event)
    except:
        gt.move_to_idle_position()
        print("Pipetting error happened!")
        sound.beep_for_tip_changing()
        sound.beep_for_tip_changing()
        time.sleep(1)


    # event.execute_event()
    # beep()
async def measure_one_spectrum_by_pyautogui(sample_name: str):

    print(f'working on sample #{sample_name}')
    ## activate nanodrop software window
    pyautogui.moveTo(2700, 510)  # Find where button.png appears on the screen and click it.
    pyautogui.click()
    # input sample name
    pyautogui.moveTo(4943, 168)
    pyautogui.click()
    pyautogui.press('backspace', presses=5)
    pyautogui.write(sample_name, interval=0.1)
    await asyncio.sleep(0.2)
    # start measurement
    pyautogui.moveTo(2604, 111)  # Find where button.png appears on the screen and click it.
    pyautogui.click()
    print('measuring spectrum')
    print(f'timestampe here: {time.strftime("%Y-%m-%d %H:%M:%S")}')
    await asyncio.sleep(time_for_measuring_one_spectrum)

async def main(events = None, only_do_ids = ()):

    assert events != None, "event list is incorrect!"

    if len(only_do_ids) > 0:
        events_for_measurement= [events[i] for i in only_do_ids]
    else:
        events_for_measurement = events

    print('cleaning pedestal...')
    await asyncio.gather(nd.flush_pedestal())
    await asyncio.gather(nd.dry_pedestal())
    print('aspirating the first sample...')
    await asyncio.gather(pick_tip(),
                         aspirate_next_sample(events_for_measurement[0]))

    for num, event in enumerate(events_for_measurement):

        vial_id = event.source_container.id['container_id']

        nd.open_lid()
        time.sleep(1)
        nd.close_air()
        print('dispensing sample...')
        dispense_sample(event)
        print('Moving and closing...')
        gt.move_to_idle_position()
        nd.close_lid()
        # time.sleep(1)

        # To make sure the lid had enough time to close fully
        #  and the wetting has equilibrated
        # time.sleep(1)

        await asyncio.gather(measure_one_spectrum_by_pyautogui(str(vial_id)))
        await asyncio.gather(pick_tip())
        time.sleep(3) # this is added for autolength measurements
        if num != len(events_for_measurement) - 1:
            await asyncio.gather(aspirate_next_sample(events_for_measurement[num+1]),
                                 nd.flush_pedestal(),
                                 nd.dry_pedestal())
        elif num == len(events_for_measurement) - 1:
            print("all measurements are done!!")
        sound.beep_for_measurement()

    print('cleaning pedestal...')
    ## flush the pedestal
    await asyncio.gather(nd.flush_pedestal())

    ## dry the pedestal
    await asyncio.gather(nd.dry_pedestal())
    await asyncio.gather(nd.dry_pedestal())
    await asyncio.gather(nd.dry_pedestal())

    for i in range(5):
        sound.beep_for_measurement()
        time.sleep(0.5)

    print("all measurements are done!!")
    nd.close_all()

def gt_move_to_pedestal():
    pd_xy = brb.nanodrop_pedestal.xy
    nd.open_lid()
    time.sleep(2)
    gt.move_xy(pd_xy)

if __name__ == '__main__':
    nd = nanodrop.Nanodrop()
    nd.close_lid()
    time.sleep(2)

    zm, gt, pt = initiate_hardware()

    events_for_measurement = construct_liquid_transfer_events_for_measurement()

    # specify source containers, USE ONLY WHEN NECESSARY
    # for event in events_for_measurement:
    #     event.source_container = brb.plate_list[6].containers[1]

    # a = [0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,13
    # #wash the nanodrop and d2
    # await asyncio.gather(nd.flush_pedestal())
    # await asyncio.gather(nd.flush_pedestal())
    # # # dry the pedestal
    # await asyncio.gather(nd.dry_pedestal())
    # time.sleep(0.5)
    # await asyncio.gather(nd.dry_pedestal())


    #
    # # # # only run after initiation of the nanodrop software and blanking
    # asyncio.run(main(events = events_for_measurement,
    #                      only_do_ids= tuple()))
    #
    # This is for discrete index
    # asyncio.run(main(events=events_for_measurement,
    #                  only_do_ids=tuple([0,1,2,3,4,5]*10)))

    # This is for continuous index
    # starting_vial_num = 35
    # ending_vial_num = 54
    # only_do_ids = tuple(range(starting_vial_num, ending_vial_num))
    # asyncio.run(main(events=events_for_measurement,
    #                  only_do_ids= only_do_ids))



# for i in range(10):
#     nd.close_lid()
#     time.sleep(1.5)
#     nd.open_lid()
#     time.sleep(1.5)


for event in events_for_measurement:
    event.transfer_volume = 2
    event.liquidClassTableIndex = 40



#
