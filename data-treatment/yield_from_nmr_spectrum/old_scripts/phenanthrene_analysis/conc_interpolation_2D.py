""""
Interpolation of concentrations for bromination reactions for phenanthrene (which is labelled as 'phen' in this script)
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



def five_fold_validation_rbf(X1, X2, y, function='multiquadric'):
    """
    Perform 5-fold cross-validation for RBF interpolation model.
    Inputs:
        X1, X2 - 1D numpy arrays (two input variables)
        y      - 1D numpy array (target)
        function - RBF kernel
    """

    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    rmse_list = []
    r2_list = []

    for train_index, test_index in kf.split(X1):

        # --- Split data ---
        X1_train, X1_test = X1[train_index], X1[test_index]
        X2_train, X2_test = X2[train_index], X2[test_index]
        y_train, y_test   = y[train_index],  y[test_index]

        # --- Fit RBF on training fold ---
        rbf = Rbf(X1_train, X2_train, y_train, function=function)

        # --- Predict on test fold ---
        y_pred = rbf(X1_test, X2_test)

        # --- Evaluation ---
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2   = r2_score(y_test, y_pred)

        rmse_list.append(rmse)
        r2_list.append(r2)

    print("==== 5-Fold CV for RBF ====")
    print("RMSE per fold:", rmse_list)
    print("Mean RMSE:    {:.4f}".format(np.mean(rmse_list)))
    print("R² per fold:  ", r2_list)
    print("Mean R²:      {:.4f}".format(np.mean(r2_list)))

    return np.mean(rmse_list), np.mean(r2_list)

def plot_interp_phen(X1, X2, y, rbf_model,
                     save_path,
                     label_points=True):
    """
    3D RBF surface + scatter for the phen/TBABr system.

    X1 = TBABr concentration (mM)
    X2 = phen concentration (mM)
    y  = phen integration

    Saves an interactive HTML file if save_path is provided.
    """

    # === Build grid ===
    tbabr_vals = np.linspace(np.nanmin(X1), np.nanmax(X1), 50)
    phen_vals = np.linspace(np.nanmin(X2), np.nanmax(X2), 50)
    tbabr_grid, phen_grid = np.meshgrid(tbabr_vals, phen_vals)

    # === Predict interpolation surface ===
    intg_pred = rbf_model(tbabr_grid, phen_grid)  # shape (50, 50)

    # === Plot ===
    fig = go.Figure()

    # Surface
    fig.add_trace(go.Surface(
        x=tbabr_grid,
        y=phen_grid,
        z=intg_pred,
        colorbar_title="Integration",
        name="RBF Surface",
        showscale=True
    ))

    # Scatter3D of original points
    fig.add_trace(go.Scatter3d(
        x=X1,
        y=X2,
        z=y,
        mode='markers+text' if label_points else 'markers',
        text=[f"{val:.1f}" for val in y] if label_points else None,
        textposition="top center",
        marker=dict(size=5),
        name="Data Points",
        hovertemplate=(
            "TBABr: %{x} mM<br>"
            "phen: %{y} mM<br>"
            "integration: %{z}<extra>Data Point</extra>"
        )
    ))

    # Layout
    fig.update_layout(
        title="3D RBF Interpolation Surface (phen system)",
        scene=dict(
            xaxis_title="TBABr (mM)",
            yaxis_title="phen (mM)",
            zaxis_title="phen integration",
            camera=dict(
                eye=dict(x=0.9, y=2.5, z=2.4)
            )
        ),
        width=950,
        height=750
    )

    # === Saving ===
    if save_path:
        out_file = os.path.join(save_path, "phen_interp_plot.html")
        if os.path.isdir(save_path):
            out_file = out_file
        else:
            # If it's a filename
            root, ext = os.path.splitext(save_path)
            out_file = save_path if ext.lower() == ".html" else root + ".html"

        os.makedirs(os.path.dirname(out_file) or ".", exist_ok=True)
        fig.write_html(out_file, include_plotlyjs="cdn", full_html=True)
        print(f"Saved: {out_file}")

    return fig


def generate_rbf_model_for_phen(X1: list,
                                X2: list,
                                y: list,save_plot=True):

    # === Calibration data ===
    # X1 = df['[TBABr] (mM)'].values        # TBABr conc
    # X2 = df['[phen] (mM)'].values         # phen conc
    # y  = df['phen_intg'].values           # phen integration

    # === Five-fold validation ===
    five_fold_validation_rbf(X1, X2, y, function='multiquadric')

    # === Fit RBF model ===
    rbf_model = Rbf(X1, X2, y, function='multiquadric')

    # === Optional: 3D plot ===
    if save_plot:
        plot_interp_phen(X1, X2, y, rbf_model, save_path=calib_data_path)

    return rbf_model


def estimate_phen_conc(
        tbabr_conc_list,
        measured_integration_list,
        rbf_model
    ):
    """
    Estimate phen concentration from measured integration(s) using numerical inversion
    of the RBF model. Supports scalar or list inputs.
    """
    # Convert to array for convenience
    tbabr_conc_arr = np.atleast_1d(tbabr_conc_list)
    meas_arr = np.atleast_1d(measured_integration_list)

    results = []

    for meas in meas_arr:
        # Skip values too small
        if meas < 1e-4:
            results.append(0.0)
            continue

        # Define the objective for current measurement
        def objective(phen_guess):
            # Broadcast phen_guess to same length as tbabr_conc_arr
            phen_arr = np.full_like(tbabr_conc_arr, phen_guess, dtype=float)

            pred = rbf_model(tbabr_conc_arr, phen_arr)

            # RBF returns an array → reduce to scalar prediction
            pred_scalar = float(np.mean(pred))

            return (pred_scalar - meas) ** 2

        # Optimization in phen concentration domain
        result = minimize_scalar(objective, bounds=(0, 400), method='bounded')

        if not result.success:
            raise RuntimeError("Inversion failed")

        est = result.x

        results.append(est)

    # Return scalar if user passed scalar
    if np.isscalar(measured_integration_list):
        return results[0]
    return results


if __name__ == "__main__":

    BRUCELEE_PROJECT_DATA_PATH = os.environ['BRUCELEE_PROJECT_DATA_PATH']

    calib_data_path = BRUCELEE_PROJECT_DATA_PATH + r"\DPE_bromination\_Refs\2025-11-09-run04_calibration_Phen_400MHz"

    calib_data_file = calib_data_path + r"\concentration_table.xlsx"

    df = pd.read_excel(calib_data_file, engine='openpyxl')

    TBABr_conc_list = df['[TBABr] (mM)']  # [0, 0, 0, 0, 0, 75, 75, 75, 75, 75, 150, 150, 150, 150, 150]

    phen_conc_list = df['[phen] (mM)']  # [25, 50, 100, 200, 400, 25, 50, 100, 200, 400, 25, 50, 100, 200, 400]

    phen_integration_list = df['phen_intg']  # [63004857.72, 126210057.9, 262883967.1, 368881550.8, 381122395.4,
                                             #  23884272.97, 42892170.13, 90001504, 160842143.3, 200029941.7,
                                             #  15487644.66, 30491082.95, 43612772.76, 89277791.87, 156836630.2]

    # phen_integration_normalized_list = phen_integration_list / 2  # phenanthrene: 2H
    phen_integration_normalized_list = phen_integration_list # this is WRONG, just for testing


    rbf_model = generate_rbf_model_for_phen(X1=TBABr_conc_list,
                                            X2=phen_conc_list,
                                            y=phen_integration_normalized_list)

    result_excel_path = BRUCELEE_PROJECT_DATA_PATH + r"\DPE_bromination\2025-11-10-phenanthrene_results\_results.xlsx"
    df_result = pd.read_excel(result_excel_path, sheet_name='Integration_results')

    tbabr_conc_list = df_result['[TBABr]0 (mM)'].to_list()

    p1_intg_list = df_result['intg_p1'].to_numpy() / 2  # P1, 2H. Normalized.
    p2_intg_list = df_result['intg_p2'].to_numpy()  # 1H
    p4_intg_list = df_result['intg_p4'].to_numpy()  # 1H
    a_intg_list  = df_result['intg_A'].to_numpy()   # 1H

    p1_conc = estimate_phen_conc(tbabr_conc_list=tbabr_conc_list,
                       measured_integration_list=p1_intg_list,
                       rbf_model=rbf_model)
    p2_conc = estimate_phen_conc(tbabr_conc_list=tbabr_conc_list,
                       measured_integration_list=p2_intg_list,
                       rbf_model=rbf_model)
    p4_conc = estimate_phen_conc(tbabr_conc_list=tbabr_conc_list,
                       measured_integration_list=p4_intg_list,
                       rbf_model=rbf_model)
    a_conc = estimate_phen_conc(tbabr_conc_list=tbabr_conc_list,
                       measured_integration_list=a_intg_list,
                       rbf_model=rbf_model)

    df_result['P1_conc'] = p1_conc
    df_result['P2_conc'] = p2_conc
    df_result['P4_conc'] = p4_conc
    df_result['A_conc'] = a_conc

    limit_reagent_for_p1_p2 = df_result[['[phen]0 (mM)', '[Br2]0 (mM)']].min(axis=1)

    safe_limit = limit_reagent_for_p1_p2.replace(0, np.nan)  # avoid divide by zero
    df_result['P1_yield'] = (df_result['P1_conc'] / safe_limit * 100).fillna(0)
    df_result['P2_yield'] = (df_result['P2_conc'] / safe_limit * 100).fillna(0)


    # save results
    df_result.to_csv(BRUCELEE_PROJECT_DATA_PATH +
                     r"\DPE_bromination\2025-11-10-phenanthrene_results\_results_with_conc_new.csv",
                     index=False)


