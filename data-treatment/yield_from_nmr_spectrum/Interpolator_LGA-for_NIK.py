import pandas as pd
import csv
import numpy as np
import json
import matplotlib.pyplot as plt
import os
from sklearn.linear_model import LinearRegression

def load_csv_after_rows(path):
    csvFile = pd.read_csv(path)
    return csvFile

def load_nmr_json(json_paths):
    dictionnary_experiments = {}
    for path in json_paths:
        with open(path, 'r') as f:
            nmr_json = json.load(f)
            dictionnary_experiments.update(nmr_json)
    
    return dictionnary_experiments
    
 

def average_integrations(*integration_lists):
    arrays = [np.array(lst) for lst in integration_lists]
    return np.mean(arrays, axis=0)

def fit_linear_model(x, y):
    model = LinearRegression()
    model.fit(np.array(x).reshape(-1, 1), y)
    return model.coef_[0], model.intercept_

def interpolate(integration, slope, intercept):
    return slope * integration + intercept

def interpolate_scaled(integration, slope, intercept, scale):
    return slope * scale * integration + intercept

def merge_and_calculate(df_csv, dictionnary_nmr, slope, intercept):
    concentration_sm=0.128
    df_csv["conc_1c"]= df_csv.iloc[:, 3]*concentration_sm / (df_csv.iloc[:,2]+df_csv.iloc[:,3]+df_csv.iloc[:,4]+df_csv.iloc[:,5]) * 1000   #Add if a diluted solution is used: +df_csv.iloc[:,6]) * 1000
    print(df_csv)
    df_csv["Integration Benzoin"]=0
    df_csv["Concentration Benzoin"]=0
    df_csv["Yield Benzoin"]=0

    df_csv["Integration Unknown double doublet"]=0
    df_csv["Concentration Unknown double doublet"]=0
    df_csv["Yield Unknown double doublet"]=0
    
    for item in dictionnary_nmr:
        integration = 0
        for index in range (df_csv.shape[0]):
            if df_csv.at[index,"spectrum_name"] == item:
                if "unkown-double_doublet_1" in dictionnary_nmr[item]:
                    integration += dictionnary_nmr[item]["unkown-double_doublet_1"]
                if "unkown-double_doublet_2" in dictionnary_nmr[item]:
                    integration += dictionnary_nmr[item]["unkown-double_doublet_2"]
                if "unkown-double_doublet_3" in dictionnary_nmr[item]:
                    integration += dictionnary_nmr[item]["unkown-double_doublet_3"]
                if "unkown-double_doublet_4" in dictionnary_nmr[item]:
                    integration += dictionnary_nmr[item]["unkown-double_doublet_4"]
                df_csv.at[index, "Integration Unknown double doublet"] = integration
                continue

    for item in dictionnary_nmr:
        integration = 0
        for index in range (df_csv.shape[0]):
            if df_csv.at[index,"spectrum_name"] == item:
                if "Benzoin_monomethoxy-CH1" in dictionnary_nmr[item]:
                    integration += dictionnary_nmr[item]["Benzoin_monomethoxy-CH1"]
                if "Benzoin_monomethoxy-CH2" in dictionnary_nmr[item]:
                    integration += dictionnary_nmr[item]["Benzoin_monomethoxy-CH2"]
                df_csv.at[index, "Integration Benzoin"] = integration
                continue

    df_csv['Concentration Unknown double doublet'] = interpolate(df_csv["Integration Unknown double doublet"], slope, intercept)
    df_csv['Yield Unknown double doublet'] = 100* df_csv['Concentration Unknown double doublet'] / (df_csv["conc_1c"])

    df_csv['Concentration Benzoin'] = interpolate(df_csv["Integration Benzoin"], slope, intercept)
    df_csv['Yield Benzoin'] = 100* df_csv['Concentration Benzoin'] / (df_csv["conc_1c"]*2)
    
    print (df_csv)
    return df_csv

def plot_graph(df, x_col, y_col, color_col, label_col, xlim=None, ylim=None, vmin=None, vmax=None, unit=None, colorbar_label=None):
    """
    Plots a single scatter plot based on selected columns.

    Parameters:
        df (pd.DataFrame): Input DataFrame.
        x_col (str): Column name for X-axis.
        y_col (str): Column name for Y-axis.
        color_col (str): Column name for color mapping.
        label_col (str): Column name for labeling points.
        colorbar_label (str, optional): Label for the colorbar.
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    
    scatter = ax.scatter(
        df[x_col],
        df[y_col],
        c=df[color_col],
        cmap='plasma',
        s=200,
        edgecolor='k',
        vmin=0,
        vmax=100
    )
    
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label(colorbar_label if colorbar_label else color_col)
    
    # Increase the offset for labels (e.g., 10 pixels right and up)
    label_memory = 0
    second_serie = False
    for i in range(len(df)):
        first_label = str(df[label_col].iloc[i])
        if label_memory > (df[label_col].iloc[i]):
            second_serie = True
        label_memory=(df[label_col].iloc[i])
        second_label = f"{df[color_col].iloc[i]:.0f}"  # Format decimal 
        if second_serie:
            full_label = f"Idx:{first_label}-2\n{second_label}{unit}"  

        else:
            full_label = f"Idx:{first_label}\n{second_label}{unit}"  

        ax.annotate(
            full_label,
            (df[x_col].iloc[i], df[y_col].iloc[i]),
            fontsize=8,
            alpha=0.8,
            xytext=(5, 5),
            textcoords='offset points'
        )
        
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(f'{x_col} vs {y_col} (Color: {color_col})')
    
    if xlim:
        ax.set_xlim(xlim)
    if ylim:
        ax.set_ylim(ylim)



    #plt.show()
    return fig

def plot_calibration_and_data(df, x_col, y_col, slope, intercept):
    """
    Plots scatter of data points and fitted calibration line.

    Parameters:
        df (pd.DataFrame): Input DataFrame.
        x_col (str): Column name for X-axis (e.g., 'Concentration_PhCHO').
        y_col (str): Column name for Y-axis (e.g., 'Conc_p-Methoxybenzaldehyde-Carbonyl').
        slope (float): Slope of the fitted calibration model.
        intercept (float): Intercept of the fitted calibration model.
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Scatter plot of actual data
    ax.scatter(x_col, y_col, color='blue', label='Data Points')
    
    # Generate X values for the fitted line
    x_fit = np.linspace(min(x_col), max(x_col), 100)
    y_fit = slope * x_fit + intercept
    
    # Plot the fitted line
    ax.plot(x_fit, y_fit, color='red', label=f'Line: y = {slope:.3f}x + {intercept:.3f}')
    
    ax.set_xlabel('Concentration Benzoin (uM)')
    ax.set_ylabel('Integration H NMR')
    ax.set_title('Calibration Line vs Data Points')
    ax.legend()
    
    plt.show()


