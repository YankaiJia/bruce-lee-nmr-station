""""
Interpolation of concentrations for bromination reactions.
"""
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd

import json
import os, re

from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, r2_score
from scipy.interpolate import Rbf
from scipy.optimize import minimize_scalar

# import matplotlib
# matplotlib.use('Agg')  # Use a non-interactive backend (no GUI)
# plt.ioff() # Turn off interactive mode, so multithreading will work

BRUCELEE_PROJECT_DATA_PATH = os.environ['BRUCELEE_PROJECT_DATA_PATH']


def json_to_intg_results():
    path = r"D:\Dropbox\brucelee\data\DPE_bromination\_Refs\ref_S_all\Results"
    json_f = r'\fitting_results.json'
    # 1. JSON
    with open(path+json_f, "r", encoding="utf-8") as file:
        data = json.load(file)

    # 2. DPE、TBABr Starting material
    rows = []
    for sample_name, content in data.items():
        match = re.search(r'TBABr_(\d+(?:\.\d+)?)mM_DPE_(\d+(?:\.\d+)?)mM', sample_name)
        if match:
            tbabr = float(match.group(1))
            dpe = float(match.group(2))
            starting_material = content.get("Starting material", None)
            rows.append({
                "DPE": dpe,
                "TBABr": tbabr,
                "DPE_intg": starting_material
            })

    # 3. DataFrame for CSV
    df = pd.DataFrame(rows)
    df.to_csv(path+r"\\dpe_tbabr_starting_material.csv", index=False)

    return df

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


def estimate_conc_by_rbf_model(tbabr_value_here, dpe_integral_value_normalized, show_plot=False):
    """
    Estimate DPE concentration from known TBABr and measured DEP NMR integral,
    using RBF interpolation on calibration data. Optionally shows a 3D plot.

    Parameters:
        tbabr_value (float): Known TBABr concentration.
        dep_integral_value (float): Measured NMR integral for DPE.
        show_plot (bool): Whether to show the 3D surface plot.

    Returns:
        float: Estimated DPE concentration.
    """
    if dpe_integral_value_normalized < 1E-4:
        return 0

    DPE_proton_count = 2

    # === Calibration data ===
    df = json_to_intg_results()
    X = df[['DPE', 'TBABr']].values
    X1 = df["DPE"].values
    X2 = df["TBABr"].values

    y = df["DPE_intg"].values / DPE_proton_count # normalized y

    # === Fit RBF interpolation model ===
    rbf_model = Rbf(X1, X2, y, function='multiquadric')
    five_fold_validation(X, y)

    # === Numerical inversion: find DPE that gives closest integral ===
    def objective(dpe_guess):
        pred = rbf_model(dpe_guess, tbabr_value_here)
        return abs(pred - dpe_integral_value_normalized)

    result = minimize_scalar(objective, bounds=(0, 450), method='bounded')
    estimated_dpe = result.x if result.success else None
    assert estimated_dpe, 'Finding estimated_dpe failed!'
    estimated_dpe = 0 if estimated_dpe < 1E-4 else estimated_dpe

    # === Optional: Show 3D interpolation surface ===
    if show_plot:
        dpe_vals = np.linspace(X1.min(), X1.max(), 50)
        tbabr_vals = np.linspace(X2.min(), X2.max(), 50)
        dpe_grid, tbabr_grid = np.meshgrid(dpe_vals, tbabr_vals)
        dep_pred = rbf_model(dpe_grid, tbabr_grid)

        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        surface = ax.plot_surface(dpe_grid, tbabr_grid, dep_pred, cmap='viridis', alpha=0.9)
        ax.scatter(X1, X2, y, color='red', label='Data Points')

        # Annotate each data point with its DPE_intg value
        for i in range(len(df)):
            print(X1)
            print(X2)
            print(y)
            a, b, c = X1[i], X2[i], y[i]
            ax.text(a, b, c + 1, f'{c:.1f}', color='black', fontsize=8, ha='center')

        ax.set_xlabel("DPE")
        ax.set_ylabel("TBABr")
        ax.set_zlabel("DPE_intg_normalized")
        ax.set_title("3D RBF Interpolated Surface of DPE_intg")
        fig.colorbar(surface, ax=ax, shrink=0.5, aspect=10, label='DPE_intg')
        plt.tight_layout()
        plt.show()
    print(f'estimated:{estimated_dpe}')
    return estimated_dpe


