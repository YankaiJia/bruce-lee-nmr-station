import json
import re

from matplotlib import pyplot as plt
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import os
import shutil

BRUCELEE_PROJECT_DATA_PATH = os.environ['BRUCELEE_PROJECT_DATA_PATH']


def plot1():
    ys_ori = {
        0: '92.03727024121508',
        1: '44.85000344605123',
        2: '21.30438829283912',
        3: '9.689694961722125',
        4: '4.404170234225603'}

    ys = [float(value) for key, value in ys_ori.items()]
    print(ys)

    xs_init = 152.4
    xs = [xs_init, xs_init / 2, xs_init / 4, xs_init / 8, xs_init / 16]

    yb_ori = {0: '58.26061628299067',
              1: '29.7097988122041',
              2: '14.252173271263246',
              3: '6.550650316834435',
              4: '2.1064971663290635'}

    yb = [float(value) for key, value in yb_ori.items()]
    xb_init = 252.1
    xb = [xb_init, xb_init / 2, xb_init / 4, xb_init / 8, xb_init / 16]

    # plt.plot(xs, ys,'o', ls = '-')
    # plt.plot(xb, yb, 'o', ls = '-')

    # plt.xscale('log')  # Set the x-axis to logarithmic scale
    # plt.plot()
    # plt.show()


def plot2():
    import pandas as pd
    # plot csv
    path = "D:\\Dropbox\\brucelee\\data\\DPE_bromination\\_Refs\\ref_B_TEST\\205244-1D EXTENDED+-B1\\data.csv"

    df = pd.read_csv(path)
    print(df.head())
    plt.plot(df['x'], df['y'], 'o', ls='-')
    plt.plot()
    plt.show()


def ask_folder_path():
    # Create a root window and hide it
    root = tk.Tk()
    root.withdraw()
    # Ask the user to select a folder
    folder_path = filedialog.askdirectory(title="Select a Folder")
    # Print the selected folder path
    if folder_path:
        print(f"Selected folder: {folder_path}")
    else:
        print("No folder selected")
    return folder_path


def arrange_folder_name():
    folder = ask_folder_path()
    print(folder)

    # get all the subfolders
    import os
    subfolders = [f.path for f in os.scandir(folder) if f.is_dir()]
    subfolders = [f for f in subfolders if '1D' in f]

    # rename the subfolders
    for subfolder in subfolders:
        file_path = os.path.join(subfolder, 'data.1d')
        if os.path.exists(file_path):
            # print(f"File does exist: {file_path}")
            # get modification time of the folder
            mod_time = os.path.getmtime(file_path)
            # get the date in the format yymmdd-hhmmss
            import datetime
            import time
            # date = time.strftime('%y%m%d-%H%M%S', time.localtime(mod_time))
            date = time.strftime('%y%m%d', time.localtime(mod_time))
            print(f"Date: {date}")
            ls = subfolder.split("Results\\")[-1].split('-')
            # print(ls)
            new_name = subfolder.split("Results")[0] + '/Results/' + '-'.join(
                [str(int(ls[2])).zfill(2), ls[1], str(date), ls[0]])
            # new_name = subfolder.replace('1D', '1D EXTENDED')
            print(f"New name: {new_name}")
            os.rename(subfolder, new_name)


def rename_folder():
    # add the sring "bad_shiming" to each of the subfolders
    folder = ask_folder_path()
    print(folder)
    folder = folder + '/Results/bad_shimming_data'

    # get all the subfolders
    import os
    subfolders = [f.path for f in os.scandir(folder) if f.is_dir()]
    subfolders = [f for f in subfolders if '1D' in f]

    # rename the subfolders
    for subfolder in subfolders:
        new_name = subfolder + '_bad_shimming'
        print(f"New name: {new_name}")
        os.rename(subfolder, new_name)


