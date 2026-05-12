"""
Read result_all.csv from each BDA revise run folder and produce interactive yield bar charts.

Outputs per single-condition run:
    <run_folder>/Results/yields_plot.html

Outputs for the mixed-condition run (revise_Q1_Q4_Q7_Q2p), one file per condition group:
    <run_folder>/Results/yields_Q1.html
    <run_folder>/Results/yields_Q4.html
    <run_folder>/Results/yields_Q2p.html
    <run_folder>/Results/yields_Q7.html

PRE-REQUISITE:
    Run conc_interpolation_2D_BDA.py (and peak_assignment_for_BDA.py beforehand for
    re-assigned results) to generate result_all.csv in each Results folder.

Yankai Jia 2026.05.01
"""

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

import config

# ---------------------------------------------------------------------------
# Build column → display name mapping from existing config constants
# 'yield_Product_PX7_prime' → "Q2'"
# ---------------------------------------------------------------------------
YIELD_COL_TO_DISPLAY = {
    f'yield_{config.REASSIGNED_SHORT_TO_COMPOUND[short]}': display
    for short, display in config.OLD_NAME_VS_NEW_NAME_DICT.items()
}

RUN_DISPLAY = {
    'revise_Q1_24h':        'Q1 (24 h)',
    'revise_Q2p_48h':       "Q2' (48 h)",
    'revise_Q4_24h':        'Q4 (24 h)',
    'revise_Q1_Q4_Q7_Q2p':  'Mixed conditions (Q1 / Q4 / Q7 / Q2)',
    'revise_Q7_24h':        'Q7 (24 h)',
}

RUN_KEYS = [
    'revise_Q1_24h',
    'revise_Q2p_48h',
    'revise_Q4_24h',
    'revise_Q1_Q4_Q7_Q2p',
    'revise_Q7_24h',
]

MIXED_RUN_KEY = 'revise_Q1_Q4_Q7_Q2p'


def label_condition(row):
    """Assign a Q-label to a row in the mixed-condition run based on [TBABr]0 and [Br2]0."""
    tbabr = row.get('[TBABr]0', 0) or 0
    br2   = row.get('[Br2]0', 0) or 0
    if tbabr == 0 and br2 <= 100:
        return 'Q1'
    if tbabr == 0 and br2 > 100:
        return 'Q4'
    if tbabr > 0 and br2 <= 100:
        return 'Q2p'
    if tbabr > 0 and br2 > 100:
        return 'Q7'
    return 'unknown'


def load_yields(csv_path):
    """
    Load result_all.csv, extract yield columns, convert fractions → %, and rename to display names.

    Returns
    -------
    pd.DataFrame
        Index matches the original CSV rows. Columns are display names (e.g. 'anti-Q1', "Q2'").
    """
    raw = pd.read_csv(csv_path, index_col=0)
    keep = {col: YIELD_COL_TO_DISPLAY[col]
            for col in raw.columns
            if col in YIELD_COL_TO_DISPLAY}
    df = raw[list(keep.keys())].rename(columns=keep)
    df = df.apply(pd.to_numeric, errors='coerce') * 100  # fraction → %
    return df


