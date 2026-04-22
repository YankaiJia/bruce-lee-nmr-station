""""
Interpolation of concentrations for bromination reactions.
"""
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import plotly.graph_objects as go

import json, os, re

from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, r2_score
from scipy.interpolate import Rbf
from scipy.optimize import minimize_scalar

import mpld3

import matplotlib

matplotlib.use('WebAgg')

import config

BRUCELEE_PROJECT_DATA_PATH = config.BRUCELEE_PROJECT_DATA_PATH
DATA_ROOT = config.DATA_ROOT

def json_to_intg_results(additive_type:str='TBABr'):

    ref_folder = os.path.join(DATA_ROOT, "DPE_bromination", "_Refs")

    if additive_type == 'TBABr':
        path = ref_folder + r"\ref_S_all_TBABr\Results"
    elif additive_type == 'TBABF4':
        path = ref_folder + r"\ref_S_all_TBABF4\Results"
    elif additive_type == 'TBPBr':
        path = ref_folder + r"\ref_S_all_TBPBr\Results"
    elif additive_type == 'TBABr3':
        path = ref_folder + r"\ref_S_all_TBABr3\Results"
    else:
        raise Exception("Salt of type:[TBABr,TBABF4,TBPBr,TBABr3] needs to be specified!")

    json_f = r'\fitting_results.json'
    # 1. load json of fitting results
    with open(path+json_f, "r", encoding="utf-8") as file:
        data = json.load(file)
    # print(f'data for calib len: {len(data)}')

    # 2. DPE、TBABr Starting material
    rows = []
    for sample_name, content in data.items():
        match = re.search(fr'{additive_type}_(\d+(?:\.\d+)?)mM_DPE_(\d+(?:\.\d+)?)mM', sample_name)
        if match:
            additive_conc = float(match.group(1))
            DPE_conc = float(match.group(2))
            starting_material = content.get("Starting material", None)
            rows.append({
                "DPE": DPE_conc,
                additive_type: additive_conc,
                "DPE_intg": starting_material
            })

    # 3. DataFrame for CSV
    df = pd.DataFrame(rows)
    assert not df.empty, "DataFrame for calibration is empty!"
    df.to_csv(path+r"\\dpe_tbabr_starting_material.csv", index=False)

    return df, path

def five_fold_validation(X, y):
    # === Initialize 5-fold cross-validation ===
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    r2_scores = []
    rmse_scores = []

    # === Cross-validation loop ===
    for train_index, test_index in kf.split(X):
        # Split into training and test sets
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = y[train_index], y[test_index]

        # Train RBF on training set
        rbf_model = Rbf(X_train[:, 0], X_train[:, 1], y_train, function='multiquadric')

        # Predict on test set
        y_pred = rbf_model(X_test[:, 0], X_test[:, 1])

        # Evaluate
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        # Store results
        rmse_scores.append(rmse)
        r2_scores.append(r2)

    # === Summary statistics ===
    avg_rmse = np.mean(rmse_scores)
    avg_r2 = np.mean(r2_scores)

    # print(f"5-Fold Cross-Validation Results:")
    # print(f"  Average RMSE: {avg_rmse:.2f}")
    # print(f"  Average R² Score: {avg_r2:.4f}")

    return avg_rmse, avg_r2


