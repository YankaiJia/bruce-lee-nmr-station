""""
Interpolation of concentrations for bromination reactions.
"""

from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from sklearn.linear_model import LinearRegression

import json
import os

import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend (no GUI)
plt.ioff() # Turn off interactive mode, so multithreading will work

import config

DATA_ROOT = config.DATA_ROOT

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

    """" Transform a JSON file into a DataFrame"""

    # Load the JSON from a file
    with open(json_file, "r") as f:
        data = json.load(f)

    # Convert to DataFrame
    df = pd.DataFrame.from_dict(data, orient="index")

    # Rename the index column to "Reaction name"
    df = df.reset_index().rename(columns={"index": "spectrum_name"})

    # Drop rows if the Warning column is not empty
    if is_delete_entry_with_warning:
        if 'Warning' in df.columns:
            df = df[df['Warning'].apply(lambda x: x == {})]  # Keep rows where Warning is empty
            # df.drop(columns=['Warning'], inplace=True)  # Drop Warning column

    # Append the dir of the spectrum to the DataFrame
    json_dir = os.path.dirname(json_file) # get the dir of the json file
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
    df.rename(columns=col_names, inplace=True)  # Rename columns

    return df


def get_interp_funcs(solvent_name, is_show_ref_curve=False, ):

    if solvent_name == 'DCE':
        # ref raw data
        folder_ref = DATA_ROOT + "\\DPE_bromination\\_Refs\\"
        df_ref_S= json_to_dataframe(folder_ref+"\\ref_S\\Results\\fitting_results.json")
        df_ref_B= json_to_dataframe(folder_ref+"\\ref_B\\Results\\fitting_results.json")

        # sort the ref_B dataframe by intg_B, from high to low
        df_ref_B.sort_values(by='intg_B', ascending=False, inplace=True)
        df_ref_B.reset_index(drop=True, inplace=True)
        # sort the ref_S dataframe by intg_S, from high to low
        df_ref_S.sort_values(by='intg_S', ascending=False, inplace=True)
        df_ref_S.reset_index(drop=True, inplace=True)


        # known conc in mM
        ref_conc_S = tuple([422.75, 211.375, 105.6875, 52.84375, 26.421875]) # known conc in mM
        ref_conc_B = tuple([484.48, 242.24, 121.12, 60.56, 30.28]) # known conc in mM

        print(f'folder for references: {folder_ref}')

    elif solvent_name == 'MeCN':
        # ref raw data
        folder_ref = DATA_ROOT + "\\DPE_bromination\\_Refs_MeCN\\"
        df_ref_S= json_to_dataframe(folder_ref+"\\ref_S\\Results\\fitting_results.json")
        df_ref_B= json_to_dataframe(folder_ref+"\\ref_B\\Results\\fitting_results.json")

        # sort the ref_B dataframe by intg_B, from high to low
        df_ref_B.sort_values(by='intg_B', ascending=False, inplace=True)
        df_ref_B.reset_index(drop=True, inplace=True)
        # sort the ref_S dataframe by intg_S, from high to low
        df_ref_S.sort_values(by='intg_S', ascending=False, inplace=True)
        df_ref_S.reset_index(drop=True, inplace=True)

        # known conc in mM
        ref_conc_B = tuple([553.430, 221.372, 110.686, 55.3430, 27.6715])
        ref_conc_S = tuple([425.350, 212.675, 106.338, 53.169, 26.584])

        print(f'folder for references: {folder_ref}')
        print(f'df_ref_B: {df_ref_B["intg_B"]}')
        print(f'df_ref_S: {df_ref_S["intg_S"]}')

    # Normalize the integrals by number of protons
    S_proton_count, B_proton_count = 2, 1
    S_intg_norm = df_ref_S['intg_S'] / S_proton_count
    B_intg_norm = df_ref_B['intg_B'] / B_proton_count

    # Combine normalized integration and concentration
    combined_intg = np.concatenate([S_intg_norm, B_intg_norm])
    combined_conc = np.concatenate([ref_conc_S, ref_conc_B])

    # create a single calibration curve
    # interp_func_combined = interp1d(combined_intg, combined_conc, kind='linear', fill_value='extrapolate')

    # Use linear regression to fit the calibration curve
    model = LinearRegression(fit_intercept=False)
    model.fit(combined_intg.reshape(-1, 1), combined_conc)

    # Plot if requested
    if is_show_ref_curve:
        x_range = np.linspace(min(combined_intg) * 0.9, max(combined_intg) * 1.1, 200)
        y_interp = model.predict(x_range.reshape(-1, 1))

        plt.figure(figsize=(8, 6))
        plt.plot(S_intg_norm, ref_conc_S, 'bo', label='S data (2H)')
        plt.plot(B_intg_norm, ref_conc_B, 'go', label='B data (1H)')
        plt.plot(x_range, y_interp, 'r-', label='Combined calibration (interp1d)')
        plt.xlabel('Normalized Integration (area per proton)')
        plt.ylabel('Concentration (mM)')
        plt.title('Unified NMR Calibration Curve')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(folder_ref + f'calibration_curve_{solvent_name}.png')

    return model

