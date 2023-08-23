"""
workflow:
1. initiate hardware
2. generate event list for detecting surface height of stock solutions
3. run events for surface detection, get liquid surface heights and write to excel
4. generate event list for pipetting
"""
import logging, copy, time, pickle, re, importlib, json, os, PySimpleGUI as sg, pandas as pd, numpy as np
import zeus, pipetter, planner as pln, breadboard as brb, prepare_reaction as prep

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'
# C:\Yankai\Dropbox\robochem

def setup_logger():
    # better logging format in console
    class CustomFormatter(logging.Formatter):
        grey = "\x1b[38;20m"
        yellow = "\x1b[33;20m"
        red = "\x1b[31;20m"
        bold_red = "\x1b[31;1m"
        reset = "\x1b[0m"
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

        FORMATS = {
            logging.DEBUG: grey + format + reset,
            logging.INFO: yellow + format + reset,
            logging.WARNING: yellow + format + reset,
            logging.ERROR: red + format + reset,
            logging.CRITICAL: bold_red + format + reset
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    # create logger with 'main'
    logger = logging.getLogger('main')
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(brb.STATUS_PATH + 'main.log')
    fh.setLevel(logging.INFO)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(CustomFormatter())
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

logger = setup_logger()



def initiate_hardware() -> (zeus.ZeusModule, pipetter.Gantry, pipetter.Pipetter):
    # initiate zeus
    zm = zeus.ZeusModule(id=1)
    time.sleep(3)
    logger.info("zeus is loaded as: zm")

    # initiate gantry
    gt = pipetter.Gantry(zeus=zm)
    time.sleep(3)
    logger.info("gantry is loaded as: gt")
    # gt.configure_grbl() # This only need to be done once.
    gt.home_xy()
    if gt.xy_position == (0, 0):
        logger.info("gantry is homed")

    # initiate pipetter
    pt = pipetter.Pipetter(zeus=zm, gantry=gt)
    time.sleep(2)
    logger.info("pipetter is loaded as: pt")

    return zm, gt, pt

def sort_events_according_to_aspiration_volume(event_list_chem):

        output_list = []

        # # group event by plate id
        # get mask for change of plate id
        split_index = []
        for index in range(1, len(event_list_chem)):
            if event_list_chem[index].destination_container.id['plate_id'] != \
                event_list_chem[index-1].destination_container.id['plate_id']:
                split_index.append(index)
        # group event by mask
        events_grouped_by_plate_id = np.split(event_list_chem, split_index)

        # group and sort events in each plate according to substance
        for index, plate_event in enumerate(events_grouped_by_plate_id):
            # get mask for change of substance
            split_index = []
            for index in range(1, len(plate_event)):
                if plate_event[index].substance != \
                    plate_event[index-1].substance:
                    split_index.append(index)
            # group event by mask
            split_list = np.split(plate_event, split_index)

            for event_of_one_substance in split_list:
                # sort events in each group according to aspiration volume
                sorted_list = sorted(event_of_one_substance, key=lambda x: x.aspirationVolume, reverse=True)
                output_list.extend(sorted_list)

        return output_list

def turn_off_lld(event_list):
    for event in event_list:
        event.asp_lld = 0

def sort_events_by_substance_volume(event_list):
    event_list_sorted = []

    # split the event list by substance
    split_index = []
    for index in range(1, len(event_list)):
        if event_list[index].substance != \
                event_list[index-1].substance:
            split_index.append(index)
    split_list = np.split(event_list, split_index)

    for event_of_one_substance in split_list:
        # sort events in each group according to aspiration volume
        sorted_list = sorted(event_of_one_substance, key=lambda x: x.transfer_volume, reverse=True)
        event_list_sorted.extend(sorted_list)

    return event_list_sorted

if __name__ == '__main__':

    ## initiate hardware
    zm, gt, pt = initiate_hardware()

    excel_path_before_treatment, \
    plate_barcodes, \
    reaction_temperature,\
    plate_barcode_for_dilution = prep.GUI_get_excel_path_plate_barcodes_temperature_etc()
    logger.info(f"excel_path_before_treatment: {excel_path_before_treatment}\n" \
    f"plate_barcodes: {plate_barcodes}\n" \
    f"reaction_temperature: {reaction_temperature}\n" \
    f"plate_barcode_for_dilution: {plate_barcode_for_dilution}")

    excel_path_for_conditions, _ = prep.prepare_excel_file_for_reaction(reaction_temperature=reaction_temperature,
                                                                        excel_path=excel_path_before_treatment,
                                                                        plate_barcodes=plate_barcodes,
                                                                        plate_barcodes_for_dilution=plate_barcode_for_dilution)
    # is_check_volume = prep.GUI_choose_if_check_surface_height()
    stock_solution_containers = \
        pln.assign_stock_solutions_to_containers_and_check_volume(excel_path = excel_path_for_conditions,
                                                                  check_volume_by_pipetter = True, pt=pt)

    df_reactions_grouped_by_plate_id,  substance_addition_sequence = prep.extract_reactions_df_to_run(excel_path_for_conditions)


    event_list_to_run = pln.generate_event_list_new(excel_path_for_conditions = excel_path_for_conditions,
                        df_reactions_grouped_by_plate_id = df_reactions_grouped_by_plate_id,
                        substance_addition_sequence = substance_addition_sequence,
                        stock_solution_containers = stock_solution_containers,
                        asp_lld = 0)

    event_list_to_run_sorted = sort_events_by_substance_volume(event_list_to_run)

    assert len(event_list_to_run_sorted) > 0, "event_list_to_run_sorted is empty"

    # event_list_to_run_sorted1 = [i for i in event_list_to_run_sorted if i.substance == 'H']
    #
    for event in event_list_to_run_sorted:
        if event.source_container.solvent == 'hbrhac1v1':
            event.liquidClassTableIndex=31
            event.tip_type='300ul'
            print(event.transfer_volume)
    #
    # do multicomponent reactions
    pln.run_events_chem(zm=zm, pt=pt,
                        event_list= event_list_to_run_sorted,
                        prewet_tip=False,
                        pause_after_every_plate_min = 10, test_mode=False)


    # ## save a event to local pickle file
    # event_temp = event_list_to_run_sorted[0]
    # with open('event_temp.pickle', 'wb') as f:
    #     pickle.dump(event_temp, f)

    # ## load a event from local pickle file
    # nd.close_lid()
    # time.sleep(1)
    # gt.move_xy((-144, -339))
    # # zm.move_z(600)
    # nd.open_lid()
    # time.sleep(1)
    # gt.move_xy((-544, -339))
    # zm.move_z(800)
    # time.sleep(1)
    # zm.move_z(600)
    # time.sleep(0.5)
    # gt.move_xy((-144, -339))
    # nd.close_lid()