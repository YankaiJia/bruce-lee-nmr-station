import numpy as np
import os
import pandas as pd
import re
import time
import Integrator_v3_baseline
import conc_interpolation_2D

import utils

# get the system path of BRUCELEE_PROJECT_DATA_PATH
BRUCELEE_PROJECT_DATA_PATH = os.environ['BRUCELEE_PROJECT_DATA_PATH']

def check_and_return_folder_structure(run_folder):

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

def process_one_folder(run_dir, run_sol, run_outliers):

    run_folder = run_dir

    solvent_name = 'MeCN' if 'MeCN' in run_folder else 'DCE'
    additive_name = 'TBABr3' if 'TBABr3' in run_folder else 'normal'

    result_folder, excel_file, out_conc_file, out_vol_file = check_and_return_folder_structure(run_folder)
    print(f'Analyzing {run_folder}')

    # Integrator_v3_baseline.analyze_one_run_folder(master_path=run_folder,
    #                                               sol_name=run_sol,
    #                                               outliers=run_outliers,
    #                                               is_show_plot=False)

    conc_interpolation_2D.interp_one_folder(run_folder)


def post_treatment_to_get_params_for_cubes(all_result_csv_path,
                                           additive_name='TBABr'):

    df = all_result_csv_path
    df = df.rename(columns={'conc_TBABr': 'conc_TBABr_0',
                            'conc_Br2': 'conc_Br2_0',
                            'conc_DPE': 'conc_DPE_0',
                            'conc_adduct': 'conc_HBr_adduct'})

    # calc the S conversion
    df['DPE_consumed'] = df['conc_DPE_0'] - df['conc_DPE_final']
    df['DPE_conversion'] = df['DPE_consumed'] / df['conc_DPE_0'].replace(0, np.nan)

    df['Bromine_source'] = df['conc_Br2_0'] + df['TBABr3'] if additive_name == 'TBABr3' else df['conc_Br2_0']
    df['limitting_conc'] = df[['conc_DPE_0', 'Bromine_source']].min(axis=1)

    df['conc_prod_A'] = pd.to_numeric(df['conc_prod_A'], errors='coerce')
    df['conc_prod_B'] = pd.to_numeric(df['conc_prod_B'], errors='coerce')
    df['limitting_conc'] = pd.to_numeric(df['limitting_conc'], errors='coerce')
    df['conc_alcohol'] = pd.to_numeric(df['conc_alcohol'], errors='coerce')
    df['conc_HBr_adduct'] = pd.to_numeric(df['conc_HBr_adduct'], errors='coerce')

    # get the yield of A
    df['yield_prod_A'] = np.where(df['limitting_conc'] != 0, df['conc_prod_A'] / df['limitting_conc'] * 100, 0)
    df['yield_prod_B'] = np.where(df['limitting_conc'] != 0, df['conc_prod_B'] / df['limitting_conc'] * 100, 0)


    # cal limiting conc for alcohol
    df['limitting_conc_for_alcohol'] = pd.DataFrame({
                                                    'A': df['conc_DPE_0'],
                                                    'half_B': 0.5 * df['Bromine_source']
                                                }).min(axis=1)

    df['yield_alcohol'] = np.where(df['limitting_conc'] != 0, df['conc_alcohol'] / df['limitting_conc_for_alcohol'] * 100, 0)
    df['yield_HBr_adduct'] = np.where(df['limitting_conc'] != 0, df['conc_HBr_adduct'] / df['limitting_conc'] * 100, 0)

    # selectivity metrics
    df['sel_prod_A'] = df['conc_prod_A'] / df['DPE_consumed']
    df['sel_prod_B'] = df['conc_prod_B'] / df['DPE_consumed']
    df['sel_alchol'] = df['conc_alcohol'] / df['DPE_consumed']
    df['sel_HBr_adduct'] = df['conc_HBr_adduct'] / df['DPE_consumed']

    # calculate residuals
    df['residual_of_AB'] = 1 - (df['sel_prod_A'] + df['sel_prod_B'])
    df['residual_of_AB_alcohol'] = 1 - (df['sel_prod_A'] + df['sel_prod_B'] + df['sel_alchol'])
    df['residual_of_AB_alcohol_HBr_adduct'] = 1 - (df['sel_prod_A'] + df['sel_prod_B'] + df['sel_alchol'] + df['sel_HBr_adduct'])

    # mole fraction of A # Set NaN when both concentrations are < 0.1
    df['mole_fraction_A_over_AB'] = np.where(
                                            (df['conc_prod_A'] < 3) & (df['conc_prod_B'] < 3),
                                            np.nan,
                                            df['conc_prod_A'] / (df['conc_prod_A'] + df['conc_prod_B'])
                                            )
    # # delete rows if the list in the uuid column name
    # patterns_to_remove = ['ZCCK', '9MEo']
    # df = df[~df['uuid'].str.contains('|'.join(patterns_to_remove), case=False, na=False)]

    # if the init substrate concs are the same, keep only the last one.
    df = df[~df.duplicated(subset=['conc_TBABr_0', 'conc_Br2_0', 'conc_DPE_0'], keep='last')]

    # reorder cols for plotting
    first_cols = ['uuid', 'conc_DPE_final', 'conc_TBABr_0', 'conc_Br2_0', 'conc_DPE_0']
    df = df[first_cols + [col for col in df.columns if col not in first_cols]]
    return df

