import os

import numpy as np
import pandas as pd

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'
craic_folder = data_folder + 'craic_microspectrometer_measurements/absorbance/'


def round_to_nearest(df_new, df_reference, column_names):
    """
    Round the values in the new dataframe to the nearest values in the reference dataframe.
    For example, if column in reference dataframe has values [0.1, 0.2, 0.3] and the new dataframe has values
    [5, 8, 11, 0.099999999999999999998, 11, 0.2000000000000000001, 0.35], the new dataframe values will be rounded to
    [5, 8, 11, 0.1, 0.2, 0.3. 11. 0.2, 0.35]
    and returned.

    Parameters
    ----------
    df_new: pd.DataFrame
        The dataframe with the new values that may be slightly different from the reference values due to rounding
        errors.

    df_reference: pd.DataFrame
        The dataframe with the reference values.

    column_names: list of str
        Only these columns will be changed in the new dataframe. Columns of same names are compared between
        the dataframes.

    Returns
    -------
    df_new: pd.DataFrame
        The dataframe with the new values rounded to the nearest values in the reference dataframe.
    """
    for column_name in column_names:
        new_values = df_new[column_name].to_numpy()
        unique_values_from_reference_df = df_reference[column_name].unique()
        for i, new_value in enumerate(new_values):
            for unique_value_from_reference in unique_values_from_reference_df:
                if np.isclose(new_value, unique_value_from_reference):
                    new_values[i] = unique_value_from_reference
        df_new[column_name] = new_values
    return df_new


def join_data_from_runs(run_names, round_on_columns=('ic001', 'am001', 'ald001', 'ptsa')):
    """
    Loads the `results/product_concentration.csv` from multiple runs and joins them into one dataframe.

    Parameters
    ----------
    run_names: list
        The names of the runs whose results will be loaded and joined. These names are the names of the subfolders
        of the data folder.

    round_on_columns
        The columns that will be rounded to the nearest values in the reference dataframe. This is done to avoid
        rounding errors when joining the dataframes.

    Returns
    -------
    df_result: pd.DataFrame
        The dataframe with the joined data. The sequence of the rows is the same as the sequence of the runs.
    """
    df_result = pd.read_csv(data_folder + run_names[0] + f'results/product_concentration.csv')
    df_result.drop('Unnamed: 0', inplace=True, axis=1)
    for run_name in run_names[1:]:
        df_temporary = pd.read_csv(data_folder + run_name + f'results/product_concentration.csv')
        df_temporary.drop('Unnamed: 0', inplace=True, axis=1)
        df_temporary = round_to_nearest(df_temporary, df_result, round_on_columns)
        df_result = df_result.append(df_temporary, ignore_index=True)
    return df_result