def plot_interp(X1, X2, y, rbf_model,
                save_path=False,
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


def generate_rbf_model(additive_type, save_plot=False):

    DPE_proton_count = 2

    # === Calibration data ===
    df, additive_ref_path = json_to_intg_results(additive_type)
    X = df[['DPE', additive_type]].values
    X1 = df["DPE"].values
    X2 = df[additive_type].values
    y = df["DPE_intg"].values / DPE_proton_count  # normalized y

    # === Fit RBF interpolation model ===
    rbf_model_here = Rbf(X1, X2, y, function='multiquadric')
    five_fold_validation(X, y)

    # === Optional: Show 3D interpolation surface ===
    if save_plot:
        plot_interp(X1, X2, y, rbf_model_here, save_path=additive_ref_path, additive_type=additive_type)

    return rbf_model_here

def estimate_conc_by_rbf_model(additive_conc_here,
                               integral_value_normalized,
                               additive_type,
                               show_plot: bool = True):

    if integral_value_normalized < 1E-4:
        return 0

    rbf_model = generate_rbf_model(additive_type, save_plot=False)

    # === Numerical inversion: find cmpd conc that gives closest integral ===
    def objective(dpe_guess):
        pred = rbf_model(dpe_guess, additive_conc_here)
        return abs(pred - integral_value_normalized)

    result = minimize_scalar(objective, bounds=(0, 450), method='bounded')
    estimated_conc = result.x if result.success else None
    assert estimated_conc, 'Finding estimated_dpe failed!'
    estimated_conc = 0 if estimated_conc < 1E-4 else estimated_conc

    return estimated_conc


def get_all_concs(intg_list=None,
                  additive_conc=None,
                  additive_type=None):

    if (intg_list==None) or (additive_conc==None):
        print(f'Waring, wrong input! intg: {intg_list},additive: {additive_conc}')
        return

    # intg_list order:
    # ["Starting material", "Product A", "Product B", 'HBr_adduct', 'Alcohol', 'Acid']
    intg_dpe, intg_a, intg_b, intg_adduct, intg_alcohol, intg_acid = intg_list

    # normalize the integrals
    proton_count = {'dpe': 2, 'a': 2, 'b': 1, 'adduct': 3, 'alcohol': 1, 'acid': 1}
    intg_dpe_normalized = intg_dpe / proton_count['dpe']
    intg_a_normalized = intg_a / proton_count['a']
    intg_b_normalized = intg_b / proton_count['b']
    intg_adduct_normalized = intg_adduct / proton_count['adduct']
    intg_alcohol_normalized = intg_alcohol / proton_count['alcohol']
    intg_acid_normalized = intg_acid / proton_count['acid']

    # Estimate concentrations using normalized integrals and the RBF model
    conc_dpe = estimate_conc_by_rbf_model(additive_conc, intg_dpe_normalized, additive_type)
    conc_a = estimate_conc_by_rbf_model(additive_conc, intg_a_normalized, additive_type)
    conc_b = estimate_conc_by_rbf_model(additive_conc, intg_b_normalized, additive_type)
    conc_adduct = estimate_conc_by_rbf_model(additive_conc, intg_adduct_normalized, additive_type)
    conc_alcohol = estimate_conc_by_rbf_model(additive_conc, intg_alcohol_normalized, additive_type)
    conc_acid = estimate_conc_by_rbf_model(additive_conc, intg_acid_normalized, additive_type)
    conc_list = [conc_dpe, conc_a, conc_b, conc_adduct, conc_alcohol, conc_acid]

    return conc_list

def get_additive_type_from_path(path: str) -> str:
    additive_types = ['TBABr3', 'TBABF4', 'TBPBr', 'TBABr']
    for salt in additive_types:
        if salt in path:
            return salt
    return 'TBABr'  # default fallback


def interp_one_folder(run_path=None,
                      forced_use_of_2d_calibration_curve_from_additive=None):

    print(f"Processing folder: {run_path}")

    additive_type = get_additive_type_from_path(run_path)

    # get the additive type for this folder
    if forced_use_of_2d_calibration_curve_from_additive:
        # when the additive is TBABr3, no 2d calibration is made due to reaction
        # between Br2 and DPE. Therefor, the calibration curve form TBABr is borrowed.
        additive_type_for_2d_fitting = forced_use_of_2d_calibration_curve_from_additive
    else:
        additive_type_for_2d_fitting = additive_type

    results_folder = run_path + r'\\Results'
    # get all the subfolders
    subfolders = [
        os.path.join(results_folder, name)
        for name in os.listdir(results_folder)
        if os.path.isdir(os.path.join(results_folder, name))
    ]
    spec_folders_path = [_folder for _folder in subfolders if '1D EXTENDED' in _folder]

    # do interpolation
    for folder in spec_folders_path:
        print(f"Interp for folder: {folder}")

        # get reaction info from json
        reaction_info_json = folder + r'\\reaction_info.json'

        # assert os.path.exists(reaction_info_json), f"File not found: {reaction_info_json}"
        if not os.path.exists(reaction_info_json):
            print(f"⚠️⚠️⚠️File not found: {reaction_info_json}")
            continue
        with open(reaction_info_json, 'r', encoding='utf-8') as f:
            reaction_info_dict = json.load(f)

        # get additive conc
        additive_conc = reaction_info_dict['conc_' + additive_type] * 1000 # M to mM

        # get fitting result from json
        fitting_result_json = folder + r'\\fitting_result.json'
        # assert os.path.exists(fitting_result_json), f"File not found: {fitting_result_json}"
        if not os.path.exists(fitting_result_json):
            print(f"⚠️⚠️⚠️Skipping — File not found: {fitting_result_json}")
            continue
        with open(fitting_result_json, 'r', encoding='utf-8') as f:
            fitting_result_dict = json.load(f)

        # get integrations for all cmpds from fitting result
        keys = fitting_result_dict.keys()
        cmpds = ["Starting material",
                 "Product A",
                 "Product B",
                 "HBr_adduct",
                 'Alcohol',
                 'Acid']
        intg_list = []
        for cmpd in cmpds:
            intg_here = fitting_result_dict[cmpd] if cmpd in keys else 0
            intg_list.append(intg_here)
        assert len(intg_list) == 6, "intg_list len incorrect!"

        # [conc_dpe, conc_a, conc_b, conc_adduct, conc_alcohol, conc_acid]
        conc_list = get_all_concs(intg_list, additive_conc, additive_type_for_2d_fitting)
        assert len(conc_list) == 6, "conc_list len incorrect!"

        # save all the concs to a json in the folder
        conc_dict = dict(zip(
            ['conc_DPE_final',
             'conc_prod_A',
             'conc_prod_B',
             'conc_adduct',
             'conc_alcohol',
             'conc_acid'],
            conc_list))

        print(f'conc_dict here: {conc_dict}')
        output_json = os.path.join(folder, 'interp_conc.json')
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(conc_dict, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":



    brom_folder = BRUCELEE_PROJECT_DATA_PATH + r"\\DPE_bromination"

    run_names = [
        # r"\2025-02-19-run02_normal_run",
        # r"\2025-03-01-run01_normal_run",
        # r"\2025-03-03-run01_normal_run",
        # r"\2025-03-03-run02_normal_run",
        # r"\2025-03-05-run01_normal_run",
        # r"\2025-03-12-run01_better_shimming",
        # r"\2025-07-01-run01_DCE_TBABr_rerun"

        # r'\2025-04-28-run01_DCE_TBABF4_normal',
        # r'\2025-04-28-run02_DCE_TBABF4_normal',
        # r'\2025-04-28-run03_DCE_TBABF4_normal',
        # r'\2025-04-28-run04_DCE_TBABF4_normal',
        # r'\2025-09-09-run01_DCE_TBABF4_add',
        # r'\2025-09-09-run01_DCE_TBABF4_add',

        # r'\2025-05-30-run01_DCE_TBPBr_normal',
        # r'\2025-05-30-run02_DCE_TBPBr_normal',
        # r'\2025-05-30-run03_DCE_TBPBr_normal',
        # r'\2025-05-30-run04_DCE_TBPBr_normal',
        # r'\2025-09-10-run01_DCE_TBPBr_add',
        # r'\2025-09-10-run02_DCE_TBPBr_add',

        # TBABr3
        r'\2025-04-15-run01_DCE_TBABr3_normal',
        r'\2025-04-15-run02_DCE_TBABr3_normal',
        r'\2025-04-15-run03_DCE_TBABr3_normal',
        r'\2025-04-15-run04_DCE_TBABr3_normal',
        r"\2025-04-22-run01_DCE_TBABr3_normal",
        r"\2025-09-11-run01_DCE_TBABr3_add",
        r"\2025-09-11-run02_DCE_TBABr3_add",

    ]

    run_folders = [brom_folder+name for name in run_names]

    for folder in run_folders:

        interp_one_folder(folder, forced_use_of_2d_calibration_curve_from_additive='TBABr')
