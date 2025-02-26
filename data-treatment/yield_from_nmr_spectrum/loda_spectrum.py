import nmrglue as ng
from nmrglue.analysis import peakpick
import numpy as np
import matplotlib.pyplot as plt
import os

peaks = None

def slice_roi_data(uc, data, low_ppm = 3.25, high_ppm = 4.50):
    
    # Convert ppm to integer point indices
    start_idx = int(uc.ppm_to_index(high_ppm))  # index for ~4.50 ppm
    stop_idx  = int(uc.ppm_to_index(low_ppm))   # index for ~3.25 ppm
    # Slice the data and create the corresponding ppm scale
    roi_data = data[start_idx:stop_idx]
    roi_ppm  = uc.ppm_scale()[start_idx:stop_idx]

    return roi_data, roi_ppm

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
    data_max = np.max(np.real(data)) # assume this is solvent peak
    idx_of_data_max = np.argmax(np.real(data))    
    ppm_of_data_max = ppm_axis[idx_of_data_max]

    real_ppm_of_CDE = 3.73
    idx_of_CDE = np.argmin(np.abs(ppm_axis - real_ppm_of_CDE))

    delta_points = idx_of_CDE - idx_of_data_max
    data = np.roll(data, delta_points)

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

if __name__ == "__main__":

    # get project_data_path from os variables
    # project_data_path = os.environ['BRUCELEE_PROJECT_DATA_PATH']
    # path = project_data_path + "\\DPE_bromination\\_Refs\\ref_B"

    # get spectrum folder path
    path = get_spectrum_path()

    # get all the subfolder in the path
    spectrum_folders = [f.path for f in os.scandir(path) if f.is_dir()]
    # sort the subfolders according to the last number in the folder name
    spectrum_folders.sort(key=lambda x: int(x[-1]))


    dic_ls, data_ls = [], []
    ppm_axis_ls, spectrum_ls = [], []
    for path in spectrum_folders:
    # read spectrum
        dic,data = ng.spinsolve.read(path)
        print(f"length of the spectrum: {data.shape[0]}")
        dic_ls.append(dic)
        data_ls.append(data)
        ppm_axis, spectrum = pre_porcessing(dic, data)
        ppm_axis_ls.append(ppm_axis)
        spectrum_ls.append(spectrum)

    # plot the spectrum
    for ppm_axis, spectrum in zip(ppm_axis_ls, spectrum_ls):
        plt.plot(ppm_axis, np.real(spectrum))

    plt.xlim(9, 0)
    plt.ylim(0, 2e5)
    plt.xlabel('ppm')
    plt.ylabel('Intensity')
    plt.title('NMR spectrum')
    plt.show()

