import concurrent.futures
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

def kinetic_equations_vectorized(concentrations, rate_constants):

    a, b, c, ab, bc, ac, abc= concentrations
    kab, kac, kbc, kabc, kacb, kbca = rate_constants

    d_a = -kab * a * b - kac * a * c - kbca * bc * a
    d_b = -kab * a * b - kbc * b * c - kacb * ac * b
    d_c = -kac * a * c - kbc * b * c - kabc * ab * c
    d_ab = kab * a * b - kabc * ab * c
    d_bc = kbc * b * c - kbca * bc * a
    d_ac = kac * a * c - kacb * ac * b
    d_abc = kabc * ab * c + kbca * bc * a + kacb * ac * b
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


def kinetic_equations(concentrations, rate_constants):
    a, b, a2, ab, b2, a2b, ab2, a2b2 = concentrations
    k1, k2, k3, k4, k5, k6, k7, k8, k9, k10, k11, k12 = rate_constants

    d_a = (-2 * k1 * a * a - k2 * a * b - k5 * ab * a
           - k7 * b2 * a - k9 * ab2 * a + k10 * a2 + k11 * ab)
    d_b = (-k2 * a * b - 2 * k3 * b * b - k4 * a2 * b - k6 * ab * b - k8 * a2b * b
           + k11 * ab + k12 * b2)
    d_a2 = k1 * a * a - k4 * a2 * b
    d_ab = k2 * a * b - k5 * ab * a - k6 * ab * b
    d_b2 = k3 * b * b - k7 * b2 * a
    d_a2b = k4 * a2 * b + k5 * ab * a - k8 * a2b * b
    d_ab2 = k6 * ab * b + k7 * b2 * a - k9 * ab2 * a
    d_a2b2 = k8 * a2b * b + k9 * ab2 * a

    ds = np.array([d_a, d_b, d_a2, d_ab, d_b2, d_a2b, d_ab2, d_a2b2])

    return ds

def concentration_iterate(reaction_product, a:float=1, b:float=1, c:float=1,
                          t_step_size:float=0.05, t_num:int=500,
                          rate_constants:tuple=tuple()):

    comp_num =0
    comp_names = []

    if reaction_product == 'a2bc':
        comp_num = 11
        comp_names = ['a', 'b', 'c', 'ab', 'ac', 'bc', 'a2', 'a2b', 'a2c', 'abc', 'a2bc']

    elif reaction_product == 'abc':
        comp_num = 7
        comp_names = ['a', 'b', 'c', 'ab', 'bc', 'ac', 'abc']
    elif reaction_product == 'a2b2':
        comp_num = 8
        comp_names = ['a', 'b', 'a2', 'ab', 'b2', 'a2b', 'ab2', 'a2b2']

    concentrations = np.array([a, b, c] + [0] * (comp_num - 3), dtype=float)
    concentration_lists = [np.zeros(t_num) for _ in range(comp_num)]
    d_concentrations = np.zeros(comp_num)

    for num in range(t_num):

        if reaction_product == 'a2bc':
            d_concentrations = kinetic_equations_a2bc(concentrations, rate_constants)
        elif reaction_product == 'abc':
            d_concentrations = kinetic_equations_vectorized(concentrations, rate_constants)
        elif reaction_product == 'a2b2':
            d_concentrations = kinetic_equations_a2b2(concentrations, rate_constants)

        concentrations += d_concentrations * t_step_size

        for i in range(comp_num):
            concentration_lists[i][num] = concentrations[i]

    return concentration_lists, comp_names


