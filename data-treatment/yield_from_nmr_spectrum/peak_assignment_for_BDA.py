"""
After integration of peaks in the crude NMR spectra, it is found that the peaks are not well
assigned to the corresponding compounds. The mis-assignment is caused mainly by overlapping
and peak shift.

So this script is an attempt to make the assignments better by studying each compound and
write a parser for each compound or compound pair.
"""
import json
import math
import os
import numpy as np
import pandas as pd
import re

import matplotlib
matplotlib.use("TKAgg")

from matplotlib import pyplot as plt

import itertools
import warnings

import conc_interpolation_2D_BDA

PROTON_COUNT = {
                 'bda_ha': 1,
                 'px1_ha': 1,
                 'px1p_ha': 1,
                 'px2_hc': 1,
                 'px2_hcp': 1,
                 'px3_hc': 1,
                 'px4_hb': 1,
                 'px5_hc': 2,
                 'px5p_hc': 2,
                 'px7_hc': 2,
                 'px7p_hc': 2,
                 'px8_hc': 1,
                 'px8p_hc': 1
                }

BR_COUNT_IN_A_CMPD = {
                "px1": 1,
                "px1p": 1,
                "px2": 2,
                "px3": 3,
                "px4": 1,
                "px5": 2,
                "px6": 3,
                "px7": 1,
                "px7p": 1,
                "px8": 2,
                "px8p": 2,
                'px8ANDpx8p': 2}

CMPD_LS = [ 'bda',
            'px1',
            'px1p',
            'px2',
            'px3',
            'px4',
            'px5',
            'px5p',
            'px6',
            'px7',
            'px7p',
            'px8',
            'px8p',
            'px8ANDpx8p']

def get_all_result_json(run_folders):
    json_list = []

    for folder in run_folders:
        result_path = os.path.join(folder, 'Results')

        # get all subfolders containing "BDA" and sort them
        spectrum_folders = sorted(
            [
                name for name in os.listdir(result_path)
                if os.path.isdir(os.path.join(result_path, name)) and "BDA" in name
            ],
            key=lambda s: int(s.rsplit('-', 1)[-1])
        )
        spectrum_folders = [result_path + '\\' + folder for folder in spectrum_folders]
        print(spectrum_folders)

        fit_result_jsons = [spectrum_folder + r'\fitting_result.json'
                            for spectrum_folder in spectrum_folders]

        json_list.extend(fit_result_jsons)

    return json_list

def parse_raw_peaks(json_data):
    """
    Extract all raw peak entries from the 'Raw peaks data' section.

    Parameters
    ----------
    json_data : dict
        Loaded JSON dictionary.

    Returns
    -------
    list of dict
        Each dict corresponds to one peak with standardized fields.
    """

    raw_peaks = json_data.get("Raw peaks data", [])

    parsed_peaks = []

    for peak in raw_peaks:
        parsed_peaks.append({
            "product": peak.get("product"),
            "center_ppm": peak.get("center"),
            "area": peak.get("area"),
            "area_uncertainty": peak.get("area_uncertainty"),
            "amplitude": peak.get("amplitude"),
            "param_A": peak.get("parameter", [None]*4)[0],
            "param_x0": peak.get("parameter", [None]*4)[1],
            "param_gamma": peak.get("parameter", [None]*4)[2],
            "param_eta": peak.get("parameter", [None]*4)[3],
            "warning": peak.get("warning")
        })

    return parsed_peaks

def pseudo_voigt(x, A, x0, gamma, eta):
    """
    Pseudo-Voigt profile.
    """
    gaussian = np.exp(-4 * np.log(2) * ((x - x0) / gamma) ** 2)
    lorentzian = 1 / (1 + 4 * ((x - x0) / gamma) ** 2)
    return A * (eta * lorentzian + (1 - eta) * gaussian)


# --------------------------------------------------
# 3. Reconstruct & plot all fitted peaks
# --------------------------------------------------
def plot_reconstructed_peaks(
    df_peaks,
    x_min=None,
    x_max=None,
    n_points=8000,
    alpha_individual=0.4,
    show_peak_legend=True
):
    """
    Plot all reconstructed fitted peaks and their summed spectrum,
    with each peak shown in the legend.
    """

    if x_min is None:
        x_min = df_peaks["center_ppm"].min() - 0.2
    if x_max is None:
        x_max = df_peaks["center_ppm"].max() + 0.2

    x = np.linspace(x_min, x_max, n_points)
    y_total = np.zeros_like(x)

    plt.figure(figsize=(10, 4), dpi=300)

    for idx, row in df_peaks.iterrows():
        y_peak = pseudo_voigt(
            x,
            row["param_A"],
            row["center_ppm"],
            row["param_gamma"],
            row["param_eta"]
        )

        y_total += y_peak

        label = (
            f"{row['product']} @ {row['center_ppm']:.3f} ppm"
            if show_peak_legend else None
        )

        plt.plot(
            x,
            y_peak,
            lw=1,
            alpha=alpha_individual,
            label=label
        )

    # summed spectrum
    plt.plot(
        x,
        y_total,
        lw=2,
        color="black",
        label="Reconstructed spectrum"
    )

    plt.gca().invert_xaxis()  # NMR convention
    plt.xlabel("Chemical shift (ppm)")
    plt.ylabel("Intensity (a.u.)")

    if show_peak_legend:
        plt.legend(
            fontsize=7,
            ncol=2,
            frameon=False
        )
    else:
        plt.legend()

    plt.tight_layout()
    plt.show()

def parse_px1_px1p(
    df,
    ppm_window,
    px1_threshold=4.962,
    intensity_min=11,
):
    """
    Parse PX1 / PX1' Ha peaks.

    Labels
    ------
      - px1_ha
      - px1_prime_ha

    Special rules:
      - amplitude filtering ONLY applies when raw peak count is 5 or 6
      - UPDATED 5-peak rule:
            if any peak has ppm < ppm_window[0] → ignore that peak
            else                                → ignore leftmost peak

    Rules (after sorting by center_ppm descending):
      2 peaks  -> px1_ha OR px1_prime_ha (threshold-based)
      3 peaks  -> left 2 px1_ha, right 1 ignored
      4 peaks  -> left 2 px1_ha, right 2 px1_prime_ha
      5 peaks  -> special rule, then apply 4-peak rule
      6 peaks  -> ignore left 2, then apply 4-peak rule
    """

    # --- slice window ---
    df_win = df[
        (df["center_ppm"] >= ppm_window[0]) &
        (df["center_ppm"] <= ppm_window[1])
    ].copy()

    if df_win.empty:
        return df_win

    df_win["assigned_species"] = "ignored"

    # --------------------------------------------------
    # sort by ppm descending (NMR: left = larger ppm)
    # --------------------------------------------------
    df_sorted = df_win.sort_values(
        "center_ppm", ascending=False
    ).reset_index()

    n_raw = len(df_sorted)

    # --------------------------------------------------
    # apply intensity filter ONLY for 5 / 6 peaks
    # --------------------------------------------------
    if n_raw in (5, 6):
        df_valid = df_sorted[
            df_sorted["amplitude"] >= intensity_min
        ].copy()

        # safety fallback
        if len(df_valid) < 4:
            df_valid = df_sorted.copy()
    else:
        df_valid = df_sorted.copy()

    n = len(df_valid)

    # ---------- case: 2 peaks ----------
    if n == 2:
        max_ppm = df_valid["center_ppm"].max()
        if max_ppm < px1_threshold:
            df_valid.loc[:, "assigned_species"] = "px1p_ha"
        else:
            df_valid.loc[:, "assigned_species"] = "px1_ha"

    # ---------- case: 3 peaks ----------
    elif n == 3:
        df_valid.loc[df_valid.index[0:2], "assigned_species"] = "px1_ha"

    # ---------- case: 4 peaks ----------
    elif n == 4:
        df_valid.loc[df_valid.index[0:2], "assigned_species"] = "px1_ha"
        df_valid.loc[df_valid.index[2:4], "assigned_species"] = "px1p_ha"

    # ---------- case: 5 peaks (UPDATED) ----------
    elif n == 5:
        low_ppm_mask = df_valid["center_ppm"] < ppm_window[0]

        if low_ppm_mask.any():
            idx_ignore = df_valid[low_ppm_mask].index[0]
            core = df_valid.drop(index=idx_ignore).copy()
        else:
            core = df_valid.iloc[1:].copy()

        core = core.sort_values("center_ppm", ascending=False)

        core.loc[core.index[0:2], "assigned_species"] = "px1_ha"
        core.loc[core.index[2:4], "assigned_species"] = "px1p_ha"

        df_valid.loc[core.index, "assigned_species"] = core["assigned_species"]

    # ---------- case: 6 peaks ----------
    elif n == 6:
        core = df_valid.iloc[2:].copy()
        core.loc[core.index[0:2], "assigned_species"] = "px1_ha"
        core.loc[core.index[2:4], "assigned_species"] = "px1p_ha"
        df_valid.loc[core.index, "assigned_species"] = core["assigned_species"]

    else:
        warnings.warn(
            f"Unexpected number of peaks ({n}) in PX1 window"
        )

    # --------------------------------------------------
    # write assignments back to df_win
    # --------------------------------------------------
    df_win.loc[
        df_valid["index"],
        "assigned_species"
    ] = df_valid["assigned_species"].values

    return df_win


