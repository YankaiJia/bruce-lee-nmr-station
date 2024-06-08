import concurrent.futures
import itertools
import json
import random
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
from pathlib import Path

matplotlib.use('Agg')
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

def kinetic_equations(concentrations, rate_constants):

    a, b, a2, ab, b2, a2b, ab2, a2b2 = concentrations
    k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, k12 = rate_constants

    d_a = (-2 * k1 * a * a - k2 * a * b - k5 * ab * a
           - k7 * b2 * a - k9 * ab2 * a + k10 * a2 + k11 * ab)
    d_b = (-k2 * a * b - 2 * k3 * b * b - k4 * a2 * b - k6 * ab * b - k8 * a2b * b
           + k11 * ab + k12 * b2)
    d_a2 = k1 * a * a - k4 * a2 * b - k10 * a2
    d_ab = k2 * a * b - k5 * ab * a - k6 * ab * b -  k11 * ab
    d_b2 = k3 * b * b - k7 * b2 * a - k12 * b2
    d_a2b = k4 * a2 * b + k5 * ab * a - k8 * a2b * b
    d_ab2 = k6 * ab * b + k7 * b2 * a - k9 * ab2 * a
    d_a2b2 = k8 * a2b * b + k9 * ab2 * a

    ds = np.array([d_a, d_b, d_a2, d_ab, d_b2, d_a2b, d_ab2, d_a2b2])

    return ds


def concentration_iterate( ks: tuple,a:float=1, b:float=1,
                          t_step_size:float=0.02, t_end:int=50000):

    comp_names = ['a', 'b', 'a2', 'ab', 'b2', 'a2b', 'ab2', 'a2b2']
    comp_num = len(comp_names)

    concentrations = np.array([a, b, 0, 0, 0, 0, 0, 0])
    concentration_lists = [np.zeros(t_end) for _ in range(comp_num)]
    d_concentrations = np.zeros(comp_num)

    for num in range(t_end):

        d_concentrations = kinetic_equations(concentrations, ks)
        concentrations += d_concentrations * t_step_size

        for i in range(comp_num):
            concentration_lists[i][num] = concentrations[i]

    return concentration_lists, comp_names


def sweep_diff_concs(path:str,c_start:float,c_stop:float,c_num:int,
                     t_step_size: float, t_num: int, ks: tuple, reaction_product, ):

    df = pd.DataFrame(columns=["a_init", "b_init",
                               f"{reaction_product}_final", f"{reaction_product}_yield"])

    concentrations = np.linspace(float(c_start), float(c_stop), c_num, endpoint=False)

    for index, (a0, b0) in enumerate(itertools.product(concentrations, repeat=2)):

        concentration_lists, comp_names = concentration_iterate(ks=ks,a=a0, b=b0,
                                                                t_step_size=t_step_size,
                                                                t_end=t_num)
        if index % 5 == 0:
            df_kinetics = pd.DataFrame(columns=comp_names)
            ## append the concentratio lists to the df
            for i in range(len(comp_names)):
                df_kinetics[comp_names[i]] = concentration_lists[i]
            save_csv_dir = path + '\\kinetics_data\\'
            # if the directory does not exist, create it
            Path(save_csv_dir).mkdir(parents=True, exist_ok=True)
            ## save the df to csv file
            df_kinetics.to_csv(save_csv_dir + f"{a0}_{b0}.csv")

        product_final = concentration_lists[-1][-1]

        if product_final == 0:
            ab_yield = 0
        else:
            # if a0 or bo is 0, then the yield is 0
            if np.isclose(a0, 0) or np.isclose(b0, 0):
                ab_yield = 0
            else:
                ab_yield = 2 * product_final / min(a0, b0)

        # print(f"a0: {a0}, b0: {b0}, product_final: {product_final}, ab_yield: {ab_yield}")

        # save the a0, b0, product_final, ab_yield to the df as one row
        row_here = {'a_init': a0, 'b_init':b0,
                    f"{reaction_product}_final": product_final,
                    f"{reaction_product}_yield": ab_yield}

        df.loc[-1] = [a0,b0, product_final, ab_yield]
        df.index = df.index + 1  # shifting index
        df = df.sort_index()  # sorting by index

        print(index)

    return df

def run_one_ks( ks, folder,
                c_start=0,
                c_stop=1,
                c_num=20,
                t_step_size=0.05,
                t_num=1000,
                reaction_product='a2b2'):

    ks_str = '_'.join([str(x) for x in ks])

    print(f'Running ks: {ks_str}')

    save_dir = (f'G:\\' + folder + f'\\k_{ks_str}\\')
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    print(f'save_dir: {save_dir}')
    time_start = datetime.now()
    df_rxn = sweep_diff_concs(path=save_dir,
                              c_start=c_start,
                              c_stop=c_stop,
                              c_num=c_num,
                              t_step_size=t_step_size,
                              t_num=t_num,
                              ks=ks,
                              reaction_product=reaction_product)
    time_end = datetime.now()
    time_now = datetime.today().strftime('%Y-%m-%d-%H-%M_%S')

    # save the df_rxn to the folder 'reaction_network_simulation'
    df_rxn.to_csv(save_dir + f"k_{ks_str}_{time_now}.csv")

    ## save the setting into a json file
    para = {}
    para["c_start"] = c_start
    para['c_stop'] = c_stop
    para['c_num'] = c_num
    para['t_step_size'] =t_step_size
    para['t_num'] = t_num
    para['ks'] = [x for x in ks]
    para['csv_path'] = save_dir + f"k_{ks_str}_{time_now}.csv"
    para['compute_time_sec'] = (time_end - time_start).seconds

    with open(save_dir + f"k_{ks_str}_{time_now}.json", 'w', encoding='utf-8') as f:
        json.dump(para, f, indent=4)


if __name__ == "__main__":

    rate_values = [1, 0.1]
    list_of_ks = list(itertools.product(rate_values, repeat=12))
    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(run_one_ks, list_of_ks, ['reaction_network_simulation_a2b2_1_0.1'] * len(list_of_ks))

    #
    # rate_values1 = [1, 0]
    # list_of_ks1 = list(itertools.product(rate_values1, repeat=12))
    # with concurrent.futures.ProcessPoolExecutor() as executor:
    #     executor.map(run_one_ks, list_of_ks1, ['reaction_network_simulation_a2b2_1_0'] * len(list_of_ks1))
    #













