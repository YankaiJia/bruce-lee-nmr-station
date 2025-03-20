import numpy as np
import os
import pandas as pd
import re
import time
import Integrator_v3_baseline
import conc_interpolation

# get teh system path of BRUCELEE_PROJECT_DATA
BRUCELEE_PROJECT_DATA = os.environ['BRUCELEE_PROJECT_DATA']

interp_func_S, interp_func_B = conc_interpolation.get_interp_funcs()

def check_and_return_folder_structure():

    # make sure run name exists
    # get run name by regex: yyyy-mm-dd-run0x(-note1-note2)
    run_name = re.search(r"\d{4}-\d{2}-\d{2}-run\d{2}", run_folder).group(0)
    assert run_name is not None, "Run folder name is in wrong format!"
    excel_file = run_folder + f'{run_name}.xlsx'
    print(f'Excel file: {excel_file}')

    # make sure the excel file exists
    assert os.path.exists(excel_file), "Excel file does not exist or in wrong name!"

    # make sure subfoler outVandC exists
    outVandC_folder = run_folder + "\\outVandC"
    assert os.path.exists(outVandC_folder), "outVandC folder does not exist!"

    # make sure 'out_concentrations.csv' and 'out_volumes_shuffled.csv' exist in outVandC folder
    out_conc_file = outVandC_folder + "\\out_concentrations.csv"
    out_vol_file = outVandC_folder + "\\out_volumes_shuffled.csv"
    assert os.path.exists(out_conc_file), "out_concentrations.csv does not exist!"
    assert os.path.exists(out_vol_file), "out_volumes_shuffled.csv does not exist!"

    # make sure Results folder exists
    result_folder = run_folder + "Results"
    assert os.path.exists(result_folder), "Results folder does not exist!"
    return result_folder, excel_file, out_conc_file, out_vol_file

      
def combine_data(df_final_conc, 
                excel_file, out_conc_file, out_vol_file, result_folder):

    # assign the vial index from reaction name. vial_index is the same as local_index
    vial_index = [int(i[0]) for i in df_final_conc['spectrum_name'].str.split('-')]
    df_final_conc['local_index'] = vial_index
    # move the vial_index to the first column
    df_final_conc = df_final_conc[['local_index'] + [col for col in df_final_conc.columns if col != 'local_index']]

    # attach reaction conditions to the dataframe
    # load exce file into df
    # df_excel = pd.read_excel(excel_file, engine='openpyxl')
    df_excel = pd.read_excel(excel_file)

    vol_cols = [col for col in df_excel.columns if 'vol#' in col]
    # get the volume data
    df_vols = df_excel[['local_index','global_index']+vol_cols]
    print(df_vols.head())

    # get the conc data
    df_init_conc = pd.read_csv(out_conc_file)
    # multiply the conc data with 1000 to convert to mM, except the first column
    df_init_conc.iloc[:, 1:] = df_init_conc.iloc[:, 1:] * 1000
    # rename the first column to global_index
    df_init_conc.columns.values[0] = 'global_index'

    # merge the df_vols with df_init_conc according to global_index
    df_merged_vols_with_init_conc = pd.merge(df_init_conc, df_vols, on='global_index', how='inner')

    # merge the result with the df_final_conc according to local_index (vial_index)
    df_final = pd.merge(df_merged_vols_with_init_conc, df_final_conc, on='local_index', how='inner')

    # sort the final dataframe according to local_index
    df_final = df_final.sort_values(by='local_index')

    return df_final

def process_one_folder(run_folder):

    result_folder, excel_file, out_conc_file, out_vol_file = check_and_return_folder_structure()
    print(f'Analyzing {run_folder}')

    Integrator_v3_baseline.analyze_one_run_folder(run_folder)

    df_final_conc = conc_interpolation.interpolate_one_folder(result_folder,
                                                              is_save_csv=True)
    df = combine_data(df_final_conc,
                      excel_file,
                      out_conc_file,
                      out_vol_file,
                      result_folder)

    # calc the S conversion
    df['S_conversion'] = 1 - df['c#_S_from_S'] / df['DPE'].replace(0, np.nan)
    df['consumed_S'] = df['DPE'] - df['c#_S_from_S']

    # get the limitting reagent
    df['limitting_conc'] = df[['DPE', 'Br2']].min(axis=1)
    df['c#_A_from_B'] = pd.to_numeric(df['c#_A_from_B'], errors='coerce')
    df['c#_B_from_B'] = pd.to_numeric(df['c#_B_from_B'], errors='coerce')
    df['limitting_conc'] = pd.to_numeric(df['limitting_conc'], errors='coerce')

    # get the yield of A
    df['yield_A'] = np.where(df['limitting_conc'] != 0, df['c#_A_from_B'] / df['limitting_conc'], 0)
    df['yield_B'] = np.where(df['limitting_conc'] != 0, df['c#_B_from_B'] / df['limitting_conc'], 0)

    # get the yield of other products
    col_list = ['intg_sol_down', 'intg_sol_up', 'intg_impr_SM1', 'intg_impr_SM2',
                'intg_impr1', 'intg_impr2', 'intg_impr3', 'intg_impr4',
                'intg_alcohol', 'intg_HBr_adduct', 'intg_acid']
    for col_name in col_list:
        if not col_name in df.columns:
            continue
        yield_str = col_name.replace('intg_', 'yield_')
        df[yield_str] = np.where(df['limitting_conc'] != 0, df[col_name] / df['limitting_conc'], 0)

    time.sleep(1)

    # selectivity metrics
    df['sel_A'] = df['c#_A_from_B'] / df['consumed_S']
    df['sel_B'] = df['c#_B_from_B'] / df['consumed_S']

    # mole fraction of A
    df['mole_fraction_A'] = df['c#_A_from_B'] / (df['c#_A_from_B'] + df['c#_B_from_B'])

    # save the final dataframe to csv
    df.to_csv(result_folder + "\\final_results.csv", index=False)

    return df

if __name__ == "__main__":

    data_dir = BRUCELEE_PROJECT_DATA

    run_folders = [
                "\\data\\DPE_bromination\\2025-02-19-run02_normal_run\\",
                # "\\data\\DPE_bromination\\2025-03-01-run01_normal_run\\",
                # "\\data\\DPE_bromination\\2025-03-03-run01_normal_run\\",
                # "\\data\\DPE_bromination\\2025-03-03-run02_normal_run\\",
                # "\\data\\DPE_bromination\\2025-03-05-run01_normal_run\\",
                # "\\data\\DPE_bromination\\2025-03-12-run01_better_shimming\\",
                ]

    run_folders = [data_dir + run_folder for run_folder in run_folders]
    print(run_folders)

    for run_folder in run_folders:
        process_one_folder(run_folder)

    # merge all the final_results.csv into one file
    df_full_experiment = pd.DataFrame()
    for run_folder in run_folders:
        result_folder = run_folder + "\\Results"
        df_full_experiment = pd.concat([df_full_experiment, pd.read_csv(result_folder + "\\final_results.csv")])

    # save final results to csv
    csv_path = data_dir + "\\DPE_bromination\\full_experiment_test_YJ_2.csv"
    df_full_experiment.to_csv(csv_path, index=False, mode='w') # use overwrite mode

    print(f'Full experiment data saved to {csv_path}')

