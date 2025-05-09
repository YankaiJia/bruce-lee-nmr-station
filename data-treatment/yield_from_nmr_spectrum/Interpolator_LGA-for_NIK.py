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
    print (concentration_lookup)
    # Normalize column names
    df_volumes.columns = df_volumes.columns.map(str)

    # Identify volume columns and group by chemical
    vol_cols = [col for col in df_volumes.columns if col.startswith("vol#")]
    
    #df = df_volumes[["global_index"] + vol_cols].copy()
    df = df_volumes[["local_index"] + vol_cols].copy()
    df.rename(columns={"local_index": "global_index"}, inplace=True)

    for col in vol_cols: #volume in uL
        chem = col.split("#")[1]  # Extract chemical name from 'vol#CHEM'
        if chem in concentration_lookup:
            df[f"Concentration_{col}"] = df[col] * concentration_lookup[chem] #concentration obtained in mM
    
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
            "NMR_Benzaldehyde-Carbonyl_satellite": values.get("Benzaldehyde-Carbonyl_satellite", 0),
            "NMR_Unknown_peak_2": values.get("Unknown_peak_2", 0),
            "spectrum_dir": os.path.join(base_dir, key)
        }
        record["NMR_Benzoin_dimethoxy"] = record["NMR_Benzoin_dimethoxy-CH1"] + record["NMR_Benzoin_dimethoxy-CH2"]
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

def main():
    #Pyr
    csv_path = r"c:\Users\UNIST\Dropbox\brucelee\data\NV\2025-05-06-run02_MeCN_Pyr\2025-05-06-run02.xlsx"
    json_path = r"c:\Users\UNIST\Dropbox\brucelee\data\NV\2025-05-06-run02_MeCN_Pyr\Results\fitting_results.json"
    #DMAP
    csv_path = r"c:\Users\UNIST\Dropbox\brucelee\data\NV\2025-05-06-run01_MeCN_DMAP\2025-05-06-run01.xlsx"
    json_path = r"c:\Users\UNIST\Dropbox\brucelee\data\NV\2025-05-06-run01_MeCN_DMAP\Results\fitting_results.json"
    # Calibration values
    concentrations = [1, 5, 10, 20, 40, 50]
    integrations_1 = [0.09788, 0.475307315, 1.078162255, 2.233064095, 4.500305881, 5.396774998] #Based on CH of Benzoin
    integrations_2 = [0.095666667, 0.511666667, 1.1185, 2.316333333, 4.541666667, 5.525333333] #Based normalised on OMe of Benzoin
    avg_integrations = average_integrations(integrations_1, integrations_2)

    slope, intercept = fit_linear_model(avg_integrations, concentrations)
    print(f"Fitted linear model: slope = {slope:.6f}, intercept = {intercept:.6f}")

    if False:
        plot_calibration_curve(avg_integrations, integrations_1, integrations_2, concentrations, slope, intercept)

    df_csv = load_csv_after_rows(csv_path)#, skip_rows=16)
    df_nmr = load_nmr_json(json_path)
    df_final = merge_and_calculate(df_csv, df_nmr, slope, intercept)
    
    print(df_final)
    
    df_final.to_csv(r"c:\Users\UNIST\Dropbox\brucelee\data\NV\CSV_with_concentration_interpolated_DMAP.csv", index=False)

if __name__ == "__main__":
    main()
    print("Done")
