import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import os
from sklearn.linear_model import LinearRegression

def load_csv_after_rows(path):
    import pandas as pd

    # Load Excel sheets
    xls = pd.ExcelFile(path)
    df_volumes = xls.parse(xls.sheet_names[0])
    df_concentrations = xls.parse(xls.sheet_names[2])  # third sheet

    # Extract concentrations
    df_concentrations = df_concentrations.rename(columns={df_concentrations.columns[0]: 'stock_solution'})
    df_concentrations.set_index('stock_solution', inplace=True)

    
    concentration_lookup = {} #concentration in M
    for row in df_concentrations.index:
        for col in df_concentrations.columns:
            val = df_concentrations.loc[row, col]
            if isinstance(val, (int, float)) and val != 0:
                concentration_lookup[row] = float(val)    
                break
    print (f"Stock solution: {concentration_lookup}")
    # Normalize column names
    df_volumes.columns = df_volumes.columns.map(str)

    # Identify volume columns and group by chemical
    vol_cols = [col for col in df_volumes.columns if col.startswith("vol#")]
    
    #df = df_volumes[["global_index"] + vol_cols].copy()
    df = df_volumes[["local_index"] + vol_cols].copy()
    df.rename(columns={"local_index": "global_index"}, inplace=True)

    # Sum of volumes across vol_cols for each row
    total_volume = df[vol_cols].sum(axis=1)

    for col in vol_cols: #volume in uL
        chem = col.split("#")[1]  # Extract chemical name from 'vol#CHEM'
        if chem in concentration_lookup:
            df[f"Concentration_{col}"] =  (( df[col] * concentration_lookup[chem] *1000) / (total_volume)).round(3) #concentration obtained in uM
    
    # Step 1: build list of base chemical names from concentration_lookup keys
    base_chems = [key.split("_")[0] for key in concentration_lookup]

    # Step 2: create new columns by aggregating matching ones
    for col in list(df.columns): 
        if not col.startswith("Concentration_"):
            continue

        short_name = col.replace("Concentration_", "")
        
        if short_name in base_chems:
            target_col = f"Concentration_{short_name}"
        else:
            # Try to parse name from inside 'vol#CHEM_xxx'
            parts = short_name.split("#")
            if len(parts) == 2:
                chem = parts[1].split("_")[0]
                target_col = f"Concentration_{chem}"
            else:
                continue  # skip if pattern doesn't match

        if target_col in df.columns:
            df[target_col] += df[col]
        else:
            df[target_col] = df[col]

        # Drop the original column after merging
        df.drop(columns=[col], inplace=True)

    # Identify target columns
    concentration_cols = [col for col in df.columns if "Concentration" in col]
    other_cols = [col for col in df.columns if col not in concentration_cols and col != "global_index"]

    # Reorder: global_index → concentration columns → rest
    df = df[["global_index"] + concentration_cols + other_cols]

    print (df)
    return df



def load_nmr_json(json_path):
    with open(json_path, 'r') as f:
        nmr_data = json.load(f)
    base_dir = os.path.dirname(json_path)
    records = []
    for key, values in nmr_data.items():
        try:
            index = int(key.split("-")[0])
        except ValueError:
            continue

        record = {
            "global_index": index,
            "NMR_p-Methoxybenzaldehyde-Carbonyl": values.get("p-Methoxybenzaldehyde-Carbonyl", 0),
            "NMR_Benzaldehyde-Carbonyl": values.get("Benzaldehyde-Carbonyl", 0),
            "NMR_Benzoin_dimethoxy-CH1": values.get("Benzoin_dimethoxy-CH1", 0),
            "NMR_Benzoin_dimethoxy-CH2": values.get("Benzoin_dimethoxy-CH2", 0),
            "NMR_Benzoin_monomethoxy-CH1": values.get("Benzoin_monomethoxy-CH1", 0),
            "NMR_Benzoin_monomethoxy-CH2": values.get("Benzoin_monomethoxy-CH2", 0),
            "NMR_Benzaldehyde-Carbonyl_satellite": values.get("Benzaldehyde-Carbonyl_satellite", 0),
            "NMR_Unknown_peak_2": values.get("Unknown_peak_2", 0),
            "spectrum_dir": os.path.join(base_dir, key)
        }
        record["NMR_Benzoin_dimethoxy"] = record["NMR_Benzoin_dimethoxy-CH1"] + record["NMR_Benzoin_dimethoxy-CH2"]
        record["NMR_Benzoin_monomethoxy"] = record["NMR_Benzoin_monomethoxy-CH1"] + record["NMR_Benzoin_monomethoxy-CH2"]
        record["NMR_p-Methoxybenzaldehyde-Carbonyl_satellite_corrected"] = record["NMR_p-Methoxybenzaldehyde-Carbonyl"] - record["NMR_Benzaldehyde-Carbonyl_satellite"]
        records.append(record)
    return pd.DataFrame(records)

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


