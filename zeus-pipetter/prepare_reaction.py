import json, math, os, openpyxl, pandas as pd, shortuuid, PySimpleGUI as sg, logging

import config

module_logger = logging.getLogger('main.prepare_reaction')

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'
# excel_path_for_reactions = 'C:\\Users\\Chemiluminescence\\Dropbox\\robochem\\data\\simple-reactions\\2023-07-17-run01\\2023-07-17-run01.xlsx'

## use pySimpleGUI to get the excel_path, plate_barcodes, temperature
def GUI_get_excel_path_plate_barcodes_temperature_etc():
    sg.theme('DarkAmber')  # Add a touch of color
    # sg.theme('BrightColors')  # Add a touch of color
    temp_path = 'C:\\Users\\Chemiluminescence\\Dropbox\\robochem\\data\\simple-reactions\\2023-07-17-run01\\2023-07-17-run01.xlsx'
    layout = [[sg.Text('Enter the path of the excel file:')],
              [sg.InputText(temp_path, key="-FILE_PATH-"),
               sg.FileBrowse(initial_folder=data_folder,
                             file_types=(("Excel Files", "*.xlsx"), ("All Files", "*.*")))],
              [sg.Text('Enter plate barcodes for pipetting, e.g.:50, 51, 52')],
              [sg.InputText('11,22,33', key="-PLATE_BARCODES-")],
              [sg.Text('Enter plate barcodes for dilution accordingly. The ORDER is essential.')],
              [sg.InputText( '44,55,66', key="-PLATE_DILUTION-")],
              [sg.Text('Enter the reaction temperature, e.g. 26')],
              [sg.InputText('26',key="-REACTION_TEMPERATURE-")],
              [sg.Submit(), sg.Cancel()]]

    window = sg.Window('Excel file path', layout,
                       size=(800, 500),
                       font=('Helvetica', 18), )

    event, values = window.read()
    window.close()

    excel_path = values['-FILE_PATH-']
    plate_barcodes = tuple([int(i) for i in values['-PLATE_BARCODES-'].split(',') if i!=''])
    reaction_temperature = int(values['-REACTION_TEMPERATURE-'])
    plate_barcodes_for_dilution = tuple([int(i) for i in values['-PLATE_DILUTION-'].split(',') if i!=''])

    assert reaction_temperature, 'Please enter the reaction temperature.'
    assert len(plate_barcodes) == len(plate_barcodes_for_dilution), \
        'The length of plate_barcodes and plate_barcodes_for_dilution should be the same.'
    assert list(set(plate_barcodes) & set(plate_barcodes_for_dilution)) == [], \
        "The plate barcodes for dilution should be different from the plate barcodes for pipetting."

    str_for_plate_barcodes = ''
    for index, plate_barcode in enumerate(plate_barcodes):
        if index < 3:
            str_for_plate_barcodes += f'{plate_barcode} @ breadboard slot {index}, dilute to {plate_barcodes_for_dilution[index]}\n'
        elif index >=3:
            str_for_plate_barcodes += f'{plate_barcode} @ breadboard slot {index},dilute to {plate_barcodes_for_dilution[index]}' \
                                      f', this is for the second round.\n'
    for  index in range(len(plate_barcodes), 6):
            str_for_plate_barcodes += f'Nothing @ slot {index}\n'

    ## make a second window to check the input
    layout1 = [[sg.Text('1. Please check the input:', text_color= 'red')],
            [sg.Text(f'excel_path: {excel_path}', font=("Helvetica", 8))],
            [sg.Text('2. Please check the plate_barcodes', text_color= 'red')],
            [sg.Text(str_for_plate_barcodes)],
            [sg.Text(f'3. Please check the reaction_temperature: {reaction_temperature}', text_color= 'red')],
            [sg.Text('Is the input correct?', size=(20, 1), font=("Helvetica", 25), text_color='red',
                     justification='center')],
            [sg.Button('Yes, proceed'), sg.Button('No, re-enter')]]

    window1 = sg.Window('Check the input', layout1,
                        size=(800, 500),
                        font=('Helvetica', 18))
    ## show window1 and read the values
    event, values = window1.read()
    # print(event, values)
    window1.close()
    # check if the "Yes, proceed" button is clicked
    if event == 'Yes, proceed':
        pass
    elif event == 'No, re-enter':
        ## if the "No, re-enter" button is clicked, re-enter the values
        excel_path, plate_barcodes, reaction_temperature, plate_barcodes_for_dilution\
            = GUI_get_excel_path_plate_barcodes_temperature_etc()

    return excel_path, plate_barcodes, reaction_temperature, plate_barcodes_for_dilution

