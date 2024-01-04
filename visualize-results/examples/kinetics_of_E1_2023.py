import os
import numpy as np
from matplotlib import pyplot as plt

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'

data = np.load(f'{data_folder}simple-reactions/2023-09-14-run01/results/kinetics/keq_fits.npy')
temps = np.array([16, 21, 26, 31, 36])

# plt.scatter(temps, data[:, 0], label=f'K_1')
plt.scatter(1000/(273.15 + temps), np.log(data[:, 1]), label=f'k_forward')
plt.scatter(1000/(273.15 + temps), np.log(data[:, 2]), label=f'k_backward')
plt.legend()
plt.ylabel('Logarithm of rate constant')
plt.xlabel('1000/T, K$^{-1}$')
plt.show()

print(data)
