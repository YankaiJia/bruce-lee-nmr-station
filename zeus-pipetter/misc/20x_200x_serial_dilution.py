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
    return dfs_here, csv_files

def manual_pipetting(dfs):
    df_manual = dfs[0]
    df_manual_280nm = df_manual.loc[280, :]

    values_manual = {'200x': [], '20x': [], '15x': [], '150x': []}
    for row in df_manual_280nm.index:
        if '200x' in row:
            values_manual['200x'].append(df_manual_280nm[row])
        elif '20x' in row:
            values_manual['20x'].append(df_manual_280nm[row])
        elif '15x' in row:
            values_manual['15x'].append(df_manual_280nm[row])
        elif '150x' in row:
            values_manual['150x'].append(df_manual_280nm[row])
    ratio_manual_200_20 = np.mean(values_manual['20x']) / np.mean(values_manual['200x'])
    ratio_manual_150_15 = np.mean(values_manual['15x']) / np.mean(values_manual['150x'])
    print(f'ratio_manual_200_20:{ratio_manual_200_20}, ratio_manual_150_15:{ratio_manual_150_15}')
    # print stds
    print(
        f'std_200x:{np.std(values_manual["200x"]):.2f}, std_20x:{np.std(values_manual["20x"]):.2f}, std_150x:{np.std(values_manual["150x"]):.2f}, std_15x:{np.std(values_manual["15x"]):.2f}')
    # print CVs
    print(
        f'CV_200x:{np.std(values_manual["200x"]) / np.mean(values_manual["200x"]) * 100:.2f}%, CV_20x:{np.std(values_manual["20x"]) / np.mean(values_manual["20x"]) * 100:.2f}%, CV_150x:{np.std(values_manual["150x"]) / np.mean(values_manual["150x"]) * 100:.2f}%, CV_15x:{np.std(values_manual["15x"]) / np.mean(values_manual["15x"]) * 100:.2f}%')


xml_folder = 'D:\\Dropbox\\robochem\\data\\BPRF\\volume_check_20240119\\serial_dilution_manual_15-20-150-200\\'
dfs,csv_files = csv_to_df(xml_folder)
# analyze the manual pipetting
manual_pipetting(dfs)

# analyze the rpbotic pipetting
name_of_robot = 'Robowski2' # Robowski1 or Robowski2
if name_of_robot == 'Robowski1': df_Robowski= dfs[2]   # 2 means robowski1, 1 means robowski2
elif name_of_robot == 'Robowski2': df_Robowski = dfs[1]

df_Robowski_200x = df_Robowski.loc[:,[i for i in df_Robowski.columns if '200x' in i]]
df_Robowski_20x = df_Robowski.loc[:,[i  for i in df_Robowski.columns if '20x' in i]]

# make two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 8))
# plot the df_Robowski in ax1
for column in df_Robowski.columns:
    ax1.plot(df_Robowski.index, df_Robowski[column], label=column)
ax1.set_xlim([250, 360])
ax1.set_ylim([0, 1])
ax1.set_xlabel('wavelength (nm)')
ax1.set_ylabel('abs')

# get the point to point ratio of 200x and 20x
ratio_280nm = df_Robowski_20x.loc[280,:].values /df_Robowski_200x.loc[280,:].values
ratio_320nm = df_Robowski_20x.loc[320,:].values / df_Robowski_200x.loc[320,:].values

# plot the ratio
ax2.plot(list(range(len(ratio_280nm))),ratio_280nm, label='280nm', marker='o')
ax2.plot(list(range(len(ratio_320nm))),ratio_320nm, label='320nm', marker='>')

# add horizontal line
ax2.axhline(y=np.mean(ratio_280nm), color='g', linestyle='--', label='10')
ax2.axhline(y=np.mean(ratio_320nm), color='b', linestyle='--', label='9')

# set x y range
ax2.set_ylim([8, 13])
ax2.set_xlim([0, 18])

# set x y label
ax2.set_xlabel('sample number')
ax2.set_ylabel('ratio')

# set title for the whole plot
fig.suptitle(f'Robowski{1 if name_of_robot=="Robowski1" else 2 }\n'
             f'mean_280nm:{np.mean(ratio_280nm):.2f},mean_280nm:{np.mean(ratio_320nm):.2f}\n'
             f'STD_280nm:{np.std(ratio_280nm):.2f},STD_280nm:{np.std(ratio_320nm):.2f}\n'
             f'CV_280nm:{np.std(ratio_280nm)/np.mean(ratio_280nm)*100:.2f}%,CV_280nm:{np.std(ratio_320nm)/np.mean(ratio_320nm)*100:.2f}%')
plt.show()

# save plot
plt.savefig(xml_folder + 'Robowski2.png')