def interpolate_one_folder(result_folder, is_save_csv=False, is_show_plot=False):

    solvent_name = "MeCN" if "MeCN" in result_folder else "DCE"
    print(f"Solvent name: {solvent_name}")

    lin_reg_model = get_interp_funcs(solvent_name=solvent_name, is_show_ref_curve=True)

    # read from integrations json file
    json_file = result_folder + "\\fitting_results.json"

    df = json_to_dataframe(json_file, is_delete_entry_with_warning=False)
    # fill the NaN values with 0
    df = df.fillna(0)
    print(df.head())
    
    # S: 2H, B: 1H, A: 2H. S is DPE
    S_proton_count, A_proton_count, B_proton_count = 2, 2, 1
    # Normalize integration values
    S_intg_norm = df['intg_S'] / S_proton_count
    A_intg_norm = df['intg_A'] / A_proton_count
    B_intg_norm = df['intg_B'] / B_proton_count

    print(f"S_intg_norm: {S_intg_norm}")

    def calculate_conc_by_interpolation(intg_norm: list, interpolate_func=lin_reg_model):

        conc_list = interpolate_func.predict(intg_norm)

        # Set predicted values to zero where the original input was zero
        intg_norm = np.array(intg_norm).flatten()  # Ensure it's a 1D array
        conc_list[intg_norm == 0] = 0  # zero_mask = intg_norm == 0

        # assert all conc_list are non-negative
        assert (conc_list >= 0).all(), "Negative concentration found in calculated concentrations"

        return conc_list

    # Calculate concentrations by interpolation
    df['conc_S'] = calculate_conc_by_interpolation(S_intg_norm.values.reshape(-1, 1))
    df['conc_A'] = calculate_conc_by_interpolation(A_intg_norm.values.reshape(-1, 1))
    df['conc_B'] = calculate_conc_by_interpolation(B_intg_norm.values.reshape(-1, 1))

    col_list = ['intg_sol_down', 'intg_sol_up',  'intg_impr_SM1',  'intg_impr_SM2',
                 'intg_impr1','intg_impr2',  'intg_impr3',  'intg_impr4',
                 'intg_alcohol',  'intg_HBr_adduct',  'intg_acid']

    for col_name in col_list:
        if not col_name in df.columns:
            continue
        conc_str = col_name.replace('intg_', 'conc_')
        print(f"Processing column: {col_name} -> {conc_str}")

        # assuming the number of protons is 1 unless specified otherwise
        if 'HBr_adduct' in conc_str:
            proton_count = 3
        else:
            proton_count = 1

        intg_norm_here = df[col_name].values.reshape(-1, 1) / proton_count

        df[conc_str] = lin_reg_model.predict(intg_norm_here)

        # Set predicted values to zero where the original input was zero
        df.loc[df[col_name] == 0, conc_str] = 0  #zero_mask = df[col_name] == 0
        # assert all conc_str are non-negative
        assert (df[conc_str] >= 0).all(), f"Negative concentration found in {conc_str}"

    # plot the integral vs conc on the reference curve
    # Prepare data for plotting
    plt.figure(figsize=(10, 5))

    # Scatter plots for interpolated concentrations
    plt.scatter(S_intg_norm, df['conc_S'], label="S", marker='o')
    plt.scatter(B_intg_norm, df['conc_B'], label="B", marker='s')
    plt.scatter(A_intg_norm, df['conc_A'], label="A", marker='^')

    plt.xlabel("Integral")
    plt.ylabel("Interpolated Concentration (mM)")
    plt.legend()
    plt.grid(True)
    # set x limit to 0 to 50
    plt.xlim(0, 50)
    # set y limit to 0 to 300
    plt.ylim(0, 250)
    plt.savefig(result_folder + 'integral_vs_conc.png')
    plt.show() if is_show_plot else plt.close()

    # save df to csv
    if is_save_csv:
        df.to_csv(result_folder + "\\conc_interpolated.csv")

    return df

if __name__ == "__main__":

    # result_folder = DATA_ROOT + "\\DPE_bromination\\2025-02-19-run02_normal_run\\Results"

    result_folder = DATA_ROOT + "\\DPE_bromination\\2025-02-19-run02_normal_run\\Results"

    df= interpolate_one_folder(result_folder,is_save_csv=True, is_show_plot=False)

    # interp_func_S, interp_func_B = get_interp_funcs(is_show_ref_curve=False)


        
