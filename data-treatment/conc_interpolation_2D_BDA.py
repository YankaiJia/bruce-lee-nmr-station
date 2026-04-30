"""
This module is for interpolation of BDA reactions ONLY. Its input is the integrated area of peaks from different
compounds, which is calculated by Louis. This module takes the area and interpolates them by a 2D calibration curve.
The output of this script is the interpolated concentrations of different compounds.

PRE-REQUISITES (run once per run folder via utils.py before executing this script):
    1. put_run_condition_in_spectrum_folder(path, spectrum_frequency='400MHz')
       → copies the reaction condition Excel into each spectrum subfolder
    2. put_fitting_results_in_spec_folder(path)
       → copies the NMR fitting JSON results into each spectrum subfolder

Yankai Jia 2026.01.05, updated 2026.04.30
"""
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from collections import defaultdict

import json, os, re

from scipy.optimize import minimize_scalar
from sklearn.metrics import mean_squared_error
from scipy.interpolate import Rbf
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error

import mpld3

import matplotlib
matplotlib.use("TKAgg")

import config

DATA_ROOT = config.DATA_ROOT

def parse_starting_materials(data):
    """
    Extract Starting material-1 and Starting material-2
    from each experiment entry.
    """
    result = {}

    for exp_name, exp_data in data.items():
        sm1 = exp_data.get("Starting material-1")
        sm2 = exp_data.get("Starting material-2")

        result[exp_name] = {
            "Starting material-1": sm1,
            "Starting material-2": sm2,
        }

    return result


def append_starting_materials_intg(
    xlsx_path,
    starting_materials,
    save_path=None,
):
    """
    Load an Excel file and append Starting material results.

    Parameters
    ----------
    xlsx_path : str
        Path to input Excel file.
    starting_materials : dict
        Parsed results:
        {
            "BDA-Cal-TBABr-0": {
                "Starting material-1": float,
                "Starting material-2": float
            },
            ...
        }
    save_path : str | None
        If provided, save updated Excel to this path.

    Returns
    -------
    pd.DataFrame
        Updated DataFrame with appended columns.
    """

    # Load Excel
    df = pd.read_excel(xlsx_path)

    # Map WS-* → experiment key
    def extract_exp_key(folder_name):
        return folder_name.replace("WS-", "")

    df["_exp_key"] = df["folder_name"].apply(extract_exp_key)

    # Append starting materials with new names
    # Starting material-1->BDA_1, Starting material-2->BDA_2
    df["BDA_1"] = df["_exp_key"].apply(
        lambda k: starting_materials.get(k, {}).get("Starting material-1")
    )

    df["BDA_2"] = df["_exp_key"].apply(
        lambda k: starting_materials.get(k, {}).get("Starting material-2")
    )

    # Cleanup
    df.drop(columns="_exp_key", inplace=True)


    # Compute average (row-wise, NaN-safe)
    df["BDA_avg"] = df[["BDA_1", "BDA_2"]].mean(axis=1)

    # Save if requested
    if save_path is not None:
        df.to_excel(save_path, index=False)

    return df


def five_fold_validation(
    x1,
    x2,
    y,
    rbf_function="multiquadric",
    random_state=42,
):
    """
    Five-fold cross validation for 2D RBF regression.

    Parameters
    ----------
    x1, x2 : array-like
        Independent variables (e.g. [BDA], [TBABr])
    y : array-like
        Target values (e.g. BDA_avg)
    rbf_function : str
        RBF kernel type for scipy.interpolate.Rbf
    random_state : int
        Random seed for reproducibility

    Returns
    -------
    dict
        {
            "rmse_per_fold": list,
            "rmse_mean": float,
            "rmse_std": float
        }
    """

    x1 = np.asarray(x1)
    x2 = np.asarray(x2)
    y = np.asarray(y)

    kf = KFold(n_splits=5, shuffle=True, random_state=random_state)

    rmses = []

    for train_idx, test_idx in kf.split(x1):
        # training data
        x1_train, x2_train, y_train = (
            x1[train_idx],
            x2[train_idx],
            y[train_idx],
        )

        # test data
        x1_test, x2_test, y_test = (
            x1[test_idx],
            x2[test_idx],
            y[test_idx],
        )

        # fit RBF
        model = Rbf(
            x1_train,
            x2_train,
            y_train,
            function=rbf_function,
        )

        # predict
        y_pred = model(x1_test, x2_test)

        # RMSE
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        rmses.append(rmse)

    return {
        "rmse_per_fold": rmses,
        "rmse_mean": float(np.mean(rmses)),
        "rmse_std": float(np.std(rmses)),
    }


