import concurrent.futures
import copy

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import plotly.express as px
from pathlib import Path
import math
from datetime import datetime
import json, random
import reaction_network_for_plotting
import itertools
matplotlib.use('Agg')


def kinetic_equations_abc(concentrations, rate_constants):

    a, b, c, ab, bc, ac, abc= concentrations
    k1, k2, k3, k4, k5, k6, k7, k8, k9 = rate_constants

    d_a = -k1 * a * b - k2 * a * c - k6 * bc * a + k7 * ab + k8 * ac
    d_b = -k1 * a * b - k3 * b * c - k5 * ac * b + k7 * ab + k9 * bc
    d_c = -k2 * a * c - k3 * b * c - k4 * ab * c + k8 * ac + k9 * bc
    d_ab = k1 * a * b - k4 * ab * c - k7 * ab
    d_bc = k3 * b * c - k6 * bc * a - k9 * bc
    d_ac = k2 * a * c - k5 * ac * b - k8 * ac
    d_abc = k4 * ab * c + k5 * ac * b + k6 * bc * a

    ds = np.array([float(x) for x in [d_a, d_b, d_c, d_ab, d_bc, d_ac, d_abc]])

    return ds


def kinetic_equations_a2bc(concentrations, rate_constants):

    a, b, c, ab, ac, bc, a2, a2b, a2c, abc, a2bc = concentrations

    (ka_b, kb_c, ka_c, ka_a,
     kab_a, kab_c, kbc_a, kac_b, kac_a, ka2_c, ka2_b,
     ka2b_c, kabc_a, ka2c_b,
     kra_b, krb_c, kra_c, kra_a) = rate_constants

    d_a = (-ka_b * a * b - ka_c * a * c - 2 * ka_a * a * a - kab_a * ab * a - kac_a * ac * a
           -kbc_a * bc * a - kabc_a * abc * a + kra_b * ab + kra_c * ac + 2 * kra_a * a2)
    d_b = (-ka_b * a * b - kb_c * b * c - kac_b * ac * b -ka2_b * a2 * b
           -ka2c_b * a2c * b + kra_b * ab + krb_c * bc)
    d_c = (-ka_c * a * c - kb_c * b * c - kab_c * ab * c - ka2_c * a2 * c - ka2b_c * a2b * c
             + kra_c * ac + krb_c * bc)
    d_ab = ka_b * a * b - kab_a * ab * a - kab_c * ab * c - kra_b * ab
    d_ac = ka_c * a * c - kac_a * ac * a - kac_b * ac * b - kra_c * ac
    d_bc = kb_c * b * c - kbc_a * bc * a  - krb_c * bc
    d_a2 = ka_a * a * a - ka2_b * a2 * b - ka2_c * a2 * c - 2 * kra_a * a2
    d_a2b = kab_a * ab * a + ka2_b * a2 * b - ka2b_c * a2b * c
    d_a2c = kac_a * ac * a + ka2_c * a2 * c - ka2c_b * a2c * b
    d_abc = kab_c * ab * c + kac_b * ac * b + kbc_a * bc * a - kabc_a * abc * a
    d_a2bc = ka2b_c * a2b * c + ka2c_b * a2c * b + kabc_a * abc * a
    ds = np.array([d_a, d_b, d_c, d_ab, d_ac, d_bc, d_a2, d_a2b, d_a2c, d_abc, d_a2bc])

    return ds


def concentration_iterate(reaction_product, a, b, c,
                          t_step_size, t_num,
                          rate_constants:tuple=tuple()):

    comp_num =0
    comp_names = []

    if reaction_product == 'a2bc':
        comp_names = ['a', 'b', 'c', 'ab', 'ac', 'bc', 'a2', 'a2b', 'a2c', 'abc', 'a2bc']
        comp_num = len(comp_names)

    elif reaction_product == 'abc':
        comp_names = ['a', 'b', 'c', 'ab', 'bc', 'ac', 'abc']
        comp_num = len(comp_names)


    concentrations = np.array([a, b, c] + [0] * (comp_num - 3), dtype=float)
    concentration_lists = [copy.deepcopy(concentrations)]
    d_concentrations = np.zeros(comp_num)

    for num in range(t_num):

        if reaction_product == 'a2bc':
            d_concentrations = kinetic_equations_a2bc(concentrations, rate_constants)
        elif reaction_product == 'abc':
            d_concentrations = kinetic_equations_abc(concentrations, rate_constants)

        concentrations += d_concentrations * t_step_size

        concentration_lists.append(copy.deepcopy(concentrations))

        # if concentration of last component converges, break the loop
        if (num > 100) and np.isclose(concentration_lists[-1][-1],concentration_lists[-2][-1],rtol=1e-5):
            print(f'Interation of concentrations stopped at {num} steps')
            break

    return concentration_lists, comp_names