if __name__ == "__main__":

    # import matplotlib
    # matplotlib.use('WebAgg')

    data_dir = BRUCELEE_PROJECT_DATA_PATH
    print(f'Data directory: {data_dir}')

    # run folder structure: [run_folder, run_sol, run_outliers]
    run_folders = [
                # ["\\DPE_bromination\\2025-03-24-run01_MeCN_normal\\", 'MeCN', None],
                # ["\\DPE_bromination\\2025-03-24-run02_MeCN_normal\\", 'MeCN', None],
                # ["\\DPE_bromination\\2025-04-01-run01_MeCN_normal\\", 'MeCN', None],
                # ["\\DPE_bromination\\2025-04-02-run01_MeCN_normal\\", 'MeCN', None],
                # ["\\DPE_bromination\\2025-04-02-run02_MeCN_normal\\", 'MeCN', None],
                # ["\\DPE_bromination\\2025-04-02-run03_MeCN_normal\\", 'MeCN', None],
                # ["\\DPE_bromination\\2025-04-03-run01_MeCN_normal\\", 'MeCN', None],
                # ["\\DPE_bromination\\2025-04-03-run02_MeCN_normal\\", 'MeCN', None],
                # ["\\DPE_bromination\\2025-04-08-run01_MeCN_normal\\", 'MeCN', None],
                # ["\\DPE_bromination\\2025-04-15-run01_DCE_TBABr3_normal\\", 'DCE', None],
                # ["\\DPE_bromination\\2025-04-15-run02_DCE_TBABr3_normal\\", 'DCE', None],
                # ["\\DPE_bromination\\2025-04-15-run03_DCE_TBABr3_normal\\", 'DCE', None],
                # ["\\DPE_bromination\\2025-04-15-run04_DCE_TBABr3_normal\\", 'DCE', None],
                # ["\\DPE_bromination\\2025-04-22-run01_DCE_TBABr3_normal\\", 'DCE', None],

                ["\\DPE_bromination\\2025-02-19-run02_normal_run\\", 'DCE', None],
                ["\\DPE_bromination\\2025-03-01-run01_normal_run\\", 'DCE', None],
                ["\\DPE_bromination\\2025-03-03-run01_normal_run\\", 'DCE', {46: 'Type1', 47: 'Type2'}],
                ["\\DPE_bromination\\2025-03-03-run02_normal_run\\", 'DCE', None],
                ["\\DPE_bromination\\2025-03-05-run01_normal_run\\", 'DCE', None],
                ["\\DPE_bromination\\2025-03-12-run01_better_shimming\\", 'DCE', None],

                # ["\\DPE_bromination\\2025-04-28-run01_DCE_TBABF4_normal\\", 'DCE-BF4', None],
                # ["\\DPE_bromination\\2025-04-28-run02_DCE_TBABF4_normal\\", 'DCE-BF4', None],
                # ["\\DPE_bromination\\2025-04-28-run03_DCE_TBABF4_normal\\", 'DCE-BF4', None],
                # ["\\DPE_bromination\\2025-04-28-run04_DCE_TBABF4_normal\\", 'DCE-BF4', None],
                # [r"\DPE_bromination\2025-05-30-run01_DCE_TBPBr_normal\\", 'DCE', None],
                # [r"\DPE_bromination\2025-05-30-run02_DCE_TBPBr_normal\\", 'DCE', None],
                # [r"\DPE_bromination\2025-05-30-run03_DCE_TBPBr_normal\\", 'DCE', None],
                # [r"\DPE_bromination\2025-05-30-run04_DCE_TBPBr_normal\\", 'DCE', None],
                [r"\DPE_bromination\2025-07-01-run01_DCE_TBABr_rerun\\", "DCE", None],

    ]

    for run_folder in run_folders:
        run_dir = data_dir + run_folder[0]
        run_sol = run_folder[1]  # solvent name
        run_outliers = run_folder[2]  # outlier type if any

        print(f'Processing {run_dir}')

        # put results in each spectrum folder
        utils.put_run_condition_in_spectrum_folder(run_dir)
        utils.put_fitting_results_in_spec_folder(run_dir)

        # do the fitting and interplation
        process_one_folder(run_dir, run_sol, run_outliers)



    run_folders_paths = [data_dir+ls[0] for ls in run_folders]
    all_results_df = utils.collect_all_json_results_form_every_spectrum(run_folders_paths)

    df = post_treatment_to_get_params_for_cubes(all_results_df)

    # save this df to csv
    save_path = data_dir + r"\\DPE_bromination"
    csv_file_name = r'\\full_experiment_DCE_TBABr_2d_interp.csv'
    df.to_csv(save_path+csv_file_name, index=False)  # index=False prevents writing the row index
    print(f"Data saved to: {save_path+csv_file_name}")