def collect_conditions_of_bad_shimming_specs(folder):
    # get the folder path
    # folder = ask_folder_path()

    # folder = ask_folder_path()
    print(folder)
    folder_bad_shimming = folder + '/Results/bad_shimming_data'

    # get the subfolders
    subfolders = [f.path for f in os.scandir(folder_bad_shimming) if f.is_dir()]
    subfolders = [f for f in subfolders if '1D' in f]
    # get the subfolder names
    subfolder_names = [os.path.basename(f) for f in subfolders]
    target_index = [int(f.split('-')[0]) for f in subfolder_names]
    print(target_index)

    # get the excel file in the folder
    excel_file = [f.path for f in os.scandir(folder) if f.is_file() and f.name.endswith('.xlsx')][0]
    print(excel_file)

    # read the excel file
    df = pd.read_excel(excel_file)
    print(df.head())

    # get the target rows where the 'local_index' is in the target_index
    df_target = df[df['local_index'].isin(target_index)]
    print(df_target)

    # save the target rows to a new excel file
    new_excel_file = folder + '/Results/bad_shimming_data/conditions_of_bad_shimming_specs.xlsx'
    df_target.to_excel(new_excel_file, index=False)
    print(f"Saved to {new_excel_file}")

    return df_target


def arrange_bad_contions_for_folders():
    folder_list = [
        r"D:\\Dropbox\\brucelee\\data\DPE_bromination\\2025-02-19-run02_normal_run",
        r"D:\\Dropbox\\brucelee\data\DPE_bromination\\2025-03-01-run01_normal_run",
        r"D:\\Dropbox\\brucelee\\data\DPE_bromination\\2025-03-03-run01_normal_run",
        r"D:\\Dropbox\\brucelee\\data\DPE_bromination\\2025-03-03-run02_normal_run",
        r"D:\\Dropbox\\brucelee\\data\DPE_bromination\\2025-03-05-run01_normal_run",

    ]

    # append all the dataframes
    df_list = []
    for folder in folder_list:
        df = collect_conditions_of_bad_shimming_specs(folder)
        df_list.append(df)

    # concatenate the dataframes
    df_all = pd.concat(df_list)
    # if not exist, create the folder
    new_excel_file = r'D:\Dropbox\\brucelee\data\DPE_bromination/conditions_of_bad_shimming_specs_all.xlsx'
    if not os.path.exists(os.path.dirname(new_excel_file)):
        os.makedirs(os.path.dirname(new_excel_file))
    df_all.to_excel(new_excel_file, index=False)
    print(f"Saved to {new_excel_file}")


def list_reaction_condtions_into_each_folder():
    # get the folder path
    folder = ask_folder_path()
    print(folder)

    # get the subfolders
    subfolders = [f.path for f in os.scandir(folder) if f.is_dir()]
    subfolders = [f for f in subfolders if '1D' in f]

    for subfolder in subfolders:
        # get the subfolder names
        subfolder_names = [os.path.basename(f) for f in subfolders]

        # get the local index
        local_index = int(subfolder.split('-')[0])
        print(local_index)
        # get the excel file in the folder
        excel_file = [f.path for f in os.scandir(folder) if f.is_file() and f.name.endswith('.xlsx')][0]
        print(excel_file)

        # read the excel file
        df = pd.read_excel(excel_file)
        print(df.head())

        # get the target rows where the 'local_index' is in the target_index
        df_target = df[df['local_index'] == local_index]
        print(df_target)

        # save the target rows to a new excel file
        new_excel_file = subfolder + '/conditions_of_bad_shimming_specs.xlsx'
        df_target.to_excel(new_excel_file, index=False)
        print(f"Saved to {new_excel_file}")
        # local_index =

    # get the excel file in the folder
    excel_file = [f.path for f in os.scandir(folder) if f.is_file() and f.name.endswith('.xlsx')][0]
    print(excel_file)

    # read the excel file
    df = pd.read_excel(excel_file)
    print(df.head())

    # get the target rows where the 'local_index' is in the target_index
    df_target = df[df['local_index'].isin(target_index)]
    print(df_target)

    # save the target rows to a new excel file
    new_excel_file = folder + '/Results/conditions_of_bad_shimming_specs.xlsx'
    df_target.to_excel(new_excel_file, index=False)
    print(f"Saved to {new_excel_file}")

    return df_target


