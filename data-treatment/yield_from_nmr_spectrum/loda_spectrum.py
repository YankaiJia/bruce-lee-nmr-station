import nmrglue as ng
from nmrglue.analysis import peakpick
import numpy as np
import matplotlib.pyplot as plt
import os

peaks = None

def reference_calibration(data, ppm_axis, real_ppm_of_CDE:float = 3.73):

    data_max = np.max(np.real(data)) # assume this is solvent peak
    idx_of_data_max = np.argmax(np.real(data))    
    ppm_of_data_max = ppm_axis[idx_of_data_max]

    idx_of_CDE = np.argmin(np.abs(ppm_axis - real_ppm_of_CDE))

    delta_points = idx_of_CDE - idx_of_data_max
    data = np.roll(data, delta_points)

    return data

def pre_porcessing(dic, data):
    # DC offset correction

    # Apodization: exponential window with line broadening 0.3 Hz
    # data = ng.proc_base.em(data, lb=0.3)

    # zero filling
    # data = ng.proc_base.zf(data, 2*length)

    # FFT
    data = ng.proc_base.fft(data)

    # manual linear phase correction
    # data = ng.proc_base.ps(data, p0=0, p1=0)

    # determine the ppm scale
    uc = ng.spinsolve.make_uc(dic, data)
    ppm_axis = uc.ppm_scale()

    # referencing/calibration of the spectrum
    data = reference_calibration(data, ppm_axis)

    # # baseline correction
    # ##Fit polynomial baseline to the real part of the spectrum
    # baseline_order = 5
    # coeffs = np.polyfit(ppm_axis, np.real(data), deg=baseline_order)
    # baseline = np.polyval(coeffs, ppm_axis)
    # # Subtract baseline from the real part only
    # spectrum = (np.real(data) - baseline) + 1j * np.imag(data)

    return ppm_axis, data

# write a funcition to get the path of the spectrum folder with tkinter GUI
def get_spectrum_path():
    import tkinter
    from tkinter import filedialog
    root = tkinter.Tk()
    root.withdraw()
    path = filedialog.askdirectory()
    return path

def peak_integration(ppm_axis, spectrum, start_ppm, end_ppm):

    mask = (ppm_axis >= end_ppm) & (ppm_axis <= start_ppm)
    ppm_axis, spectrum = ppm_axis[mask], spectrum[mask]
    area = np.trapz(np.real(spectrum), ppm_axis)
    return abs(area)

if __name__ == "__main__":

    # get project_data_path from os variables
    # project_data_path = os.environ['BRUCELEE_PROJECT_DATA_PATH']
    # path = project_data_path + "\\DPE_bromination\\_Refs\\ref_B"

    # get spectrum folder path
    path = get_spectrum_path()

    # get all the subfolder in the path
    spectrum_folders = [f.path for f in os.scandir(path) if f.is_dir()]
    spectrum_folders = [f for f in spectrum_folders if 'Reference' not in f]
    # sort the subfolders according to the last number in the folder name
    spectrum_folders.sort(key=lambda x: int(x.split('+-')[-1]))
    spectrum_names = [int(i.split('+-')[-1]) for i in spectrum_folders]
    print(spectrum_folders)

    dic_ls, data_ls = [], []
    ppm_axis_ls, spectrum_ls = [], []
    for path_here in spectrum_folders:
    # read spectrum
        dic,data = ng.spinsolve.read(path_here)
        print(f"length of the spectrum: {data.shape[0]}")
        dic_ls.append(dic)
        data_ls.append(data)
        ppm_axis, spectrum = pre_porcessing(dic, data)
        ppm_axis_ls.append(ppm_axis)
        spectrum_ls.append(spectrum)

    # plot the spectrum
    for ppm_axis, spectrum in zip(ppm_axis_ls, spectrum_ls):
        plt.plot(ppm_axis, np.real(spectrum))

    plt.xlim(7, 6.6)
    plt.ylim(0, 1e5)
    plt.xlabel('ppm')
    plt.ylabel('Intensity')
    plt.title('NMR spectrum')
    plt.show()

    start_ppm = 6.90
    end_ppm = 6.65

    # peak integration
    integrals = []
    for ppm_axis, spectrum in zip(ppm_axis_ls, spectrum_ls):
        integral = peak_integration(ppm_axis, spectrum, start_ppm, end_ppm)
        integrals.append(integral)
    
    # conc = [484.48, 484.48/2, 484.48/4, 484.48/8, 484.48/16]

    # save the integrals and concentrations to a csv file
    import csv
    with open(path + '/conc_integral_Bs.csv', mode='w') as file:
        writer = csv.writer(file)
        writer.writerow(['Concentration(mM)', 'Integral'])
        for c, i in zip(spectrum_names, integrals):
            print(path)
            writer.writerow([c, round(i,2)])
            print(f"Concentration: {c}, Integral: {i}")

    # plot the integrals
    plt.plot(integrals, 'o')
    plt.xlabel('Spectrum number')
    plt.ylabel('Integral')
    plt.title('Integral of the peak')
    plt.show()