def plot_interp(X1, X2, y, rbf_model,
                save_path=None,
                label_points=True, additive_type='TBABr'):
    """
    Interactive 3D RBF surface + scatter with Plotly.
    - Saves to plot.html if save_path is provided (directory or full file path).
    - show=True opens an interactive window in your browser.
    - label_points=True shows value labels above scatter points.
    """

    # Make grid and predict
    dpe_vals = np.linspace(np.nanmin(X1), np.nanmax(X1), 50)
    tbabr_vals = np.linspace(np.nanmin(X2), np.nanmax(X2), 50)
    dpe_grid, tbabr_grid = np.meshgrid(dpe_vals, tbabr_vals)
    dep_pred = rbf_model(dpe_grid, tbabr_grid)  # shape (50, 50)

    # Build figure
    fig = go.Figure()

    # Surface
    fig.add_trace(go.Surface(
        x=dpe_grid, y=tbabr_grid, z=dep_pred,
        colorbar_title="Integration",
        name="RBF Surface",
        showscale=True
    ))

    # Scatter3d of original points with hover
    fig.add_trace(go.Scatter3d(
        x=X1, y=X2, z=y,
        mode='markers+text' if label_points else 'markers',
        text=[f"{val:.1f}" for val in y] if label_points else None,
        textposition="top center",
        marker=dict(size=5),
        name="Data Points",
        hovertemplate=(
            "DPE: %{x}<br>"
            "TBABr: %{y}<br>"
            "DPE_intg_norm: %{z}<extra>Data Point</extra>"
        )
    ))

    fig.update_layout(
        title="3D Interpolated Surface",
        scene=dict(
            xaxis_title="DPE(mM)",
            yaxis_title=f"{additive_type}(mM)",
            zaxis_title="Normalized DPE Integration",
            camera=dict(
                eye=dict(x=0, y=2.5, z=2.5)  # Adjust orientation here
            )

        ),
        width=950,
        height=750
    )

    # Save: accept folder or full path
    if save_path:
        out_file = os.path.join(save_path, "plot.html")
        if os.path.isdir(save_path):
            out_file = out_file
        else:
            # If a filename was passed, ensure it ends with .html
            root, ext = os.path.splitext(save_path)
            out_file = save_path if ext.lower() == ".html" else root + ".html"
        os.makedirs(os.path.dirname(out_file) or ".", exist_ok=True)
        fig.write_html(out_file, include_plotlyjs="cdn", full_html=True)
        print(f"Saved: {out_file}")

    return fig


def estimate_conc_by_rbf_model(additive_conc_here,
                               integral_value_normalized,
                               rbf_model):

    if integral_value_normalized < 1E-4:
        return 0

    # === Numerical inversion: find cmpd conc that gives closest integral ===
    def objective(dpe_guess):
        pred = rbf_model(dpe_guess, additive_conc_here)
        return abs(pred - integral_value_normalized)

    result = minimize_scalar(objective, bounds=(0, 450), method='bounded')
    estimated_conc = result.x if result.success else None
    assert estimated_conc, 'Finding estimated_dpe failed!'
    estimated_conc = 0 if estimated_conc < 1E-10 else estimated_conc

    return estimated_conc

def extract_products_and_starting_materials(data):
    """
    Extract Product_* and Starting material-* entries from a result dict.

    Parameters
    ----------
    data : dict
        Result dictionary containing aggregated peak areas.

    Returns
    -------
    dict
        Combined dictionary of products and starting materials with values.
    """
    result = {}

    for k, v in data.items():
        if not isinstance(v, (int, float)):
            continue

        if k.startswith("Product_") or k.startswith("Starting material"):
            result[k] = v

    result_final = {'intg_norm': {}, 'conc_mM': {}}

    for key, value in result.items():
        result_final['intg_norm'][key] = value / config.dictionnary_H_count[key]

    return result_final