def delete_unused_file():
    run_folders = ["D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-02-19-run02_normal_run\\",
                   "D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-03-01-run01_normal_run\\",
                   "D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-03-03-run01_normal_run\\",
                   "D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-03-03-run02_normal_run\\",
                   "D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-03-05-run01_normal_run\\",
                   "D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-03-12-run01_better_shimming\\",
                   ]
    result_folders = [i + 'Results' for i in run_folders]

    # get all the subfolders for each folder
    for folder in result_folders:
        subfolders = [f.path for f in os.scandir(folder) if f.is_dir()]
        subfolders = [f for f in subfolders if '1D EXTENDED' in f]
        print(subfolders)
        for dir in subfolders:
            # if there is a file named slices.png, delete it
            if os.path.exists(dir + '/slices.png'):
                os.remove(dir + '/slices.png')
                print(f"Deleted: {dir + '/slices.png'}")
            if os.path.exists(dir + '/fitting_slices.png'):
                os.remove(dir + '/fitting_slices.png')
                print(f"Deleted: {dir + '/fitting_slices.png'}")
            if os.path.exists(dir + '/test-Louis-fitting_results.png'):
                os.remove(dir + '/test-Louis-fitting_results.png')
                print(f"Deleted: {dir + '/test-Louis-fitting_results.png'}")


def move_files():
    # i need to move the subfolder to the main folder, do it with python
    # i will use the shutil library to move the files

    path = 'D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-02-19-run01_time_varied\\Results\\_000'
    folders = os.listdir(path)
    print(folders)
    for folder in folders:
        # get subfolder path
        subfolder = os.path.join(path, folder)
        # get files in subfolder
        files = os.listdir(subfolder)
        for file in files:
            # get file path
            file_path = os.path.join(subfolder, file)
            # move file to main folder
            shutil.move(file_path, path)


def find_missing_conditions():
    df_exp_done = pd.read_csv(BRUCELEE_PROJECT_DATA_PATH + "\\DPE_bromination\\full_experiment_DCE_TBABr3_YJ_good.csv")

    df_all = pd.read_csv(
        BRUCELEE_PROJECT_DATA_PATH + "\\DPE_bromination\\2025-04-15-run01_DCE_TBABr3_normal\\outVandC\\out_volumes_shuffled.csv")

    df_all.columns = ['global_index', 'vol#TBABr3', 'vol#Br2', 'vol#DPE', 'vol#DCE']

    # Round to consistent decimal places to avoid float comparison issues, if needed
    df_all = df_all.round(2)
    df_exp_done_subset = df_exp_done.round(2)

    # Drop duplicates if any
    df_all_unique = df_all.drop_duplicates()
    df_done_unique = df_exp_done_subset.drop_duplicates()

    # Find the rows in df_all that are not in df_exp_done
    df_missing = pd.merge(df_all_unique, df_done_unique, on=['vol#TBABr3', 'vol#Br2', 'vol#DPE', 'vol#DCE'], how='left',
                          indicator=True)
    df_missing = df_missing[df_missing['_merge'] == 'left_only'].drop(columns=['_merge'])

    print(df_missing)
    # Save to CSV
    output_path = os.path.join(BRUCELEE_PROJECT_DATA_PATH, "DPE_bromination", "missing_conditions.csv")
    df_missing.to_csv(output_path, index=False)

    return df_missing


# df_missing = find_missing_conditions

