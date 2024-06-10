import concurrent.futures
import glob
import json,os

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import plotly.express as px
from pathlib import Path
import math
from datetime import datetime

from plotly.subplots import make_subplots

matplotlib.use('Agg')
import plotly.graph_objects as go


def plot_scatter():

    fig = px.scatter_3d(df_rxn, x='a_init', y='b_init', z='c_init',
                        color='abc_yield', size='abc_yield', size_max=18, opacity=0.7)

    # tight layout
    fig.update_layout(margin=dict(l=0, r=0, b=0, t=0))

    return fig


def plot_isosurface(df, ks, reaction_product):

    X = df['a_init']
    Y = df['b_init']
    Z = df['c_init']

    fig = make_subplots(rows=1, cols=2,subplot_titles=(f'Yield_{reaction_product}',  f'Conc_{reaction_product}'),
                        specs=[[{'type': 'Isosurface'}, {'type': 'Isosurface'}]])

    plot1 = go.Isosurface(
        x=X,
        y=Y,
        z=Z,
        value=df[f'{reaction_product}_yield'],
        isomin=min(df[f'{reaction_product}_yield']),
        isomax=max(df[f'{reaction_product}_yield']),
        surface_count=10, colorscale='Rainbow',colorbar=dict(len=0.5, x=0.45 ,y=0.5),
        caps=dict(x_show=False, y_show=False), text=f'{reaction_product}_yield'
    )
    plot2 = go.Isosurface(
        x=X,
        y=Y,
        z=Z,
        value=df[f'{reaction_product}_final'],
        isomin=min(df[f'{reaction_product}_final']),
        isomax=max(df[f'{reaction_product}_final']),
        surface_count=10, colorscale='Rainbow',colorbar=dict(len=0.5, x=1.0 ,y=0.5),
        caps=dict(x_show=False, y_show=False), text=f'{reaction_product}_final'

    )

    fig.add_trace(plot1, 1, 1)
    fig.add_trace(plot2, 1, 2)

    fig.update_layout(scene=dict(
        xaxis_title='conc_A0',
        yaxis_title='conc_B0',
        zaxis_title='conc_C0'),
        width=1600,
        margin=dict(r=80, b=80, l=80, t=100),
        title= f"k={ks}",
        title_font_size = 30,)

    fig.update_annotations(font_size=30)

    return fig

def plot_concs(a_list, b_list, c_list, ab_list, bc_list, ac_list, abc_list, a0, b0, c0):
    t_step_size = 0.02

    ## make 7 subplots for each species
    fig, axs = plt.subplots(1, 7, figsize=(20, 5))
    axs[0].plot([x*t_step_size for x in list(range((len(a_list))))],a_list)
    axs[0].set_title(f'a0={round(a0,2)}')
    axs[1].plot([x*t_step_size for x in list(range((len(b_list))))],b_list)
    axs[1].set_title(f'b0={round(b0,2)}')
    axs[2].plot([x*t_step_size for x in list(range((len(c_list))))],c_list)
    axs[2].set_title(f'c0={round(c0,2)}')
    axs[3].plot([x*t_step_size for x in list(range((len(ab_list))))],ab_list)
    axs[3].set_title('ab')
    axs[4].plot([x*t_step_size for x in list(range((len(ac_list))))],ac_list)
    axs[4].set_title('ac')
    axs[5].plot([x*t_step_size for x in list(range((len(bc_list))))],bc_list)
    axs[5].set_title('bc')
    axs[6].plot([x*t_step_size for x in list(range((len(abc_list))))],abc_list)
    axs[6].set_title('abc')

    for i in range(7):
        axs[i].set_xlabel('t')

    return fig

