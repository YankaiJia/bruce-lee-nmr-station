import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import plotly.express as px
from pathlib import Path
import math
from datetime import datetime

matplotlib.use('Agg')
import plotly.graph_objects as go

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

def plot_scatter():

    fig = px.scatter_3d(df_rxn, x='a_init', y='b_init', z='c_init',
                        color='abc_yield', size='abc_yield', size_max=18, opacity=0.7)

    # tight layout
    fig.update_layout(margin=dict(l=0, r=0, b=0, t=0))

    return fig

def plot_isosurface(df, ks):

    X = df['a_init']
    Y = df['b_init']
    Z = df['c_init']

    abc_final = df['abc_final']
    abc_yield = df['abc_yield']

    fig = go.Figure(data=go.Isosurface(
        x=X,
        y=Y,
        z=Z,
        value=abc_final,
        isomin=min(abc_final) ,
        isomax=max(abc_final) ,
        surface_count=8,
        opacity=1,
        caps=dict(x_show=False, y_show=False),
        colorscale="Rainbow"
    ))

    fig.update_layout(scene=dict(
        xaxis_title='conc_A0',
        yaxis_title='conc_B0',
        zaxis_title='conc_C0'),
        width=1200,
        margin=dict(r=50, b=50, l=50, t=100),
        title= f"k=({ks[0]}, {ks[1]}, {ks[2]}, {ks[3]}, {ks[4]}, {ks[5]})",
        title_font_size = 30)

    return fig


if __name__ == "__main__":

    # data_dir = ('reaction_network_simulation\\k_0.1_0.1_0.1_1_1_1\\')
    # data_dir = ('reaction_network_simulation\\k_1_0.1_0.1_1_0.1_0.1\\')
    # data_dir = ('reaction_network_simulation\\k_1_1_0.1_1_1_0.1\\')
    data_dir = ('reaction_network_simulation\\k_1_1_1_0.1_0.1_0.1\\')
    # data_dir = ('reaction_network_simulation\\k_1_1_1_1_1_1\\')

    time_now = datetime.today().strftime('%Y-%m-%d-%H-%M')

    df_rxn = pd.read_csv(data_dir + data_dir.split('\\')[-2] + '.csv')

    ks = [float(i) for i in data_dir.split('\\')[-2].split('_')[1:]]

    # fig_scatter = plot_scatter()
    # fig_scatter.show()
    fig_isosurface = plot_isosurface(df=df_rxn, ks=(ks[0],ks[1],ks[2],ks[3],ks[4],ks[5]))
    fig_isosurface.write_html(data_dir + f'k_{ks[0]}_{ks[1]}_{ks[2]}_{ks[3]}_{ks[4]}_{ks[5]}_{time_now}.html')
    fig_isosurface.show()












