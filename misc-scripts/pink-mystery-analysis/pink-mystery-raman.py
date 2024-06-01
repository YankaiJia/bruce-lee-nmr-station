import numpy as np
import os

from matplotlib import pyplot as plt
from scipy.optimize import curve_fit
from scipy.optimize import least_squares

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'

def simpleaxis(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()

def open_raman_file(filenames, nobkg=False):
    averaged_spectra = []
    for filename in filenames:
        wavenumbers, intensities = np.loadtxt(filename, delimiter=',', skiprows=9, unpack=True)
        averaged_spectra.append(intensities)
    #     plt.plot(wavenumbers, intensities, label=filename.split('/')[-1])
    # plt.legend()
    # plt.show()

    spectrum = np.mean(averaged_spectra, axis=0)
    # only use the points with wavenumbers above 130
    mask = (wavenumbers > 217) & (wavenumbers < 1950)
    wavenumbers = wavenumbers[mask]
    intensities = intensities[mask]
    # use robust least squares of curve_fit to fit function func(x, *params) to the data
    def polyfunc(p, t, y=0):
        return p[0] + p[1]*t + p[2]*t**2 + p[3]*t**3 - y

    popt = least_squares(polyfunc, args=(wavenumbers, intensities), x0=np.zeros(4), loss='soft_l1', f_scale=70)

    intensities_fit = polyfunc(popt.x, wavenumbers)
    # plt.plot(wavenumbers, intensities)
    # plt.plot(wavenumbers, intensities_fit)
    # plt.show()
    subtracted = intensities - intensities_fit
    if nobkg:
        return wavenumbers, intensities
    else:
        return wavenumbers, subtracted

if __name__ == '__main__':
    raman_folder = data_folder + 'Yaroslav/mystery-product-raman/2024-04-27/mystery-product/'

    nspectra = 7
    # make n sumplots with sharex=True
    fig, axs = plt.subplots(nspectra, 1, figsize=(10, 10), sharex=True)

    k = 3
    wavenumbers, intensities = open_raman_file([raman_folder + f'SN1RFdimer-785nm-50x-30s_rep{i}.csv' for i in [1, 2]])
    axs[k].plot(wavenumbers, intensities, label='dimer')

    k = 2
    wavenumbers, intensities = open_raman_file([raman_folder + f'SN1simpleproduct-785nm-50x-30s_rep{i+1}.csv' for i in range(5)])
    axs[k].plot(wavenumbers, intensities, label='product')

    k = 1
    wavenumbers, intensities = open_raman_file([raman_folder + f'SN1OH01-785nm-50x-30s_rep{i}.csv' for i in [1, 2, 4, 5, 6]])
    axs[k].plot(wavenumbers, intensities, label='substrate')

    k = 0
    wavenumbers, intensities = open_raman_file([data_folder + 'Yaroslav/mystery-product-raman/literature/DMF.csv'], nobkg=True)
    axs[k].plot(wavenumbers, intensities, label='DMF, literature')

    k = 4
    wavenumbers, intensities = open_raman_file([data_folder + 'Yaroslav/mystery-product-raman/literature/Zheng 2012 1-CS neutral.txt'], nobkg=True)
    axs[k].plot(wavenumbers, intensities - np.min(intensities), color='C0', label='Literature dimer, neutral (=)')

    k = 4
    wavenumbers, intensities = open_raman_file([data_folder + 'Yaroslav/mystery-product-raman/literature/Zheng 2012 1-CS charged oxidized.txt'], nobkg=True)
    axs[k].plot(wavenumbers, intensities - np.min(intensities), color='C1', label='Literature dimer, oxidized (-)')

    k = 5
    wavenumbers, intensities = open_raman_file(
        [raman_folder + f'needle/dried-pink-needle-785nm-50x-30s_rep{i}.csv' for i in [2, 6, 9]])
    axs[k].plot(wavenumbers, intensities, label='dried pink crude')

    k = 6
    wavenumbers, intensities = open_raman_file(
        [raman_folder + f'lyophilized//pink_lyo-785nm-50x-30s_rep{i}.csv' for i in [1, 2, 3, 4, 5, 6, 9, 10]])
    axs[k].plot(wavenumbers, intensities, color='C0', label='lyophilized pink crude, A')
    wavenumbers, intensities = open_raman_file(
        [raman_folder + f'lyophilized//pink_lyo-785nm-50x-30s_rep{i}.csv' for i in [7, 8]])
    axs[k].plot(wavenumbers, intensities, color='C1', label='lyophilized pink crude, B')

    for k in range(nspectra):
        simpleaxis(axs[k])
        # axs[k].legend(loc='upper right')
        axs[k].legend(loc='upper left')
        # add vertical grid
        axs[k].grid(axis='x')
        # add minor ticks gridlines
        axs[k].grid(axis='x', which='minor', color='grey', alpha=0.15)

    plt.xlabel('Wavenumber, cm⁻¹')
    # make x minor ticks spacing 50
    plt.gca().xaxis.set_minor_locator(plt.MultipleLocator(5))
    # set x major ticks to 50
    plt.gca().xaxis.set_major_locator(plt.MultipleLocator(50))
    plt.ylabel('Intensity, a.u.')
    plt.show()