def write_conc_into_result_csv():

    results_folders = [
        # r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\4-Pyrrolidinopyridine\2025-05-19-run01_MeCN_4_pyrrolidinopyridine\Results",
        # r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\4-Pyrrolidinopyridine\2025-05-19-run02_MeCN_4_pyrrolidinopyridine\Results",
        # r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\DMAP\2025-06-16-run01_MeCN_DMAP\Results",
        # r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\DMAP\2025-06-16-run02_MeCN_DMAP\Results"
        # r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\Pyridine\2025-05-15-run01_MeCN_Pyr\Results"
        # r'D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methyl pyridine\2025-06-18-run01_MeCN_4_Me_Pyr\Results',
        # r'D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methyl pyridine\2025-06-18-run02_MeCN_4_Me_Pyr\Results'
        r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Pyrrolidinopyridine\2025-05-19-run01_MeCN_4_pyrrolidinopyridine\Results",
        r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Pyrrolidinopyridine\2025-05-19-run02_MeCN_4_pyrrolidinopyridine\Results"
    ]

    json_file_to_save = r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Pyrrolidinopyridine" + r"\hardy_fitting_compd3_conc.json"

    # get all the subfolders in the results folder if "1D EXTENDED" is in the name
    subfolders = []
    for folder in results_folders:
        subfolders.extend([f.path for f in os.scandir(folder) if f.is_dir() and "1D EXTENDED" in f.name])

    compd3_conc_dict = {}
    for folder in subfolders:
        key = str(folder).split('Results\\')[-1]
        print(f"Processing folder: {key}")
        json_file = folder + r'\hardy_fitting_report.json'
        with open(json_file, 'r') as file:
            data = json.load(file)
            concentration = data['compd3_concentration']

        compd3_conc_dict[key] = concentration
    # save the compd3_conc_dict to a json file
    with open(json_file_to_save, 'w') as file:
        json.dump(compd3_conc_dict, file, indent=4)
    print(f"Saved compd3_conc_dict to {json_file_to_save}")

    return compd3_conc_dict

# write_conc_into_result_csv()

def merge_result_from_hardy_fitting():

    compd3_conc_dict = write_conc_into_result_csv()

    result_csv = r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\4-Pyrrolidinopyridine\CSV_4-Pyro_Final.csv"
    df = pd.read_csv(result_csv)
    df['spectrum_name'] = df['spectrum_dir'].apply(lambda x: x.split('\\')[-1].strip())

    print(df['spectrum_name'])

    # merge the compd3_conc_dict into df according to the 'spectrum_name' matching with the keys of compd3_conc_dict
    df['Conc_compd3_by_hardy_fitting'] = df['spectrum_name'].map(compd3_conc_dict)

    print(df['Conc_compd3_by_hardy_fitting'])

    # df['Yield_compd3_by_hardy_fitting'] = df['Conc_compd3_by_hardy_fitting']

    #save the df to a new csv file
    output_csv = r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\4-Pyrrolidinopyridine\CSV_4-Pyro_Final_with_hardy_fitting.csv"
    df.to_csv(output_csv, index=False)

# merge_result_from_hardy_fitting()

def get_conc_for_all_reactions():

    run_folder = r'D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Pyrrolidinopyridine'
    outvandc_file = r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Pyrrolidinopyridine\2025-05-19-run01_MeCN_4_pyrrolidinopyridine\OutVandC\conc_vol_list.csv"

    results_folder1 = r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Pyrrolidinopyridine\2025-05-19-run01_MeCN_4_pyrrolidinopyridine\Results"
    results_folder2 = r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Pyrrolidinopyridine\2025-05-19-run02_MeCN_4_pyrrolidinopyridine\Results"

    excel_file1 = r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Pyrrolidinopyridine\2025-05-19-run01_MeCN_4_pyrrolidinopyridine\2025-05-19-run01.xlsx"
    excel_file2 = r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Pyrrolidinopyridine\2025-05-19-run02_MeCN_4_pyrrolidinopyridine\2025-05-19-run02.xlsx"

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

    # merge the df_combined with df_conc_vol on 'global_index'
    df_merged = pd.merge(df_combined, df_conc_vol, on='global_index', how='left')
    # save to a new csv file
    output_csv = run_folder + r'\conc_for_all_reactions.csv'
    df_merged.to_csv(output_csv, index=False)

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

# df_merged = get_conc_for_all_reactions()


