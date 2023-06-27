import os
import pandas as pd

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'
craic_folder = data_folder + 'craic_microspectrometer_measurements/absorbance/'


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
    run_name = experiment_name.split('/')[1]

    # if there is not 'results' folder in the run folder, create it
    target_folder = data_folder + experiment_name + 'results'
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    # open dilution_info.csv as dataframe
    df_dilution = pd.read_csv(data_folder + experiment_name + 'dilution/dilution_info.csv')

    # open run_info.csv as dataframe
    df_pipetter = pd.read_csv(data_folder + experiment_name + 'pipetter_io/run_info.csv', delimiter=', ', header=None,
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
    assert len(df_dilution) == len(df_pipetter) == len(df_structure) == len(df_craic)

    # verify that number of rows is divisible by 54
    assert len(df_dilution) % 54 == 0

    # iterate over the plates of df_pipetter
    for row_id, row in enumerate(df_pipetter.itertuples()):
        # verify that the logic of the data is correct
        reaction_plate = row.plate_code
        assert df_dilution.iloc[row_id]['from'] == reaction_plate
        plate_for_dilution = df_dilution.iloc[row_id]['to']
        assert df_craic.iloc[row_id]['plate_id'] == plate_for_dilution
        craic_folder = df_craic.iloc[row_id]['folder']

        # populate the structure dataframe with the plate codes and the craic folder
        df_structure.at[row_id * 54:(row_id + 1) * 54 - 1, 'reaction_plate_id'] = reaction_plate
        df_structure.at[row_id * 54:(row_id + 1) * 54 - 1, 'diluted_plate_id'] = plate_for_dilution
        df_structure.at[row_id * 54:(row_id + 1) * 54 - 1, 'craic_folder'] = craic_folder
        df_structure.at[row_id * 54:(row_id + 1) * 54 - 1, 'vial_id'] = tuple(range(54))

    # save the dataframe as csv
    df_structure.to_csv(data_folder + experiment_name + 'results/run_structure.csv', index=False)


if __name__ == '__main__':
    organize_run_structure('multicomp-reactions/2023-06-20-run01/')
