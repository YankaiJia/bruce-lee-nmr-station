import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import plotly.express as px
from pathlib import Path
import math

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

def kinetic_equations(a, b, c, ab, bc, ac, k1, k2, k3, k4, k5, k6, k7, k8, k9):

    d_a = -k1 * a * b - k2 * a * c - k6 * bc * a + k7 * ab + k8 * ac
    d_b = -k1 * a * b - k3 * b * c - k5 * ac * b + k7 * ab + k9 * bc
    d_c = -k2 * a * c - k3 * b * c - k4 * ab * c + k8 * ac + k9 * bc
    d_ab = k1 * a * b - k4 * ab * c - k7 * ab
    d_ac = k2 * a * c - k5 * ac * b - k8 * ac
    d_bc = k3 * b * c - k6 * bc * a - k9 * bc
    d_abc = k4 * ab * c + k5 * ac * b + k6 * bc * a

    return d_a, d_b, d_c, d_ab, d_bc, d_ac, d_abc

def concentration_iterate(a:float=1, b:float=1, c:float=1,
                          k1:float=1, k2:float=1, k3:float=1,
                          k4:float=1, k5:float=1, k6:float=1,
                          k7:float = 0.5, k8:float = 0.5, k9:float = 0.5,
                          t_step_size:float=0.05, t_num:int=500):

    a_list, b_list, c_list, ab_list, bc_list, ac_list, abc_list = [], [], [], [], [], [], []
    ab, bc, ac, abc = 0, 0, 0, 0

    num = 0
    while num < t_num:
        d_a, d_b, d_c, d_ab, d_bc, d_ac, d_abc = (
            kinetic_equations(a, b, c, ab, bc, ac, k1, k2, k3, k4, k5, k6, k7, k8, k9))

        a += d_a*t_step_size
        b += d_b*t_step_size
        c += d_c*t_step_size
        ab += d_ab*t_step_size
        bc += d_bc*t_step_size
        ac += d_ac*t_step_size
        abc += d_abc*t_step_size

        a_list.append(a)
        b_list.append(b)
        c_list.append(c)
        ab_list.append(ab)
        bc_list.append(bc)
        ac_list.append(ac)
        abc_list.append(abc)

        num += 1

        if num > 100 and math.isclose(abc_list[-1],abc_list[-2],  rel_tol=1e-07):
            # print(f"conc_abc converged after {num} steps at {abc_list[-1]} and {abc_list[-2]}.")
            break

    return a_list, b_list, c_list, ab_list, bc_list, ac_list, abc_list


def sweep_diff_concs(path:str,c_start:float,c_stop:float,c_num:int,
                     k1:float, k2:float, k3:float,
                     k4:float, k5:float, k6:float,
                     k7:float, k8:float, k9:float,
                     t_step_size:float, t_num:int):

    df = pd.DataFrame(columns=["a_init", "b_init", "c_init", "abc_final", "abc_yield"])    # set column names as "a_init", "b_init", "c_init"

    index = 0
    for a0 in np.linspace(c_start, c_stop,c_num, endpoint= False):
        for b0 in np.linspace(c_start, c_stop,c_num, endpoint= False):
            for c0 in np.linspace(c_start, c_stop,c_num, endpoint= False):

                a_list, b_list, c_list, ab_list, bc_list, ac_list, abc_list\
                                            = concentration_iterate(a=a0, b=b0, c=c0,
                                                                    k1=k1, k2=k2, k3=k3,
                                                                    k4=k4, k5=k5, k6=k6,
                                                                    k7=k7, k8=k8, k9=k9,
                                                                    t_step_size=t_step_size, t_num=t_num)
                if index % 19999 == 0:
                    print(len(abc_list),'saved!')
                    fig_kinetics = plot_concs(a_list, b_list, c_list,
                                              ab_list, bc_list, ac_list, abc_list,
                                              a0,b0,c0)
                    Path(path + '/kinetics_2d_plots').mkdir(parents=True, exist_ok=True)
                    fig_kinetics.savefig(path + '/kinetics_2d_plots/' + f'a0_{round(a0,2)}_b0_{round(b0,2)}_c0_{round(c0,2)}.png')
                    plt.close(fig_kinetics)

                abc_final = abc_list[-1]
                abc_list.append(abc_final)

                if abc_final == 0:
                    abc_yield = 0
                else:
                    abc_yield = abc_final / min(a0, b0, c0)
                df.loc[index] = [a0, b0, c0, abc_final, abc_yield]

                index += 1

                print(index)


    return df

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

    # plot_name = 'conc_abc'
    plot_name = 'yield_abc'

    if plot_name == 'conc_abc': plotted_para = df['abc_final']
    elif plot_name == 'yield_abc': plotted_para = df['abc_yield']
    else: plot_name = ' '

    fig = go.Figure(data=go.Isosurface(
        x=X,
        y=Y,
        z=Z,
        value=plotted_para,
        isomin=min(plotted_para),
        isomax=max(plotted_para),
        surface_count=8,
        caps=dict(x_show=False, y_show=False),
    ))

    fig.update_layout(scene=dict(
        xaxis_title='conc_A0',
        yaxis_title='conc_B0',
        zaxis_title='conc_C0'),
        width=1200,
        margin=dict(r=50, b=50, l=50, t=100),
        title= f"{plot_name},k=({ks[0]}, {ks[1]}, {ks[2]}, {ks[3]}, {ks[4]}, {ks[5]}, {ks[6]}, {ks[7]}, {ks[8]})",
        title_font_size = 30)

    return fig


if __name__ == "__main__":

    # sweeping of a0, b0, c0
    c_start = 0
    c_stop = 1
    c_num = 20

    # for each (a0, b0, c0), settings to get the abc_final
    t_step_size = 0.01
    t_num = 500

    for ks in [
               [1, 1, 1, 1, 1, 1, 0.1, 0.1, 0.1],
               # [1, 1, 1, 0.1, 0.1, 0.1],
               # [0.1, 0.1, 0.1, 1, 1, 1],
               # [1, 0.1, 0.1, 1, 0.1, 0.1],
               # [1, 1, 0.1, 1, 1, 0.1]
              ]:

        save_dir = (f'C:\\PycharmProjects\\RoboRea\\zeus-pipetter\\reaction_network_simulation'
                    f'\\k_{ks[0]}_{ks[1]}_{ks[2]}_{ks[3]}_{ks[4]}_{ks[5]}_{ks[6]}_{ks[7]}_{ks[8]}\\')
        Path(save_dir).mkdir(parents=True, exist_ok=True)

        df_rxn = sweep_diff_concs(save_dir,c_start,
                                  c_stop, c_num,
                                  ks[0],ks[1],ks[2],ks[3],ks[4],ks[5],ks[6],ks[7],ks[8],
                                  t_step_size, t_num)

        # save the df_rxn to the folder 'reaction_network_simulation'
        df_rxn.to_csv(save_dir + f"k_{ks[0]}_{ks[1]}_{ks[2]}_{ks[3]}_{ks[4]}_{ks[5]}_{ks[6]}_{ks[7]}_{ks[8]}.csv")

        # fig_scatter = plot_scatter()
        # fig_scatter.show()
        fig_isosurface = plot_isosurface(df=df_rxn, ks=(ks[0],ks[1],ks[2],ks[3],ks[4],ks[5],ks[6],ks[7],ks[8]))
        fig_isosurface.write_html(save_dir+f'k_{ks[0]}_{ks[1]}_{ks[2]}_{ks[3]}_'
                                           f'{ks[4]}_{ks[5]}_{ks[6]}_{ks[7]}_{ks[8]}.html')
        fig_isosurface.show()