def csv_plot_and_save_one_folder(folder):

    print('working on folder: ',folder)

    ## plot all csvs in the kinetics_data folder

    os.chdir(folder)
    csv_files = glob.glob('*.csv')
    print(f'csv_files: {csv_files}')

    for csv_file in csv_files:

        png_file = Path(csv_file).with_suffix('.png')

        # if png_fileexist, delete it
        if png_file.exists():
            os.remove(png_file)

        df = pd.read_csv(csv_file)
        # make the first column the index
        df.set_index(df.columns[0], inplace=True)
        titles = df.columns
        # make len(titles) subplots for each species
        fig, axs = plt.subplots(1, len(titles), figsize=(25, 6))
        TIME_STEP = 0.05
        x = [i * TIME_STEP for i in df.index.tolist()]
        for index, title in enumerate(titles):
            axs[index].plot(x,df[title])
            axs[index].set_title(title)
            axs[index].set_xlabel('t')

        a0 = df[titles[0]][0]
        b0 = df[titles[1]][0]
        c0 = df[titles[2]][0]
        product_final = df[titles[-1]][len(df[titles[-1]]) - 1]

        if np.isclose(a0, 0) or np.isclose(b0, 0):
            product_yield = 0
        else:
            product_yield = product_final / min(a0, b0)

        fig.suptitle(f'a0 = {round(a0, 2)},   b0 = {round(b0, 2)},   c0 = {round(c0, 2)},   '
                     f'abc_final = {round(product_final, 2)},   abc_yield = {round(product_yield, 2)}  \n \n'
                     f'\n\n\n',
                     fontsize=16)
        # print(f'a0 = {a0}, b0 = {b0}, c0 = {c0}, '
        #              f'abc_final = {product_final}, abc_yield = {product_yield}')

        # Save the plot as a png file
        plt.savefig(png_file, dpi=100)
        # print(f'csv_file: {csv_file}')
        plt.close()

        # elif png_file.exists():
        #     print(f'{png_file} already exists')

if __name__ == "__main__":


    # data_dir = 'G:\\reaction_network_simulation_abc_1_0_with_reverse'
    # folders_with_ks = [(str(f) + '\\kinetics_data') for f in Path(data_dir).iterdir() if f.is_dir()]
    # with concurrent.futures.ProcessPoolExecutor() as executor:
    #     executor.map(csv_plot_and_save_one_folder,folders_with_ks)


    # data_dir = 'G:\\reaction_network_simulation_abc_1_0.1_with_reverse_5000steps'
    # data_dir = 'G:\\reaction_network_simulation_abc_1_0_with_reverse'
    # folders_with_ks = [(str(f) + '\\kinetics_data') for f in Path(data_dir).iterdir() if f.is_dir()]
    # with concurrent.futures.ProcessPoolExecutor() as executor:
    #     executor.map(csv_plot_and_save_one_folder,folders_with_ks)

    # data_dir = 'G:\\reaction_network_simulation_abc_1_0.1_with_reverse'
    # folders_with_ks = [(str(f) + '\\kinetics_data') for f in Path(data_dir).iterdir() if f.is_dir()]
    # with concurrent.futures.ProcessPoolExecutor() as executor:
    #     executor.map(csv_plot_and_save_one_folder,folders_with_ks)
    #
    data_dir = 'G:\\reaction_network_simulation_abc_1_0.1_wo_reverse_5000steps'
    # data_dir = 'G:\\reaction_network_simulation_abc_1_0.1_with_reverse'
    folders_with_ks = [(str(f) + '\\kinetics_data') for f in Path(data_dir).iterdir() if f.is_dir()]
    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(csv_plot_and_save_one_folder,folders_with_ks)

    data_dir = 'G:\\reaction_network_simulation_abc_1_0.1_wo_reverse'
    # data_dir = 'G:\\reaction_network_simulation_abc_1_0.1_with_reverse'
    folders_with_ks = [(str(f) + '\\kinetics_data') for f in Path(data_dir).iterdir() if f.is_dir()]
    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(csv_plot_and_save_one_folder,folders_with_ks)





















