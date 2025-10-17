import json, pandas as pd, os

def get_conc_for_all_reactions_for_nik_reactions(run_folder,
                                                 run_name1,
                                                 run_name2,
                                                 excel_name1,
                                                 excel_name2,
                                                 is_cmpd3_ready=False):

    """
    Process reaction data by merging concentration and spectrum information from multiple sources.

    This function performs the following steps:
    1. Defines paths to two experimental runs and their associated data files (Excel and CSV).
    2. Extracts subfolders containing processed 1D NMR spectra.
    3. Maps spectrum folder names to their corresponding local indices from Excel files.
    4. Combines data from both experimental runs into a single DataFrame.
    5. Merges the combined data with concentration/volume information from a CSV file (OutVandC).
    6. Loads compound 3 concentration values from a JSON file and maps them to the merged DataFrame.
    7. Saves intermediate and final processed DataFrames to CSV files.

    Returns:
        pd.DataFrame: A DataFrame containing selected columns including local index, global index,
                      spectrum name, key component concentrations, and compound 3 concentration.

    Output files:
        - conc_for_all_reactions.csv: Contains merged data from Excel and OutVandC CSV.
        - conditions_with_compd3_conc.csv: Final output including compound 3 concentration.
    """

    # This file conc_vol_list.csv is copy-pasted manually from robotics_concentration_calculator_NVxxxx.xlsx
    outvandc_file = run_folder + run_name1 + r"\OutVandC\conc_vol_list.csv"

    results_folder1 = run_folder + run_name1 + r"\Results"
    results_folder2 = run_folder + run_name2 + r"\Results"

    excel_file1 = run_folder + run_name1 + excel_name1
    excel_file2 = run_folder + run_name2 + excel_name2

    # get all the subfolders in the results folder if "1D EXTENDED" is in the name
    reaction_folder_list1 = [f.path for f in os.scandir(results_folder1) if f.is_dir() and "1D EXTENDED" in f.name]
    reaction_folder_list2 = [f.path for f in os.scandir(results_folder2) if f.is_dir() and "1D EXTENDED" in f.name]
    spectrum_name_list1 = [path.split('\\')[-1] for path in reaction_folder_list1]
    spectrum_name_list2 = [path.split('\\')[-1] for path in reaction_folder_list2]
    spectrum_name_dict1 = {int(item.split('-')[0]): item for item in spectrum_name_list1}
    spectrum_name_dict2 = {int(item.split('-')[0]): item for item in spectrum_name_list2}


    # read the excel files into df
    df1 = pd.read_excel(excel_file1)
    df2 = pd.read_excel(excel_file2)

    # map the spectrum_name_dict1 to the local_index in df1
    df1['spectrum_name'] = df1['local_index'].map(spectrum_name_dict1)
    df2['spectrum_name'] = df2['local_index'].map(spectrum_name_dict2)

    # combine the two dfs
    df_combined = pd.concat([df1, df2], ignore_index=True)

    print(df_combined.head())

    # outVandC
    df_conc_vol = pd.read_csv(outvandc_file)
    # add global_index column if it is not already exist
    if 'global_index' not in df_conc_vol.columns:
        df_conc_vol['global_index'] = range(len(df_conc_vol))

    # merge the df_combined with df_conc_vol on 'global_index'
    df_merged = pd.merge(df_combined, df_conc_vol, on='global_index', how='left')
    # save to a new csv file
    output_csv = run_folder + r'\conc_for_all_reactions.csv'
    df_merged.to_csv(output_csv, index=False)
    # save only certain columns
    all_columns = df_merged.columns
    columns_to_be_save = [col for col in all_columns if ('index' in col
                                                         or 'conc' in col
                                                         or 'spectrum' in col)]
    df_merged_simplified = df_merged[columns_to_be_save]
    output_csv = run_folder + r'\conc_for_all_reactions_simplified.csv'
    df_merged_simplified.to_csv(output_csv, index=False)

    if is_cmpd3_ready:
        # read the json with compd3 concentration
        compd3_conc_json = run_folder + r'\hardy_fitting_compd3_conc.json'
        with open(compd3_conc_json, 'r') as file:
            compd3_conc_dict = json.load(file)
        # convert the json to a dataframe
        df_compd3_conc = pd.DataFrame(list(compd3_conc_dict.items()), columns=['spectrum_name', 'compd3_conc'])
        # map the compd3 conc by 'spectrum_name'
        df_merged['compd3_conc'] = df_merged['spectrum_name'].map(df_compd3_conc.set_index('spectrum_name')['compd3_conc'])

        # save the df_merged to a new csv file
        needed_columns =['local_index', 'global_index',
               'spectrum_name', 'conc_1c', 'conc_PhCHO', 'conc_DMAP', ]
        df_merged = df_merged[needed_columns + ['compd3_conc']]
        output_csv_merged = run_folder + r'\conditions_with_compd3_conc.csv'
        df_merged.to_csv(output_csv_merged, index=False)

    return df_merged

if __name__ == "__main__":


    ##########EXAMPLE FOR MECN FOLDER#############
    # run_folder = (r'D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\\4-Pyrrolidinopyridine\\')
    # run_name1 = "2025-06-25-run01_MeCN_4_Pyrrol_Pyr"
    # run_name2 = "2025-06-25-run02_MeCN_4_Pyrrol_Pyr"
    # excel_name1 = r"\2025-06-25-run01.xlsx"
    # excel_name2 = r"\2025-06-25-run02.xlsx"
    ##################################################

    ##########EXAMPLE FOR DMSO FOLDER#############
    run_folder = (r'D:\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\4-Morpholino pyridine\\')
    run_name1 = "2025-06-21-run01_DMSO_4_Morph_Pyr"
    run_name2 = "2025-06-21-run02_DMSO_4_Morph_Pyr"
    excel_name1 = r"\2025-06-21-run01.xlsx"
    excel_name2 = r"\2025-06-21-run02.xlsx"
    ##################################################


    get_conc_for_all_reactions_for_nik_reactions(run_folder=run_folder,
                                                 run_name1=run_name1,
                                                 run_name2=run_name2,
                                                 excel_name1=excel_name1,
                                                 excel_name2=excel_name2
                                                 )