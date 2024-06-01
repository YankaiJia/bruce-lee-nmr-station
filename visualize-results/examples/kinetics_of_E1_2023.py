import os
import numpy as np
from matplotlib import pyplot as plt

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'

data = np.load(f'{data_folder}simple-reactions/2023-09-14-run01/results/kinetics/keq_fits.npy')
temps = np.array([16, 21, 26, 31, 36])

fig = plt.figure(figsize=(1.3,1.5), dpi=300)

# plt.scatter(temps, data[:, 0], label=f'K_1')
plt.scatter(1000/(273.15 + temps), np.log(data[:, 1]), label=f'k_forward')
plt.scatter(1000/(273.15 + temps), np.log(data[:, 2]), label=f'k_backward')

xs = 1000/(273.15 + temps)
ys = np.log(data[:, 1]) - np.log(data[:, 2])
plt.scatter(xs, ys, label='K', alpha=0.5, color='black')
# fit line and get slope and intersept
z = np.polyfit(xs, ys, 1)
f = np.poly1d(z)
print(f'Intercept {f[0]}, slope {f[1]}')
R_gas = 8.31446261815324  # J/(K*mol)
print(f'Delta S {f[0] * R_gas} J/(K*mol), delta H {-1 * f[1] * R_gas} kJ/mol')
plt.plot(xs, f(xs), '--', color='black')

from scipy.optimize import curve_fit


def func(x, a, b):
    return a + b * x

popt, pcov = curve_fit(func, xs, ys, sigma=0.08 * np.ones(len(xs)), absolute_sigma=True)
print(popt)
p_sigma = np.sqrt(np.diag(pcov))
print(p_sigma)
print(
    f'Delta S {f[0] * R_gas} +- {p_sigma[0] * R_gas} J/(K*mol), delta H {-1 * f[1] * R_gas} +- {-1 * p_sigma[1] * R_gas} kJ/mol')

# plt.legend()
# plt.ylabel('Logarithm of rate constant')
# plt.xlabel('1000/T, K$^{-1}$')
# plt.show()

plt.xlabel('1000/T, K$^{-1}$')
plt.ylabel('ln K')
plt.xlim(3.20, 3.51)
plt.ylim(0.58, 3.2)
plt.tight_layout()
fig.savefig('misc-scripts/figures/kinetics_of_E1_2023-12_hoff.png', dpi=300)

plt.show()
print(data)
