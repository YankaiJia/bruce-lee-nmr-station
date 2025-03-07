from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
import json

# import gui_utils as gui

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


def json_to_dataframe(json_file):
    # Load the JSON from a file (or you can pass the JSON string directly to json.loads)
    with open(json_file, "r") as f:
        data = json.load(f)

    # Convert to DataFrame:
    #   - orient="index" treats the top-level keys (reaction names) as row indices
    df = pd.DataFrame.from_dict(data, orient="index")

    # Make sure all columns exist in the desired order:
    desired_cols = ["Starting material", "Product A", "Product B"]
    df = df.reindex(columns=desired_cols)

    # Move the index into a regular column named "Reaction name"
    df = df.reset_index().rename(columns={"index": "Reaction name"})

    # At this point, df will have columns:
    #   Reaction name | Starting material | Product A | Product B

    df.columns = ['name', "intg_S", "intg_A", "intg_B"]
    # df = df.reindex(columns=desired_cols)
    return df


def get_interp_funcs():
    # ref data
    folder_ref = "D:\\Dropbox\\brucelee\\data\\DPE_bromination\\_Refs\\"

    df_ref_S= json_to_dataframe(folder_ref+"\\ref_S\\Results\\integration_results.json")
    df_ref_B= json_to_dataframe(folder_ref+"\\ref_B\\Results\\integration_results.json")
    df_ref_S.columns = ['name', "intg_S", "intg_A", "intg_B"]
    df_ref_B.columns = ['name', "intg_S", "intg_A", "intg_B"]


    print(df_ref_S.head())
    print(df_ref_B.head())
    ref_conc_S = tuple([422.75, 211.375, 105.6875, 52.84375, 26.421875]) # conc in mM
    ref_conc_B = tuple([484.48, 242.24, 121.12, 60.56, 30.28]) # conc in mM

    # Create interpolation functions (linear by default)
    interp_func_S = interp1d(df_ref_S['intg_S'], ref_conc_S, 
                            kind='linear',fill_value="extrapolate")

    interp_func_B = interp1d(df_ref_B['intg_B'],ref_conc_B, 
                            kind='linear',fill_value="extrapolate")
    
    return interp_func_S, interp_func_B

if __name__ == "__main__":

    interp_func_S, interp_func_B = get_interp_funcs()

    # folder to analyze
    # data_folders = gui.select_folders()

    run_folders = ["D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-02-19-run02_normal_run\\",
                    "D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-03-01-run01_normal_run\\",
                    "D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-03-03-run01_normal_run\\",
                    "D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-03-03-run02_normal_run\\"
                    ]

    # results_folders = [i+"\\Results" for i in run_folders]
    
    for run_folder in run_folders:

        result_folder = run_folder + "\\Results"
        
        # read from json file
        json_file = result_folder+ "\\integration_results.json"

        df = json_to_dataframe(json_file)
        # fill the NaN values with 0
        df = df.fillna(0)
        print(df.head())
        
        # S: 2H, B: 1H, A: 1H. S is DPE
        # int_s / (2 * conc_s) = int_b / conc_b = int_a / (2 * conc_a)
        interpolated_conc_S_from_ref_S = interpolate(interp_func = interp_func_S, 
                                        measured_integrals=df['intg_S'])
        # get conc from reference curve of S and use it as internal standard             
        interpolated_conc_B_from_ref_S = 2 * df['intg_B'] / (df['intg_S'] / interpolated_conc_S_from_ref_S)
        interpolated_conc_A_from_ref_S = 1 * df['intg_A'] / (df['intg_S'] / interpolated_conc_S_from_ref_S)
        
        
        # get conc from reference curve of B and use it as internal standard        
        interpolated_conc_B_from_ref_B = interpolate(interp_func = interp_func_B,
                                        measured_integrals=df['intg_B'])
        interpolated_conc_S_from_ref_B = 0.5 * df['intg_S'] / (df['intg_B'] / interpolated_conc_B_from_ref_B)
        interpolated_conc_A_from_ref_B = 0.5 * df['intg_A'] / (df['intg_B'] / interpolated_conc_B_from_ref_B)

        df['S_from_S'] = interpolated_conc_S_from_ref_S
        df['S_from_B'] = interpolated_conc_S_from_ref_B
        df['B_from_S'] = interpolated_conc_B_from_ref_S
        df['B_from_B'] = interpolated_conc_B_from_ref_B
        df['A_from_S'] = interpolated_conc_A_from_ref_S
        df['A_from_B'] = interpolated_conc_A_from_ref_B

        print(df.head(20))

        # save df to csv
        # df.to_csv(result_folder + "\\conc_interpolated.csv")

        # read volumns from the excel file of pipetting
        run_name = os.path.basename(run_folder)
        # formation of run folder: yyyy-mm-dd-run0x(-note1-note2)
        # get real run name with regex
        excel_file = data_folder
