import pickle, re, csv, os


with open('multicomponent_reaction\\event_list_chem_backup_0322_first_half.pickle', 'rb') as f:
    transfer_list = pickle.load(f)

with open('multicomponent_reaction\\event_list_chem.pickle', 'rb') as f:
    transfer_list_later = pickle.load(f)

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

aa= list(split_by_plate(transfer_list))

bb = list(split_by_plate(transfer_list_later))

list_of_plate_barcode = ['16','17','19','22','23','34','18','20','21','03','09','11']

transfer_list_all = transfer_list[:1094] + transfer_list_later[1094:]

cc = list(split_by_plate(transfer_list_all))


fields=['plate_code',
        'experiment_name',
        'start_time_unix',
        'start_time_datetime',
        'finish_time_unix',
        'finish_time_datetime',
        'pipetting_event_id',
        'note']
data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'
path = 'multicomp-reactions\\2023-03-20-run01\\pipetter_io\\run_info_0322_new.csv'
with open(data_folder + path, 'a', newline='') as f:
        f.write(', '.join(fields) + '\n')

for count, list_of_one_plate in enumerate(cc):

    a = list_of_one_plate[0].event_label[-5:]

    # get event id from string
    starting_event_id = re.findall(r'\d+', list_of_one_plate[0].event_label)[0]
    ending_event_id = re.findall(r'\d+', list_of_one_plate[-1].event_label)[0]

    ## string format: 'start_time_unix, start_time_datetime, finish_time_unix, finish_time_datetime'
    start_finish_string = f'{list_of_plate_barcode[count]}, ' \
                          f'multicomponent_0320, ' \
                          f'{int(list_of_one_plate[0].event_start_time_utc)}, ' \
                          f'{list_of_one_plate[0].event_start_time_datetime[:-7]}, ' \
                          f'{int(list_of_one_plate[-1].event_finish_time)}, ' \
                          f'{list_of_one_plate[-1].event_finish_time_datetime[:-7]}, ' \
                          f"'{starting_event_id}-{ending_event_id}', \n"
    print(start_finish_string)
    print(count)

    with open(data_folder + path, 'a', newline='') as f:
        f.write(start_finish_string)

    print(f'file {path} saved')


with open('multicomponent_reaction\\event_list_chem_0322_ALL_good.pickle', 'wb') as f:
    pickle.dump(transfer_list_all, f)