def _within_frac(a, b, frac):
    """Return True if a and b are within +/- frac of each other (order-independent)."""
    a = float(a); b = float(b)
    if a <= 0 or b <= 0:
        return False
    ratio = max(a, b) / min(a, b)
    return ratio <= (1.0 + frac)

def _test_px2_quad(
    df4,
    area_pair_tol=0.2,
    area_sum_tol=0.2,
    max_doublet_span=0.05,
    coupling_match_tol=0.01,
):
    # sort by ppm descending (NMR left is larger ppm)
    df4s = df4.sort_values("center_ppm", ascending=False)

    ppm = df4s["center_ppm"].to_numpy(dtype=float)
    areas = df4s["area"].to_numpy(dtype=float)

    left_span = abs(ppm[0] - ppm[1])
    right_span = abs(ppm[2] - ppm[3])

    if left_span >= max_doublet_span or right_span >= max_doublet_span:
        return False, None, None, None

    if abs(left_span - right_span) > coupling_match_tol:
        return False, None, None, None

    left_sum = areas[:2].sum()
    right_sum = areas[2:].sum()
    if not _within_frac(left_sum, right_sum, area_sum_tol):
        return False, None, None, None

    # big2/small2 area similarity
    df_area = df4s.sort_values("area", ascending=False)
    big2 = df_area.iloc[:2]["area"].to_numpy(dtype=float)
    small2 = df_area.iloc[2:]["area"].to_numpy(dtype=float)

    if not _within_frac(big2[0], big2[1], area_pair_tol):
        return False, None, None, None
    if not _within_frac(small2[0], small2[1], area_pair_tol):
        return False, None, None, None

    # assign all 4 peaks
    idx_sorted = df4s.index.to_list()
    assignment = pd.Series(index=idx_sorted, data="px2_hc", dtype=object)
    assignment.loc[idx_sorted[:2]] = "px2_hcp"
    assignment.loc[idx_sorted[2:]] = "px2_hc"

    # mark smaller-area-sum doublet
    small_mask = pd.Series(index=idx_sorted, data=False, dtype=bool)
    if left_sum <= right_sum:
        small_mask.loc[idx_sorted[:2]] = True
    else:
        small_mask.loc[idx_sorted[2:]] = True

    score = abs(left_sum - right_sum) / max(left_sum, right_sum, 1e-12)

    return True, assignment, small_mask, score


def _is_weak_strong_strong_weak(df4):
    """
    After sorting by ppm descending, check if the two largest areas
    are at middle positions (1 and 2): weak-strong-strong-weak.
    """
    df4s = df4.sort_values("center_ppm", ascending=False)
    areas = df4s["area"].to_numpy(dtype=float)

    strong_pos = set(np.argsort(areas)[-2:])  # positions of 2 largest
    return strong_pos == {1, 2}


def _area_sum_closeness_score(df4):
    """
    After sorting by ppm descending:
      score = |sum(left2) - sum(right2)| / (sum(left2) + sum(right2))
    Smaller is better. Range ~[0,1].
    """
    df4s = df4.sort_values("center_ppm", ascending=False)
    areas = df4s["area"].to_numpy(dtype=float)
    left_sum = areas[:2].sum()
    right_sum = areas[2:].sum()
    denom = (left_sum + right_sum)
    if denom <= 0:
        return np.inf
    return abs(left_sum - right_sum) / denom

def parse_px2_hc_hcp_bruteforce(
    df,
    ppm_window=(4.225, 4.475),
    intensity_min=10.0,
    area_pair_tol=1,
    area_sum_tol=1,
    max_doublet_span=0.05,
    max_combos_warn=50000,
):
    """
    Brute-force PX2 Hc / Hc′ assignment in the 1H NMR fitting peaks table.

    Output:
      - assigned_species: assigns ALL 4 peaks of the chosen quad:
            higher-ppm doublet -> px2_hcp
            lower-ppm  doublet -> px2_hc
      - px2_small_doublet: True only for the 2 peaks belonging to the
            smaller-area-sum doublet (label only; still assigns all 4 peaks)

    Notes:
      - Requires `_test_px2_quad()` to return: (ok, assign, small_mask, score)
      - Requires `_is_weak_strong_strong_weak(df4)` and `_area_sum_closeness_score(df4)`
    """

    # --- slice window (keep all peaks in output) ---
    df_win_all = df[
        (df["center_ppm"] >= ppm_window[0]) &
        (df["center_ppm"] <= ppm_window[1])
    ].copy()

    if df_win_all.empty:
        return df_win_all

    df_win_all["assigned_species"] = "ignored"
    df_win_all["px2_small_doublet"] = False  # NEW: label smaller doublet only

    # --- candidates used for brute force (do NOT drop from output) ---
    if "amplitude" in df_win_all.columns:
        df_cand = df_win_all[df_win_all["amplitude"] >= intensity_min].copy()
    else:
        df_cand = df_win_all.copy()

    n = len(df_cand)
    if n < 4:
        return df_win_all

    # --- helper to apply assignment back to full window ---
    def _apply(assign, small_mask):
        df_win_all.loc[assign.index, "assigned_species"] = assign.values
        df_win_all.loc[small_mask.index, "px2_small_doublet"] = small_mask.values
        return df_win_all

    # --- exact 4 peaks ---
    if n == 4:
        ok, assign, small_mask, _score = _test_px2_quad(
            df_cand,
            area_pair_tol=area_pair_tol,
            area_sum_tol=area_sum_tol,
            max_doublet_span=max_doublet_span,
        )
        if ok:
            return _apply(assign, small_mask)
        return df_win_all

    # --- brute force for >4 peaks ---
    idxs = list(df_cand.index)
    nC4 = (n * (n - 1) * (n - 2) * (n - 3)) // 24
    if nC4 > max_combos_warn:
        warnings.warn(
            f"PX2 brute force will test ~{nC4} combinations (n={n}). "
            f"Consider filtering by amplitude/area more aggressively."
        )

    best_any = None          # (score, assign, small_mask)
    best_any_score = np.inf

    best_wssw = None         # (score, assign, small_mask)
    best_wssw_score = np.inf

    for comb in itertools.combinations(idxs, 4):
        df4 = df_cand.loc[list(comb)]

        ok, assign, small_mask, _score_internal = _test_px2_quad(
            df4,
            area_pair_tol=area_pair_tol,
            area_sum_tol=area_sum_tol,
            max_doublet_span=max_doublet_span,
        )
        if not ok:
            continue

        # your selection score: closest left-vs-right area sums
        score = _area_sum_closeness_score(df4)

        # best overall valid
        if score < best_any_score:
            best_any_score = score
            best_any = (assign, small_mask)

        # best valid that also matches weak-strong-strong-weak
        if _is_weak_strong_strong_weak(df4):
            if score < best_wssw_score:
                best_wssw_score = score
                best_wssw = (assign, small_mask)

    # preference: best wssw; fallback: best overall valid
    if best_wssw is not None:
        assign, small_mask = best_wssw
        return _apply(assign, small_mask)

    if best_any is not None:
        assign, small_mask = best_any
        return _apply(assign, small_mask)

    return df_win_all


def parse_px3(
    df,
    target_ppm=6.43,
    ppm_window=(6.35, 6.50),
    tol=0.1
):
    """
    Parse PX3 using the characteristic singlet at ~6.43 ppm (Hc).

    Rules:
      - find peaks within ppm_window
      - if none: return empty
      - if one: assign as px3_hc
      - if multiple: choose the one closest to target_ppm as px3_hc
                     others ignored
    """

    # --- slice PX3 window ---
    df_win = df[
        (df["center_ppm"] >= ppm_window[0]) &
        (df["center_ppm"] <= ppm_window[1])
    ].copy()

    if df_win.empty:
        return df_win

    # initialize
    df_win["assigned_species"] = "ignored"

    # distance to target
    df_win["ppm_dist"] = np.abs(df_win["center_ppm"] - target_ppm)

    # pick closest peak
    best_idx = df_win["ppm_dist"].idxmin()
    best_ppm = df_win.loc[best_idx, "center_ppm"]

    # sanity check (optional but recommended)
    if abs(best_ppm - target_ppm) <= tol:
        df_win.loc[best_idx, "assigned_species"] = "px3_hc"

    else:
        # outside tolerance: treat as unreliable
        pass

    # cleanup
    df_win.drop(columns=["ppm_dist"], inplace=True)

    return df_win

