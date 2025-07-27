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
                "DEP_intg": starting_material
            })

    # 3. DataFrame for CSV
    df = pd.DataFrame(rows)
    df.to_csv(path+r"\\dpe_tbabr_starting_material.csv", index=False)

    return df

def five_fold_validation(df):
    # === Initialize 5-fold cross-validation ===
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    r2_scores = []
    rmse_scores = []

    X = df[["DPE", "TBABr"]].values
    y = df["DEP_intg"].values

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

    print(f"5-Fold Cross-Validation Results:")
    print(f"  Average RMSE: {avg_rmse:.2f}")
    print(f"  Average R² Score: {avg_r2:.4f}")

    return avg_rmse, avg_r2


def estimate_dpe_rbf_model(tbabr_value, dep_integral_value, show_plot=True):
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
    # === Calibration data ===
    df = json_to_intg_results()
    # === Fit RBF interpolation model ===
    rbf_model = Rbf(df["DPE"], df["TBABr"], df["DEP_intg"], function='multiquadric')
    five_fold_validation(df)
    # === Numerical inversion: find DPE that gives closest integral ===
    def objective(dpe_guess):
        pred = rbf_model(dpe_guess, tbabr_value)
        return abs(pred - dep_integral_value)

    result = minimize_scalar(objective, bounds=(0, 450), method='bounded')
    estimated_dpe = result.x if result.success else None

    # === Optional: Show 3D interpolation surface ===
    if show_plot:
        dpe_vals = np.linspace(df["DPE"].min(), df["DPE"].max(), 100)
        tbabr_vals = np.linspace(df["TBABr"].min(), df["TBABr"].max(), 100)
        dpe_grid, tbabr_grid = np.meshgrid(dpe_vals, tbabr_vals)
        dep_pred = rbf_model(dpe_grid, tbabr_grid)

        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        surface = ax.plot_surface(dpe_grid, tbabr_grid, dep_pred, cmap='viridis', alpha=0.9)
        ax.scatter(df["DPE"], df["TBABr"], df["DEP_intg"], color='red', label='Data Points')

        # Annotate each data point with its DEP_intg value
        for i in range(len(df)):
            x, y, z = df["DPE"][i], df["TBABr"][i], df["DEP_intg"][i]
            ax.text(x, y, z + 1, f'{z:.1f}', color='black', fontsize=8, ha='center')

        ax.set_xlabel("DPE")
        ax.set_ylabel("TBABr")
        ax.set_zlabel("DEP_intg")
        ax.set_title("3D RBF Interpolated Surface of DEP_intg")
        fig.colorbar(surface, ax=ax, shrink=0.5, aspect=10, label='DEP_intg')
        plt.tight_layout()
        plt.show()

    return estimated_dpe

def process_one_folder(run_path = None):

    results_folder = run_path + r'\\Results'
    # get all the subfolders
    subfolders = [
        os.path.join(results_folder, name)
        for name in os.listdir(results_folder)
        if os.path.isdir(os.path.join(results_folder, name))
    ]
    spec_folders_path = [folder for folder in subfolders if '1D EXTENDED' in folder]

    for folder in spec_folders_path:

        reaction_info_json = folder + r'\\reaction_info.json'
        assert os.path.exists(reaction_info_json), f"File not found: {reaction_info_json}"
        with open(reaction_info_json, 'r', encoding='utf-8') as f:
            reaction_info_dict = json.load(f)
        tbabr_conc = reaction_info_dict['conc_TBABr']

        # reaction_info_json =



if __name__ == "__main__":

    # result_folder = BRUCELEE_PROJECT_DATA_PATH + "\\DPE_bromination\\2025-02-19-run02_normal_run\\Results"

    result_folder = BRUCELEE_PROJECT_DATA_PATH + "\\DPE_bromination\\2025-02-19-run02_normal_run\\Results"

    a = estimate_dpe_rbf_model(150,50)

    print(a)