def plot_yields_for_run(df, title, save_path, csv_path=None, min_mean_pct=0.1):
    """
    Bar chart of mean yield ± std for each detected compound.

    Parameters
    ----------
    df : pd.DataFrame
        Rows = spectra, columns = compound display names, values in %.
    title : str
        Plot title.
    save_path : str
        Full path to output HTML file.
    csv_path : str | None
        Source CSV path shown as subtitle on the plot for traceability.
    min_mean_pct : float
        Compounds with mean yield below this threshold are hidden.
    """
    means = df.mean()
    stds  = df.std().fillna(0)

    # Filter to detected compounds and sort by yield descending
    detected = means[means >= min_mean_pct].sort_values(ascending=False)

    if detected.empty:
        print(f'  No compounds above {min_mean_pct}% — skipping {title}')
        return

    x_labels = detected.index.tolist()
    y_means  = detected.values
    y_stds   = stds[x_labels].values

    # Build hover text showing individual spectrum values
    hover_texts = []
    for cmpd in x_labels:
        vals = df[cmpd].dropna().values
        lines = [f'<b>{cmpd}</b>', f'mean: {means[cmpd]:.1f}%', f'std:  {stds[cmpd]:.1f}%', '']
        lines += [f'spec {i+1}: {v:.1f}%' for i, v in enumerate(vals)]
        hover_texts.append('<br>'.join(lines))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x_labels,
        y=y_means,
        error_y=dict(type='data', array=y_stds, visible=True),
        text=[f'{v:.1f}%' for v in y_means],
        textposition='outside',
        hovertext=hover_texts,
        hoverinfo='text',
        marker_color='steelblue',
    ))

    full_title = title
    if csv_path:
        full_title += f'<br><span style="font-size:11px;color:grey">{csv_path}</span>'

    fig.update_layout(
        title=full_title,
        xaxis_title='Compound',
        yaxis_title='Yield (%)',
        yaxis=dict(rangemode='tozero'),
        width=800,
        height=500,
        template='simple_white',
    )

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig.write_html(save_path, include_plotlyjs='cdn', full_html=True)
    print(f'Saved: {save_path}')