def parse_px4(
    df,
    target_ppm=8.00,
    ppm_window=(7.95, 8.05),
    tol=0.05,
):
    """
    PX4 parser using singlet at ~8.00 ppm.
    """

    df_win = df[
        (df["center_ppm"] >= ppm_window[0]) &
        (df["center_ppm"] <= ppm_window[1])
    ].copy()

    if df_win.empty:
        return df_win

    df_win["assigned_species"] = "ignored"
    n = len(df_win)

    # ---------- 1 peak ----------
    if n == 1:
        df_win.loc[df_win.index[0], "assigned_species"] = "px4_hb"
        return df_win

    # ---------- 2 peaks: compare PEAK HEIGHT, not param_A ----------
    if n == 2:
        x_dense = np.linspace(ppm_window[0], ppm_window[1], 2000)

        heights = {}
        for idx, r in df_win.iterrows():
            y = pseudo_voigt(
                x_dense,
                A=r["param_A"],
                x0=r["param_x0"],
                gamma=r["param_gamma"],
                eta=r["param_eta"]
            )
            heights[idx] = y.max()

        best_idx = max(heights, key=heights.get)
        df_win.loc[best_idx, "assigned_species"] = "px4_hb"
        return df_win

    # ---------- >=3 peaks: fallback to ppm proximity ----------
    df_win["ppm_dist"] = np.abs(df_win["center_ppm"] - target_ppm)
    best_idx = df_win["ppm_dist"].idxmin()

    if abs(df_win.loc[best_idx, "center_ppm"] - target_ppm) <= tol:
        df_win.loc[best_idx, "assigned_species"] = "px4_hb"

    df_win.drop(columns=["ppm_dist"], inplace=True)
    return df_win
def parse_px5_px5p_by_hc(
    df,
    ppm_window=(4.45, 4.85),
    px5_center=4.52,
    px5p_center=4.75,
    split_ppm=4.65,
    pair_ppm_tol=0.03,
    area_ratio_tol=0.20,
):
    """
    Parse PX5 / PX5' using Hc singlets at ~4.52 (PX5) and ~4.75 ppm (PX5').

    Labels
    ------
      - px5_hc
      - px5_prime_hc

    Rules
    -----
    1) Work in ppm_window
    2) Detect unknown compound peak pairs:
         - |Δppm| < pair_ppm_tol
         - area difference <= area_ratio_tol
       → mark these two peaks as 'ignored'
       → DO NOT abort parsing
    3) PX5  : center_ppm < split_ppm
       PX5' : center_ppm > split_ppm
    4) Assignment logic:
       - if 1–2 valid peaks:
             assign by hard ppm rule first,
             fallback to closest center
       - if ≥3 valid peaks:
             pick best px5 (< split_ppm)
             pick best px5' (> split_ppm)
             others ignored
    """

    # --------------------------------------------------
    # slice window
    # --------------------------------------------------
    df_win = df[
        df["center_ppm"].between(*ppm_window)
    ].copy()

    if df_win.empty:
        return df_win

    df_win["assigned_species"] = "ignored"

    # --------------------------------------------------
    # Step 1: detect unknown compound peak pairs
    # --------------------------------------------------
    unknown_indices = set()

    df_sorted = df_win.sort_values("center_ppm").reset_index()

    for i in range(len(df_sorted) - 1):
        r1 = df_sorted.loc[i]
        r2 = df_sorted.loc[i + 1]

        d_ppm = abs(r1["center_ppm"] - r2["center_ppm"])
        if d_ppm >= pair_ppm_tol:
            continue

        a1, a2 = r1["area"], r2["area"]
        if a1 is None or a2 is None or a1 <= 0 or a2 <= 0:
            continue

        area_ratio = abs(a1 - a2) / ((a1 + a2) / 2)

        if area_ratio <= area_ratio_tol:
            unknown_indices.update([r1["index"], r2["index"]])

    if unknown_indices:
        df_win.loc[list(unknown_indices), "assigned_species"] = "ignored"

    # --------------------------------------------------
    # Step 2: candidate pool
    # --------------------------------------------------
    df_cand = df_win.drop(index=list(unknown_indices), errors="ignore").copy()

    if df_cand.empty:
        return df_win

    df_cand["dist_px5"] = abs(df_cand["center_ppm"] - px5_center)
    df_cand["dist_px5p"] = abs(df_cand["center_ppm"] - px5p_center)

    n = len(df_cand)

    # --------------------------------------------------
    # Step 3: assignment
    # --------------------------------------------------
    # ---------- case: 1–2 peaks ----------
    if n <= 2:
        for idx, r in df_cand.iterrows():
            ppm = r["center_ppm"]

            if ppm < split_ppm:
                df_win.loc[idx, "assigned_species"] = "px5_hc"
            elif ppm > split_ppm:
                df_win.loc[idx, "assigned_species"] = "px5p_hc"
            else:
                # fallback: closest center
                if r["dist_px5"] <= r["dist_px5p"]:
                    df_win.loc[idx, "assigned_species"] = "px5_hc"
                else:
                    df_win.loc[idx, "assigned_species"] = "px5p_hc"

    # ---------- case: ≥3 peaks ----------
    else:
        df_left = df_cand[df_cand["center_ppm"] < split_ppm]
        df_right = df_cand[df_cand["center_ppm"] > split_ppm]

        if not df_left.empty:
            idx_px5 = df_left["dist_px5"].idxmin()
            df_win.loc[idx_px5, "assigned_species"] = "px5_hc"

        if not df_right.empty:
            idx_px5p = df_right["dist_px5p"].idxmin()
            df_win.loc[idx_px5p, "assigned_species"] = "px5p_hc"

    return df_win


def parse_px6(
    df,
    hb_window=(8.18, 8.28),
    hc_window=(6.95, 7.05),
    hb_target=8.23,
    hc_target=7.00,
    area_tol=0.20,     # 20%
    strict=False,      # True -> raise AssertionError on mismatch
    verbose=True,      # print when Hb candidate exists
):
    """
    Parse PX6 (minor) using Hb singlet (~8.23 ppm) with Hc confirmation (~7.00 ppm).

    Rules (per your spec):
      1) Find Hb in hb_window. If none -> return (all ignored).
      2) If Hb exists -> print a message (PX6 is usually absent).
      3) Assertion/confirmation: find Hc in hc_window and require
         area(Hc) ~= area(Hb) within area_tol (default 20%).
         If confirmation fails -> treat as unreliable and ignore both.

    Returns
    -------
    df_win : DataFrame
        Peaks within hb_window OR hc_window, with column 'assigned_species'
        in {'px6_hb','px6_hc','ignored'}.
    """

    # --- window slices (keep original index) ---
    df_hb = df[(df["center_ppm"] >= hb_window[0]) & (df["center_ppm"] <= hb_window[1])].copy()
    df_hc = df[(df["center_ppm"] >= hc_window[0]) & (df["center_ppm"] <= hc_window[1])].copy()

    # union for return
    df_win = pd.concat([df_hb, df_hc], axis=0).copy()
    if df_win.empty:
        return df_win

    df_win["assigned_species"] = "ignored"

    # -------------------------
    # Step 1) Hb candidate
    # -------------------------
    if df_hb.empty:
        return df_win

    df_hb = df_hb.copy()
    df_hb["dist"] = np.abs(df_hb["center_ppm"] - hb_target)
    # choose closest to target; tie-breaker by larger area (or amplitude if you prefer)
    hb_pick = df_hb.sort_values(["dist", "area"], ascending=[True, False]).iloc[0]
    hb_idx = hb_pick.name

    # print whenever Hb window has something (you asked for this)
    if verbose:
        fpath = df["file_path"].iloc[0] if "file_path" in df.columns and len(df) > 0 else ""
        msg = (f"[PX6] Hb candidate found: ppm={hb_pick['center_ppm']:.4f}, "
               f"area={hb_pick['area']:.2f} | {fpath[-80:]}")
        warnings.warn(msg)

    # -------------------------
    # Step 3) Hc confirmation
    # -------------------------
    if df_hc.empty:
        txt = f"[PX6] Hb exists but no Hc found in window {hc_window}. Treat as unreliable."
        if strict:
            raise AssertionError(txt)
        warnings.warn(txt)
        return df_win  # keep all ignored (do NOT assign Hb alone)

    df_hc = df_hc.copy()
    df_hc["dist"] = np.abs(df_hc["center_ppm"] - hc_target)
    hc_pick = df_hc.sort_values(["dist", "area"], ascending=[True, False]).iloc[0]
    hc_idx = hc_pick.name

    # area check
    if not _within_frac(hb_pick["area"], hc_pick["area"], area_tol):
        txt = (f"[PX6] Hb/Hc area mismatch: Hb={hb_pick['area']:.2f} @ {hb_pick['center_ppm']:.4f}, "
               f"Hc={hc_pick['area']:.2f} @ {hc_pick['center_ppm']:.4f} "
               f"(tol={area_tol*100:.0f}%). Treat as unreliable.")
        if strict:
            raise AssertionError(txt)
        warnings.warn(txt)
        return df_win  # keep all ignored

    # passed: assign both
    df_win.loc[hb_idx, "assigned_species"] = "px6_hb"
    df_win.loc[hc_idx, "assigned_species"] = "px6_hc"

    # optional: sort for nicer display (NMR: left larger ppm)
    df_win = df_win.sort_values("center_ppm", ascending=False)
    return df_win