def sweep_diff_concs(path:str, c_start:float, c_stop:float, c_num:int,
                     t_step_size:float, t_num:int, ks:tuple,reaction_product,):

    df = pd.DataFrame(columns=["a_init", "b_init", "c_init", f"{reaction_product}_final", f"{reaction_product}_yield"])
    product_yield = None

    concentrations = np.linspace(float(c_start), float(c_stop), c_num, endpoint=False)

    for index, (a0, b0, c0) in enumerate(itertools.product(concentrations, repeat=3)):

        concentration_lists, comp_names = concentration_iterate(a=a0, b=b0, c=c0,
                                                    t_step_size=t_step_size, t_num=t_num,
                                                    rate_constants=ks, reaction_product = reaction_product)
        if random.randint(0, 100) == 1:
            df_conc = pd.DataFrame(concentration_lists).T
            df_conc.columns = comp_names
            # generate a subfolder named kinetics_data if not exist
            kinetics_data_path = path + '\\kinetics_data\\'
            Path(kinetics_data_path).mkdir(parents=True, exist_ok=True)
            df_conc.to_csv(kinetics_data_path + f'concentrations_{round(a0,2)}_{round(b0,2)}_{round(c0,2)}.csv')

        product_final = concentration_lists[-1][-1]

        if a0==0 or b0==0 or c0 == 0:
            product_yield = 0
        else:
            if np.isclose(min(a0, b0, c0),a0):
                product_yield = 2 * product_final / a0
            elif np.isclose(min(a0,b0,c0),b0) or np.isclose(min(a0,b0, c0), c0):
                product_yield = product_final / min(a0,b0,c0)


        df.loc[index] = [a0, b0, c0, product_final, product_yield]

        # print(index + 1)

    return df


def run_one_ks(ks, reaction_product,
               is_show_html= True,
               c_start = 0,
               c_stop = 1,
               c_num = 20,
               t_step_size = 0.05,
               t_num = 1000,) -> None:

    time_start = datetime.now()

    ks_str = '_'.join([str(x) for x in ks])

    save_dir = (f'F:\\reaction_network_simulation_systematic_cal_a2bc_8k_points_0_1_wo_reverse_test'
                f'\\k_{ks_str}\\')
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    df_rxn = sweep_diff_concs(save_dir,c_start,
                              c_stop, c_num,
                              t_step_size, t_num, ks, reaction_product = reaction_product)

    time_now = datetime.today().strftime('%Y-%m-%d-%H-%M_%S')

    # save the df_rxn to the folder 'reaction_network_simulation'
    df_rxn.to_csv(save_dir + f"k_{ks_str}_{time_now}.csv")

    time_end = datetime.now()
    # print(f"Time taken for ks = {ks} is {(time_end - time_start).seconds} seconds.")

    para = {}
    para["c_start"] = c_start
    para['c_stop'] = c_stop
    para['c_num'] = c_num
    para['t_step_size'] =t_step_size
    para['t_num'] = t_num
    para['ks'] = [ks[0],ks[1],ks[2],ks[3],ks[4],ks[5]]
    para['csv_path'] = save_dir + f"k_{ks_str}_{time_now}.csv"
    para['compute_time_sec'] = (time_end - time_start).seconds

    # save the para to json file
    with open(save_dir + f'para_{time_now}.json', 'w', encoding='utf-8') as f:
        json.dump(para, f, indent=4)


    if is_show_html:
        # fig_scatter = reaction_network_for_plotting.plot_scatter()
        # fig_scatter.show()
        fig_isosurface = reaction_network_for_plotting.plot_isosurface(df=df_rxn, ks=ks,
                                                                       reaction_product = reaction_product)
        fig_isosurface.write_html(save_dir+f'k_{ks_str}_{time_now}.html')
        # fig_isosurface.show()

    print(f'Finished one run at {time_now} for ks = {ks}.')


if __name__ == "__main__":

    rate_num = 0
    ks = []
    list_of_ks = []

    reaction_product ='a2b2'
    if reaction_product == 'a2b2':
        rate_num = 12
        rate_values = [1, 0]
        list_of_ks = list(itertools.product(rate_values, repeat=rate_num-3))
        list_of_ks = [list(i) + [0]*3 for i in list_of_ks][:5]

    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(run_one_ks, list_of_ks, [reaction_product] * len(list_of_ks))

