import numpy as np
import pandas as pd
import os

from matplotlib import pyplot as plt

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'

def exrobotocrudes():
    run_name = 'BPRF/2024-03-06-run02/'
    df_results_2 = pd.read_csv(data_folder + run_name + f'results/product_concentration.csv')
    df_results = pd.read_excel(data_folder + run_name + f'NMR/hantzschexnmroyes.xlsx', sheet_name=0)


    # xs = df_results.index.to_numpy()
    # ys = df_results['pc#HRP01'].to_numpy()
    # xs = df_results.index.to_numpy()
    # colstoplot = ['NMR HE C', 'OYES HE C']

    colstoplot = ['NMR HA C', 'OYES HA C']
    xs = df_results[colstoplot[0]].to_numpy()
    # ys = df_results[colstoplot[1]].to_numpy()
    ys = df_results_2['pc#bb017']
    # ys = df_results_2['pc#HRP01']
    plt.xlabel(colstoplot[0] + 'oncentration, mol/L')
    plt.ylabel(colstoplot[1] + 'oncentration, mol/L')

    maxval = max([np.max(xs), np.max(ys)])
    plt.plot([0, maxval], [0, maxval], 'k--')

    # set same color foe each three points
    labels = ['Conditions for HE max', 'Conditions for HA max', 'Conditions for HE max, repeat', 'Conditions for HA max, repeat']
    for i in range(4):
        plt.scatter(xs[i*3:i*3+3], ys[i*3:i*3+3], c=f'C{i}', marker='o', label=labels[i])

    # annotate points by index
    for i in range(len(xs)):
        plt.annotate(i, (xs[i], ys[i]))

    # plt.xlim(0, np.max(xs))
    # plt.ylim(0, np.max(ys))
    plt.legend()
    plt.show()

def inrobotocrudes():
    run_name = 'BPRF/2024-03-06-run01/'
    df_results_2 = pd.read_csv(data_folder + run_name + f'results/product_concentration.csv')
    df_results = pd.read_excel(data_folder + run_name + f'NMR/hantzschrobotnmroyes.xlsx', sheet_name=0)

    name = 'Hantzsch ester'
    ys = df_results['NMR HE C'].to_numpy()
    xs = df_results_2['pc#HRP01'].to_numpy()
    xs_err = df_results_2['pcerr#HRP01'].to_numpy()

    # name = 'Hemiaminal'
    # ys = df_results['NMR HA C'].to_numpy()
    # xs = df_results_2['pc#bb017'].to_numpy()
    # xs_err = df_results_2['pcerr#bb017'].to_numpy()

    # plot with error bars in x
    plt.title('In roboto crudes, 2024-03-06-run01, minLambda 235 nm')
    dataset_dividing_indes = 9
    plt.errorbar(xs[:dataset_dividing_indes], ys[:dataset_dividing_indes], xerr=xs_err[:dataset_dividing_indes], fmt='o',
                 capsize=5, capthick=2, alpha=0.5, label='Condition A (Hantzsch ester max)', color='C0')
    plt.errorbar(xs[dataset_dividing_indes:], ys[dataset_dividing_indes:], xerr=xs_err[dataset_dividing_indes:], fmt='o',
                 capsize=5, capthick=2, alpha=0.5, label='Condition B (hemiaminal max)', color='C2')
    maxval = max([np.max(xs), np.max(ys)])
    plt.plot([0, maxval], [0, maxval], 'k--')
    for i in range(len(xs)):
        plt.annotate(i, (xs[i], ys[i]))
    plt.ylabel(f'{name} concentration by NMR, mol/L')
    plt.xlabel(f'{name} concentration by UV-VIS, mol/L')
    plt.xlim(-0.05 * maxval, 1.1 * maxval)
    plt.ylim(-0.05 * maxval, 1.1 * maxval)
    plt.legend()
    plt.show()
    # xs = df_results.index.to_numpy()
    # ys = df_results['pc#HRP01'].to_numpy()
    # xs = df_results.index.to_numpy()
    # colstoplot = ['NMR HE C', 'OYES HE C']


if __name__ == '__main__':
    inrobotocrudes()