def func_check_doublet(
    r1,
    r2,
    area_tol=0.20,
    ppm_span_min=0.01,
    ppm_span_max=0.10,
):
    """
    Check whether two peaks form a Ha doublet.

    Conditions:
      - ppm distance in (ppm_span_min, ppm_span_max)
      - areas within ±area_tol
    """
    ppm1, ppm2 = r1["center_ppm"], r2["center_ppm"]
    a1, a2 = r1["area"], r2["area"]

    if a1 <= 0 or a2 <= 0:
        return False

    d_ppm = abs(ppm1 - ppm2)
    if not (ppm_span_min <= d_ppm <= ppm_span_max):
        return False

    area_diff = abs(a1 - a2) / ((a1 + a2) / 2)
    if area_diff > area_tol:
        return False

    return True

def _area_diff_score(r1, r2):
    """Smaller is better."""
    return abs(r1["area"] - r2["area"])


def parse_px7_px7p_ha_doublets(
    df,
    ppm_window=(6.85, 7.05),
    area_tol=0.20,
    ppm_span_min=0.01,
    ppm_span_max=0.10,
    max_pairs=2,
):
    """
    Rewritten Ha parser for PX7 / PX7′ assuming Ha always appears as doublets.

    Logic:
      - 0 doublet  → return empty
      - 1 doublet  → return one pair
      - 2 doublets → return two pairs (max)

    Returns
    -------
    list of tuples
        Each element is (idx1, idx2) representing one doublet
    """

    # -----------------------------
    # slice window
    # -----------------------------
    df_win = df[
        (df["center_ppm"] >= ppm_window[0]) &
        (df["center_ppm"] <= ppm_window[1])
    ].copy()

    n = len(df_win)
    if n < 2:
        return []

    rows = list(df_win.iterrows())  # [(idx, row), ...]

    # -----------------------------
    # collect all valid doublet pairs
    # -----------------------------
    valid_pairs = []

    for (i1, r1), (i2, r2) in itertools.combinations(rows, 2):
        if func_check_doublet(
            r1, r2,
            area_tol=area_tol,
            ppm_span_min=ppm_span_min,
            ppm_span_max=ppm_span_max,
        ):
            score = _area_diff_score(r1, r2)
            valid_pairs.append({
                "pair": (i1, i2),
                "score": score,
            })

    if not valid_pairs:
        return []

    # -----------------------------
    # case: n == 2
    # -----------------------------
    if n == 2:
        # only one possible pair
        return [valid_pairs[0]["pair"]]

    # -----------------------------
    # case: n == 3
    # -----------------------------
    if n == 3:
        # choose best (smallest area diff)
        best = min(valid_pairs, key=lambda x: x["score"])
        return [best["pair"]]

    # -----------------------------
    # case: n >= 4
    # -----------------------------
    # sort by score (best first)
    valid_pairs.sort(key=lambda x: x["score"])

    selected_pairs = []
    used_indices = set()

    for item in valid_pairs:
        i1, i2 = item["pair"]

        # do not reuse the same peak
        if i1 in used_indices or i2 in used_indices:
            continue

        selected_pairs.append((i1, i2))
        used_indices.update([i1, i2])

        if len(selected_pairs) >= max_pairs:
            break

    return selected_pairs


def _area_within(a, b, tol=0.15):
    """Check if a and b are within ±tol (fraction)."""
    if a <= 0 or b <= 0:
        return False
    return abs(a - b) / ((a + b) / 2) <= tol

def _area_sum(idxs, df):
    return df.loc[list(idxs), "area"].sum()

def assign_px7_px7p_by_hc(
    df: pd.DataFrame,
    ha_pairs,
    hc_window_left=(4.05, 4.2),   # ~4.12 → PX7 Hc (2H singlet)
    hc_window_right=(4.2, 4.4),  # ~4.34 → PX7′ Hc (2H singlet)
    area_tol=0.20,
):
    """
    Assign PX7 / PX7′ using Hc singlets (~4.12 / ~4.34 ppm)
    and Ha doublet pair(s) (~6.9–7.0 ppm).

    Chemical model
    --------------
    - Each compound (PX7 or PX7′):
        Ha = 1H doublet
        Hc = 2H singlet

    - Therefore:
        area(Hc) ≈ 2 × area(Ha doublet)

    - Ha doublets may overlap:
        one observed Ha doublet can be:
          (a) from PX7 only
          (b) from PX7′ only
          (c) overlap of PX7 + PX7′

    Parameters
    ----------
    df : DataFrame
        Full peak table.
    ha_pairs : list of tuple
        Output from Ha doublet parser:
          - []                 → no Ha
          - [(i1,i2)]          → one Ha doublet
          - [(i1,i2),(i3,i4)]  → two Ha doublets

    Returns
    -------
    dict
        {
          "px7":  [indices of Hc peaks],
          "px7p": [indices of Hc peaks],
        }

    Raises
    ------
    RuntimeError
        If area relations cannot be satisfied.
    """

    ## if ha_pairs is empty, return empty
    if len(ha_pairs) == 0:
        return {
            "px7": [],
            "px7p": [],
        }

    # --------------------------------------------------
    # Step 1: collect Hc candidates
    # --------------------------------------------------
    df_left = df[
        df["center_ppm"].between(*hc_window_left)
    ]
    df_right = df[
        df["center_ppm"].between(*hc_window_right)
    ]

    if df_left.empty and df_right.empty:
        raise RuntimeError("No Hc peaks found for PX7 / PX7′")

    pf_left = list(df_left.index)
    pf_right = list(df_right.index)

    # --------------------------------------------------
    # Precompute Ha pair areas
    # --------------------------------------------------
    ha_areas = [
        df.loc[list(pair), "area"].sum()
        for pair in ha_pairs
    ]

    # ==================================================
    # CASE 1: only ONE Ha doublet detected
    # ==================================================
    if len(ha_pairs) == 1:

        ha_area = ha_areas[0] * 2  # account for 2 HC
        # print(f'ha_area: {ha_area}')

        best_idx = None
        best_side = None
        best_diff = float("inf")

        # ==================================================
        # CASE 1 (UPDATED): ONE Ha doublet → ALWAYS assume overlap
        # ==================================================
        # print(f"[PX7] Ha doublet area = {ha_area:.3f}")

        best_idx = None
        best_side = None
        best_diff = float("inf")

        # ----------------------------------------------
        # Step 1: find Hc peak closest to Ha area
        # ----------------------------------------------
        for idx in pf_left:
            hc_area = df.loc[idx, "area"]
            diff = abs(hc_area - ha_area)
            if diff < best_diff:
                best_diff = diff
                best_idx = idx
                best_side = "left"

        for idx in pf_right:
            hc_area = df.loc[idx, "area"]
            diff = abs(hc_area - ha_area)
            if diff < best_diff:
                best_diff = diff
                best_idx = idx
                best_side = "right"

        if best_idx is None:
            raise RuntimeError("PX7/PX7p: no Hc candidates found")

        assign = {"px7": [], "px7p": []}

        # ----------------------------------------------
        # Step 2: assign primary & search complementary
        # ----------------------------------------------
        if best_side == "left":
            assign["px7"].append(best_idx)

            for idx in pf_right:
                hc_area = df.loc[idx, "area"]
                if _area_within(hc_area, best_diff, 0.40):
                    assign["px7p"].append(idx)
                    break
            else:
                pass
                # warnings.warn("No px7p_Hc detected!")

        else:  # best_side == "right"
            assign["px7p"].append(best_idx)

            for idx in pf_left:
                hc_area = df.loc[idx, "area"]
                if _area_within(hc_area, best_diff, 0.30):
                    assign["px7"].append(idx)
                    break
            else:
                warnings.warn("No px7_hc detected!")

        return assign


    # ==================================================
    # CASE 2: TWO Ha doublets detected
    # ==================================================
    if len(ha_pairs) == 2:
        ha_area1, ha_area2 = ha_areas

        # total-area sanity check (important but implicit)
        for i_left in pf_left:
            for i_right in pf_right:
                a_left = df.loc[i_left, "area"]
                a_right = df.loc[i_right, "area"]

                # print((a_left + a_right) / 2, ha_area1 + ha_area2)

                # pf1 + pf2 must match total Ha area
                if not _area_within(
                    (a_left + a_right) / 2, # two equal protons of Hc
                    ha_area1 + ha_area2,
                    area_tol,
                ):

                    continue

                # ------------------------------------------
                # mapping option A:
                #   left  ↔ ha1
                #   right ↔ ha2
                # ------------------------------------------
                if (
                    _area_within(a_left/2, ha_area1, area_tol) or
                    _area_within(a_right/2, ha_area2, area_tol)
                ):
                    return {
                        "px7": [i_left],
                        "px7p": [i_right],
                    }

                # ------------------------------------------
                # mapping option B:
                #   left  ↔ ha2
                #   right ↔ ha1
                # ------------------------------------------
                if (
                    _area_within(a_left/2, ha_area2, area_tol) or
                    _area_within(a_right/2, ha_area1, area_tol)
                ):
                    return {
                        "px7": [i_left],
                        "px7p": [i_right],
                    }

        raise RuntimeError(
            "PX7/PX7′ assignment failed (2 Ha doublets): "
            "cannot map Hc peaks to Ha pairs consistently"
        )

    # ==================================================
    # Unsupported
    # ==================================================
    raise RuntimeError(
        f"Unsupported number of Ha doublets: {len(ha_pairs)}"
    )


