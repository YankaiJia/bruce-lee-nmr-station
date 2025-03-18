from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
import json
import os
import re
import sys
# import gui_utils as gui
# use the TkAgg backend for matplotlib
import matplotlib
matplotlib.use('TkAgg')

import gui_tools as gui

def plot_integral(df, column_name_x, column_name_y, plot_name):
    labels = [f'reaction_{i}' for i in range(6)]
    ls=[i*6 for i in range(9)]
    for i in range(6):
        ls = [j*6+i for j in range(9)]
        df_chosen = df.loc[ls]
        plt.plot(df_chosen[column_name_x], 
                df_chosen[column_name_y], 
                label=labels[i],
                marker='o',)
                # linestyle='None')
        plt.xlabel(column_name_x)
        # plt.xscale('log')  # Set x-axis to log scale
        plt.ylabel(column_name_y)
        # set x limit to 0 to 20
        # plt.xlim(0, 20)
        plt.legend()
    # save the plot
    plt.savefig(folder + f'{column_name_y}_{plot_name}.png')
    plt.show()

# Example data (same as above)
def interpolate(interp_func, measured_integrals):
    
    try:
        # Attempt to get an iterator for measured_integrals
        _ = iter(measured_integrals)
        # If successful, treat measured_integrals as an iterable of values
        conc_ls = []
        for val in measured_integrals:
            if val == 0:
                conc_ls.append(0)
                continue
            estimated_conc = interp_func(val)
            conc_ls.append(abs(estimated_conc))
        return conc_ls
    except TypeError:
        # If we get a TypeError, measured_integrals is a single value
        return 0 if measured_integrals == 0 else abs(interp_func(measured_integrals))


def json_to_dataframe(json_file, is_delete_entry_with_warning=False):
    # Load the JSON from a file (or you can pass the JSON string directly to json.loads)
    with open(json_file, "r") as f:
        data = json.load(f)

    print(f'data: {data}')

    # exit()
    # raise ValueError("Stop here")

    # Convert to DataFrame:
    #   - orient="index" treats the top-level keys (reaction names) as row indices
    df = pd.DataFrame.from_dict(data, orient="index")

    if is_delete_entry_with_warning:
        # Check if 'Warning' column exists and exclude rows where 'Warning' is not empty
        if 'Warning' in df.columns:
            df = df[df['Warning'].apply(lambda x: x == {})]  # Keep rows where Warning is empty
            # df.drop(columns=['Warning'], inplace=True)  # Drop Warning column

    # Make sure all columns exist in the desired order:
    # desired_cols = ["Starting material", "Product A", "Product B"]
    # df = df.reindex(columns=desired_cols)

    # Move the index into a regular column named "Reaction name"
    df = df.reset_index().rename(columns={"index": "spectrum_name"})

    # df.columns = ['spectrum_name', "intg_S", "intg_A", "intg_B"]

    # get the dir of the json file
    json_dir = os.path.dirname(json_file)
    spectrum_dir = [os.path.join(json_dir, spectrum_name) for spectrum_name in df['spectrum_name']]
    df['spectrum_dir'] = spectrum_dir

    # change the column names according to the following dictionary
    col_names = {
        "Starting material": 'intg_S',  # ppm
        "Product A": 'intg_A',  # ppm
        "Product B": 'intg_B',  # ppm
        "SolventDown": 'intg_sol_down',  # ppm
        "SolventUp": 'intg_sol_up',  # ppm
        "Unknown impurity SM peak 1": 'intg_impr_SM1',  # ppm
        "Unknown impurity SM peak 2": 'intg_impr_SM2',  # ppm
        "Unknown impurity 1": 'intg_impr1',
        "Unknown impurity 2": 'intg_impr2',  # ppm
        "Unknown impurity 3": 'intg_impr3',  # ppm
        "Unknown impurity 4": 'intg_impr4',  # ppm
        "Alcohol": 'intg_alcohol',  # ppm
        "HBr_adduct": 'intg_HBr_adduct',  # ppm
        "Acid": 'intg_acid',  # ppm
    }

    # Rename columns
    df.rename(columns=col_names, inplace=True)

    return df


