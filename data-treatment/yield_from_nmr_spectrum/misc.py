import json

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
        r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\4-Pyrrolidinopyridine\2025-05-19-run01_MeCN_4_pyrrolidinopyridine\Results",
        r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\4-Pyrrolidinopyridine\2025-05-19-run02_MeCN_4_pyrrolidinopyridine\Results"
    ]

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

    return compd3_conc_dict

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

merge_result_from_hardy_fitting()