def apply_px7_px7p_to_df_win(
    df_win,
    assign_map,
    ha_window=(6.85, 7.05),
):
    df_win = df_win.copy()

    # clear old px7 labels
    df_win.loc[
        df_win["assigned_species"].isin(
            ["px7_hc", "px7p_hc", "px7_ha"]
        ),
        "assigned_species"
    ] = "ignored"

    # -------- px7 --------
    for idx in assign_map.get("px7", []):
        if idx in df_win.index:
            ppm = df_win.loc[idx, "center_ppm"]
            if ha_window[0] <= ppm <= ha_window[1]:
                df_win.loc[idx, "assigned_species"] = "px7_Ha"
            else:
                df_win.loc[idx, "assigned_species"] = "px7_hc"

    # -------- px7p --------
    for idx in assign_map.get("px7p", []):
        if idx in df_win.index:
            df_win.loc[idx, "assigned_species"] = "px7p_hc"

    return df_win


def parse_px7_px7p_block(
    df_peaks: pd.DataFrame,
    ha_window=(6.85, 7.05),
    hc_window_7=(4.05, 4.20),
    hc_window_7p=(4.20, 4.40),
    area_tol=0.20,
):
    """
    Parse PX7 / PX7p using:
      - Ha doublets at ~6.9–7.0 ppm
      - Hc singlets at ~4.12 (PX7) and ~4.34 (PX7p)

    This function:
      1) Collects all relevant Ha + Hc peaks into df_win7
      2) Detects 0 / 1 / 2 Ha doublets
      3) Uses Hc–Ha area logic to assign px7 / px7p
      4) Writes assignments back into df_win7

    Returns
    -------
    df_win7 : pandas.DataFrame
        Subset of df_peaks with column `assigned_species`
        ∈ {"px7", "px7p", "ignored"}
    """

    # --------------------------------------------------
    # Step 0: collect window (Ha + Hc)
    # --------------------------------------------------
    df_win7 = df_peaks[
        (df_peaks["center_ppm"].between(*ha_window)) |
        (df_peaks["center_ppm"].between(*hc_window_7)) |
        (df_peaks["center_ppm"].between(*hc_window_7p))
    ].copy()

    if df_win7.empty:
        return df_win7

    df_win7["assigned_species"] = "ignored"  # default

    # --------------------------------------------------
    # Step 1: find Ha doublets
    # --------------------------------------------------
    df_ha = df_win7[df_win7["center_ppm"].between(*ha_window)]

    ha_pairs = parse_px7_px7p_ha_doublets(df_ha)
    # expected:
    #   [] |
    #   [(i1, i2)] |
    #   [(i1, i2), (i3, i4)]
    # where i's are row indices of df_peaks

    if not ha_pairs:
        # no Ha → nothing to assign
        return df_win7

    # --------------------------------------------------
    # Step 2: assign px7 / px7p via Hc peaks
    # --------------------------------------------------
    assign_map = assign_px7_px7p_by_hc(
        df=df_peaks,
        ha_pairs=ha_pairs,
        hc_window_left=hc_window_7,
        hc_window_right=hc_window_7p,
        area_tol=area_tol,
    )

    if not assign_map:
        # assignment failed safely upstream
        return df_win7

    # --------------------------------------------------
    # Step 3: write assignment back to df_win7
    # --------------------------------------------------
    df_win7 = apply_px7_px7p_to_df_win(
        df_win=df_win7,
        assign_map=assign_map,
        ha_window=ha_window,  # IMPORTANT: distinguish Ha vs Hc
    )

    return df_win7

def parse_px8_px8p_by_hc(
    df,
    ppm_window=(5.8, 6.2),
    px8_center=6.05,
    px8p_center=6.15,
    tol=None,  # optional hard tolerance
):
    """
    Parse PX8 / PX8' using Hc singlets near 6.05 (PX8) and 6.15 (PX8').

    Labels:
      - px8_hc
      - px8_prime_hc

    Rules
    -----
    1) Slice peaks in ppm_window
    2) Init assigned_species = "ignored"
    3) If 1 peak:
         assign to whichever center is closer
    4) If >=2 peaks:
         pick closest to px8_center  -> px8_hc
         pick closest to px8p_center -> px8_prime_hc
         (resolve collision if both pick the same peak)
    """

    # -------------------------
    # slice window
    # -------------------------
    df_win = df[
        df["center_ppm"].between(*ppm_window)
    ].copy()

    if df_win.empty:
        return df_win

    df_win["assigned_species"] = "ignored"

    # distances
    df_win["dist_px8"] = abs(df_win["center_ppm"] - px8_center)
    df_win["dist_px8p"] = abs(df_win["center_ppm"] - px8p_center)

    n = len(df_win)

    # -------------------------
    # case: only 1 peak
    # -------------------------
    if n == 1:
        idx = df_win.index[0]

        if df_win.loc[idx, "dist_px8"] <= df_win.loc[idx, "dist_px8p"]:
            if tol is None or df_win.loc[idx, "dist_px8"] <= tol:
                df_win.loc[idx, "assigned_species"] = "px8_hc"
        else:
            if tol is None or df_win.loc[idx, "dist_px8p"] <= tol:
                df_win.loc[idx, "assigned_species"] = "px8p_hc"

        return df_win.drop(columns=["dist_px8", "dist_px8p"])

    # -------------------------
    # case: >=2 peaks
    # -------------------------
    px8_sorted = df_win.sort_values("dist_px8")
    px8p_sorted = df_win.sort_values("dist_px8p")

    idx_px8 = px8_sorted.index[0]
    idx_px8p = px8p_sorted.index[0]

    # collision: same peak picked for both
    if idx_px8 == idx_px8p:
        d8 = df_win.loc[idx_px8, "dist_px8"]
        d8p = df_win.loc[idx_px8, "dist_px8p"]

        if d8 <= d8p:
            # keep for px8
            if tol is None or d8 <= tol:
                df_win.loc[idx_px8, "assigned_species"] = "px8_hc"

            # find next-best px8p
            for idx2 in px8p_sorted.index[1:]:
                if tol is None or df_win.loc[idx2, "dist_px8p"] <= tol:
                    df_win.loc[idx2, "assigned_species"] = "px8p_hc"
                    break
        else:
            # keep for px8'
            if tol is None or d8p <= tol:
                df_win.loc[idx_px8, "assigned_species"] = "px8p_hc"

            # find next-best px8
            for idx2 in px8_sorted.index[1:]:
                if tol is None or df_win.loc[idx2, "dist_px8"] <= tol:
                    df_win.loc[idx2, "assigned_species"] = "px8_hc"
                    break
    else:
        # normal case
        if tol is None or df_win.loc[idx_px8, "dist_px8"] <= tol:
            df_win.loc[idx_px8, "assigned_species"] = "px8_hc"

        if tol is None or df_win.loc[idx_px8p, "dist_px8p"] <= tol:
            df_win.loc[idx_px8p, "assigned_species"] = "px8p_hc"

    return df_win.drop(columns=["dist_px8", "dist_px8p"])



def merge_px8_px8p(species_area_sum):

    '''It is difficult to separate px8 and px8p, so they are merged.'''
    px8_area, px8p_area = 0, 0
    if ("px8" in species_area_sum['area_sum'].keys()):
        px8_area = species_area_sum['area_sum']['px8']
    if ("px8p" in species_area_sum['area_sum'].keys()):
        px8p_area = species_area_sum['area_sum']['px8p']
    species_area_sum['area_sum']['px8ANDpx8p'] = px8_area + px8p_area
    species_area_sum['area_sum_normalized']['px8ANDpx8p'] = px8_area + px8p_area

    return species_area_sum


