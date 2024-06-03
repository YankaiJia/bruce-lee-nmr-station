import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import plotly.express as px
from pathlib import Path
import math

matplotlib.use('Agg')
import plotly.graph_objects as go
import seaborn as sns


def plot_concs(a_list, b_list, ab_list, a0, b0):
    t_step_size = 0.02

    ## make 7 subplots for each species
    fig, axs = plt.subplots(1, 3, figsize=(20, 5))
    axs[0].plot([x*t_step_size for x in list(range((len(a_list))))],a_list)
    axs[0].set_title(f'a0={round(a0,2)}')
    axs[1].plot([x*t_step_size for x in list(range((len(b_list))))],b_list)
    axs[1].set_title(f'b0={round(b0,2)}')
    axs[2].plot([x*t_step_size for x in list(range((len(ab_list))))],ab_list)
    axs[2].set_title('ab')

    for i in range(3):
        axs[i].set_xlabel('t')

    return fig

def kinetic_equations(a, b, kab):

    d_a = -kab * a * b
    d_b = -kab * a * b
    d_ab = kab * a * b

    return d_a, d_b, d_ab

def concentration_iterate(a:float=1, b:float=1, ab:float = 0, kab:float=1,
                          t_step_size:float=0.02, t_end:int=50000):

    a_list, b_list, ab_list = [], [], []

    num = 0
    while num < t_end:
        d_a, d_b, d_ab = kinetic_equations(a, b, kab)
        a += d_a*t_step_size
        b += d_b*t_step_size
        ab += d_ab*t_step_size

        a_list.append(a)
        b_list.append(b)
        ab_list.append(ab)

        num += 1

        if num > 100 and math.isclose(ab_list[-1],ab_list[-2],  rel_tol=1e-07):
            print(f"conc_abc converged after {num} steps at {ab_list[-1]} and {ab_list[-2]}.")
            break

    return a_list, b_list, ab_list


def sweep_diff_concs(path:str,c_start:float,c_stop:float,c_num:int, kab:float):

    df = pd.DataFrame(columns=["a_init", "b_init", "ab_final", "ab_yield"])    # set column names as "a_init", "b_init", "c_init"

    index = 0
    for a0 in np.linspace(c_start, c_stop,c_num, endpoint= False):
        for b0 in np.linspace(c_start, c_stop,c_num, endpoint= False):

                a_list, b_list, ab_list = concentration_iterate(a=a0, b=b0, kab=kab)

                if index // 50 == 0:
                    print(len(ab_list),'saved!')
                    fig_kinetics = plot_concs(a_list, b_list,
                                              ab_list, a0, b0)
                    Path(path + '/kinetics_2d_plots').mkdir(parents=True, exist_ok=True)
                    fig_kinetics.savefig(path + '/kinetics_2d_plots/' + f'a0_{round(a0,2)}_b0_{round(b0,2)}.png')
                    plt.close(fig_kinetics)

                ab_final = ab_list[-1]
                ab_list.append(ab_final)

                if ab_final == 0:
                    ab_yield = 0
                else:
                    ab_yield = ab_final / min(a0, b0)

                df.loc[index] = [a0, b0, ab_final, ab_yield]

                index += 1

                print(index)


    return df


if __name__ == "__main__":

    c_start = 0
    c_stop = 1
    c_num = 200

    for kab in [0.0001,0.001, 0.01, 0.1, 1, 10, 100]:

        save_dir = (f'C:\\PycharmProjects\\RoboRea\\zeus-pipetter\\reaction_network_simulation'
                    f'\\k_{kab}\\')
        Path(save_dir).mkdir(parents=True, exist_ok=True)

        df_rxn = sweep_diff_concs(save_dir,c_start, c_stop, c_num, kab)

        # save the df_rxn to the folder 'reaction_network_simulation'
        df_rxn.to_csv(save_dir + f"k_{kab}.csv")


        table = df_rxn.pivot(index = 'a_init', columns = 'b_init', values = 'ab_yield')
        ax = sns.heatmap(table)
        ax.invert_yaxis()
        # print(table)
        plt.savefig(save_dir+f'kab_{kab}.png')
        # plt.show()

        # # fig_scatter = plot_scatter()
        # # fig_scatter.show()
        # fig_isosurface = plot_isosurface(df=df_rxn, ks=(kab,kac,kbc,kabc,kacb,kbca))
        # fig_isosurface.write_html(save_dir+f'k_{kab}_{kac}_{kbc}_{kabc}_{kacb}_{kbca}.html')
        # fig_isosurface.show()














