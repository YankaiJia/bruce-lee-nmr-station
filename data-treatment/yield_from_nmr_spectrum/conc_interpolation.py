from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d



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
def interpolate(ref_concs, ref_integrals, measured_integrals):
    conc_ls = []
    # Create an interpolation function (linear by default)
    interp_func = interp1d(ref_integrals, ref_concs, kind='linear',fill_value="extrapolate")
    for measured_integral in measured_integrals:
        # Estimate the concentration for the new integral
        estimated_conc_scipy = interp_func(measured_integral)
        conc_ls.append(abs(estimated_conc_scipy))
    return conc_ls


if __name__ == "__main__":

    folder = "D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-02-19-run01_time_varied\\Results\\"
    path_S = folder + "integrals_S.csv"
    path_B = folder + "integrals_B.csv"

    df_S = pd.read_csv(path_S)
    df_B = pd.read_csv(path_B)

    plot_integral(df_S, 'Time(hrs)', 'Integral', 'S')
    plot_integral(df_B, 'Time(hrs)', 'Integral', 'B')

    # Interpolation
    folder_ref = "D:\\Dropbox\\brucelee\\data\\DPE_bromination\\_Refs\\"
    path_ref_S = folder_ref + "\\ref_S\\integrals.csv"
    path_ref_B = folder_ref + "\\ref_B\\integrals.csv"
    df_ref_S = pd.read_csv(path_ref_S)
    df_ref_B = pd.read_csv(path_ref_B)


    conc_S = interpolate(ref_concs=df_ref_S['Concentration(mM)'], 
                ref_integrals=df_ref_S['Integral'], 
                measured_integrals=df_S['Integral'])

    conc_B = interpolate(ref_concs=df_ref_B['Concentration(mM)'],
                ref_integrals=df_ref_B['Integral'],
                measured_integrals=df_B['Integral'])

    # Save the interpolated concentrations to a csv file
    df_S['Concentration(mM)'] = np.array(conc_S)*5.6
    df_B['Concentration(mM)'] = conc_B
    df_S.to_csv(folder + 'conc_S.csv', index=False)
    df_B.to_csv(folder + 'conc_B.csv', index=False)

    df_B['Concentration(mM)'][41] = 230 # this is an outlier
    plot_integral(df_S, 'Time(hrs)', 'Concentration(mM)', 'S')
    plot_integral(df_B, 'Time(hrs)', 'Concentration(mM)', 'B')