def parse_bda_by_ha_doublet(
    df,
    ppm_window=(6.5, 6.8),
    target_center=6.67,
    area_tol=0.20,
    ppm_span_min=0.01,
    ppm_span_max=0.10,
):
    """
    Identify BDA by its Ha doublet (~6.67 ppm, d, J~16 Hz).

    Rules
    -----
    1) Slice peaks in ppm_window
    2) Bruteforce choose 2 peaks
    3) A valid doublet satisfies:
         - ppm distance in [ppm_span_min, ppm_span_max]
         - areas within ±area_tol
    4) If multiple valid doublets:
         - choose the one whose center is closest to target_center
    5) Assign BOTH peaks as 'bda_ha'

    Returns
    -------
    df_win : DataFrame
        Peaks in window with column 'assigned_species'
        in {'bda_ha', 'ignored'}
    """

    # -------------------------
    # slice window
    # -------------------------
    df_win = df[
        df["center_ppm"].between(*ppm_window)
    ].copy()

    if len(df_win) < 2:
        return df_win

    df_win["assigned_species"] = "ignored"

    best_pair = None
    best_center_diff = float("inf")

    rows = list(df_win.iterrows())

    # -------------------------
    # brute-force doublet search
    # -------------------------
    for (i1, r1), (i2, r2) in itertools.combinations(rows, 2):

        # ppm span
        d_ppm = abs(r1["center_ppm"] - r2["center_ppm"])
        if not (ppm_span_min <= d_ppm <= ppm_span_max):
            continue

        # area similarity
        a1, a2 = r1["area"], r2["area"]
        if a1 <= 0 or a2 <= 0:
            continue

        area_diff = abs(a1 - a2) / ((a1 + a2) / 2)
        if area_diff > area_tol:
            continue

        # center closeness
        center = 0.5 * (r1["center_ppm"] + r2["center_ppm"])
        center_diff = abs(center - target_center)

        if center_diff < best_center_diff:
            best_center_diff = center_diff
            best_pair = (i1, i2)

    # -------------------------
    # assign
    # -------------------------
    if best_pair is not None:
        df_win.loc[list(best_pair), "assigned_species"] = "bda_ha"

    return df_win



def plot_peak_parser_debug(
    df,
    df_win,
    ppm_window,
    title_prefix="",
    assignment_labels=None,
):
    if assignment_labels is None:
        assignment_labels = []

    # ---------- robustness ----------
    if "assigned_species" not in df_win.columns:
        df_win = df_win.copy()
        df_win["assigned_species"] = "ignored"

    IGNORED_COLOR = "tab:gray"
    COLOR_CYCLE = [
        "tab:blue", "tab:orange", "tab:green",
        "tab:red", "tab:purple", "tab:brown", "tab:pink"
    ]

    x_dense = np.linspace(ppm_window[0], ppm_window[1], 2000)

    # -------------------------
    # original slice
    # -------------------------
    df_slice = df[
        (df["center_ppm"] >= ppm_window[0]) &
        (df["center_ppm"] <= ppm_window[1])
    ]

    fig, axes = plt.subplots(
        2, 1,
        figsize=(9, 5),
        sharex=True,
        gridspec_kw={"height_ratios": [1, 1.2]}
    )

    # =========================
    # Top: original peaks
    # =========================
    ax0 = axes[0]

    for _, r in df_slice.iterrows():
        y = pseudo_voigt(
            x_dense,
            A=r["param_A"],
            x0=r["param_x0"],
            gamma=r["param_gamma"],
            eta=r["param_eta"]
        )
        ax0.plot(x_dense, y, color="black", alpha=0.6)

    ax0.set_title(
        f"{title_prefix} | Original\n"
        + df.loc[0, "file_path"][-60:]
    )
    ax0.set_ylabel("intensity (fit)")
    ax0.grid(True, linestyle="--", alpha=0.5)

    # =========================
    # Bottom: parser result
    # =========================
    ax1 = axes[1]

    # ---- dynamic color assignment ----
    assigned_unique = [
        lab for lab in df_win["assigned_species"].unique()
        if lab != "ignored"
    ]

    color_map = {
        lab: COLOR_CYCLE[i % len(COLOR_CYCLE)]
        for i, lab in enumerate(assigned_unique)
    }

    # ---- annotate insufficient assignment ----
    if df_win.empty or (
        assignment_labels and
        not any(df_win["assigned_species"].isin(assignment_labels))
    ):
        ax1.text(
            0.5, 0.5,
            f"No valid assignment\n(n={len(df_win)})",
            ha="center",
            va="center",
            transform=ax1.transAxes,
            fontsize=10,
            color="red"
        )

    for _, r in df_win.iterrows():
        y = pseudo_voigt(
            x_dense,
            A=r["param_A"],
            x0=r["param_x0"],
            gamma=r["param_gamma"],
            eta=r["param_eta"]
        )

        label = r["assigned_species"]

        color = (
            IGNORED_COLOR
            if label == "ignored"
            else color_map[label]
        )

        ax1.plot(
            x_dense,
            y,
            color=color,
            linewidth=2 if label != "ignored" else 1,
            alpha=0.9 if label != "ignored" else 0.4,
            label=label
        )

    ax1.set_title(f"{title_prefix} | Parser assignment")
    ax1.set_ylabel("intensity (fit)")
    ax1.grid(True, linestyle="--", alpha=0.5)

    # deduplicate legend
    handles, labels = ax1.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax1.legend(by_label.values(), by_label.keys())

    # NMR-style x-axis
    ax1.invert_xaxis()
    ax1.set_xlabel("ppm")

    plt.tight_layout()
    plt.show()

def plot_peak_parser_debug_with_full_spectrum(
    df,
    df_win,
    ppm_window,
    title_prefix="",
    assignment_labels=None,
    full_margin=0.2,
):
    if assignment_labels is None:
        assignment_labels = []

    # ---------- robustness ----------
    if "assigned_species" not in df_win.columns:
        df_win = df_win.copy()
        df_win["assigned_species"] = "ignored"

    IGNORED_COLOR = "tab:gray"
    COLOR_CYCLE = [
        "tab:blue", "tab:orange", "tab:green",
        "tab:red", "tab:purple", "tab:brown", "tab:pink"
    ]

    # ---------- x ranges ----------
    x_win = np.linspace(ppm_window[0], ppm_window[1], 3000)

    x_full_min = df["center_ppm"].min() - full_margin
    x_full_max = df["center_ppm"].max() + full_margin
    x_full = np.linspace(x_full_min, x_full_max, 12000)

    # ---------- slices ----------
    df_slice = df[
        (df["center_ppm"] >= ppm_window[0]) &
        (df["center_ppm"] <= ppm_window[1])
    ]

    # =========================
    # layout: 2 rows × 2 cols
    # =========================
    fig, axes = plt.subplots(
        2, 2,
        figsize=(15, 6),
        gridspec_kw={"height_ratios": [1, 1.2], "width_ratios": [1, 1.3]}
    )

    # =========================
    # (0,0) Original slice
    # =========================
    ax00 = axes[0, 0]
    for _, r in df_slice.iterrows():
        y = pseudo_voigt(
            x_win, r["param_A"], r["param_x0"],
            r["param_gamma"], r["param_eta"]
        )
        ax00.plot(x_win, y, color="black", alpha=0.6)

    ax00.set_title(
        f"{title_prefix} | Original slice\n"
        + df["file_path"].iloc[0][-60:]
    )
    ax00.set_ylabel("intensity")
    ax00.grid(True, linestyle="--", alpha=0.4)

    # =========================
    # (1,0) Parser assignment
    # =========================
    ax10 = axes[1, 0]

    assigned_unique = [
        lab for lab in df_win["assigned_species"].unique()
        if lab != "ignored"
    ]
    color_map = {
        lab: COLOR_CYCLE[i % len(COLOR_CYCLE)]
        for i, lab in enumerate(assigned_unique)
    }

    for _, r in df_win.iterrows():
        y = pseudo_voigt(
            x_win, r["param_A"], r["param_x0"],
            r["param_gamma"], r["param_eta"]
        )
        label = r["assigned_species"]
        color = IGNORED_COLOR if label == "ignored" else color_map[label]

        ax10.plot(
            x_win, y,
            lw=2 if label != "ignored" else 1,
            alpha=0.9 if label != "ignored" else 0.4,
            color=color,
            label=label
        )

    ax10.set_title("Parser assignment (window)")
    ax10.set_ylabel("intensity")
    ax10.grid(True, linestyle="--", alpha=0.4)

    h, l = ax10.get_legend_handles_labels()
    ax10.legend(dict(zip(l, h)).values(), dict(zip(l, h)).keys())

    # =========================
    # (0,1) Full reconstructed spectrum
    # =========================
    ax01 = axes[0, 1]

    y_full = np.zeros_like(x_full)
    for _, r in df.iterrows():
        y_full += pseudo_voigt(
            x_full, r["param_A"], r["param_x0"],
            r["param_gamma"], r["param_eta"]
        )

    ax01.plot(x_full, y_full, color="black", lw=1.5)
    ax01.set_title("Full reconstructed spectrum (all peaks)")
    ax01.set_ylabel("intensity")
    ax01.grid(True, linestyle="--", alpha=0.4)

    # =========================
    # (1,1) Full spectrum + window highlight
    # =========================
    ax11 = axes[1, 1]
    ax11.plot(x_full, y_full, color="black", lw=1.2)

    ax11.axvspan(
        ppm_window[0], ppm_window[1],
        color="tab:blue", alpha=0.15,
        label="parser window"
    )

    ax11.set_title("Full spectrum (window highlighted)")
    ax11.legend()
    ax11.grid(True, linestyle="--", alpha=0.4)

    # ---------- NMR axis ----------
    for ax in axes.flatten():
        ax.invert_xaxis()
        ax.set_xlabel("ppm")

    plt.tight_layout()

    plt.show()