def merge_and_calculate(df_csv, df_nmr, slope, intercept):
    df_csv = df_csv.copy()

    # Merge all columns on global_index
    df_merged = pd.merge(df_csv, df_nmr, on="global_index", how="inner")
    # Define any custom scaling overrides
    scaling_exceptions = {
        #"NMR_Carbene_precursor-Methoxy": 1/3, #Not fitted at the moment
    }

    # Interpolate all NMR_ columns
    for col in df_merged.columns:
        if col.startswith("NMR_"):
            output_col = col.replace("NMR_", "Conc_")
            scale = scaling_exceptions.get(col, 1.0)
            if scale != 1.0:
                df_merged[output_col] = interpolate_scaled(df_merged[col], slope, intercept, scale=scale)
            else:
                df_merged[output_col] = interpolate(df_merged[col], slope, intercept)

    # Define the limitating reagent concentration column
    reference_conc_col = 'Concentration_1c'
    stockiometry=2

    # Add Yield_ columns based on existing Conc_ columns
    for col in df_merged.columns:
        if col.startswith("Conc_") and col != reference_conc_col:
            yield_col = col.replace("Conc_", "Yield_")
            df_merged[yield_col] = 100 * df_merged[col] / (df_merged[reference_conc_col]*stockiometry)


    return df_merged

def plot_calibration_curve(integrations_avg, integrations_1, integrations_2, concentrations, slope, intercept):
    plt.figure(figsize=(8, 6))
    plt.scatter(integrations_1, concentrations, color='green', label='Integrations 1', marker='x')
    plt.scatter(integrations_2, concentrations, color='orange', label='Integrations 2', marker='o')
    plt.scatter(integrations_avg, concentrations, color='blue', label='Average Integrations', marker='s')
    x_vals = np.linspace(min(integrations_avg), max(integrations_avg), 100)
    y_vals = slope * x_vals + intercept
    plt.plot(x_vals, y_vals, color='red', label=f'Model: y = {slope:.2f}x + {intercept:.2f}')
    plt.xlabel('Integration')
    plt.ylabel('Concentration')
    plt.title('Calibration Curve')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


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
        vmin=vmin,
        vmax=vmax
    )
    
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label(colorbar_label if colorbar_label else color_col)
    
    # Increase the offset for labels (e.g., 10 pixels right and up)
    for i in range(len(df)):
        first_label = str(df[label_col].iloc[i])
        second_label = f"{df[color_col].iloc[i]:.0f}"  # Format decimal 
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
    ax.scatter(df[x_col], df[y_col], color='blue', label='Data Points')
    
    # Generate X values for the fitted line
    x_fit = np.linspace(df[x_col].min(), df[x_col].max(), 100)
    y_fit = slope * x_fit + intercept
    
    # Plot the fitted line
    ax.plot(x_fit, y_fit, color='red', label=f'Line: y = {slope:.3f}x + {intercept:.3f}')
    
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title('Calibration Line vs Data Points')
    ax.legend()
    
    plt.show()