def get_interp_funcs(is_show_ref_curve=False):

    brucelee_path = gui.select_folder()
    # ref data
    folder_ref = brucelee_path + "\\data\\DPE_bromination\\_Refs\\"

    df_ref_S= json_to_dataframe(folder_ref+"\\ref_S\\Results\\fitting_results.json",
                                is_delete_entry_with_warning=False)
    df_ref_B= json_to_dataframe(folder_ref+"\\ref_B\\Results\\fitting_results.json",
                                is_delete_entry_with_warning=False)

    # df_ref_S.columns = ['name', "intg_S", "intg_A", "intg_B", "dir"]
    # df_ref_B.columns = ['name', "intg_S", "intg_A", "intg_B", "dir"]

    print(df_ref_S.head())
    print(df_ref_B.head())

    ref_conc_S = tuple([422.75, 211.375, 105.6875, 52.84375, 26.421875]) # conc in mM
    ref_conc_B = tuple([484.48, 242.24, 121.12, 60.56, 30.28]) # conc in mM

    # plot the reference curve. plot dots with lines
    plt.plot(df_ref_S['intg_S'], ref_conc_S,  'o-', label='S')
    plt.plot(df_ref_B['intg_B'], ref_conc_B,  's-', label='B')
    plt.xlabel('Integral')
    plt.ylabel('Concentration (mM)')
    plt.legend()
    # save the plot
    plt.savefig(folder_ref + 'ref_curve.png')
    if is_show_ref_curve:
        plt.show()

    # Create interpolation functions (linear by default)
    interp_func_S = interp1d(df_ref_S['intg_S'], ref_conc_S, 
                            kind='linear',fill_value="extrapolate")

    interp_func_B = interp1d(df_ref_B['intg_B'],ref_conc_B, 
                            kind='linear',fill_value="extrapolate")

    # display the interpolation curve and the parameters
    print(interp_func_S)
    print(interp_func_B)


    # Generate fine-grained x values for smooth interpolation curve
    x_smooth_S = np.linspace(min(df_ref_S['intg_S']), max(df_ref_S['intg_S']), 100)
    x_smooth_B = np.linspace(min(df_ref_B['intg_B']), max(df_ref_B['intg_B']), 100)

    # Compute interpolated values
    y_interp_S = interp_func_S(x_smooth_S)
    y_interp_B = interp_func_B(x_smooth_B)

    # Plot the interpolation curves
    plt.figure()
    plt.plot(df_ref_S['intg_S'], ref_conc_S, 'o', label='S Data')
    plt.plot(x_smooth_S, y_interp_S, '-', label='S Interp')

    plt.plot(df_ref_B['intg_B'], ref_conc_B, 's', label='B Data')
    plt.plot(x_smooth_B, y_interp_B, '-', label='B Interp')

    plt.xlabel('Integral')
    plt.ylabel('Concentration (mM)')
    plt.legend()
    plt.grid(True)

    # Save and optionally show the interpolation curve
    plt.savefig(folder_ref + 'interp_curve.png')
    if is_show_ref_curve:
        plt.show()

    return interp_func_S, interp_func_B

# interp_func_S, interp_func_B = get_interp_funcs()


