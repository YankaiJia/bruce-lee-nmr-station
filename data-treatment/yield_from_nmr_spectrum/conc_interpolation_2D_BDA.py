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

BRUCELEE_PROJECT_DATA_PATH = os.environ['BRUCELEE_PROJECT_DATA_PATH']

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
    df["BDA_avg"] = round(df[["BDA_1", "BDA_2"]].mean(axis=1),1)

    # Save if requested
    if save_path is not None:
        df.to_excel(save_path, index=False)

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

    print(f"5-Fold Cross-Validation Results:")
    print(f"  Average RMSE: {avg_rmse:.2f}")
    print(f"  Average R² Score: {avg_r2:.4f}")

    return avg_rmse, avg_r2

import numpy as np
from scipy.interpolate import Rbf
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error


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


if __name__ == "__main__":

    intg_result_file = r"D:\Dropbox\brucelee\data\DPE_bromination\_BDA_Benzylideneacetone\2025-12-12-run03_BDA_calibration\400MHz\Results\fitting_results.json"
    calib_info_path = r"D:\Dropbox\brucelee\data\DPE_bromination\_BDA_Benzylideneacetone\2025-12-12-run03_BDA_calibration\400MHz\Results\calibration_TBABr_BDA_conc.xlsx"

    calib_info_path_updated = r"D:\Dropbox\brucelee\data\DPE_bromination\_BDA_Benzylideneacetone\2025-12-12-run03_BDA_calibration\400MHz\Results\calibration_TBABr_BDA_conc_with_BDA.xlsx"

    # load json to dict
    with open(intg_result_file) as f:
        intg_result_dict = json.load(f)

    starting_material_intg = parse_starting_materials(intg_result_dict)
    print(starting_material_intg)

    calib_info_df = append_starting_materials_intg(xlsx_path=calib_info_path,
                                                    starting_materials=starting_material_intg,
                                                    save_path=calib_info_path_updated)
    print(f'calib_info_df: {calib_info_df}')

    x1 = calib_info_df['[BDA](mM)']
    x2 = calib_info_df['[TBABr](mM)']
    y = calib_info_df['BDA_avg']
    rbf_model_here = Rbf(x1, x2, y, function='multiquadric')
    cv_result = five_fold_validation(x1, x2, y,)
    print(cv_result)