def sweep_diff_concs(path:str, c_start:float, c_stop:float, c_num:int,
                     t_step_size:float, t_num:int, ks:tuple,reaction_product,):

    df = pd.DataFrame(columns=["a_init", "b_init", "c_init", f"{reaction_product}_final", f"{reaction_product}_yield"])
    product_yield = None

    concentrations = np.linspace(float(c_start), float(c_stop), c_num, endpoint=False)

    abc_comb = sorted(itertools.product(concentrations, repeat=3), reverse=True)

    for index, (a0, b0, c0) in enumerate(abc_comb):

        concentration_lists, comp_names = concentration_iterate(reaction_product,
                                                                a0, b0, c0,
                                                                t_step_size, t_num, ks)

        ####save a csv file if (all of a0, b0, c0) is in [0.9, 0.5, 0.1, 0.0]
        if all([(i in [0.90, 0.50, 0.10]) for i in [round(a0,2), round(b0,2), round(c0,2)]]):
            df_conc = pd.DataFrame(concentration_lists)
            df_conc.columns = comp_names
            # generate a subfolder named kinetics_data if not exist
            kinetics_data_path = path + '\\kinetics_data\\'
            Path(kinetics_data_path).mkdir(parents=True, exist_ok=True)
            df_conc.to_csv(kinetics_data_path + f'{round(a0,2)}_{round(b0,2)}_{round(c0,2)}.csv')
        #####################################################################
        product_final = concentration_lists[-1][-1]

        if a0==0 or b0==0 or c0 == 0:
            product_yield = 0
        else:
            if reaction_product == 'a2bc':
                if np.isclose(min(a0, b0, c0),a0):
                    product_yield = 2 * product_final / a0
                elif np.isclose(min(a0,b0,c0),b0) or np.isclose(min(a0,b0, c0), c0):
                    product_yield = product_final / min(a0,b0,c0)
            elif reaction_product == 'abc':
                product_yield = product_final / min(a0, b0, c0)

        df.loc[index] = [a0, b0, c0, product_final, product_yield]

        # print(index)

    return df


def run_one_ks(ks, reaction_product, ks_set_str,
               is_write_html=True,
               c_start=0,
               c_stop=1,
               c_num=10,
               t_step_size=0.05,
               t_num=500,) -> None:

    time_start = datetime.now()

    ks_str = '_'.join([str(x) for x in ks])

    save_dir = (f'G:\\reaction_network_simulation_'
                f'{reaction_product}_{ks_set_str}_wo_reverse'
                f'\\k_{ks_str}\\')

    Path(save_dir).mkdir(parents=True, exist_ok=True)

    df_rxn = sweep_diff_concs(save_dir,
                              c_start,c_stop, c_num,
                              t_step_size, t_num,
                              ks,
                              reaction_product)

    time_now = datetime.today().strftime('%Y-%m-%d-%H-%M_%S')

    # save the df_rxn to the folder 'reaction_network_simulation'
    df_rxn.to_csv(save_dir + f"k_{ks_str}_{time_now}.csv")

    time_end = datetime.now()
    print(f"Time taken for ks = {ks} is {(time_end - time_start).seconds} seconds.")

    para = {}
    para["c_start"] = c_start
    para['c_stop'] = c_stop
    para['c_num'] = c_num
    para['t_step_size'] =t_step_size
    para['t_num'] = t_num
    para['ks'] = ks
    para['csv_path'] = save_dir + f"k_{ks_str}_{time_now}.csv"
    para['compute_time_sec'] = (time_end - time_start).seconds

    # save the para to json file
    with open(save_dir + f'para_{time_now}.json', 'w', encoding='utf-8') as f:
        json.dump(para, f, indent=4)

    if is_write_html:

        # fig_scatter = reaction_network_for_plotting.plot_scatter()
        # fig_scatter.show()
        fig_isosurface = reaction_network_for_plotting.plot_isosurface(df_rxn, ks, reaction_product)
        fig_isosurface.write_html(save_dir+f'k_{ks_str}_{time_now}.html')
        # fig_isosurface.show()

    print(f'Finished one run at {time_now} for ks = {ks}.')

def is_save(list):
    return any([list[0], list[1], list[2]]) and any([list[3], list[4], list[5]])

if __name__ == "__main__":

    reaction_product = 'abc'
    #
    # rate_values = [1, 0]
    #
    # ks_set_str = '_'.join([str(x) for x in rate_values])
    # list_of_ks = list(itertools.product(rate_values, repeat=9))
    # print(len(list_of_ks))
    #
    # list_of_ks_proper = [ i for i in list_of_ks if is_save(i)]
    #
    #
    # with concurrent.futures.ProcessPoolExecutor() as executor:
    #     executor.map(run_one_ks,
    #                  list_of_ks_proper,
    #                  [reaction_product] * len(list_of_ks_proper),
    #                  [ks_set_str] * len(list_of_ks_proper))
    #
    #
    #
    rate_values = [1, 0.1]

    ks_set_str = '_'.join([str(x) for x in rate_values])
    list_of_ks = list(itertools.product(rate_values, repeat=9))
    print(len(list_of_ks))

    list_of_ks_proper = [ list(i) for i in list_of_ks if is_save(i)]

    # make the last three components of the list_of_ks_proper to be 0
    for i in list_of_ks_proper:
        i[-3:] = [0, 0, 0]



    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(run_one_ks,
                     list_of_ks_proper,
                     [reaction_product] * len(list_of_ks_proper),
                     [ks_set_str] * len(list_of_ks_proper))