def main():
    # List of (csv_path, json_path) tuples
    dataset_paths = [

        # # Pyridine
        (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\Pyridine_cmpd\run_result_combined.csv", 
        [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\Pyridine_cmpd\2025-05-15-run01_MeCN_Pyr\Results\fitting_results.json"]),

        # # DMAP
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\DMAP\run_result_combined.csv", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\DMAP\2025-06-16-run01_MeCN_DMAP\Results\fitting_results.json",
        # r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\DMAP\2025-06-16-run02_MeCN_DMAP\Results\fitting_results.json"]),

        # 4-Pyrrolidinopyridine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Pyrrolidinopyridine\run_result_combined.csv", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Pyrrolidinopyridine\2025-05-19-run01_MeCN_4_pyrrolidinopyridine\Results\fitting_results.json",
        # r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Pyrrolidinopyridine\2025-05-19-run02_MeCN_4_pyrrolidinopyridine\Results\fitting_results.json"]),

        # # 4-Morpholino pyridine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Morpholino pyridine\run_result_combined.csv", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Morpholino pyridine\2025-06-20-run01_MeCN_4_Morph_Pyr\Results\fitting_results.json",
        # r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Morpholino pyridine\2025-06-20-run02_MeCN_4_Morph_Pyr\Results\fitting_results.json"]),

        # 4-Methyl pyridine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methyl pyridine\run_result_combined.csv", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methyl pyridine\2025-06-18-run01_MeCN_4_Me_Pyr\Results\fitting_results.json",
        # r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methyl pyridine\2025-06-18-run02_MeCN_4_Me_Pyr\Results\fitting_results.json"]),

        # 4-Methoxy pyridine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methoxy pyridine\run_result_combined.csv", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methoxy pyridine\2025-06-22-run01_MeCN_4_Methoxy_Pyr\Results\fitting_results.json",
        # r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methoxy pyridine\2025-06-22-run02_MeCN_4_Methoxy_Pyr\Results\fitting_results.json"]),

    ]

    output_path=r"C:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\Pyridine_cmpd"
    CSV_path = output_path+r"\CSV_Pyr_Final.csv"
    graph_path =  output_path+r"\Graph_"




    # Calibration values (same across all datasets)
    concentrations = [1, 5, 10, 20, 30, 40]
    #Based on: Voigt Model1
    avg_integrations = [ 0.0801355799917056,
                        0.11599857529630507+0.16631693270585013,
                        0.31388639951035774+0.32183804682600353,
                        0.4761589598811118+0.486672555648419, 
                        0.841743510340705+0.8133081903368717,
                        1.1708533529756018+1.0451229871106824]

    # Fit the calibration model
    slope, intercept = fit_linear_model(avg_integrations, concentrations )
    print(f"Fitted linear model: slope = {slope:.6f}, intercept = {intercept:.6f}")

    # Process and combine all datasets
    for csv_path, json_path in dataset_paths:
        df_csv = load_csv_after_rows(csv_path)
        dictionnary_nmr = load_nmr_json(json_path)
        df_final = merge_and_calculate(df_csv, dictionnary_nmr, slope, intercept)
        
          
    #plot_calibration_and_data(df_final, y_col=concentrations, x_col=avg_integrations, slope=slope, intercept=intercept)
    
    fig=plot_graph(df_final, x_col='conc_Nucleophile ', y_col='conc_PhCHO', color_col='Yield Benzoin', label_col='local_index',xlim=(-20,650), ylim=(-20,650), unit="%")
    #Save the plot as a PNG file
    fig.savefig(f'{graph_path}_benzoin.png', format='png')
    #Clear the figure to avoid overlapping plots if this is inside a loop
    plt.close()

    fig=plot_graph(df_final, x_col='conc_Nucleophile ', y_col='conc_PhCHO', color_col='Yield Unknown double doublet', label_col='local_index',xlim=(-20,650), ylim=(-20,650), unit="%")
    #Save the plot as a PNG file
    fig.savefig(f'{graph_path}_unknown_doublet.png', format='png')
    #Clear the figure to avoid overlapping plots if this is inside a loop
    plt.close()

    df_final.to_csv(CSV_path, index=False)
    print(f"Saved combined output to: {CSV_path}")


if __name__ == "__main__":
    main()
    print("Done")