## from gui the following paras should be obtained: excel_path, plate_barcodes, temperature
def prepare_excel_file_for_reaction(reaction_temperature ,
                                    excel_path: str ,
                                    plate_barcodes: tuple,
                                    plate_barcodes_for_dilution: tuple,
                                    sheet_name_for_run_info:str = config.sheet_name_for_run_info):
    ## if there is no backup sheet, create one
    wb = openpyxl.load_workbook(excel_path)
    reaction_sheet = wb['reactions_with_run_info']
    if 'reactions_backup' not in wb.sheetnames:
        target = wb.copy_worksheet(reaction_sheet)
        target.title = 'reactions_backup'
        wb.save(excel_path)
        # close the Excel file
        wb.close()

    ## open the 'reactions_with_run_info' sheet, and assign a uuid to each reaction
    df = pd.read_excel(excel_path, sheet_name=sheet_name_for_run_info, engine='openpyxl')

    ## set reaction_uuid and assign as index
    if 'reaction_uuid' not in df.columns:
        ## assign a uuid to each reaction
        df['reaction_uuid'] = df['reactions'].map(lambda x: str(shortuuid.uuid()))
        ## set 'unique_reaction_id' as index
        # ## print the index of the dataframe
        # print(df.index)
    else:
        # print('The reaction_uuid column already exists. Overwriting is not allowed.')
        module_logger.info('The reaction_uuid column already exists. Overwriting is not allowed.')

    # set the index
    df.set_index('reaction_uuid', inplace=True)

    ## preserve the original order of the columns
    columns_all = df.columns.tolist()
    substance_addition_sequence = [column for column in columns_all if 'vol#' in column]
    # print(f'substance_addition_sequence: {substance_addition_sequence}')

    # creat new columns
    columns_to_append = ['temperature','breadboard_plate_id','plate_barcode',
                         'container_id', 'status_of_substances',
                         'status_of_reaction',
                         'plate_barcodes_for_dilution']
    for column in columns_to_append:
        if column not in df.columns:
            if column == 'status_of_reaction':
                ## use json.dumps to convert a dict to a json string
                df[column] = [json.dumps({"status": ("not_started", 0)}) for i in range(len(df))]
            elif column == 'temperature':
                df[column] = reaction_temperature
            else:
                df[column] = None
            # df[column] = None if column != 'status_of_reaction' else tuple(('not_started',0)) # set the 'status_of_reaction' to 'not_started'
            print('column: ', column, ' is created.')
            module_logger.info(f'column: {column} is created.')

    # set the 'status_of_substance' to a json string: '{"substance1": ("not_started", timestamp), "substance2": ("not_started", timestamp)}'
    # print('substances_to_be_transferred: ', [i.split("#")[1] for i in df.columns if "vol#" in i])
    module_logger.info(f'substances_to_be_transferred: {[i.split("#")[1] for i in df.columns if "vol#" in i]}')

    for index, row in df.iterrows():
        df.at[index, 'status_of_substances'] = json.dumps({column[4:]: ("not_started", 0) for column in df.columns if 'vol#' in column
                                               and df.at[index, column] != 0})

    ##ensure the number of plate barcodes provided is sufficient
    assert len(plate_barcodes) >= math.ceil(len(df) / 54), 'The number of plates provided is not sufficient. '

    ## assign the breadboard_plate_id, plate_barcode, container id and dilution destination to each row
    breadboard_plate_id = [0, 1, 2, 0, 1, 2]
    for i in range(len(df) // 54 + 1):
        for j in range(54):
            if i * 54 + j < len(df):
                df.at[df.index[i * 54 + j], 'plate_barcode'] = plate_barcodes[i]
                df.at[df.index[i * 54 + j], 'breadboard_plate_id'] = breadboard_plate_id[i]
                df.at[df.index[i * 54 + j], 'container_id'] = j
                df.at[df.index[i * 54 + j], 'plate_barcodes_for_dilution'] = plate_barcodes_for_dilution[i]
            else:
                break


    ## TODO: add the dilution destination column

    ## dave df to excel sheet. "if_sheet_exists=" this argument is important to only overwrite one sheet
    with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists="replace") as writer:
        df.to_excel(writer, sheet_name=config.sheet_name_for_run_info, index=True, index_label='reaction_uuid')

    # print('The excel file is prepared for the reaction.')
    module_logger.info('The excel file is prepared for the reaction.')

    return excel_path, df
if __name__ == '__main__':
    excel_path, plate_barcodes, reaction_temperature, plate_barcodes_for_dilution\
        = GUI_get_excel_path_plate_barcodes_temperature_etc()

    _, df = prepare_excel_file_for_reaction(reaction_temperature=reaction_temperature,
                                    excel_path=excel_path,
                                    plate_barcodes=plate_barcodes,
                                    plate_barcodes_for_dilution=plate_barcodes_for_dilution,
                                    sheet_name_for_run_info=config.sheet_name_for_run_info)
