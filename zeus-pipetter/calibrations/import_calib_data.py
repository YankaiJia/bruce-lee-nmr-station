# read json file
import json
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')
import pandas as pd
import os
from functools import reduce

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'

def treat_one_file(folder, file, date):

    with open(folder + file) as f:
        data = json.load(f)

    key_name = list(data.keys())[0]

    values_list_of_dict = data[key_name]

    pipetted_volumes = {}
    pipetted_volumes_mean_cv = {}

    for dict in values_list_of_dict:
        key = list(dict.keys())[0]
        key_int = int(re.findall(r'\d+', key)[0])
        dict_here = dict[key]
        volumes = dict_here['volume']
        pipetted_volumes[key_int] = volumes
        pipetted_volumes_mean_cv[key_int] = [round(np.mean(volumes),2), round(np.std(volumes) / np.mean(volumes) * 100,2)]

    # # plot the mean of pipetted volumes, and add cv as error bar
    # fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    # ax.errorbar(pipetted_volumes_mean_cv.keys(), [i[0] for i in pipetted_volumes_mean_cv.values()], yerr=[i[1] for i in pipetted_volumes_mean_cv.values()], fmt='.')
    # # plot the line y=x
    # ax.plot(ax.get_xlim(), ax.get_ylim(), ls="--", c=".3")
    # ax.set_xlabel('volume (uL)')
    # ax.set_ylabel('pipetted volume (uL)')
    # ax.set_title('pipetted volume vs. volume set')

    # transform pipetted_volumes to a dataframe
    df = pd.DataFrame(pipetted_volumes).T
    df.columns = [str(i)+"_"+date for i in df.columns]
    df['mean'+"_"+date] = np.round(df.mean(axis=1),2)
    df['std'+"_"+date] = df.std(axis=1)
    df['cv'+"_"+date] = df['std'+"_"+date] / df['mean'+"_"+date] * 100
    # make a new column named 'vol_delta' to show the difference between the set volume and the pipetted volume
    df['vol_delta'+"_"+date] = df['mean'+"_"+date]-df.index
    df['error_%'+"_"+date] = df['vol_delta'+"_"+date] / df.index * 100

    # split the dataframe into three parts: 5-50, 60-300, 320-1000
    df_50 = df.loc[(df.index >= 5) & (df.index <= 50),:]
    df_300 = df.loc[(df.index >= 60) & (df.index <= 300),:]
    df_1000 = df.loc[(df.index >= 320) & (df.index <= 1000),:]

    df.to_csv(folder + '\\results_all.csv')

    return df, df_50, df_300, df_1000

def treat_ethanol():

    folder = data_folder + '\\pipetter_calib\\2024-01-24-calib-ethanol\\'

    file_0124 = 'results_20240124.json'
    file_0125 = 'results_20240125.json'
    file_0126 = 'results_20240126.json'
    file_0127 = 'results_20240127.json'

    df_0124, df_50_0124, df_300_0124, df_1000_0124 = treat_one_file(folder,file_0124, '0124')
    df_0125, df_50_0125, df_300_0125, df_1000_0125 = treat_one_file(folder,file_0125, '0125')
    df_0126, df_50_0126, df_300_0126, df_1000_0126 = treat_one_file(folder,file_0126, '0126')
    df_0127, df_50_0127, df_300_0127, df_1000_0127 = treat_one_file(folder,file_0127, '0127')

    # # merge
    df_temp = pd.merge(df_0124, df_0125, how='outer', left_index=True, right_index=True)
    df_temp = pd.merge(df_temp, df_0126, how='outer', left_index=True, right_index=True)
    df_all = pd.merge(df_temp, df_0127, how='outer', left_index=True, right_index=True)

    ## remove outliers. No sure why these three values are way out.
    df_all.loc[700,'2_0126'] = np.nan
    df_all.loc[700,'3_0126'] = np.nan
    df_all.loc[700,'4_0126'] = np.nan

    df_delta = df_all.loc[:,[i for i in df_all.columns if 'delta' in i]]

    columns_data = [i for i in df_all.columns if len(set(i)&set('abcdefghijklmnopqrstuvwxyz')) ==0]
    df_all['mean_all'] = df_all[columns_data].mean(axis=1)
    df_all['std_all'] = df_all[columns_data].std(axis=1)
    df_all['cv_all'] = df_all['std_all'] / df_all['mean_all'] * 100
    df_all['vol_delta_all'] = df_all['mean_all'] - df_all.index

    # save the df_all to csv
    df_all.to_csv(data_folder + '\\pipetter_calib\\2024-01-24-calib-ethanol\\results_all.csv')

    return df_all


