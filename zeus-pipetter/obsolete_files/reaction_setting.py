import time

def do_calibration_on_events(zm,pt,calibration_event_list,logger):
    '''This function is used to calibrate the pipetting of substances.'''
    results_for_calibration = []
    if zm.tip_on_zeus:
        pt.discard_tip()
    starting_index = 32
    ending_index = len(calibration_event_list)
    # ending_index = 3
    for event_index in range(starting_index, ending_index):
        if zm.tip_on_zeus != calibration_event_list[event_index].tip_type:
            pt.change_tip(calibration_event_list[event_index].tip_type)
            logger.info(f'The tip is changed to : {calibration_event_list[event_index].tip_type}')

        result = pt.pipetting_to_balance_and_weight_n_times(transfer_event=calibration_event_list[event_index], n_times=10)
        results_for_calibration.append(result)

        time.sleep(1)
        logger.info(f"Performed one measurement: {calibration_event_list[event_index].event_label}")
        logger.info(f'Result: {result}')
        # check tip type and change the tip if needed
        if event_index != len(calibration_event_list) - 1:  # check if this is the last event.
            if calibration_event_list[event_index].substance != calibration_event_list[event_index + 1].substance:
                pt.discard_tip()
        time.sleep(0.5)
    pt.discard_tip()
    return results_for_calibration

def run_events_bio(zm, pt, logger, event_list):
    if zm.tip_on_zeus:
        pt.discard_tip()

    starting_index = 169
    ending_index = len(event_list)
    for event_index in range(starting_index, ending_index):
        if zm.tip_on_zeus != event_list[event_index].tip_type:
            pt.change_tip(event_list[event_index].tip_type)
            logger.info(f'The tip is changed to : {event_list[event_index].tip_type}')

        pt.transfer_liquid(event_list[event_index])

        time.sleep(0.5)
        logger.info(f"Performed one event: {event_list[event_index].event_label}")

        # check tip type and change tip if needed
        if event_index != len(event_list) - 1:  # check if this is the last event.
            if event_list[event_index].substance != event_list[event_index + 1].substance:
                pt.change_tip(event_list[event_index + 1].tip_type)
        time.sleep(0.5)
    pt.discard_tip()