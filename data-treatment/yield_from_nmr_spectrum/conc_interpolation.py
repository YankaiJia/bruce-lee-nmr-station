from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
import json

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
            estimated_conc = interp_func(val)
            conc_ls.append(abs(estimated_conc))
        return conc_ls
    except TypeError:
        # If we get a TypeError, measured_integrals is a single value
        return abs(interp_func(measured_integrals))


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

    df.columns = ['name', "DPE", "Prod_A", "Prod_B"]
    # df = df.reindex(columns=desired_cols)
    return df

if __name__ == "__main__":

    # ref data
    folder_ref = "D:\\Dropbox\\brucelee\\data\\DPE_bromination\\_Refs\\"

    df_ref_S= json_to_dataframe(folder_ref+"\\ref_S\\Results\\integration_results.json")
    df_ref_B= json_to_dataframe(folder_ref+"\\ref_B\\Results\\integration_results.json")
    print(df_ref_S.head())
    print(df_ref_B.head())
    ref_conc_S = tuple([422.75, 211.375, 105.6875, 52.84375, 26.421875]) # conc in mM
    ref_conc_B = tuple([484.48, 242.24, 121.12, 60.56, 30.28]) # conc in mM

    # Create interpolation functions (linear by default)
    interp_func_S = interp1d(df_ref_S['DPE'], ref_conc_S, 
                            kind='linear',fill_value="extrapolate")

    interp_func_B = interp1d(df_ref_B['Prod_B'],ref_conc_B, 
                            kind='linear',fill_value="extrapolate")

    # read from json file
    json_file = "D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-02-19-run02_normal_run\\Results\\integration_results.json"

    df = json_to_dataframe(json_file)
    # fill the NaN values with 0
    df = df.fillna(0)
    print(df.head())
    
    # Interpolate the concentrations
    interpolated_conc_S = interpolate(interp_func = interp_func_S, 
                                    measured_integrals=df['DPE'])

    interpolated_conc_B = interpolate(interp_func = interp_func_B,
                                    measured_integrals=df['Prod_B'])

    exit()











    # Save the interpolated concentrations to a csv file
    df_S['Concentration(mM)'] = np.array(conc_S)*5.6
    df_B['Concentration(mM)'] = conc_B
    df_S.to_csv(folder + 'conc_S.csv', index=False)
    df_B.to_csv(folder + 'conc_B.csv', index=False)

    df_B['Concentration(mM)'][41] = 230 # this is an outlier
    plot_integral(df_S, 'Time(hrs)', 'Concentration(mM)', 'S')
    plot_integral(df_B, 'Time(hrs)', 'Concentration(mM)', 'B')