import sys

import pandas as pd, os, glob, numpy as np, time, datetime
from scipy.signal import savgol_filter
import xml.etree.ElementTree as ET
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from labellines import labelLine, labelLines

# import df from a csv

xml_folder = 'D:\\Dropbox\\robochem\\data\\BPRF\\volume_check_20240119\\check_nanodrop_on_one_sample\\'
os.chdir(xml_folder)
csv_files = glob.glob('*.csv')

df = pd.read_csv(csv_files[0])
df.rename(columns={'Unnamed: 0': 'wavelength'}, inplace=True)
df.set_index('wavelength', inplace=True)

df_with_heat = df.iloc[50:220, 0:20]
df_without_heat = df.iloc[50:220, 20:].drop(columns='38', axis=1)

# plot the two dfs in two subplots
fig, ((ax0, ax1), (ax2, ax3),(ax4, ax5)) = plt.subplots(3, 2, figsize=(15, 10))
ax0.plot(df_with_heat.index, df_with_heat.iloc[:, 0:20])
ax1.plot(df_without_heat.index, df_without_heat.iloc[:, 0:20])
# ax0.set_xlabel('Wavelength (nm)')
ax0.set_ylabel('Absorbance (AU)')
ax0.set_title('one-sample-repeatibility-w/-heat')
ax1.set_title('one-sample-repeatibility-wo-heat')

# filter the two dfs
df_with_heat_smooth = df_with_heat.apply(lambda x: savgol_filter(x, 21, 5) if x.dtype.kind in 'biufc' else x)
df_without_heat_smooth = df_without_heat.apply(lambda x: savgol_filter(x, 21, 5) if x.dtype.kind in 'biufc' else x)

ax2.plot(df_with_heat_smooth.index, df_with_heat_smooth.iloc[:, 0:20], label='with heat')
ax3.plot(df_without_heat_smooth.index, df_without_heat_smooth.iloc[:, 0:20], label='without heat')
ax2.set_title('one-sample-repeatibility-w/-heat-smooth')
ax3.set_title('one-sample-repeatibility-w/-heat-smooth')


df_with_heat_smooth_280nm = df_with_heat_smooth.loc[280]
df_without_heat_smooth_280nm = df_without_heat_smooth.loc[280]
ax4.plot(df_with_heat_smooth_280nm.index, df_with_heat_smooth_280nm, label='with heat', marker='o', linestyle='None')
ax5.plot(df_without_heat_smooth_280nm.index, df_without_heat_smooth_280nm, label='without heat', marker='>', linestyle='None')
# plot a horizontal line at y = 0.55
ax4.axhline(y=0.55, color='r', linestyle='--')
ax5.axhline(y=0.55, color='r', linestyle='--')
# set title
ax4.set_title('one-sample-repeatibility-w/-heat-smooth-280nm')
ax5.set_title('one-sample-repeatibility-wo-heat-smooth-280nm')

# calulate the mean and std of the two dfs
df_with_heat_mean = df_with_heat_smooth_280nm.mean()
df_with_heat_std = df_with_heat_smooth_280nm.std()
df_without_heat_mean = df_without_heat_smooth_280nm.mean()
df_without_heat_std = df_without_heat_smooth_280nm.std()
print(f'with heat mean: {round(df_with_heat_mean,5)}, std: {round(df_with_heat_std,5)}, RSD: {round(df_with_heat_std/df_with_heat_mean*100,5)}%')
print(f'without heat mean: {round(df_without_heat_mean,5)}, std: {round(df_without_heat_std,5)}, RSD: {round(df_without_heat_std/df_without_heat_mean*100,5)}%')

n=3
summary_title1 = (f'w/ heat m: {round(df_with_heat_mean,n)}, '
                 f'std: {round(df_with_heat_std,n)}, '
                 f'RSD: {round(df_with_heat_std/df_with_heat_mean*100,n)}%')
summary_title2 = (f'wo heat m: {round(df_without_heat_mean,n+1)}, '
                  f'std: {round(df_without_heat_std,n)}, '
                  f'RSD: {round(df_without_heat_std/df_without_heat_mean*100,n)}%')

fig.suptitle(summary_title1 + '\n' + summary_title2, fontsize=15,fontweight='bold')
plt.show()
plt.savefig(xml_folder+'one-sample-repeatibility.png')