def main():
    # List of (csv_path, json_path) tuples
    dataset_paths = [
        #Pyr(old)
        # (r"c:\Users\louis\Dropbox\brucelee\data\NV\2025-05-06-run02_MeCN_Pyr\2025-05-06-run02.xlsx", 
        #  r"c:\Users\louis\Dropbox\brucelee\data\NV\2025-05-06-run02_MeCN_Pyr\Results\fitting_results.json"),
        #DMAP(old)
        #(r"c:\Users\louis\Dropbox\brucelee\data\NV\2025-05-06-run01_MeCN_DMAP\2025-05-06-run01.xlsx", 
        #r"c:\Users\louis\Dropbox\brucelee\data\NV\2025-05-06-run01_MeCN_DMAP\Results\fitting_results.json"),
        # #Pyr
        # (r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine\2025-05-15-run01_MeCN_Pyr\2025-05-15-run01.xlsx", 
        # r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine\2025-05-15-run01_MeCN_Pyr\Results\fitting_results.json"),
        # #Pyr-DMSO
        # (r"C:\Users\louis\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine\2025-06-04-run01_DMSO_Pyr\2025-06-04-run01.xlsx", 
        # r"C:\Users\louis\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine\2025-06-04-run01_DMSO_Pyr\Results\fitting_results.json"),
        # #Pyr-DMSO-Part2
        # (r"C:\Users\louis\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine\2025-06-04-run02_DMSO_Pyr\2025-06-04-run02.xlsx", 
        # r"C:\Users\louis\Dropbox\brucelee\data\NV\Final Data\DMSO\Pyridine\2025-06-04-run02_DMSO_Pyr\Results\fitting_results.json"),
        # #DMAP
        # (r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\DMAP\2025-05-14-run01_MeCN_DMAP\2025-05-14-run01.xlsx", 
        # r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\DMAP\2025-05-14-run01_MeCN_DMAP\Results\fitting_results.json"),
        # #DMAP-part2
        # (r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\DMAP\2025-05-14-run02_MeCN_DMAP\2025-05-14-run02.xlsx", 
        # r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\DMAP\2025-05-14-run02_MeCN_DMAP\Results\fitting_results.json"),
        # #Piperidine
        # (r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\Piperidine\2025-06-01-run01_MeCN_Piper\2025-06-01-run01.xlsx", 
        # r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\Piperidine\2025-06-01-run01_MeCN_Piper\Results\fitting_results.json"),
        # #Piperidine-part2
        # (r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\Piperidine\2025-06-01-run02_MeCN_Piper\2025-06-01-run02.xlsx", 
        # r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\Piperidine\2025-06-01-run02_MeCN_Piper\Results\fitting_results.json"),
        # #Methyl-Piperidine
        # (r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\1-Methyl piperidine\2025-05-26-run01_MeCN_1MePiper\2025-05-28-run01.xlsx", 
        # r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\1-Methyl piperidine\2025-05-26-run01_MeCN_1MePiper\Results\fitting_results.json"),
        # #Methyl-Piperidine-part2
        # (r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\1-Methyl piperidine\2025-05-26-run02_MeCN_1MePiper\2025-05-28-run02.xlsx", 
        # r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\1-Methyl piperidine\2025-05-26-run02_MeCN_1MePiper\Results\fitting_results.json"),
        # #4-Pyrrolidinopyridine
        # (r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\4-Pyrrolidinopyridine\2025-05-19-run01_MeCN_4_pyrrolidinopyridine\2025-05-19-run01.xlsx", 
        # r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\4-Pyrrolidinopyridine\2025-05-19-run01_MeCN_4_pyrrolidinopyridine\Results\fitting_results.json"),
        # #4-Pyrrolidinopyridine-part2
        # (r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\4-Pyrrolidinopyridine\2025-05-19-run02_MeCN_4_pyrrolidinopyridine\2025-05-19-run02.xlsx", 
        # r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\4-Pyrrolidinopyridine\2025-05-19-run02_MeCN_4_pyrrolidinopyridine\Results\fitting_results.json"),
        # #DABCO
        # (r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\DABCO\2025-06-02-run01_MeCN_DABCO\2025-06-02-run01.xlsx", 
        # r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\DABCO\2025-06-02-run01_MeCN_DABCO\Results\fitting_results.json"),
        # #DABCO-part2
        # (r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\DABCO\2025-06-02-run02_MeCN_DABCO\2025-06-02-run02.xlsx", 
        # r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\DABCO\2025-06-02-run02_MeCN_DABCO\Results\fitting_results.json"),
        # #DBN
        # (r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\DBN\2025-06-03-run01_MeCN_DBN\2025-06-03-run01.xlsx", 
        # r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\DBN\2025-06-03-run01_MeCN_DBN\Results\fitting_results.json"),
        # #DBN-part2
        # (r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\DBN\2025-06-03-run02_MeCN_DBN\2025-06-03-run02.xlsx", 
        # r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\DBN\2025-06-03-run02_MeCN_DBN\Results\fitting_results.json"),
        #DBU
        (r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\DBU\2025-05-21-run01_MeCN_DBU\2025-05-21-run01.xlsx", 
        r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\DBU\2025-05-21-run01_MeCN_DBU\Results\fitting_results.json"),
        #DBU-part2
        (r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\DBU\2025-05-21-run02_MeCN_DBU\2025-05-21-run02.xlsx", 
        r"c:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\DBU\2025-05-21-run02_MeCN_DBU\Results\fitting_results.json"),
    ]

    output_path=r"C:\Users\louis\Dropbox\brucelee\data\NV\Final Data\MeCN\DBU"
    CSV_path = output_path+r"\CSV_DBU_Final.csv"
    graph_path1 =  output_path+r"\Graph_concentration_aldehyde.png"
    graph_path2 =  output_path+r"\Graph_yield_methoxyaldehyde.png"
    graph_path3 =  output_path+r"\Graph_yield_benzoin.png"
    graph_path4 =  output_path+r"\Graph_yield_dimethoxybenzoin.png"



    # Calibration values (same across all datasets)
    concentrations = [1, 5, 10, 20, 40, 50]
    integrations_1 = [0.09788, 0.475307315, 1.078162255, 2.233064095, 4.500305881, 5.396774998]
    integrations_2 = [0.095666667, 0.511666667, 1.1185, 2.316333333, 4.541666667, 5.525333333]
    avg_integrations = average_integrations(integrations_1, integrations_2)

    # Fit the calibration model
    slope, intercept = fit_linear_model(avg_integrations, concentrations)
    print(f"Fitted linear model: slope = {slope:.6f}, intercept = {intercept:.6f}")

    # Process and combine all datasets
    all_dataframes = []
    for csv_path, json_path in dataset_paths:
        df_csv = load_csv_after_rows(csv_path)
        df_nmr = load_nmr_json(json_path)
        df_final = merge_and_calculate(df_csv, df_nmr, slope, intercept)
        
        varX=None
        for x in df_final.columns.tolist():
            if 'Concentration' in x:
                if x not in ('Concentration_1c', 'Concentration_PhCHO'):
                    varX=x
                    break
        if varX==None:
            varX=df_final.columns.tolist()[1]
        plot_graph(df_final, x_col=varX, y_col='Concentration_PhCHO', color_col='Conc_Benzaldehyde-Carbonyl', label_col='global_index',xlim=(-20,650), ylim=(-20,600))
        
        all_dataframes.append(df_final)

    # Concatenate and export
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    #print(combined_df.columns.tolist())
    varX=None
    for x in combined_df.columns.tolist():
        if 'Concentration' in x:
            if x not in ('Concentration_1c', 'Concentration_PhCHO'):
                varX=x
                break
    if varX==None:
        varX=combined_df.columns.tolist()[1]
        
            

    #plot_calibration_and_data(combined_df, x_col='Concentration_PhCHO', y_col='Conc_Benzaldehyde-Carbonyl', slope=1, intercept=0)
    
    fig=plot_graph(combined_df, x_col=varX, y_col='Concentration_PhCHO', color_col='Conc_Benzaldehyde-Carbonyl', label_col='global_index',xlim=(-20,650), ylim=(-20,650), unit="uM")
    #Save the plot as a PNG file
    fig.savefig(f'{graph_path1}.png', format='png')
    #Clear the figure to avoid overlapping plots if this is inside a loop
    plt.close()
    
    fig=plot_graph(combined_df, x_col=varX, y_col='Concentration_PhCHO', color_col='Yield_p-Methoxybenzaldehyde-Carbonyl_satellite_corrected', label_col='global_index', xlim=(-20,650), ylim=(-20,650),vmin=0, vmax=100, unit="%")
    #Save the plot as a PNG file
    fig.savefig(f'{graph_path2}.png', format='png')
    #Clear the figure to avoid overlapping plots if this is inside a loop
    plt.close()

    fig=plot_graph(combined_df, x_col=varX, y_col='Concentration_PhCHO', color_col='Yield_Benzoin_monomethoxy', label_col='global_index', xlim=(-20,650), ylim=(-20,650),vmin=0, vmax=100, unit="%")
    #Save the plot as a PNG file
    fig.savefig(f'{graph_path3}.png', format='png')
    #Clear the figure to avoid overlapping plots if this is inside a loop
    plt.close()
    
    fig=plot_graph(combined_df, x_col=varX, y_col='Concentration_PhCHO', color_col='Yield_Benzoin_dimethoxy', label_col='global_index', xlim=(-20,650), ylim=(-20,650),vmin=0, vmax=100, unit="%")
    #Save the plot as a PNG file
    fig.savefig(f'{graph_path4}.png', format='png')
    #Clear the figure to avoid overlapping plots if this is inside a loop
    plt.close()
    
    combined_df.to_csv(CSV_path, index=False)
    print(f"Saved combined output to: {CSV_path}")


if __name__ == "__main__":
    main()
    print("Done")
