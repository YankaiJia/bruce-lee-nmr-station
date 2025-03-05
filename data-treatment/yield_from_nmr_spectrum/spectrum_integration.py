import nmrglue as ng
from nmrglue.analysis import peakpick
import numpy as np
import matplotlib.pyplot as plt
import os, csv

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


def read_spectra(path:str):
    print(f'path: {path}')
    # get all the subfolder in the path
    spectrum_folders = [f.path for f in os.scandir(path) if f.is_dir()]
    spectrum_folders = [f for f in spectrum_folders if '1D EXTENDED' in f]
    if not '_Refs' in path:
        # sort for data, not for references
        spectrum_folders.sort(key=lambda x: int(x.split('+-')[-1]))
    spectrum_names = [i.split('+-')[-1] for i in spectrum_folders]
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
    return dic_ls, data_ls, ppm_axis_ls, spectrum_ls, spectrum_names


def plot_spectrum(ppm_axis_ls, spectrum_ls):
    # plot the spectrum
    for ppm_axis, spectrum in zip(ppm_axis_ls, spectrum_ls):
        plt.plot(ppm_axis, np.real(spectrum))

    plt.xlim(9, 2)
    plt.ylim(0, 1e5)
    plt.xlabel('ppm')
    plt.ylabel('Intensity')
    plt.title('NMR spectrum')
    plt.show()

def integrate_a_peak(ppm_axis_ls, spectrum_ls, start_ppm, end_ppm):

    # peak integration
    integrals = []
    for ppm_axis, spectrum in zip(ppm_axis_ls, spectrum_ls):
        integral = peak_integration(ppm_axis, spectrum, start_ppm, end_ppm)
        integrals.append(integral)
    
    return integrals

def write_csv(csv_path, spectrum_names, integrals, time_taken_ls, header):
    with open(csv_path, mode='w') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        for c, i, t in zip(spectrum_names, integrals, time_taken_ls):
            # print(path)
            writer.writerow([c, round(i,2), t])
            print(f"Concentration: {c}, Integral: {i}, Time taken: {t}")

def get_time_gap(time_start, time_current):
        from datetime import datetime

        timestamp1_str = time_start
        timestamp2_str = time_current
        # Define the format that matches your timestamps
        fmt = '%Y-%m-%dT%H:%M:%S.%f'
        # Convert the string timestamps to datetime objects
        time1 = datetime.strptime(timestamp1_str, fmt)
        time2 = datetime.strptime(timestamp2_str, fmt)
        # Calculate the difference (a timedelta object)
        time_diff = time2 - time1
        # Convert the difference to total minutes
        time_diff_hours = time_diff.total_seconds() / 60 /60

        return time_diff_hours

if __name__ == "__main__":

    # get project_data_path from os variables
    # project_data_path = os.environ['BRUCELEE_PROJECT_DATA_PATH']
    # path_B_ref = project_data_path + "\\DPE_bromination\\_Refs\\ref_B"
    # path_S_ref = project_data_path + "\\DPE_bromination\\_Refs\\ref_S"
    # path_S_and_B = project_data_path + "\\DPE_bromination\\2025-02-19-run01_time_varied\\Results"

    # path = path_S_and_B
    # path = path_B_ref
    # path = path_S_ref

    # get spectrum folder path
    path = get_spectrum_path()
    
    dic_ls, data_ls, ppm_axis_ls, spectrum_ls, spectrum_names = read_spectra(path)
    plot_spectrum(ppm_axis_ls, spectrum_ls)

    # get measurement time of spectra
    time_stamp_ls = [dic['acqu']['startTime'] for dic in dic_ls]
    time_taken_ls = [get_time_gap(time_stamp_ls[0], time) for time in time_stamp_ls]
    print(time_taken_ls)
    

###################################################################################################

    ## for B refs
    integrals = integrate_a_peak(ppm_axis_ls, 
                                spectrum_ls, 
                                start_ppm = 6.95,
                                end_ppm = 6.65)
    conc = [484.48, 484.48/2, 484.48/4, 484.48/8, 484.48/16]
    spectrum_names = conc
    csv_path = os.path.join(path, 'integrals_S.csv')
    write_csv(csv_path, spectrum_names, integrals, header=['Concentration(mM)', 'Integral'])

###################################################################################################


    # ## for S refs
    # integrals_S_ref = integrate_a_peak(ppm_axis_ls, 
    #                             spectrum_ls, 
    #                             start_ppm = 5.8,
    #                             end_ppm = 5.1)
    # conc = [422.75, 422.75/2, 422.75/4, 422.75/8, 422.75/16]
    # spectrum_names = conc
    # ## save the integrals and concentrations to a csv file
    # csv_path = os.path.join(path, 'integrals_B.csv')
    # write_csv(csv_path, spectrum_names, integrals, header=['Concentration(mM)', 'Integral'])

###################################################################################################

    # ## for B of all specs
    # integrals = integrate_a_peak(ppm_axis_ls, 
    #                             spectrum_ls, 
    #                             start_ppm = 6.95,
    #                             end_ppm = 6.65)
    # # save the integrals and concentrations to a csv file
    # csv_path = os.path.join(path, 'integrals_B.csv')
    # write_csv(csv_path, 
    #         spectrum_names, 
    #         integrals,
    #         time_taken_ls, 
    #         header=['Spectrum_id', 'Integral', 'Time(hrs)'])

###################################################################################################

    ## for S of all specs
    # integrals_S = integrate_a_peak(ppm_axis_ls, 
    #                             spectrum_ls, 
    #                             start_ppm = 5.6,
    #                             end_ppm = 5.2)
    # ## save the integrals and concentrations to a csv file
    # csv_path = os.path.join(path, 'integrals_S.csv')
    # write_csv(csv_path, 
    #         spectrum_names, 
    #         integrals_S,
    #         time_taken_ls, 
    #         header=['Spectrum_id', 'Integral', 'Time(hrs)'])
    # integrals = integrals_S
###################################################################################################

    # plot the integrals
    plt.plot(spectrum_names, integrals, 'o')
    plt.xlabel('Spectrum number')
    plt.ylabel('Integral')
    plt.title('Integral of the peak')
    plt.show()