import sys

import pandas as pd, os, glob, numpy as np, time, datetime
from scipy.signal import savgol_filter
import xml.etree.ElementTree as ET
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from labellines import labelLine, labelLines

def csv_to_df(xml_folder):
    os.chdir(xml_folder)
    csv_files = glob.glob('*.csv')
    dfs_here = []
    for csv_file in csv_files:
        df =pd.read_csv(csv_file)
        df.rename(columns={'Unnamed: 0': 'wavelength'}, inplace=True)
        df.set_index('wavelength', inplace=True)
        dfs_here.append(df)
    return dfs_here

xml_folder = 'D:\\Dropbox\\robochem\\data\\BPRF\\volume_check_20240119\\20x_twice_test\\'
dfs = csv_to_df(xml_folder)
df_20x_1 = dfs[0].iloc[40:220, 0:20]
df_20x_2 = dfs[1].iloc[40:220, 0:20]


# plot the two dfs in two subplots
fig, ((ax0, ax1), (ax2, ax3),(ax4, ax5)) = plt.subplots(3, 2, figsize=(15, 10))
ax0.plot(df_20x_1.index, df_20x_1)
ax1.plot(df_20x_2.index, df_20x_2)
# ax0.set_xlabel('Wavelength (nm)')
ax0.set_ylabel('Absorbance (AU)')
ax0.set_title('20x-twice-test-1')
ax1.set_title('20x-twice-test-2')

# filter the two dfs
df_20x_1_smooth = df_20x_1.apply(lambda x: savgol_filter(x, 21, 5) if x.dtype.kind in 'biufc' else x)
df_20x_2_smooth = df_20x_2.apply(lambda x: savgol_filter(x, 21, 5) if x.dtype.kind in 'biufc' else x)

ax2.plot(df_20x_1_smooth.index, df_20x_1_smooth.iloc[:, 0:20], label='20x-twice-test-1')
ax3.plot(df_20x_2_smooth.index, df_20x_2_smooth.iloc[:, 0:20], label='20x-twice-test-2')
ax2.set_title('20x-twice-test-1-smooth')
ax3.set_title('20x-twice-test-2-smooth')

# plot abs at 280nm
df_20x_1_smooth_280nm = df_20x_1_smooth.loc[280]
df_20x_2_smooth_280nm = df_20x_2_smooth.loc[280]
ax4.plot(df_20x_1_smooth_280nm.index, df_20x_1_smooth_280nm, label='20x-twice-test-1', marker='o', linestyle='None')
ax5.plot(df_20x_2_smooth_280nm.index, df_20x_2_smooth_280nm, label='20x-twice-test-2', marker='>', linestyle='None')
# plot a horizontal line
ax4.axhline(y=1.047, color='r', linestyle='--')
ax5.axhline(y=1.083, color='r', linestyle='--')
# set title
ax4.set_title('20x-twice-test-1-smooth-280nm')
ax5.set_title('20x-twice-test-2-smooth-280nm')
# set y limits
ax4.set_ylim(0.95, 1.3)
ax5.set_ylim(0.95, 1.3)

# calulate the mean, std and RSD of the two dfs
df_20x_1_smooth_mean = df_20x_1_smooth_280nm.mean()
df_20x_1_smooth_std = df_20x_1_smooth_280nm.std()
df_20x_2_smooth_mean = df_20x_2_smooth_280nm.mean()
df_20x_2_smooth_std = df_20x_2_smooth_280nm.std()
print(f'20x-twice-test-1 mean: {round(df_20x_1_smooth_mean,5)}, std: {round(df_20x_1_smooth_std,5)}, RSD: {round(df_20x_1_smooth_std/df_20x_1_smooth_mean*100,5)}%')
print(f'20x-twice-test-2 mean: {round(df_20x_2_smooth_mean,5)}, std: {round(df_20x_2_smooth_std,5)}, RSD: {round(df_20x_2_smooth_std/df_20x_2_smooth_mean*100,5)}%')

n=3
summary_title1 = (f'20x-plate1 m: {round(df_20x_1_smooth_mean,n)}, '
                 f'std: {round(df_20x_1_smooth_std,n)}, '
                 f'RSD: {round(df_20x_1_smooth_std/df_20x_1_smooth_mean*100,n)}%')
summary_title2 = (f'20x-plate2 m: {round(df_20x_2_smooth_mean,n)}, '
                  f'std: {round(df_20x_2_smooth_std,n)}, '
                  f'RSD: {round(df_20x_2_smooth_std/df_20x_2_smooth_mean*100,n)}%')
plt.suptitle(f'{summary_title1}\n{summary_title2}', fontsize=16,fontweight='bold')
plt.show()

# save the plot
plt.savefig(xml_folder+'20x_twice_test.png')