def organize_run_structure(experiment_name):
    """
    Automatically combine `run_info.csv`, `dilution_info.csv` and CRAIC plate database into
    a unified "run structure" table saved into `results/run_structure.csv`.

    The output table indicates for each condition the vial_id, the reaction plate id, the id of plate it was
    diluted into, and the CRAIC folder name that contains the spectra for this plate.

    Parameters
    ----------
    experiment_name: str
        The name of the experiment, e.g. `multicomp-reactions/2023-06-26-run01/`
    """
    global craic_folder
    global data_folder

    run_name = experiment_name.split('/')[1]

    # if there is not 'results' folder in the run folder, create it
    target_folder = data_folder + experiment_name + 'results'
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    # open dilution_info.csv as dataframe
    df_dilution = pd.read_csv(data_folder + experiment_name + 'dilution/dilution_info.csv')

    # open run_info.csv as dataframe
    # take care of the version of run_info:
    run_info_filename = data_folder + experiment_name + 'pipetter_io/run_info.csv'
    with open(run_info_filename, 'r') as f:
        first_line = f.readline()
    if first_line.startswith('#version: 1.00'):
        df_pipetter = pd.read_csv(run_info_filename, delimiter=',', header=0,
                                  names=['plate_code', 'experiment_name', 'start_time_unix',
                                         'start_time_string', 'finish_time_unix', 'finish_time_string', 'note'])
    else:
        df_pipetter = pd.read_csv(run_info_filename, delimiter=', ', header=None,
                                  names=['plate_code', 'experiment_name', 'start_time_unix',
                                         'start_time_string', 'finish_time_unix', 'finish_time_string', 'note'])

    # open the Excel file with the volumes, use first sheet
    df_structure = pd.read_excel(data_folder + experiment_name + f'{run_name}.xlsx', sheet_name=0)
    df_structure['vial_id'] = 0
    df_structure['reaction_plate_id'] = 0
    df_structure['diluted_plate_id'] = 0
    df_structure['craic_folder'] = ''
    df_structure['is_outlier'] = 0

    exp_names_craic = [f'multicomp_reactions_{run_name}']
    df_craic = pd.read_csv(craic_folder + 'database_about_these_folders.csv')
    df_craic = df_craic.loc[df_craic['exp_name'].isin(exp_names_craic)].copy().reset_index()

    # verify than numbers of rows in all the dataframes are the same
    assert len(df_dilution) == len(df_pipetter) == len(df_structure) / 54 == len(df_craic)

    # verify that number of rows is divisible by 54
    assert len(df_structure) % 54 == 0

    # iterate over the plates of df_pipetter
    for row_id, row in enumerate(df_pipetter.itertuples()):
        # verify that the logic of the data is correct
        reaction_plate = row.plate_code
        assert df_dilution.iloc[row_id]['from'] == reaction_plate
        plate_for_dilution = df_dilution.iloc[row_id]['to']
        assert df_craic.iloc[row_id]['plate_id'] == plate_for_dilution
        craic_folder_here = df_craic.iloc[row_id]['folder']

        # populate the structure dataframe with the plate codes and the craic folder
        df_structure.at[row_id * 54:(row_id + 1) * 54 - 1, 'reaction_plate_id'] = reaction_plate
        df_structure.at[row_id * 54:(row_id + 1) * 54 - 1, 'diluted_plate_id'] = plate_for_dilution
        df_structure.at[row_id * 54:(row_id + 1) * 54 - 1, 'craic_folder'] = craic_folder_here
        df_structure.at[row_id * 54:(row_id + 1) * 54 - 1, 'vial_id'] = tuple(range(54))

    # save the dataframe as csv
    df_structure.to_csv(data_folder + experiment_name + 'results/run_structure.csv', index=False)


def outV_to_outC_by_lookup(experiment_name, lookup_run):
    df_lookup_C = pd.read_csv(data_folder + lookup_run + 'outVandC/outC.csv')
    df_lookup_C.drop('Unnamed: 0', inplace=True, axis=1)
    df_lookup_V = pd.read_csv(data_folder + lookup_run + 'outVandC/outV.csv')
    df_lookup_V.drop('Unnamed: 0', inplace=True, axis=1)

    # load Excel file from experiment_name run into dataframe
    run_name = experiment_name.split('/')[1]
    df_excel = pd.read_excel(data_folder + experiment_name + f'{run_name}.xlsx', sheet_name=0)

    df_outC = pd.DataFrame().reindex_like(df_lookup_C)[0:0]
    # iterate over df_excel, look for row of df_lookup_C with index equal to 'reactions' and populate df_outC
    for row_id, row in df_excel.iterrows():
        # Zero-filled rows in Excel are used as padding for matching to 54 conditions on each plate).
        # In this case, fill row of concentrations in df_outC with zeros.
        if (row.to_numpy()[1:] == 0).all():
            df_outC.loc[row_id] = df_lookup_C.loc[0] * 0
        else:
            # find the row with same id in df_lookup_C and write to df_outC
            df_outC.loc[row_id] = df_lookup_C.loc[row['reactions']]
            # Lake sure that the volumes in this row are the same as in the row in lookup_V, unless the row is all zeros
            same_row_in_lookup_V = df_lookup_V.loc[row['reactions']].to_numpy()
            assert np.isclose(same_row_in_lookup_V, row.to_numpy()[1:]).all()

    # save outC to /outVandC/outC.csv
    # if there is not 'outVansC' folder in the run folder, create it
    target_folder = data_folder + experiment_name + 'outVandC'
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    df_outC.to_csv(data_folder + experiment_name + 'outVandC/outC.csv')


if __name__ == '__main__':
    run_name = '2023-06-28-run03'
    organize_run_structure(f'multicomp-reactions/{run_name}/')
    outV_to_outC_by_lookup(experiment_name=f'multicomp-reactions/{run_name}/',
                           lookup_run='multicomp-reactions/2023-06-19-run01/')
    pass
