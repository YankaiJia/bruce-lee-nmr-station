import numpy as np
import pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, Matern, WhiteKernel, ConstantKernel as C
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from scipy.stats import norm
from sklearn.preprocessing import MinMaxScaler
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.gaussian_process.kernels import RationalQuadratic
from sklearn.model_selection import cross_val_score, KFold
import random

import matplotlib as mpl

mpl.rcParams.update({
    "font.family": "Arial",
    "font.size": 20,
    "mathtext.fontset": "custom",
    "mathtext.rm": "Arial",
    "mathtext.it": "Arial:italic",
    "mathtext.bf": "Arial:bold"
})

from mpl_toolkits.axes_grid1 import make_axes_locatable

raw_data_folder = r'D:\Dropbox\brucelee\manuscript\figures\Fig7\raw_data_for_coorelation'
df = pd.read_excel(raw_data_folder + r'\result_all_long_short_with_selectivity.xlsx')

# assign first 48 rows to 24h data, and remaining to 48h data.
df_20h = df.iloc[:48].reset_index(drop=True)
df_48h = df.iloc[48:].reset_index(drop=True)

df_delta = df_48h - df_20h

print(df_delta.columns)

including_col_ls = [
    'conc_px1',
    'conc_px1p',
    'conc_px2',
    'conc_px3',
    'conc_px4',
    'conc_px5',
    # 'conc_px5p',
    # 'conc_px6',
    'conc_px7',
    'conc_px7p',
    # 'conc_px8',
    # 'conc_px8p'
]

old_name_vs_new_name_dict = {
    'px1': 'anti-Q1',
    'px1p': 'syn-Q1',
    'px2': 'Q4',
    'px3': 'Q5',
    'px4': 'Q6',
    'px5': 'Q7',
    'px5p': "Q7'",
    'px6': 'Q8',
    'px7': 'Q2',
    'px7p': "Q2'",
    'px8': 'Q3',
    'px8p': "Q3'"
}

df_delta = df_delta[including_col_ls]

#calcultate the Perason correlation between columns from 'conc_bda' to 'conc_px8p'
correlation_matrix_concentration = df_delta.corr(method='pearson')

#remove the str conc_ from col and row names
correlation_matrix_concentration.columns = correlation_matrix_concentration.columns.str.replace('^conc_', '', regex=True)
correlation_matrix_concentration.index = correlation_matrix_concentration.index.astype(str).str.replace('^conc_', '', regex=True)

# map old px names to new display names
correlation_matrix_concentration = correlation_matrix_concentration.rename(
    index=old_name_vs_new_name_dict,
    columns=old_name_vs_new_name_dict
)

# desired plotting order (new names)
new_order = [
    'anti-Q1',
    'syn-Q1',
    'Q2',
    "Q2'",
    'Q4',
    'Q5',
    'Q6',
    'Q7'
]

# keep only labels that exist (safe guard)
new_order = [x for x in new_order if x in correlation_matrix_concentration.index]

# reorder rows and columns
correlation_matrix_concentration = correlation_matrix_concentration.loc[
    new_order, new_order
]

# heatmap text size
text_size = 20

# create figure and main axis
fig, ax = plt.subplots(figsize=(12, 10))

# create a divider for the colorbar
divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="5%", pad=0.1)

# plot the heatmap
sns.heatmap(
    correlation_matrix_concentration,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    vmin=-1,
    vmax=1,
    square=True,
    annot_kws={"size": text_size, "fontfamily": "Arial"},
    ax=ax,
    cbar_ax=cax
)
# axis tick label sizes
ax.tick_params(axis="x", labelsize=text_size)
ax.tick_params(axis="y", labelsize=text_size)

cax.tick_params(labelsize=text_size)

ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
ax.set_yticklabels(ax.get_yticklabels(), rotation=0)

# colorbar tick label size
cax.tick_params(labelsize=text_size)

def format_label(text):
    if text.startswith("anti-"):
        q = text.replace("anti-", "")
        return rf"$\it{{anti\text{{-}}}}\mathbf{{{q}}}$"
    if text.startswith("syn-"):
        q = text.replace("syn-", "")
        return rf"$\it{{syn\text{{-}}}}\mathbf{{{q}}}$"
    if text.startswith("Q"):
        return rf"$\mathbf{{{text}}}$"
    return text

# X-axis
ax.set_xticklabels([format_label(l.get_text()) for l in ax.get_xticklabels()])

# Y-axis
ax.set_yticklabels([format_label(l.get_text()) for l in ax.get_yticklabels()])

# save the plot to png
output_path = raw_data_folder + r"/correlation_heatmap.png"
fig.savefig(output_path, dpi=600, bbox_inches="tight")
print(f"saved png to : {output_path}")

plt.show()


#
# #calcultate the Perason correlation between columns from 'Yield_bda' to 'Yield_px8p'
# correlation_matrix_yield = df_delta.loc[:, 'Yield_bda':'Yield_px8p'].corr(method='pearson')
#
# #plot the correlation matrix using seaborn heatmap
# plt.figure(figsize=(12, 10))
# sns.heatmap(correlation_matrix_yield, annot=True, fmt=".2f", cmap='coolwarm', square=True)
# plt.title('Pearson Correlation Matrix of Yields (Delta 20h to 48h)', fontsize=16)
# plt.show()
#
# #calcultate the Perason correlation between columns from 'Sel_bda' to 'Sel_px8p'
# correlation_matrix_selectivity = df_delta.loc[:, 'sel_bda':'Sel_px8p'].corr(method='pearson')
#
# #plot the correlation matrix using seaborn heatmap
# plt.figure(figsize=(12, 10))
# sns.heatmap(correlation_matrix_selectivity, annot=True, fmt=".2f", cmap='coolwarm', square=True)
# plt.title('Pearson Correlation Matrix of selectivities (Delta 20h to 48h)', fontsize=16)
# plt.show()

#df_delta.to_excel('delta_20h_48h_results.xlsx', index=False)
# correlation_matrix_concentration.to_excel('correlation_matrix_concentration_delta_20h_48h.xlsx', index=True)
# correlation_matrix_yield.to_excel('correlation_matrix_yield_delta_20h_48h.xlsx', index=True)
# correlation_matrix_selectivity.to_excel('correlation_matrix_selectivity_delta_20h_48h.xlsx', index=True)