if __name__ == '__main__':

    F = config.BDA_RUN_FOLDERS
    saved_htmls = []
    collected = {}   # key → data for combined PNG

    for key in RUN_KEYS:
        csv_path = os.path.join(F[key], 'Results', 'result_all.csv')
        if not os.path.isfile(csv_path):
            print(f'Skipping {key}: no result_all.csv at {csv_path}')
            continue

        df_yields = load_yields(csv_path)
        results_dir = os.path.join(F[key], 'Results')

        if key == MIXED_RUN_KEY:
            raw = pd.read_csv(csv_path, index_col=0)
            raw['_condition'] = raw.apply(label_condition, axis=1)

            # Collect mean yield per condition; find all detected compounds across all groups
            cond_means = {}
            cond_stds  = {}
            for cond, group_idx in raw.groupby('_condition').groups.items():
                cond_means[cond] = df_yields.loc[group_idx].mean()
                cond_stds[cond]  = df_yields.loc[group_idx].std().fillna(0)
            collected[key] = {'type': 'mixed', 'cond_means': cond_means, 'cond_stds': cond_stds}

            all_cmpds = sorted(
                {c for means in cond_means.values() for c in means.index if means[c] >= 0.1},
                key=lambda c: max(m[c] for m in cond_means.values() if c in m.index),
                reverse=True,
            )

            fig = go.Figure()
            for cond, means in sorted(cond_means.items()):
                stds = df_yields.loc[raw.groupby('_condition').groups[cond]].std().fillna(0)
                fig.add_trace(go.Bar(
                    name=cond,
                    x=all_cmpds,
                    y=[means.get(c, 0) for c in all_cmpds],
                    error_y=dict(type='data', array=[stds.get(c, 0) for c in all_cmpds], visible=True),
                    text=[f'{means.get(c, 0):.1f}%' for c in all_cmpds],
                    textposition='outside',
                ))

            full_title = RUN_DISPLAY[key]
            full_title += f'<br><span style="font-size:11px;color:grey">{csv_path}</span>'
            fig.update_layout(
                title=full_title,
                xaxis_title='Compound',
                yaxis_title='Yield (%)',
                yaxis=dict(rangemode='tozero'),
                barmode='group',
                width=900,
                height=520,
                template='simple_white',
            )
            save_path = os.path.join(results_dir, 'yields_plot.html')
            fig.write_html(save_path, include_plotlyjs='cdn', full_html=True)
            print(f'Saved: {save_path}')
            saved_htmls.append(save_path)
        else:
            save_path = os.path.join(results_dir, 'yields_plot.html')
            plot_yields_for_run(df_yields, title=RUN_DISPLAY[key], save_path=save_path,
                                csv_path=csv_path)
            saved_htmls.append(save_path)
            collected[key] = {
                'type':  'single',
                'means': df_yields.mean(),
                'stds':  df_yields.std().fillna(0),
            }

    print('\n--- Output HTML files ---')
    for p in saved_htmls:
        print(p)

    # -------------------------------------------------------------------------
    # Combined summary figure — all runs in one PNG
    # Layout: top row Q1 / Q2' / Q4 / Q7  (4 simple panels)
    #         bottom row: mixed run (full width, grouped bars per condition)
    # -------------------------------------------------------------------------
    COND_COLORS = {'Q1': '#1f77b4', 'Q2p': '#ff7f0e', 'Q4': '#2ca02c', 'Q7': '#d62728'}
    SINGLE_KEYS = [k for k in RUN_KEYS if k != MIXED_RUN_KEY]
    MIN_PCT = 0.1

    fig = plt.figure(figsize=(20, 11))
    gs  = gridspec.GridSpec(2, 4, figure=fig, hspace=0.55, wspace=0.35)

    # ── top row: one panel per single-condition run ──
    for col, key in enumerate(SINGLE_KEYS):
        ax = fig.add_subplot(gs[0, col])
        if key not in collected:
            ax.set_visible(False)
            continue
        means = collected[key]['means']
        stds  = collected[key]['stds']
        detected = means[means >= MIN_PCT].sort_values(ascending=False)
        if detected.empty:
            ax.text(0.5, 0.5, 'none detected', ha='center', va='center',
                    transform=ax.transAxes, color='grey')
        else:
            xs = range(len(detected))
            ax.bar(xs, detected.values, yerr=stds[detected.index].values,
                   color='steelblue', capsize=4, alpha=0.85, width=0.6)
            ax.set_xticks(xs)
            ax.set_xticklabels(detected.index, rotation=35, ha='right', fontsize=9)
            for i, v in enumerate(detected.values):
                ax.text(i, v + stds[detected.index[i]] + 0.5, f'{v:.1f}%',
                        ha='center', va='bottom', fontsize=7.5)
        ax.set_title(RUN_DISPLAY[key], fontsize=11, fontweight='bold')
        ax.set_ylabel('Yield (%)')
        ax.set_ylim(bottom=0)
        ax.spines[['top', 'right']].set_visible(False)

    # ── bottom row: mixed run spanning all 4 columns ──
    ax_mix = fig.add_subplot(gs[1, :])
    if MIXED_RUN_KEY in collected:
        info       = collected[MIXED_RUN_KEY]
        cond_means = info['cond_means']
        cond_stds  = info['cond_stds']
        conds      = sorted(cond_means.keys())

        all_cmpds = sorted(
            {c for m in cond_means.values() for c in m.index if m[c] >= MIN_PCT},
            key=lambda c: max(m.get(c, 0) for m in cond_means.values()),
            reverse=True,
        )

        n_conds = len(conds)
        bar_w   = 0.7 / n_conds
        xs      = np.arange(len(all_cmpds))

        for i, cond in enumerate(conds):
            offsets = xs + (i - n_conds / 2 + 0.5) * bar_w
            ys   = [cond_means[cond].get(c, 0) for c in all_cmpds]
            errs = [cond_stds[cond].get(c, 0)  for c in all_cmpds]
            ax_mix.bar(offsets, ys, bar_w, yerr=errs,
                       label=cond, color=COND_COLORS.get(cond, f'C{i}'),
                       capsize=3, alpha=0.85)

        ax_mix.set_xticks(xs)
        ax_mix.set_xticklabels(all_cmpds, rotation=30, ha='right', fontsize=9)
        ax_mix.legend(fontsize=9, title='Condition')
    ax_mix.set_title(RUN_DISPLAY[MIXED_RUN_KEY], fontsize=11, fontweight='bold')
    ax_mix.set_ylabel('Yield (%)')
    ax_mix.set_ylim(bottom=0)
    ax_mix.spines[['top', 'right']].set_visible(False)

    png_path = os.path.join(
        config.DATA_ROOT, 'DPE_bromination', '_BDA_Benzylideneacetone',
        'yields_summary_all_runs.png'
    )
    os.makedirs(os.path.dirname(png_path), exist_ok=True)
    fig.savefig(png_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'\nSaved combined PNG: {png_path}')