def add_conc_mM_median(data, ignore_zero=False):
    """
    Add median concentration per molecule (collapsed key) to data dict.

    Parameters
    ----------
    data : dict
        Must contain key 'conc_mM'
    ignore_zero : bool
        If True, zeros / near-zeros are ignored in median calculation

    Returns
    -------
    dict
        Same dict with added key 'conc_mM_median'
    """

    grouped = defaultdict(list)

    for k, v in data.get('conc_mM', {}).items():
        # remove trailing -number
        base_key = re.sub(r'-\d+$', '', k)

        val = float(v)

        if ignore_zero and val <= 0:
            continue

        grouped[base_key].append(val)

    data['conc_mM_median'] = {
        k: float(np.median(vs))
        for k, vs in grouped.items()
        if vs
    }

    return data

from collections import defaultdict
from typing import Dict, Any

def add_intg_norm_grouped(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collapse intg_norm replicate values into lists by molecule name
    and append the result as 'intg_norm_grouped'.
    """
    if "intg_norm" not in data or not isinstance(data["intg_norm"], dict):
        raise ValueError("data must contain an 'intg_norm' dictionary")

    grouped = defaultdict(list)

    for key, value in data["intg_norm"].items():
        molecule = key.rsplit("-", 1)[0]
        grouped[molecule].append(value)

    data["intg_norm_grouped"] = dict(grouped)
    return data


intg_result_folder = os.path.join(DATA_ROOT, "DPE_bromination", "_BDA_Benzylideneacetone", "2025-12-12-run03_BDA_calibration", "400MHz", "Results")
intg_result_file = os.path.join(intg_result_folder, "fitting_results.json")
calib_info_path = os.path.join(intg_result_folder, "calibration_TBABr_BDA_conc.xlsx")

calib_info_path_updated = os.path.join(intg_result_folder, "calibration_TBABr_BDA_conc_with_BDA.xlsx")

# load json to dict
with open(intg_result_file) as f:
    intg_result_dict = json.load(f)

starting_material_intg = parse_starting_materials(intg_result_dict)
print(starting_material_intg)

calib_info_df = append_starting_materials_intg(xlsx_path=calib_info_path,
                                               starting_materials=starting_material_intg,
                                               save_path=calib_info_path_updated)
print(f'calib_info_df: {calib_info_df}')
calib_info_df.to_csv(intg_result_folder + r'\BDA_calibration_all.csv')

BDA_proton_count = config.dictionnary_H_count.get("Starting material-1")
x1 = calib_info_df['[BDA](mM)']
x2 = calib_info_df['[TBABr](mM)']
y = calib_info_df['BDA_avg'] / BDA_proton_count
# y = np.log10(y)  # logarithm the values to avoid very large numbers

rbf_model = Rbf(x1, x2, y, function='multiquadric')
cv_result = five_fold_validation(x1, x2, y, )
print(cv_result)

plot_interp(x1, x2, y, rbf_model, save_path=intg_result_folder)

a = estimate_conc_by_rbf_model(additive_conc_here=75,
                               integral_value_normalized=1195527,
                               rbf_model=rbf_model)

print(a)


# ==================================================
# Linear calibration: y = k * x  (through origin)
# ==================================================
def fit_linear_origin(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)

    if np.any(x < 0) or np.any(y < 0):
        raise ValueError("Negative values detected.")

    denom = np.dot(x, x)
    if denom == 0:
        raise ZeroDivisionError("All x are zero.")

    return np.dot(x, y) / denom


def linear_origin_metrics(x, y, k):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    y_pred = k * x

    rmse = np.sqrt(np.mean((y - y_pred) ** 2))
    r2 = 1 - np.sum((y - y_pred) ** 2) / np.sum(y ** 2)

    return {"slope": k, "rmse": rmse, "r2_origin": r2}

def predict_linear(integral_value_normalized):

    BDA_proton_count = config.dictionnary_H_count["Starting material-1"]

    xx = calib_info_df["BDA_avg"] / BDA_proton_count  # normalized integral
    y = calib_info_df["[BDA](mM)"]  # concentration

    k_bda = fit_linear_origin(xx, y)
    metrics = linear_origin_metrics(xx, y, k_bda)
    # print(metrics)

    k = k_bda

    return k * np.asarray(integral_value_normalized, float)


import numpy as np
import matplotlib.pyplot as plt
import os

# ============================================
# Plot linear regression through origin
# ============================================
def plot_linear_origin_fit(
    save_path='linear_fit.png',
    title="Linear calibration (through origin)",
    xlabel="Normalized NMR integral",
    ylabel="Concentration (mM)",
):

    x = calib_info_df["BDA_avg"] / BDA_proton_count  # normalized integral
    y = calib_info_df["[BDA](mM)"]  # concentration

    k_bda = fit_linear_origin(x, y)
    k = k_bda

    x = np.asarray(x, float)
    y = np.asarray(y, float)

    # regression line
    x_line = np.linspace(0, x.max() * 1.05, 200)
    y_line = k_bda * x_line

    plt.figure(figsize=(5, 4), dpi=300)

    # scatter
    plt.scatter(x, y, s=35, alpha=0.8, label="Calibration points")

    # regression line
    plt.plot(
        x_line,
        y_line,
        color="red",
        lw=2,
        label=f"y = {k:.4g} · x"
    )

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend(frameon=False)
    plt.grid(True, linestyle="--", alpha=0.4)

    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()



if __name__ == "__main__":

    _bda = os.path.join(DATA_ROOT, "DPE_bromination", "_BDA_Benzylideneacetone")
    run_folders = [
        # os.path.join(_bda, "2025-12-12-run01_BDA_2nd", "Results_2025-12-12-run01_long_400MHz"),
        # os.path.join(_bda, "2025-12-12-run01_BDA_2nd", "Results_2025-12-12-run01_400MHz"),
        # os.path.join(_bda, "2025-12-12-run02_BDA_2nd", "Results_2025-12-12-run02_long_48h_400MHz"),
        # os.path.join(_bda, "2025-12-12-run02_BDA_2nd", "Results_2025-12-12-run02_400MHz"),
        # os.path.join(_bda, "2026-04-22-run01_BDA_revise_Q1_24h"),
        # os.path.join(_bda, "2026-04-22-run02_BDA_revise_Q2p_48h"),
        # os.path.join(_bda, "2026-04-22-run03_BDA_revise_Q4_24h"),
        # os.path.join(_bda, "2026-04-22-run04_BDA_revise_Q1_Q4_Q7_Q2p"),
        os.path.join(_bda, "2026-04-23-run01_BDA_revise_Q7_24h"),

    ]

    # PRE-REQUISITE: before running this script, prepare each run folder using utils.py:
    #   1. put_run_condition_in_spectrum_folder(path, spectrum_frequency='400MHz')
    #      → copies the reaction condition Excel into each spectrum subfolder
    #   2. put_fitting_results_in_spec_folder(path)
    #      → copies the NMR fitting JSON results into each spectrum subfolder
    # Both steps are needed so that each spectrum folder contains its own condition + fitting data.

    spectrum_folders = []
    for folder in run_folders:
        result_folder = folder + r'\Results'
        assert os.path.isdir(result_folder), f'Result folder does not exist: {result_folder}'
        # get all subfolders that contain 'BDA' in the folder name
        subfolders_for_spectrum = [
            os.path.join(result_folder, name)
            for name in os.listdir(result_folder)
            if 'BDA' in name and os.path.isdir(os.path.join(result_folder, name))
        ]
        assert len(subfolders_for_spectrum)>0, 'Results folder is empty!!'
        spectrum_folders.extend(subfolders_for_spectrum)

    print(spectrum_folders)

    for folder in spectrum_folders:
        print(f'processing folder: {folder}')
        fitting_result_json = folder + r'\\fitting_result.json'
        reaction_info_json = folder + r'\\reaction_info.json'
        assert os.path.isfile(fitting_result_json), f'Result folder does not exist in {fitting_result_json}'
        with open(fitting_result_json) as f:
            fitting_result_here = json.load(f)

        assert os.path.isfile(reaction_info_json), f'Result folder does not exist in {spectrum_folders}'
        with open(reaction_info_json) as f:
            reaction_info_here = json.load(f)

        conc_additive = reaction_info_here.get('conc_AA')

        fitting_intg_and_conc = extract_products_and_starting_materials(fitting_result_here)

        for key, value in fitting_intg_and_conc['intg_norm'].items():

            fitting_intg_and_conc['conc_mM'][key] = (
                estimate_conc_by_rbf_model(additive_conc_here=conc_additive,
                                           integral_value_normalized=value,
                                           rbf_model=rbf_model))

        fitting_intg_and_conc = add_conc_mM_median(fitting_intg_and_conc, ignore_zero=True)

        # add intg_norm_grouped into one dict
        fitting_intg_and_conc = add_intg_norm_grouped(fitting_intg_and_conc)

        fitting_result_with_conc_json = folder + r'\\fitting_result_with_conc.json'
        with open(fitting_result_with_conc_json,'w', encoding='utf-8') as f:
            json.dump(fitting_intg_and_conc,f,ensure_ascii=False,indent=2)
        print(f'Saved json: {fitting_intg_and_conc}')

    for folder in run_folders:
        df_all = pd.DataFrame()
        result_folder = folder + r'\Results'
        result_all_csv = result_folder + r'\result_all.csv'
        # get all the files iteratively in the subfolders of result_folder named: fitting_result_with_conc.json
        for root, dirs, files in os.walk(result_folder):
            if 'fitting_result_with_conc.json' in files:
                fitting_result_json_path = os.path.join(root, 'fitting_result_with_conc.json')
                with open(fitting_result_json_path, encoding='utf-8') as f:
                    fitting_result_from_json = json.load(f)
                reaction_info_json = os.path.join(root, 'reaction_info.json')
                with open(reaction_info_json, encoding='utf-8') as f:
                    reaction_info = json.load(f)

                ## append the info to df_all
                row_here = pd.json_normalize(reaction_info)
                for key, value in fitting_result_from_json['intg_norm_grouped'].items():
                    row_here[f'intg_norm_grouped_{key}'] = [value]

                for key, value in fitting_result_from_json['conc_mM_median'].items():
                    row_here[f'conc_{key}'] = value

                df_all = pd.concat([df_all, row_here], ignore_index=True)
                df_all = df_all.sort_values(by='local_index')
        # change col name for AA, BB, CC->TBABr, Br2, BDA
        rename_map = {
                    "conc_AA": "[TBABr]0",
                    "conc_BB": "[Br2]0",
                    "conc_CC": "[BDA]0", }
        df_all = df_all.rename(columns=rename_map)

        # add cols of 0s if not detected.
        compds_in_crude = config.compds_in_crude
        compds_in_crude_with_conc = [f'conc_{compd}' for compd in compds_in_crude]
        compds_in_crude_with_intg = [f'intg_norm_grouped_{compd}' for compd in compds_in_crude]
        # add missing columns filled with 0
        for col in compds_in_crude_with_conc:
            if col not in df_all.columns:
                df_all[col] = 0.0
        for col in compds_in_crude_with_intg:
            if col not in df_all.columns:
                df_all[col] = 0.0

        # reorder columns: keep existing non-conc columns first, then conc columns in given order
        non_intg_cols = [c for c in df_all.columns if c not in compds_in_crude_with_intg]
        df_all = df_all[non_intg_cols + compds_in_crude_with_intg]

        non_conc_cols = [c for c in df_all.columns if c not in compds_in_crude_with_conc]
        df_all = df_all[non_conc_cols + compds_in_crude_with_conc]


        # calculate the yield for all the cmpds
        for cmpd in compds_in_crude:
            cmpd_with_conc = f'conc_{cmpd}'
            stoi_dict = config.dictionnary_stockiometry

            # cal for limiting reagent conc
            stoi_for_br2 = stoi_dict.get(cmpd).get('Br')
            stoi_for_bda = stoi_dict.get(cmpd).get('BDA')
            if stoi_for_br2 == 0:
                limit_reagent_conc = df_all['[BDA]0'] * stoi_for_bda
            elif stoi_for_bda == 0:
                limit_reagent_conc = df_all['[Br2]0'] * stoi_for_br2
            else:
                limit_reagent_conc = np.minimum(df_all['[Br2]0'] * stoi_for_br2, df_all['[BDA]0'] * stoi_for_bda)

            # cal for yield
            numerator = df_all[cmpd_with_conc]
            denominator = limit_reagent_conc

            yield_col = f"yield_{cmpd}"

            df_all[yield_col] = np.where(
                numerator == 0,
                0.0,
                np.where(
                    denominator == 0,
                    np.nan,
                    numerator / denominator,
                ),
            )


        # save df_all to local file
        df_all.to_csv(result_all_csv)