def build_df_win_from_ha_pairs(
    df,
    ha_pairs,
    ha_window=(6.85, 7.05),
    label="px7_ha",
):
    """
    Build df_win for plotting Ha doublets using existing debug plot function.
    """

    # 1) slice Ha window
    df_win = df[df["center_ppm"].between(*ha_window)].copy()

    if df_win.empty:
        return df_win

    # 2) init
    df_win["assigned_species"] = "ignored"

    # 3) mark selected doublet peaks
    for pair in ha_pairs:
        df_win.loc[list(pair), "assigned_species"] = label

    return df_win



def remove_assigned_peaks_by_index(df_peaks, df_assigned, assigned_labels):
    """
    Remove peaks from df_peaks using row index (robust).
    df_assigned must keep original df_peaks indices (your parsers do).
    """
    if df_assigned is None or df_assigned.empty:
        return df_peaks.copy()

    idx_drop = df_assigned.index[df_assigned["assigned_species"].isin(assigned_labels)]
    return df_peaks.drop(index=idx_drop, errors="ignore").copy()


def merge_assignment_into_master(
    df_master: pd.DataFrame,
    df_win: pd.DataFrame,
    label_col="assigned_species",
):
    """
    Merge assignments from df_win into df_master by index.

    Rules:
      - Only rows with assigned_species != 'ignored' are merged
      - Assignment is written by index
      - Existing values in df_master are overwritten
    """

    if label_col not in df_win.columns:
        return df_master

    mask = df_win[label_col] != "ignored"
    if not mask.any():
        return df_master

    df_master.loc[
        df_win.loc[mask].index,
        label_col
    ] = df_win.loc[mask, label_col]

    return df_master

def sort_df_by_px_number(
    df: pd.DataFrame,
    col="assigned_species",
):
    """
    Sort dataframe by px_N number extracted from assigned_species.

    Examples:
      px1, px1_prime   -> 1
      px2_hc, px2_hcp  -> 2
      px8_prime        -> 8
      ignored / NaN    -> inf (sorted last)
    """

    def extract_px_num(val):
        if not isinstance(val, str):
            return np.inf

        m = re.match(r"px(\d+)", val)
        if m:
            return int(m.group(1))
        return np.inf

    df = df.copy()
    df["_px_order"] = df[col].apply(extract_px_num)

    df = df.sort_values(
        by=["_px_order", col],
        ascending=[True, True]
    )

    return df.drop(columns="_px_order")


def merge_species_with_normalization(
    species_area_sum,
    new_name,
    old_names,
    norm_divisor=1,
):
    """
    Merge multiple species into one.

    area_sum:
        - direct sum

    area_sum_normalized:
        - (direct sum) / norm_divisor
    """

    # ---------- area_sum ----------
    total_area = 0.0
    for old in old_names:
        if old in species_area_sum["area_sum"]:
            total_area += species_area_sum["area_sum"].pop(old)

    if total_area > 0:
        species_area_sum["area_sum"][new_name] = total_area

    # ---------- area_sum_normalized ----------
    total_norm = 0.0
    for old in old_names:
        if old in species_area_sum["area_sum_normalized"]:
            total_norm += species_area_sum["area_sum_normalized"].pop(old)

    if total_norm > 0:
        species_area_sum["area_sum_normalized"][new_name] = total_norm / norm_divisor

    return species_area_sum


def reorder_intg_and_conc_columns(df):
    """
    Reorder DataFrame columns so that:
      1) base columns come first
      2) all intg_norm_* columns come next (sorted by px number)
      3) all conc_* columns come last (sorted by px number)

    Special rule:
      - bda is always placed before px species
    """

    cols = list(df.columns)

    # ------------------------------
    # 1. base columns
    # ------------------------------
    base_cols = [
        c for c in cols
        if not (c.startswith("intg_norm_") or c.startswith("conc_"))
    ]

    # ------------------------------
    # 2. collect species names
    # ------------------------------
    species = set()
    for c in cols:
        if c.startswith("intg_norm_"):
            species.add(c.replace("intg_norm_", ""))
        elif c.startswith("conc_"):
            species.add(c.replace("conc_", ""))

    # ------------------------------
    # 3. sorting rule for px species
    # ------------------------------
    def px_key(s):
        if s == "bda":
            return (-1, "")     # always first
        m = re.match(r"px(\d+)(p?)", s)
        if m:
            return (int(m.group(1)), m.group(2))
        return (999, s)

    species_sorted = sorted(species, key=px_key)

    # ------------------------------
    # 4. build ordered column lists
    # ------------------------------
    intg_cols = [
        f"intg_norm_{s}"
        for s in species_sorted
        if f"intg_norm_{s}" in cols
    ]

    conc_cols = [
        f"conc_{s}"
        for s in species_sorted
        if f"conc_{s}" in cols
    ]

    # ------------------------------
    # 5. reorder DataFrame
    # ------------------------------
    return df[base_cols + intg_cols + conc_cols]


