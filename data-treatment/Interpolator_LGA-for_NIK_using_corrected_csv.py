import pandas as pd
import csv
import numpy as np
import json
import matplotlib.pyplot as plt
import os
from sklearn.linear_model import LinearRegression

def load_csv_after_rows(path):
    # Load Excel file (.xls or .xlsx). By default, header=0 means first row is the header.
    df = pd.read_excel(path, header=0)
 
    return df

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
    model = LinearRegression(fit_intercept=False)
    model.fit(np.array(x).reshape(-1, 1), y)
    
    # Predictions and residuals
    y_predicted = model.predict(np.array(x).reshape(-1, 1))
    residual = y - y_predicted
    n = len(y)
    p = 2  # number of fitted parameters (slope, intercept)

    # Residual variance (unbiased estimate)
    s2 = np.sum(residual**2) / (n - p)
    # Calibration scatter (residual SD)
    scatter = np.sqrt(s2)
    return model.coef_[0], model.intercept_, scatter

def interpolate(integration, slope, intercept):
    return  integration / slope + intercept
    #return integration / slope   - intercept
def interpolate_scaled(integration, slope, intercept, scale):
    return  scale * integration/slope + intercept

def _uncertainty_searcher(entry_dict, area, product_name: str) -> float:
    """Exctract area_uncertainty for all raw peaks matching product_name."""
    unc = 0.0
    for pk in entry_dict.get("Raw peaks data", []):
        if pk.get("product") == product_name and pk.get("area") == area:
            u = pk.get("area_uncertainty", 0.0) or 0.0
            unc += u 
    return unc

def merge_and_calculate(df_csv, dictionnary_nmr, slope, intercept, scatter):
    df_csv["Integration Benzoin"]=0
    df_csv["Concentration Benzoin"]=0
    df_csv["Yield Benzoin"]=0
    df_csv["Integration uncertainty Benzoin"]=0
    df_csv["Integration uncertainty Unknown double doublet"]=0
    df_csv["Yield uncertainty Benzoin"]=0
    df_csv["Yield uncertainty Unknown double doublet"]=0
    df_csv["Integration Unknown double doublet"]=0
    df_csv["Concentration Unknown double doublet"]=0
    df_csv["Yield Unknown double doublet"]=0
    
    for item in dictionnary_nmr:
        integration = 0
        uncertainty = 0
        for index in range (df_csv.shape[0]):
            if df_csv.at[index,"spectrum_dir"] == item:
                if "unknown-double_doublet_1" in dictionnary_nmr[item]:
                    integration += dictionnary_nmr[item]["unknown-double_doublet_1"]
                    uncertainty += _uncertainty_searcher(dictionnary_nmr[item],dictionnary_nmr[item]["unknown-double_doublet_1"],
                                                             "unknown-double_doublet_1")
                if "unknown-double_doublet_2" in dictionnary_nmr[item]:
                    integration += dictionnary_nmr[item]["unknown-double_doublet_2"]
                    uncertainty += _uncertainty_searcher(dictionnary_nmr[item],dictionnary_nmr[item]["unknown-double_doublet_2"],
                                                             "unknown-double_doublet_2")
                if "unknown-double_doublet_3" in dictionnary_nmr[item]:
                    integration += dictionnary_nmr[item]["unknown-double_doublet_3"]
                    uncertainty += _uncertainty_searcher(dictionnary_nmr[item],dictionnary_nmr[item]["unknown-double_doublet_3"],
                                                             "unknown-double_doublet_3")
                if "unknown-double_doublet_4" in dictionnary_nmr[item]:
                    integration += dictionnary_nmr[item]["unknown-double_doublet_4"]
                    uncertainty += _uncertainty_searcher(dictionnary_nmr[item],dictionnary_nmr[item]["unknown-double_doublet_4"],
                                                             "unknown-double_doublet_4")
                df_csv.at[index, "Integration Unknown double doublet"] = integration
                df_csv.at[index, "Integration uncertainty Unknown double doublet"] = uncertainty 
                continue

    for item in dictionnary_nmr:
        integration = 0
        uncertainty = 0
        for index in range (df_csv.shape[0]):
            if df_csv.at[index,"spectrum_dir"] == item:
                if "Benzoin_monomethoxy-CH1" in dictionnary_nmr[item]:
                    integration += dictionnary_nmr[item]["Benzoin_monomethoxy-CH1"]
                    uncertainty += _uncertainty_searcher(dictionnary_nmr[item],dictionnary_nmr[item]["Benzoin_monomethoxy-CH1"],
                                                             "Benzoin_monomethoxy-CH1")
                if "Benzoin_monomethoxy-CH2" in dictionnary_nmr[item]:
                    integration += dictionnary_nmr[item]["Benzoin_monomethoxy-CH2"]
                    uncertainty += _uncertainty_searcher(dictionnary_nmr[item],dictionnary_nmr[item]["Benzoin_monomethoxy-CH2"],
                                                             "Benzoin_monomethoxy-CH2")
                df_csv.at[index, "Integration Benzoin"] = integration
                df_csv.at[index, "Integration uncertainty Benzoin"] = uncertainty 
                continue

    df_csv['Concentration Unknown double doublet'] = interpolate(df_csv["Integration Unknown double doublet"], slope, intercept)
    df_csv['Yield Unknown double doublet'] = 100* df_csv['Concentration Unknown double doublet'] / (df_csv["conc_1c"])
    df_csv['Yield uncertainty Unknown double doublet'] = 100* ((df_csv['Integration uncertainty Unknown double doublet'] + scatter**2)/slope/ (df_csv["conc_1c"]))

    df_csv['Concentration Benzoin'] = interpolate(df_csv["Integration Benzoin"], slope, intercept)
    df_csv['Yield Benzoin'] = 100* df_csv['Concentration Benzoin'] / (df_csv["conc_1c"]*2)
    df_csv['Yield uncertainty Benzoin'] = 100* (((df_csv['Integration uncertainty Benzoin']+ scatter**2)/slope/ (df_csv["conc_1c"])))

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

