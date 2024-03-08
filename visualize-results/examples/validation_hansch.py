import numpy as np
import pandas as pd
import os

from matplotlib import pyplot as plt

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'
run_name = 'BPRF/2024-03-06-run02/'
df_results_2 = pd.read_csv(data_folder + run_name + f'results/product_concentration.csv')
df_results = pd.read_excel(data_folder + run_name + f'NMR/hantzschexnmroyes.xlsx', sheet_name=0)


# xs = df_results.index.to_numpy()
# ys = df_results['pc#HRP01'].to_numpy()
# xs = df_results.index.to_numpy()
colstoplot = ['NMR HE C', 'OYES HE C']

# colstoplot = ['NMR HA C', 'OYES HA C']
xs = df_results[colstoplot[0]].to_numpy()
# ys = df_results[colstoplot[1]].to_numpy()
# ys = df_results_2['pc#bb017']
ys = df_results_2['pc#HRP01']
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