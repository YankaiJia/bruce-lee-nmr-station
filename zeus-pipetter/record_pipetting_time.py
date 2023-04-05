import pickle, re, csv, os
import PySimpleGUI as sg



# use GUI to specify Excel path
def load_excel_path_by_pysimplegui():
    sg.theme('BrightColors')  # Add a touch of color
    working_directory = os.getcwd()
    # All the stuff inside your window.
    layout = [[sg.Text('Select Excel file for reactions')],
              [sg.InputText(key="-FILE_PATH-"),
               sg.FileBrowse(initial_folder=working_directory,
                             file_types=(("Pickle Files", "*.pickle"), ("All Files", "*.*")))],
              [sg.Submit(), sg.Cancel()]]

    # Create the Window
    window = sg.Window('Select Excel file for reactions',
                       layout,
                       size=(600, 200),
                       font=('Helvetica', 14), )

    # Event Loop to process "events" and get the "values" of the inputs
    event, values = window.read()
    # print(event, values[0])
    window.close()
    print(f"Excel file for reactions is selected: {values['-FILE_PATH-']}")
    return values['-FILE_PATH-']

path_for_event_status_record = load_excel_path_by_pysimplegui()
# path_for_event_status_record = 'C:\\Users\\Chemiluminescence\\OneDrive\\roborea\\' \
#                                'zeus-pipetter\\multicomponent_reaction\\event_list_chem.pickle'

with open(path_for_event_status_record, 'rb') as f:
    transfer_list = pickle.load(f)

# for event in transfer_list:
#     print(event.event_label)
#     print(event.is_event_conducted)
#     print(event.event_start_time_datetime)

def split_by_plate(transfer_list):
    """A generator to divide a sequence into chunks of n units."""
    index = 0

    index_start = 0
    index_finish = 0

    while index < len(transfer_list)-1:
        # print(f'index: {index}')
        if transfer_list[index].event_label[-5:] != transfer_list[index + 1].event_label[-5:]:
            index_finish = index
            yield transfer_list[index_start:index_finish + 1]

            index_start = index_finish + 1
        index += 1

event_list_in_each_plate = list(split_by_plate(transfer_list[270:]))

len_of_event_list_in_each_plate = sum([len(event_list) for event_list in event_list_in_each_plate])
print(f'len_of_event_list_in_each_plate: {len_of_event_list_in_each_plate}')
event_list_in_each_plate = event_list_in_each_plate + [transfer_list[len_of_event_list_in_each_plate:]]

# event_list_in_each_plate = [transfer_list]

def save_cvs():

    for list in event_list_in_each_plate:
        for event in list:
            if event.is_event_conducted:
                print(event.event_label)
                print(event.is_event_conducted)
                print(event.event_start_time_datetime)

    list_of_plate_barcode = ['21', '22']

    fields=['plate_code',
            'experiment_name',
            'start_time_unix',
            'start_time_datetime',
            'finish_time_unix',
            'finish_time_datetime',
            'pipetting_event_id',
            'reaction_id',
            'excel_path',
            'note']
    # path = 'C:\\Users\\Chemiluminescence\\OneDrive' \
    #        '\\roborea\\zeus-pipetter\\multicomponent_reaction\\0323\\0323_record.csv'

    path = 'C:\\Users\\Chemiluminescence\\OneDrive\\roborea\\' \
            'zeus-pipetter\\multicomponent_reaction\\csvs\\event_status_record.csv'

    with open(path, 'a', newline='') as f:
            f.write(', '.join(fields) + '\n')

    print(path)

    for count, list_of_one_plate in enumerate(event_list_in_each_plate):

        # a = list_of_one_plate[0].event_label[-5:]

        # get event id from string
        starting_event_id = re.findall(r'\d+', list_of_one_plate[0].event_label)[0]
        ending_event_id = re.findall(r'\d+', list_of_one_plate[-1].event_label)[0]

        ## string format: 'start_time_unix, start_time_datetime, finish_time_unix, finish_time_datetime'
        start_finish_string = f'{list_of_plate_barcode[count]}, ' \
                              f'multicomponent_0320, ' \
                              f'{int(list_of_one_plate[0].event_start_time_utc)}, ' \
                              f'{list_of_one_plate[0].event_start_time_datetime}, ' \
                              f'{int(list_of_one_plate[-1].event_finish_time)}, ' \
                              f'{list_of_one_plate[-1].event_finish_time_datetime}, ' \
                              f"'{starting_event_id}-{ending_event_id}', \n"
        print(f'Finished this plate: {start_finish_string}')

        with open(path, 'a', newline='') as f:
            f.write(start_finish_string)

        print(f'file {path} saved')

save_cvs()

def convert_unix_time_to_datetime(unix_time):
    import datetime
    return datetime.datetime.fromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S')


def convert_datetime_to_unix_time(datetime_string):
    import datetime
    return int(datetime.datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S').timestamp())

# convert_unix_time_to_datetime(1679909368)

convert_datetime_to_unix_time('2023-04-03 23:42:49')
# 2023-04-03 23:42:49

def print_info():
    for num, event in enumerate(transfer_list):
        # get numbers from string by regular expression
        id = re.findall(r'\d+', event.destination_container.container_id)

        print(num, event.event_label)
        print(f'This pipetting is for reaction_id: {str(id[-1])}')

        print('source container    :', event.source_container.container_id)
        print('desination container:', event.destination_container.container_id)
        print(' ')