def interpolate_one_folder(result_folder, is_save_csv=False):

    interp_func_S, interp_func_B = get_interp_funcs()

    # read from integrations json file
    json_file = result_folder + "\\fitting_results.json"

    df = json_to_dataframe(json_file, is_delete_entry_with_warning=False)
    # fill the NaN values with 0
    df = df.fillna(0)
    print(df.head())
    
    # S: 2H, B: 1H, A: 1H. S is DPE
    # int_s / (2 * conc_s) = int_b / conc_b = int_a / (2 * conc_a)
    # get conc from reference curve of S and use it as internal standard
    interpolated_conc_S_from_ref_S = interpolate(interp_func = interp_func_S, measured_integrals=df['intg_S'])
    # interpolated_conc_B_from_ref_S = 2 * df['intg_B'] / (df['intg_S'] / interpolated_conc_S_from_ref_S)
    # interpolated_conc_A_from_ref_S = 1 * df['intg_A'] / (df['intg_S'] / interpolated_conc_S_from_ref_S)
    interpolated_conc_B_from_ref_S = interpolate(interp_func = interp_func_S, measured_integrals=df['intg_B'] * 2)
    interpolated_conc_A_from_ref_S = interpolate(interp_func = interp_func_S, measured_integrals=df['intg_A'] * 1)

    # get conc from reference curve of B and use it as internal standard        
    interpolated_conc_B_from_ref_B = interpolate(interp_func = interp_func_B,measured_integrals=df['intg_B'])
    # interpolated_conc_S_from_ref_B = 0.5 * df['intg_S'] / (df['intg_B'] / interpolated_conc_B_from_ref_B)
    # interpolated_conc_A_from_ref_B = 0.5 * df['intg_A'] / (df['intg_B'] / interpolated_conc_B_from_ref_B)
    interpolated_conc_S_from_ref_B = interpolate(interp_func = interp_func_B,measured_integrals=df['intg_S'] * 0.5)
    interpolated_conc_A_from_ref_B = interpolate(interp_func = interp_func_B,measured_integrals=df['intg_A'] * 0.5)

    df['c#_S_from_S'] = interpolated_conc_S_from_ref_S
    df['c#_S_from_B'] = interpolated_conc_S_from_ref_B
    df['c#_B_from_S'] = interpolated_conc_B_from_ref_S
    df['c#_B_from_B'] = interpolated_conc_B_from_ref_B
    df['c#_A_from_S'] = interpolated_conc_A_from_ref_S
    df['c#_A_from_B'] = interpolated_conc_A_from_ref_B

    col_list = ['intg_sol_down', 'intg_sol_up',  'intg_impr_SM1',  'intg_impr_SM2',
                 'intg_impr1','intg_impr2',  'intg_impr3',  'intg_impr4',
                 'intg_alcohol',  'intg_HBr_adduct',  'intg_acid']

    for col_name in col_list:
        if not col_name in df.columns:
            continue
        conc_str = col_name.replace('intg_', 'c#_')
        df[conc_str+'_from_S'] = interpolate(interp_func = interp_func_S,measured_integrals=df[col_name])
        df[conc_str+'_from_B'] = interpolate(interp_func = interp_func_B,measured_integrals=df[col_name])

    # plot the integral vs conc on the reference curve
    # Prepare data for plotting
    plt.figure(figsize=(10, 5))

    # Scatter plots for interpolated concentrations
    plt.scatter(df['intg_S'], interpolated_conc_S_from_ref_S, label="S from Ref S", marker='o')
    plt.scatter(df['intg_B'], interpolated_conc_B_from_ref_S, label="B from Ref S", marker='s')
    plt.scatter(df['intg_A'], interpolated_conc_A_from_ref_S, label="A from Ref S", marker='^')

    plt.scatter(df['intg_S'], interpolated_conc_S_from_ref_B, label="S from Ref B", marker='o', facecolors='none', edgecolors='r')
    plt.scatter(df['intg_B'], interpolated_conc_B_from_ref_B, label="B from Ref B", marker='s', facecolors='none', edgecolors='r')
    plt.scatter(df['intg_A'], interpolated_conc_A_from_ref_B, label="A from Ref B", marker='^', facecolors='none', edgecolors='r')

    plt.xlabel("Integral")
    plt.ylabel("Interpolated Concentration (mM)")
    plt.legend()
    plt.grid(True)
    # set x limit to 0 to 50
    plt.xlim(0, 50)
    # set y limit to 0 to 300
    plt.ylim(0, 250)
    # plt.show()
    plt.savefig(result_folder + 'integral_vs_conc.png')

    print(df.head(20))

    # save df to csv
    if is_save_csv:
        df.to_csv(result_folder + "\\conc_interpolated.csv")

    return df

if __name__ == "__main__":

    brucelee_path = gui.select_folder()
    result_folder = brucelee_path + "\\data\\DPE_bromination\\2025-02-19-run02_normal_run\\Results"
    #
    df= interpolate_one_folder(result_folder,is_save_csv=True)

    # interp_func_S, interp_func_B = get_interp_funcs(is_show_ref_curve=False)


        