def get_conc_for_all_reactions_one_run_folder():

    run_folder = r'D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\Pyridine'
    outvandc_folder = run_folder + r'\2025-05-15-run01_MeCN_Pyr\OutVandC'
    results_folder1 = run_folder + r'\2025-05-15-run01_MeCN_Pyr\Results'
    excel_file1 = run_folder + r"\2025-05-15-run01_MeCN_Pyr\2025-05-15-run01.xlsx"

    # get all the subfolders in the results folder if "1D EXTENDED" is in the name
    reaction_folder_list1 = [f.path for f in os.scandir(results_folder1) if f.is_dir() and "1D EXTENDED" in f.name]
    # reaction_folder_list2 = [f.path for f in os.scandir(results_folder2) if f.is_dir() and "1D EXTENDED" in f.name]
    spectrum_name_list1 = [path.split('\\')[-1] for path in reaction_folder_list1]
    # spectrum_name_list2 = [path.split('\\')[-1] for path in reaction_folder_list2]
    spectrum_name_dict1 = {int(item.split('-')[0]): item for item in spectrum_name_list1}
    # spectrum_name_dict2 = {int(item.split('-')[0]): item for item in spectrum_name_list2}


    # read the excel files into df
    df1 = pd.read_excel(excel_file1)
    # df2 = pd.read_excel(excel_file2)

    # map the spectrum_name_dict1 to the local_index in df1
    df1['spectrum_name'] = df1['local_index'].map(spectrum_name_dict1)
    # df2['spectrum_name'] = df2['local_index'].map(spectrum_name_dict2)

    # combine the two dfs
    # df_combined = pd.concat([df1, df2], ignore_index=True)
    df_combined = df1

    print(df_combined.head())

    # outVandC
    conc_vol_pipetting = outvandc_folder + r'\conc_vol_list.csv'
    df_conc_vol = pd.read_csv(conc_vol_pipetting)

    # merge the df_combined with df_conc_vol on 'global_index'
    df_merged = pd.merge(df_combined, df_conc_vol, on='global_index', how='left')
    # save to a new csv file
    output_csv = run_folder + r'\conc_for_all_reactions.csv'
    df_merged.to_csv(output_csv, index=False)

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
    print(df_merged.head())
    output_csv_merged = run_folder + r'\conditions_with_compd3_conc.csv'

    print(f"Saved merged conditions with compd3 concentration to {output_csv_merged}")

    df_merged.to_csv(output_csv_merged, index=False)
    print(f"Saved merged conditions with compd3 concentration to {output_csv_merged}")

    return df_merged

# df_merged = get_conc_for_all_reactions_one_run_folder()

def check_pulse_angle_in_dot_par_files():
    def find_all_dot_par_files_in_a_folder():
        from pathlib import Path
        # folder = Path(r"D:\Dropbox\brucelee\data\NV\Final Data") # Nick's data folder
        folder = Path(r"D:\Dropbox\brucelee\data\DPE_bromination")
        par_files = list(folder.rglob("*.par")) # recursively find all .par files
        return par_files

    par_files = find_all_dot_par_files_in_a_folder()
    df = pd.DataFrame(columns=["par_file", "pulse_angle"])
    for par_file in par_files:
        if not "1D EXTENDED+" in str(par_file):
            continue
        if 'SHIM' in str(par_file):
            continue
        # read the file by line
        with open(par_file, 'r') as file:
            lines = file.readlines()
        for i, line in enumerate(lines):
            if 'Options' in line:
                print(f"Found PulseAngle in {par_file} at line {i}: {line.strip()}")
                pulse_angle_line = line.strip()
                pulse_angle = int(re.search(r'PulseAngle\((\d+)\)', pulse_angle_line).group(1))
                dict_here = {"par_file": str(par_file), "pulse_angle": pulse_angle}
                df = df._append(dict_here, ignore_index=True)
                break

    df_90_degree = df[df['pulse_angle'] == 90]
    # save the df to a csv file
    output_csv = r"D:\Dropbox\brucelee\data\DPE_bromination\pulse_angle_check_90.csv"
    if not os.path.exists(os.path.dirname(output_csv)):
        os.makedirs(os.path.dirname(output_csv))
    df_90_degree.to_csv(output_csv, index=False)

    return df, df_90_degree