if __name__ == "__main__":

    run_folders = \
        [
        r'D:\Dropbox\brucelee\data\DPE_bromination\_BDA_Benzylideneacetone\2025-12-12-run01_BDA_2nd\Results_2025-12-12-run01_400MHz',
        r'D:\Dropbox\brucelee\data\DPE_bromination\_BDA_Benzylideneacetone\2025-12-12-run02_BDA_2nd\Results_2025-12-12-run02_400MHz',
        r'D:\Dropbox\brucelee\data\DPE_bromination\_BDA_Benzylideneacetone\2025-12-12-run01_BDA_2nd\Results_2025-12-12-run01_long_400MHz',
        r'D:\Dropbox\brucelee\data\DPE_bromination\_BDA_Benzylideneacetone\2025-12-12-run02_BDA_2nd\Results_2025-12-12-run02_long_48h_400MHz'
        ]

    json_list = get_all_result_json(run_folders)

    idx_to_proceed = 0
    # string_to_proceed = "12-12-run01-7"
    # idx_to_proceed = next(i for i, s in enumerate(json_list) if string_to_proceed in s)

    all_species_name = []

    df_result_reassigned_short = pd.DataFrame()
    df_result_reassigned_long = pd.DataFrame()


    for idx, fit_json in enumerate(json_list):

        folder = os.path.dirname(fit_json)

        if idx < idx_to_proceed:
            continue

        with open(fit_json) as f:
            fit_result_dict = json.load(f)

        raw_peaks = parse_raw_peaks(fit_result_dict)
        df_peaks = pd.DataFrame(raw_peaks)
        df_peaks["file_path"] = fit_json
        df_peaks.rename(columns={"product": "product_by_Louis"}, inplace=True)

        print(f'fit_json: {fit_json}')

        df_master = df_peaks.copy()
        df_master["assigned_species"] = "ignored"

        do_show_plot = False

        # ## work on px1 and px1p
        px1_px1p_window = (4.85, 5.05)
        df_win1 = parse_px1_px1p(df_peaks, ppm_window=px1_px1p_window)
        df_master = merge_assignment_into_master(df_master, df_win1)

        if do_show_plot:
            plot_peak_parser_debug_with_full_spectrum(
                df_peaks,
                df_win1,
                ppm_window=px1_px1p_window,
                title_prefix="PX1",
                assignment_labels=["px1_ha", "px1p_ha"],
                )

        ## work on px5
        df_px5 = parse_px5_px5p_by_hc(df_peaks)
        df_master = merge_assignment_into_master(df_master, df_px5)

        if do_show_plot:
            plot_peak_parser_debug_with_full_spectrum(
                df_peaks,
                df_px5,
                ppm_window=(4.45, 4.85),
                title_prefix="PX5 / PX5′ (Hc-based)",
                assignment_labels=["px5", "px5p"],
                )

        # # work on px2
        df_win2 = parse_px2_hc_hcp_bruteforce(df_peaks)
        df_master = merge_assignment_into_master(df_master, df_win2)

        if do_show_plot:
            plot_peak_parser_debug_with_full_spectrum(
                                                df_peaks,
                                                df_win2,
                                                ppm_window=(4.225, 4.475),
                                                title_prefix="PX2 (Hc / Hc′)",
                                                assignment_labels=["px2_hc", "px2_hcp"],
                                                )

        df_peaks_no_px2 = remove_assigned_peaks_by_index(df_peaks,df_win2,["px2_hc", "px2_hcp"])

        # work on px7 and px7p. Remove PX2 quad first
        df_px7 = parse_px7_px7p_block(df_peaks_no_px2)
        df_master = merge_assignment_into_master(df_master, df_px7)

        if do_show_plot:
            plot_peak_parser_debug_with_full_spectrum(
            df=df_peaks_no_px2,  # full peak table (PX2 already removed)
            df_win=df_px7,  # window + px7_Ha / px7_Hc / px7p_Hc
            ppm_window=(4.0, 7.05),
            title_prefix="PX7 / PX7′ debug"
            )

        # ## work on px3
        df_px3 = parse_px3(df_peaks)
        df_master = merge_assignment_into_master(df_master, df_px3)

        if do_show_plot:
            plot_peak_parser_debug_with_full_spectrum(
            df_peaks,
            df_px3,
            ppm_window=(6.35, 6.50),
            title_prefix="PX3",
            assignment_labels=["px3_hc"],
            )

        # ## work on px4
        df_px4 = parse_px4(df_peaks)
        df_master = merge_assignment_into_master(df_master, df_px4)

        if do_show_plot:
            plot_peak_parser_debug_with_full_spectrum(
            df_peaks,
            df_px4,
            ppm_window=(7.95, 8.05),
            title_prefix="PX4",
            assignment_labels=["px4_hb"],
            )

        ## work on px8 and px8p
        window_for_px8_and_px8p = (5.95, 6.2)
        df_px8 = parse_px8_px8p_by_hc(df_peaks, ppm_window=window_for_px8_and_px8p)
        df_master = merge_assignment_into_master(df_master, df_px8)

        if do_show_plot:
            plot_peak_parser_debug_with_full_spectrum(
            df_peaks,
            df_px8,
            ppm_window=window_for_px8_and_px8p,
            title_prefix="PX8 / PX8′ (Hc)",
            assignment_labels=["px8", "px8p"],
            )

        ## work on the starting material BDA
        df_bda = parse_bda_by_ha_doublet(df_peaks)
        df_master = merge_assignment_into_master(df_master, df_bda)

        if do_show_plot:
            plot_peak_parser_debug_with_full_spectrum(
                df_peaks,
                df_bda,
                ppm_window=(6.5, 6.8),
                title_prefix="BDA (Ha doublet)",
                assignment_labels=["bda_ha"],
                )

        # work on px6
        # df_px6 = parse_px6(df_peaks, strict=False, verbose=True)
        # df_master = merge_assignment_into_master(df_master, df_px6)

        ### THE FOLLOWING IS POST PROCESSING####

        df_master = df_master[df_master['assigned_species'] != 'ignored']
        df_master = sort_df_by_px_number(df_master)
        json_folder_path = folder
        df_master.to_csv(json_folder_path + r'/re_assignment.csv', index=False)
        assigned_ls = df_master['assigned_species'].tolist()
        print(assigned_ls)

        all_species_name.extend(assigned_ls)

        species_area_sum = {
            "area_sum": {},
            "area_sum_normalized": {},
        }

        ## cal the sum area of each species and normalized the sum by proton count
        for species, df_grp in df_master.groupby("assigned_species"):
            if species not in PROTON_COUNT:
                warnings.warn(f"No proton count defined for {species}, skipping")
                continue

            area_sum = df_grp["area"].sum()
            area_norm = area_sum / PROTON_COUNT[species]

            species_area_sum["area_sum"][species] = area_sum
            species_area_sum["area_sum_normalized"][species] = area_norm


        ## merge px2_hc and px2_hcp
        species_area_sum = merge_species_with_normalization(
                                        species_area_sum,
                                        new_name="px2",
                                        old_names=["px2_hc", "px2_hcp"],
                                        norm_divisor=1,  # sum conc of px8 and px8p
                                    )

        ## Remove proton name, only keep px1, px2...
        species_area_sum = {
            k: {s.split("_")[0]: v for s, v in d.items()}
            for k, d in species_area_sum.items()
        }

        ## NEW: merge px8 and px8p AFTER parsing
        species_area_sum = merge_px8_px8p(species_area_sum)
        print(f'species_area_sum: {species_area_sum}')

        with open(json_folder_path + r"\fitting_result_with_conc_re-assigned.json", "w", encoding="utf-8") as f:
            json.dump(species_area_sum, f, indent=2, default=float)

        ## get reaction info from json
        reaction_info_json = folder + r'\\reaction_info.json'
        assert os.path.isfile(reaction_info_json), f'Result folder does not exist in {folder}'
        with open(reaction_info_json) as f:
            reaction_info_here = json.load(f)
        # reassemble the dict for fitting_result_all_reassigned
        fitting_result_all_reassigned = reaction_info_here

        fitting_result_all_reassigned.update({
            f"intg_norm_{k}": v
            for k, v in species_area_sum["area_sum_normalized"].items()
        })
        # delete unnecessary items.
        for k in ['status', 'plate_barcodes_for_dilution',
                  'full_status', 'slot_id', 'plate_barcode', 'container_id',]:
            fitting_result_all_reassigned.pop(k, None)

        rename_map = {'conc_AA': '[TBABr]0', 'conc_BB': '[Br2]0', 'conc_CC': '[BDA]0'}
        fitting_result_all_reassigned = {rename_map.get(k, k): v for k, v in fitting_result_all_reassigned.items()}

        ## assign zero values to integration. if characteristic peak for a cmpd is not found, its ingt is considered to be zero.
        for cmpd in CMPD_LS:
            cmpd_intg_name = f'intg_norm_{cmpd}'
            if cmpd_intg_name not in fitting_result_all_reassigned.keys():
                fitting_result_all_reassigned[cmpd_intg_name] = 0

        ## calculate conc for all products
        init_conc_of_TBABr = fitting_result_all_reassigned['[TBABr]0']
        intg_norm_ls = [key for key in fitting_result_all_reassigned.keys() if 'intg_norm' in key]
        for intg in intg_norm_ls:
            cmpd_name = intg.split('_')[-1]
            # RBF model does not work well at lower intg values.
            # fitting_result_all_reassigned[f'conc_{cmpd_name}'] = (
            #     conc_interpolation_2D_BDA.estimate_conc_by_rbf_model(
            #                                    additive_conc_here=init_conc_of_TBABr,
            #                                    integral_value_normalized=fitting_result_all_reassigned[intg],
            #                                    rbf_model=conc_interpolation_2D_BDA.rbf_model))

            fitting_result_all_reassigned[f'conc_{cmpd_name}'] = \
                conc_interpolation_2D_BDA.predict_linear(integral_value_normalized=fitting_result_all_reassigned[intg])

        ## calculate yield
        for cmpd, br_count in BR_COUNT_IN_A_CMPD.items():

            if f'conc_{cmpd}' in fitting_result_all_reassigned.keys():
                limiting_reagent_conc = min(fitting_result_all_reassigned['[BDA]0'],
                                            fitting_result_all_reassigned['[Br2]0'] / br_count)

                fitting_result_all_reassigned[f'yield_{cmpd}'] = \
                        fitting_result_all_reassigned[f'conc_{cmpd}'] / limiting_reagent_conc * 100

            # save fitting_result_all_reassigned
            with open("fitting_result_all_reassigned.json", "w", encoding="utf-8") as f:
                json.dump(fitting_result_all_reassigned, f, indent=2, ensure_ascii=False, default=float)

        ## save re-assigned results to two separated dataframe
        new_row = pd.DataFrame([fitting_result_all_reassigned])
        # ✅ remove 'Unnamed' cols
        new_row = new_row.loc[:, ~new_row.columns.str.startswith("Unnamed")]

        if 'long' in fit_json:
            df_result_reassigned_long = pd.concat(
                [df_result_reassigned_long, new_row],
                ignore_index=True
            )
        else:
            df_result_reassigned_short = pd.concat(
                [df_result_reassigned_short, new_row],
                ignore_index=True
            )

        # conc_interpolation_2D_BDA.plot_linear_origin_fit()

        print(fitting_result_all_reassigned)

        # assert 0

    df_result_reassigned_short = reorder_intg_and_conc_columns(df_result_reassigned_short)
    df_result_reassigned_long = reorder_intg_and_conc_columns(df_result_reassigned_long)
    campaign_folder = r'D:\Dropbox\brucelee\data\DPE_bromination\_BDA_Benzylideneacetone'
    df_result_reassigned_short.to_csv(campaign_folder + r'\result_all_short_reassigned.csv', index=False)
    df_result_reassigned_long.to_csv(campaign_folder + r'\result_all_long_reassigned.csv', index=False)


    print(1)