def plot_calibration_and_data(df, x_col, y_col, slope, intercept, uncertainties=None):
    """
    Plots scatter of data points and fitted calibration line.

    Parameters:
        df (pd.DataFrame): Input DataFrame.
        x_col (str): Column name for X-axis (e.g., 'Concentration_PhCHO').
        y_col (str): Column name for Y-axis (e.g., 'Conc_p-Methoxybenzaldehyde-Carbonyl').
        slope (float): Slope of the fitted calibration model.
        intercept (float): Intercept of the fitted calibration model.
    """
    
    print (type(x_col),type(y_col),type(uncertainties))

    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Scatter plot of actual data
    if uncertainties is not None:
        ax.errorbar(x_col, y_col, yerr=uncertainties, fmt='o', capsize=3, label="data")
    else:
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
    
    #plt.show()
    return fig


def main():
    # List of (csv_path, json_path) tuples
    dataset_paths = [
        #MECN
        #PYRIDINE serie
        # # Pyridine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\Pyridine_cmpd\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\Pyridine_cmpd\2025-05-15-run01_MeCN_Pyr\Results\fitting_results.json"]),

        # # DMAP
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\DMAP\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\DMAP\2025-06-16-run01_MeCN_DMAP\Results\fitting_results.json",
        # r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\DMAP\2025-06-16-run02_MeCN_DMAP\Results\fitting_results.json"]),

        # # 4-Pyrrolidinopyridine
        (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Pyrrolidinopyridine\_old\run_combined_Louis.xlsx", 
        [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Pyrrolidinopyridine\_old\2025-05-19-run01_MeCN_4_pyrrolidinopyridine\Results\fitting_results.json",
        r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Pyrrolidinopyridine\_old\2025-05-19-run02_MeCN_4_pyrrolidinopyridine\Results\fitting_results.json"]),

        # # 4-Pyrrolidinopyridine old
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Pyrrolidinopyridine\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Pyrrolidinopyridine\2025-06-25-run01_MeCN_4_Pyrrol_Pyr\Results\fitting_results.json",
        # r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Pyrrolidinopyridine\2025-06-25-run02_MeCN_4_Pyrrol_Pyr\Results\fitting_results.json"]),

        # # 4-Morpholino pyridine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Morpholino pyridine\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Morpholino pyridine\2025-06-20-run01_MeCN_4_Morph_Pyr\Results\fitting_results.json",
        # r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Morpholino pyridine\2025-06-20-run02_MeCN_4_Morph_Pyr\Results\fitting_results.json"]),

        # 4-Methyl pyridine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methyl pyridine\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methyl pyridine\2025-06-18-run01_MeCN_4_Me_Pyr\Results\fitting_results.json",
        # r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methyl pyridine\2025-06-18-run02_MeCN_4_Me_Pyr\Results\fitting_results.json"]),

        # # 4-Methoxy pyridine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methoxy pyridine\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methoxy pyridine\2025-06-22-run01_MeCN_4_Methoxy_Pyr\Results\fitting_results.json",
        # r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methoxy pyridine\2025-06-22-run02_MeCN_4_Methoxy_Pyr\Results\fitting_results.json"]),

        #Non-PYRIDINE serie
        # #DABCO
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\DABCO\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\DABCO\2025-06-02-run01_MeCN_DABCO\Results\fitting_results.json",
        #  r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\DABCO\2025-06-02-run02_MeCN_DABCO\Results\fitting_results.json"]),

        # #DBN
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\DBN\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\DBN\2025-06-03-run01_MeCN_DBN\Results\fitting_results.json",
        #  r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\DBN\2025-06-03-run02_MeCN_DBN\Results\fitting_results.json"]),

        # #DBU
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\DBU\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\DBU\2025-05-21-run01_MeCN_DBU\Results\fitting_results.json",
        #  r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\DBU\2025-05-21-run02_MeCN_DBU\Results\fitting_results.json"]),

        # #Morpholine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\Morpholine\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\Morpholine\2025-06-23-run01_MeCN_Morph\Results\fitting_results.json",
        #  r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\Morpholine\2025-06-23-run02_MeCN_Morph\Results\fitting_results.json"]),


        # #N-Me Piperidine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\N-Methyl piperidine\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\N-Methyl piperidine\2025-05-26-run01_MeCN_1MePiper\Results\fitting_results.json",
        #  r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\N-Methyl piperidine\2025-05-26-run02_MeCN_1MePiper\Results\fitting_results.json"]),

        # #Piperidine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\Piperidine\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\Piperidine\2025-06-01-run01_MeCN_Piper\Results\fitting_results.json",
        #  r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\Piperidine\2025-06-01-run02_MeCN_Piper\Results\fitting_results.json"]),


        # #Quinuclidine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\Quinuclidine\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\Quinuclidine\2025-06-14-run01_MeCN_Quinuclidine\Results\fitting_results.json",
        #  r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Other nucleophiles\Quinuclidine\2025-06-14-run02_MeCN_Quinuclidine\Results\fitting_results.json"]),

        #DMSO
        #PYRIDINE serie
        # # Pyridine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\Pyridine\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\Pyridine\2025-06-04-run01_DMSO_Pyr\Results\fitting_results.json",
        #  r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\Pyridine\2025-06-04-run02_DMSO_Pyr\Results\fitting_results.json"]),

        # # DMAP
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\DMAP\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\DMAP\2025-06-17-run01_DMSO_DMAP\Results\fitting_results.json",
        # r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\DMAP\2025-06-17-run02_DMSO_DMAP\Results\fitting_results.json"]),

        # # 4-Pyrrolidinopyridine
        #(r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\4-Pyrrolidino pyridine\run_combined_Louis2025-06-26.xlsx", 
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\4-Pyrrolidino pyridine\run_combined_Louis2025-06-07.xlsx", 
        # [r"C:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\4-Pyrrolidino pyridine\2025-06-07-run01_DMSO_4_Pyrr_Pyr\Results\fitting_results.json",
        #  r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\4-Pyrrolidino pyridine\2025-06-07-run01_DMSO_4_Pyrr_Pyr\Results\fitting_results.json"]),

        # # 4-Morpholino pyridine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\4-Morpholino pyridine\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\4-Morpholino pyridine\2025-06-21-run01_DMSO_4_Morph_Pyr\Results\fitting_results.json",
        # r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\4-Morpholino pyridine\2025-06-21-run02_DMSO_4_Morph_Pyr\Results\fitting_results.json"]),

        # # 4-Methyl pyridine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\4-Methyl pyridine\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\4-Methyl pyridine\2025-06-19-run01_DMSO_4_Me_Pyr\Results\fitting_results.json",
        # r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\4-Methyl pyridine\2025-06-19-run02_DMSO_4_Me_Pyr\Results\fitting_results.json"]),

        # 4-Methoxy pyridine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\4-Methoxy pyridine\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\4-Methoxy pyridine\2025-06-22-run01_DMSO_4_Methoxy_Pyr\Results\fitting_results.json",
        # r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine-based nucleophiles\4-Methoxy pyridine\2025-06-22-run02_DMSO_4_Methoxy_Pyr\Results\fitting_results.json"]),

        #Non-PYRIDINE serie
        # #DABCO
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\DABCO\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\DABCO\2025-06-12-run01_DMSO_DABCO\Results\fitting_results.json",
        #  r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\DABCO\2025-06-12-run02_DMSO_DABCO\Results\fitting_results.json"]),

        # #DBN
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\DBN\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\DBN\2025-06-09-run01_DMSO_DBN\Results\fitting_results.json",
        #  r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\DBN\2025-06-09-run02_DMSO_DBN\Results\fitting_results.json"]),

        # #DBU
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\DBU\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\DBU\2025-06-08-run01_DMSO_DBU\Results\fitting_results.json",
        #  r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\DBU\2025-06-08-run02_DMSO_DBU\Results\fitting_results.json"]),

        # #Morpholine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\Morpholine\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\Morpholine\2025-06-26-run01_DMSO_Morpholine\Results\fitting_results.json",
        #  r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\Morpholine\2025-06-26-run02_DMSO_Morpholine\Results\fitting_results.json"]),


        # #N-Me Piperidine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\N-Methyl piperidine\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\N-Methyl piperidine\2025-06-11-run01_DMSO_1_Me_Piper\Results\fitting_results.json",
        #  r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\N-Methyl piperidine\2025-06-11-run02_DMSO_1_Me_Piper\Results\fitting_results.json"]),

        # #Piperidine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\Piperidine\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\Piperidine\2025-06-10-run01_DMSO_Piper\Results\fitting_results.json",
        #  r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\Piperidine\2025-06-10-run02_DMSO_Piper\Results\fitting_results.json"]),


        # # #Quinuclidine
        # (r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\Quinuclidine\run_combined_Louis.xlsx", 
        # [r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\Quinuclidine\2025-06-15-run01_DMSO_Quinuclidine\Results\fitting_results.json",
        #  r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\DMSO\Other nucleophiles\Quinuclidine\2025-06-15-run02_DMSO_Quinuclidine\Results\fitting_results.json"]),



    ]

    output_path=r"c:\Users\UNIST\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Pyrrolidinopyridine\_old"
    CSV_path = output_path+r"\CSV_4_pyrro_Final.csv"
    graph_path =  output_path+r"\Graph_"




    # Calibration values (same across all datasets)
    concentrations = [1, 5, 10, 20, 30, 40]
    #Based on: Voigt Model1, MeCN
    avg_integrations = [ 0.07421381949419896,                   #+/-0.0076678653540433695
                        0.11607666031360743 + 0.1663764644514101,  #+/-0.009052300265113567 + +/-0.012029311086255658
                        0.31436517252467905 + 0.3224413883292846,  #+/-0.014519349140480057  +  +/-0.015593063938080312
                        0.49757485848940836 + 0.4917400265687633,  #+/-0.009041346617507811 + +/- 0.009010154773923989
                        0.8296015483261383 + 0.7952657692158747,  #+/-0.010820594427569205 + +/- 0.010962649869136505
                        1.1955437565284728 + 1.07000972199386]  #+/-0.03996247170519104 + +/-0.03988062733037813

    uncertainties_integrations = [
                        0.0076678653540433695,
                        0.009052300265113567 + 0.012029311086255658,
                        0.014519349140480057  + 0.015593063938080312,
                        0.009041346617507811 + 0.009010154773923989,
                        0.010820594427569205 + 0.010962649869136505,
                        0.03996247170519104 + 0.03988062733037813
                        ]

    # Fit the calibration model
    slope, intercept,scatter = fit_linear_model(concentrations,avg_integrations )
    print(f"Fitted linear model: slope = {slope:.6f}, intercept = {intercept:.6f}")

    # Process and combine all datasets
    for csv_path, json_path in dataset_paths:
        df_csv = load_csv_after_rows(csv_path)
        dictionnary_nmr = load_nmr_json(json_path)
        df_final = merge_and_calculate(df_csv, dictionnary_nmr, slope, intercept,scatter)
        
          
    fig_calibration=plot_calibration_and_data(df_final, x_col=concentrations, y_col=avg_integrations, slope=slope, intercept=intercept , uncertainties=uncertainties_integrations)
    fig_calibration.savefig(f'{graph_path}_calibration.png', format='png')

    fig=plot_graph(df_final, x_col='conc_Nucleophile', y_col='conc_PhCHO', color_col='Yield Benzoin', label_col='global_index',unit="%")
    #fig=plot_graph(df_final, x_col='conc_DMAP', y_col='conc_PhCHO', color_col='Yield Benzoin', label_col='local_index',xlim=(-20,650), ylim=(-20,650), unit="%")
    #fig=plot_graph(df_final, x_col='conc_4_Morph_Pyr', y_col='conc_PhCHO', color_col='Yield Benzoin', label_col='local_index',xlim=(-20,650), ylim=(-20,650), unit="%")
    #Save the plot as a PNG file
    fig.savefig(f'{graph_path}_benzoin.png', format='png')
    #Clear the figure to avoid overlapping plots if this is inside a loop
    plt.close()

    fig=plot_graph(df_final, x_col='conc_Nucleophile', y_col='conc_PhCHO', color_col='Yield Unknown double doublet', label_col='global_index', unit="%")
    #fig=plot_graph(df_final, x_col='conc_DMAP', y_col='conc_PhCHO', color_col='Yield Unknown double doublet', label_col='local_index',xlim=(-20,650), ylim=(-20,650), unit="%")
    #fig=plot_graph(df_final, x_col='conc_4_Morph_Pyr', y_col='conc_PhCHO', color_col='Yield Unknown double doublet', label_col='local_index',xlim=(-20,650), ylim=(-20,650), unit="%")
    #Save the plot as a PNG file
    fig.savefig(f'{graph_path}_unknown_doublet.png', format='png')
    #Clear the figure to avoid overlapping plots if this is inside a loop
    plt.close()

    df_final.to_csv(CSV_path, index=False)
    print(f"Saved combined output to: {CSV_path}")


if __name__ == "__main__":
    main()
    print("Done")