# df = check_pulse_angle_in_dot_par_files()


def put_run_condition_in_spectrum_folder(run_path=None):
    print(f'running: {path}')

    conc_file = run_path + r'//outVandC//out_concentrations.csv'
    df_global_conc = pd.read_csv(conc_file)
    columns_of_conc = ['conc_'+i for i in df_global_conc.columns[1:].tolist()]
    df_global_conc.columns = ['global_index'] + columns_of_conc

    run_folder_name = os.path.basename(run_path)
    excel_name = re.match(r'^(\d{4}-\d{2}-\d{2}-run\d{2})', run_folder_name).group(1)
    excel_file = run_path + r'\\' + excel_name + '.xlsx'
    assert os.path.exists(excel_file), "Run excel file not found: {excel_path}"
    df_run_excel = pd.read_excel(excel_file)
    # merge by 'global_index'
    df_merged = pd.merge(df_run_excel, df_global_conc, on='global_index', how='inner')  # or 'left' if needed

    # save each row to the corresponding folder
    results_folder = run_path + r'\\Results'

    # get all the subfolders
    subfolders = [
        os.path.join(results_folder, name)
        for name in os.listdir(results_folder)
        if os.path.isdir(os.path.join(results_folder, name))
    ]
    spec_folders_path = [folder for folder in subfolders if '1D EXTENDED' in folder]
    spec_folders_path = sorted(spec_folders_path,
                            key=lambda x: int(re.search(r'\\\s*(\d+)-1D EXTENDED', x).group(1)))
    spec_folders_name = [os.path.basename(folder) for folder in spec_folders_path]
    spec_indices = [int(name.split('-1D')[0]) for name in spec_folders_name]

    # save each row to corresponding spec folder
    for idx, spec_index in enumerate(spec_indices):
        # match spec_index with the df_merged row where its local_index is the same, and save to json
        match_row = df_merged[df_merged['local_index'] == spec_index]
        json_path = spec_folders_path[idx] + r"\\reaction_info.json"
        # Save as JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            row_dict = match_row.iloc[0].to_dict()
            json.dump(row_dict, f, ensure_ascii=False, indent=2)

def put_fitting_results_in_spec_folder(run_path=None):

    results_folder = run_path + r'\\Results'
    fitting_result_json = results_folder + r'\\fitting_results.json'
    assert os.path.exists(fitting_result_json), f"❌ File not found: {fitting_result_json}"
    with open(fitting_result_json, 'r', encoding='utf-8') as f:
        fitting_result_dict = json.load(f)

    # get all the subfolders
    subfolders = [
        os.path.join(results_folder, name)
        for name in os.listdir(results_folder)
        if os.path.isdir(os.path.join(results_folder, name))
    ]

    for key, values in fitting_result_dict.items():
        for folder in subfolders:
            if key in folder:
                # save the dict to the folder
                save_path = os.path.join(folder, 'fitting_result.json')
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(values, f, ensure_ascii=False, indent=2)

                print(f"✔ Saved {key} → {save_path}")
                break  # stop searching after the first match


if __name__ == '__main__':

    run_folders = [
        r"D:\Dropbox\brucelee\data\DPE_bromination\2025-02-19-run02_normal_run",
        r"D:\Dropbox\brucelee\data\DPE_bromination\2025-03-01-run01_normal_run",
        r"D:\Dropbox\brucelee\data\DPE_bromination\2025-03-03-run01_normal_run",
        r"D:\Dropbox\brucelee\data\DPE_bromination\2025-03-03-run02_normal_run",
        r"D:\Dropbox\brucelee\data\DPE_bromination\2025-03-05-run01_normal_run",
        r"D:\Dropbox\brucelee\data\DPE_bromination\2025-03-12-run01_better_shimming"
    ]
    for path in run_folders:
        # put_run_condition_in_spectrum_folder(path)
        put_fitting_results_in_spec_folder(path)