def get_all_concs(intg_list=None, conc_tbabr=None):
    if (intg_list==None) or (conc_tbabr==None):
        print(f'Waring, wrong input: {intg_list}_{conc_tbabr}')
        return
    # intg_list order: ["Starting material", "Product A", "Product B", 'HBr_adduct', 'Alcohol', 'Acid']
    intg_dpe, intg_a, intg_b, intg_adduct, intg_alcohol, intg_acid = intg_list
    proton_count = {
        'dpe': 2, 'a': 2, 'b': 1, 'adduct': 3, 'alcohol': 1, 'acid': 1,
    }
    intg_dpe_normalized = intg_dpe / proton_count['dpe']
    intg_a_normalized = intg_a / proton_count['a']
    intg_b_normalized = intg_b / proton_count['b']
    intg_adduct_normalized = intg_adduct / proton_count['adduct']
    intg_alcohol_normalized = intg_alcohol / proton_count['alcohol']
    intg_acid_normalized = intg_acid / proton_count['acid']

    # Estimate concentrations using normalized integrals and the RBF model
    conc_dpe = estimate_conc_by_rbf_model(conc_tbabr, intg_dpe_normalized)
    conc_a = estimate_conc_by_rbf_model(conc_tbabr, intg_a_normalized)
    conc_b = estimate_conc_by_rbf_model(conc_tbabr, intg_b_normalized)
    conc_adduct = estimate_conc_by_rbf_model(conc_tbabr, intg_adduct_normalized)
    conc_alcohol = estimate_conc_by_rbf_model(conc_tbabr, intg_alcohol_normalized)
    conc_acid = estimate_conc_by_rbf_model(conc_tbabr, intg_acid_normalized)
    conc_list = [conc_dpe, conc_a, conc_b, conc_adduct, conc_alcohol, conc_acid]

    return conc_list

def process_one_folder(run_path = None):

    print(f"Processing folder: {run_path}")
    results_folder = run_path + r'\\Results'
    # get all the subfolders
    subfolders = [
        os.path.join(results_folder, name)
        for name in os.listdir(results_folder)
        if os.path.isdir(os.path.join(results_folder, name))
    ]
    spec_folders_path = [folder for folder in subfolders if '1D EXTENDED' in folder]

    for folder in spec_folders_path:
        print(f"Interp for folder: {folder}")
        reaction_info_json = folder + r'\\reaction_info.json'
        assert os.path.exists(reaction_info_json), f"File not found: {reaction_info_json}"
        with open(reaction_info_json, 'r', encoding='utf-8') as f:
            reaction_info_dict = json.load(f)
        tbabr_conc = reaction_info_dict['conc_TBABr'] * 1000 # M to mM

        fitting_result_json = folder + r'\\fitting_result.json'
        assert os.path.exists(fitting_result_json), f"File not found: {fitting_result_json}"
        with open(fitting_result_json, 'r', encoding='utf-8') as f:
            fitting_result_dict = json.load(f)

        keys = fitting_result_dict.keys()
        cmpds = ["Starting material", "Product A", "Product B", 'HBr_adduct', 'Alcohol', 'Acid']
        intg_list = []
        for cmpd in cmpds:
            conc = fitting_result_dict[cmpd] if cmpd in keys else 0
            intg_list.append(conc)
        assert len(intg_list)==6, "intg_list len incorrect!"
        print(f'intg_list: {intg_list}')

        conc_list = get_all_concs(intg_list, tbabr_conc) # [conc_dpe, conc_a, conc_b, conc_adduct, conc_alcohol, conc_acid]
        print(f'conc_list: {conc_list}')
        assert len(conc_list)==6, "conc_list len incorrect!"
        # save all the concs to a json in the folder
        conc_dict = dict(zip(
            ['conc_DPE', 'conc_prod_A', 'conc_prod_B', 'conc_adduct', 'conc_alcohol', 'conc_acid'],
            conc_list
        ))

        output_json = os.path.join(folder, 'interp_conc.json')
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(conc_dict, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":

    brom_folder = BRUCELEE_PROJECT_DATA_PATH + r"\\DPE_bromination"

    run_names = [
        r"\2025-02-19-run02_normal_run",
        r"\2025-03-01-run01_normal_run",
        r"\2025-03-03-run01_normal_run",
        r"\2025-03-03-run02_normal_run",
        r"\2025-03-05-run01_normal_run",
        r"\2025-03-12-run01_better_shimming"
    ]

    run_folders = [brom_folder+name for name in run_names]

    for folder in run_folders:

        process_one_folder(folder)