def treat_ethanol_after_calib(file, date):

    folder = data_folder + 'pipetter_calib\\2024-01-24-calib-ethanol\\'

    df_ethanol_after_cali, df_50_0124, df_300_0124, df_1000_0124 = treat_one_file(folder, file, date)

    # save the df_all to csv
    df_ethanol_after_cali.to_csv(folder + '\\results_ethanol_after_calib.csv')

    # plot the error
    # fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    # ax.plot(df_ethanol_after_cali.index, df_ethanol_after_cali['error_%'], marker='o')
    # ax.set_xlabel('volume (uL)')
    # ax.set_ylabel('error (%)')
    # ax.set_title('error vs. volume set')
    # plt.show()
    return df_ethanol_after_cali

def treat_water():
    pass

def treat_acetonitrile():
    pass

def treat_chloroform():
    pass

def treat_hbracoh():
    pass

def treat_nitromethane():
    pass

if __name__ == '__main__':

    df_ethanol = treat_ethanol()
    df_ethanol_after_calib_0128 = treat_ethanol_after_calib(file='results_after_calib_ethanol_0128.json', date='0128')
    df_ethanol_after_calib_0129 = treat_ethanol_after_calib(file='results_after_calib_ethanol_0129.json', date='0129')
    df_ethanol_after_calib_0130 = treat_ethanol_after_calib(file='results_after_calib_ethanol_0130.json', date='0130')

    df_ethanol_after_calib_all_less_than_50 = pd.concat([df_ethanol_after_calib_0128.loc[df_ethanol_after_calib_0128.index <= 50,:],
                                                         df_ethanol_after_calib_0129.loc[df_ethanol_after_calib_0129.index <= 50,:],
                                                         df_ethanol_after_calib_0130.loc[df_ethanol_after_calib_0130.index <= 50,:]], axis=1)
    columns_here = df_ethanol_after_calib_all_less_than_50.columns
    columns_here = [i for i in columns_here if len(set(i)&set('abcdefghijklmnopqrstuvwxyz')) ==0]

    df_ethanol_after_calib_all_less_than_50['mean'] = df_ethanol_after_calib_all_less_than_50[columns_here].mean(axis=1)
    df_ethanol_after_calib_all_less_than_50['std'] = df_ethanol_after_calib_all_less_than_50[columns_here].std(axis=1)
    df_ethanol_after_calib_all_less_than_50['cv'] = df_ethanol_after_calib_all_less_than_50['std'] / df_ethanol_after_calib_all_less_than_50['mean'] * 100
    df_ethanol_after_calib_all_less_than_50['vol_delta'] = df_ethanol_after_calib_all_less_than_50['mean'] - df_ethanol_after_calib_all_less_than_50.index

    # plot error in df_ethanol_after_calib_0128 and df_ethanol_after_calib_0129
    df_ethanol_correction_less_than_50 = df_ethanol_after_calib_all_less_than_50.loc[:,'vol_delta']

    fig, (ax1,ax2) = plt.subplots(1, 2, figsize=(12, 8))
    ax1.plot(df_ethanol_after_calib_0128.index, df_ethanol_after_calib_0128['error_%_0128'], marker='o', label='0128')
    ax1.plot(df_ethanol_after_calib_0129.index, df_ethanol_after_calib_0129['error_%_0129'], marker='o', label='0129')
    ax1.plot(df_ethanol_after_calib_0130.index, df_ethanol_after_calib_0130['error_%_0130'], marker='o', label='0130')
    ax1.set_xscale('log')
    ax1.set_xlabel('log(volume) (uL)')
    ax1.set_ylabel('error (%)')
    ax1.set_title('error vs. volume set')
    ax1.legend()

    # on ax2, plot the error
    ax2.plot(df_ethanol_after_calib_0128.index, df_ethanol_after_calib_0128['vol_delta_0128'], marker='o', label='0128')
    ax2.plot(df_ethanol_after_calib_0129.index, df_ethanol_after_calib_0129['vol_delta_0129'], marker='o', label='0129')
    ax2.plot(df_ethanol_after_calib_0130.index, df_ethanol_after_calib_0130['vol_delta_0130'], marker='o', label='0130')
    ax2.set_xlabel('volume (uL)')
    ax2.set_ylabel('delta (%)')
    ax2.set_title('delta vs. volume set')
    ax2.legend()
    ax2.set_xscale('log')
    # plot the horizontal line y=0
    ax2.axhline(y=0, color='g', linestyle='--', label='0')
    plt.show()

    df_dioxane,_, _, _= treat_one_file(data_folder + '\\pipetter_calib\\2024-01-27-calib-dioxane\\',
                                       'results_dioxane_0128.json', '0128')
    df_DCE,_,_,_ = treat_one_file(data_folder + '\\pipetter_calib\\2024-01-28-calib-DCE\\',
                                  'results_DCE_0128.json', '0128')
    df_DMF,_,_,_= treat_one_file(data_folder + '\\pipetter_calib\\2024-01-28-calib-DMF\\',
                                'results_DMF_0128.json', '0128')



    # df_water = treat_water()
    # df_acetonitrile = treat_acetonitrile()
    # df_chloroform = treat_chloroform()
    # df_hbracoh = treat_hbracoh()
    # df_nitromethane = treat_nitromethane()



