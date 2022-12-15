import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import pandas as pd
from scipy.signal import savgol_filter
from scipy import interpolate
from scipy.optimize import curve_fit

plt.ioff()

def load_msp_file(experimental_data_filename, cut=False):
    input_spectrum = np.loadtxt(experimental_data_filename, skiprows=10,
                                delimiter='\t')
    input_spectrum = np.transpose(input_spectrum)
    # input_spectrum_cut = np.flipud(input_spectrum)
    if cut:
        min_id = cut[0]
        max_id = cut[1]
        input_spectrum_cut = input_spectrum[min_id:max_id, :]
    return input_spectrum

def get_spectra_file_list(target_folder, prefix='spectrum_'):
    os.chdir(target_folder)
    file_list = glob.glob(f"{prefix}*.msp")
    file_list.remove(f'{prefix}-3D.msp') # this file contains the 2D map of absorbance at single fixed wavelength
    return file_list


def compare_to_spectrophotometer():
    data_folder = 'D:\\Docs\\Science\\UNIST\\Projects\\robochem\\data\\'
    experiment_folder = data_folder + 'multicomp-reactions\\2022-11-26-run01\\'
    spectra_folder = experiment_folder + 'microspectrometer_data\\timepoint_003\\'
    # compare to the true spectrim from the spectrophotometer
    plate_id = 1
    plate_folder = spectra_folder + f'plate-{plate_id:02d}\\'


    i = 0
    data = load_msp_by_id(plate_folder, i + 1)
    plt.plot(data[:, 0], data[:, 1], color='black', alpha=0.3)

    #load spectrophotometer data
    spectrophotometer_file = data_folder+\
                             'multicomp-reactions\\2022-11-26-run01\\spectrophotometer_data\\' \
                             'plate-01-last-bottom-right-well.csv'

    # data2 = np.genfromtxt(spectrophotometer_file, skip)
    df = pd.read_csv(spectrophotometer_file, skiprows=[0], nrows=600, usecols=[8, 9])
    # df = pd.read_csv(spectrophotometer_file, skiprows=[0], nrows=600, usecols=[2, 3])
    scalefactor = 1
    plt.plot(df.loc[:, 'Wavelength (nm).4'], scalefactor * (df.loc[:, 'Abs.4'] - df.loc[330, 'Abs.4']))
    # plt.plot(df.loc[:, 'Wavelength (nm).1'], scalefactor * (df.loc[:, 'Abs.1'] - df.loc[330, 'Abs.1']))

    plt.ylim(-0.1, 2)
    plt.show()

# compare_to_spectrophotometer()

# data_folder = 'D:\\Docs\\Science\\UNIST\\Projects\\robochem\\data\\'
# experiment_folder = data_folder + 'multicomp-reactions\\2022-12-07-run01\\'
# spectra_folder = experiment_folder + 'microspectrometer_data\\timepoint_001\\'
# for plate_id in [1, 2, 3]:
#     plate_folder = spectra_folder + f'plate-{plate_id:02d}\\'
#     show_all_spectra(plate_folder)
# plt.show()

def compare_chroma_bandpass():
    data_folder = 'D:\\Docs\\Science\\UNIST\\Projects\\robochem\\data\\'
    experiment_folder = data_folder + 'multicomp-reactions\\2022-11-26-run01\\'
    # spectra_folder = experiment_folder + 'microspectrometer_data\\timepoint_003\\'
    # compare to the true spectrim from the spectrophotometer
    # plate_id = 1
    # plate_folder = spectra_folder + f'plate-{plate_id:02d}\\'


    i = 0
    data = load_msp_file(experimental_data_filename=experiment_folder + 'microspectrometer_data\\calibration'
                                                                        '\\2022-11-30\\enchroma_tests\\enchroma-flat-1.msp')
    plt.plot(data[:, 0], data[:, 1], color='black', alpha=1, label='CRAIC')

    #load spectrophotometer data
    spectrophotometer_file = data_folder+\
                         'multicomp-reactions\\2022-11-26-run01\\spectrophotometer_data' \
                         '\\2022-11-30\\enchroma-flat.csv'

    # data2 = np.genfromtxt(spectrophotometer_file, skip)
    # df = pd.read_csv(spectrophotometer_file, skiprows=[0], nrows=600, usecols=[8, 9])
    df = pd.read_csv(spectrophotometer_file, skiprows=[0], nrows=600, usecols=[2, 3])
    scalefactor = 1
    # plt.plot(df.loc[:, 'Wavelength (nm).4'], scalefactor * (df.loc[:, 'Abs.4'] - df.loc[330, 'Abs.4']))
    plt.plot(df.loc[:, 'Wavelength (nm).1'], scalefactor * (df.loc[:, 'Abs.1'] - df.loc[330, 'Abs.1']),
             label='Ground truth (Agilent)')

    # plt.ylim(-0.1, 2)
    plt.ylabel('Absorbance')
    plt.xlabel('Wavelength, nm')
    plt.legend()
    plt.show()

def construct_calibration_interpolators():
    nd_names =      [0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0, 3.5, 4.0]
    nd_names_used = [0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 1.2, 1.5, 1.8,      2.5, 3.0, 3.5, 4.0]
    microspec_folder = 'uv-vis-absorption-spectroscopy/microspectrometer-calibration/2022-12-01/2-inch-nd-calibrations'
    microspec_absorbances = dict()

    example_data = load_msp_file(experimental_data_filename=microspec_folder +
                                                            f'/{nd_names_used[0]:.1f}'.replace('.', 'p') + '.msp')
    craic_data = [np.zeros_like(example_data[:, 1])]
    for nd_name in nd_names_used:
        data = load_msp_file(experimental_data_filename=microspec_folder + f'/{nd_name:.1f}'.replace('.', 'p') + '.msp')
        # plt.plot(data[:, 0], data[:, 1], color='blue', alpha=0.5, label='CRAIC')
        data[:, 1] = savgol_filter(data[:, 1], window_length=31, polyorder=2)
        microspec_absorbances[nd_name] = data[:, 1]
        wavelengths = data[:, 0]
        craic_data.append(data[:, 1])
    craic_data = np.stack(craic_data)

    spectrophotometer_file = 'uv-vis-absorption-spectroscopy/spectrophotometer-references/' \
                             '2-inch-nd-filters/nd-filters.csv'
    df = pd.read_csv(spectrophotometer_file, skiprows=[0], nrows=451)
    wavelengths_agilent = df.loc[:, 'Wavelength (nm)']
    agilent_data = [np.zeros_like(example_data[:, 1])]
    for nd_name in nd_names_used:
        absorbances_agilent = df.loc[:, f'Abs.{nd_names.index(nd_name) + 2}']
        absorbances_agilent = savgol_filter(absorbances_agilent, window_length=7, polyorder=2)
        agilent_interpolator = interpolate.interp1d(wavelengths_agilent, absorbances_agilent)
        agilent_data.append(agilent_interpolator(wavelengths))
    agilent_data = np.stack(agilent_data)

    for wavelength_id, wavelength in enumerate(wavelengths):
        agilent_here = np.copy(agilent_data[:, wavelength_id])
        craic_here = np.copy(craic_data[:, wavelength_id])
        sorting_ids = craic_here.argsort()
        agilent_here = agilent_here[sorting_ids]
        craic_here = craic_here[sorting_ids]
        # agilent_here = np.insert(agilent_here, 0, 0)
        # craic_here = np.insert(craic_here, 0, 0)
        agilent_data[:, wavelength_id] = np.copy(agilent_here)
        craic_data[:, wavelength_id] = np.copy(craic_here)

    np.save('uv-vis-absorption-spectroscopy/microspectrometer-calibration/2022-12-01/interpolator-dataset/'
            'craic_data.npy', craic_data)
    np.save('uv-vis-absorption-spectroscopy/microspectrometer-calibration/2022-12-01/interpolator-dataset/'
            'agilent_data.npy', agilent_data)


def load_calibration(target_folder='uv-vis-absorption-spectroscopy/microspectrometer-calibration/'
                                   '2022-12-01/interpolator-dataset/'):
    craic_data = np.load(target_folder + 'craic_data.npy')
    agilent_data = np.load(target_folder + 'agilent_data.npy')
    return [craic_data, agilent_data]

def apply_correction(input_craic_spectrum, calibration_dataset):
    craic_data, agilent_data = calibration_dataset
    result = np.zeros_like(input_craic_spectrum)
    for wavelength_id in range(input_craic_spectrum.shape[0]):
        f = interpolate.interp1d(craic_data[:, wavelength_id], agilent_data[:, wavelength_id],
                                 fill_value='extrapolate')
        result[wavelength_id] = f(input_craic_spectrum[wavelength_id])
    return result


def compare_chroma_bandpass():
    calibration_dataset = load_calibration()
    data_folder = 'D:\\Docs\\Science\\UNIST\\Projects\\robochem\\data\\'
    experiment_folder = data_folder + 'multicomp-reactions\\2022-11-26-run01\\'
    # spectra_folder = experiment_folder + 'microspectrometer_data\\timepoint_003\\'
    # compare to the true spectrim from the spectrophotometer
    # plate_id = 1
    # plate_folder = spectra_folder + f'plate-{plate_id:02d}\\'


    i = 0
    data = load_msp_file(experimental_data_filename=experiment_folder + 'microspectrometer_data\\calibration'
                                                                        '\\2022-11-30\\enchroma_tests\\enchroma-flat-2.msp')
    #load_msp_by_id(plate_folder, i + 1)
    corrected_craic = apply_correction(data[:, 1], calibration_dataset)
    plt.plot(data[:, 0], data[:, 1], color='black', alpha=0.5, label='CRAIC')
    plt.plot(data[:, 0], corrected_craic, color='red', alpha=0.5, label='corrected CRAIC')

    #load spectrophotometer data
    spectrophotometer_file = data_folder+\
                         'multicomp-reactions\\2022-11-26-run01\\spectrophotometer_data' \
                         '\\2022-11-30\\enchroma-flat.csv'

    # data2 = np.genfromtxt(spectrophotometer_file, skip)
    # df = pd.read_csv(spectrophotometer_file, skiprows=[0], nrows=600, usecols=[8, 9])
    df = pd.read_csv(spectrophotometer_file, skiprows=[0], nrows=600, usecols=[2, 3])
    scalefactor = 1
    # plt.plot(df.loc[:, 'Wavelength (nm).4'], scalefactor * (df.loc[:, 'Abs.4'] - df.loc[330, 'Abs.4']))
    plt.plot(df.loc[:, 'Wavelength (nm).1'], scalefactor * (df.loc[:, 'Abs.1'] - df.loc[330, 'Abs.1']),
             label='Ground truth (Agilent)')

    # plt.ylim(-0.1, 2)
    plt.ylabel('Absorbance')
    plt.xlabel('Wavelength, nm')
    plt.legend()
    plt.show()

construct_calibration_interpolators()
# compare_chroma_bandpass()
calibration_dataset = load_calibration()

def well_id_to_file_id(well_id):
    '''Microspectrometer scans from bottom right corner. Each scan line goes up. Next scan line is to the left
    of the previous one. Well id is counted from top left corner in left-to-right lines, each next line below
    the previous one.'''
    # well_id to i,j. Index i is left-to-right. Index j is top-to-bottom. Both start from zero.
    j = well_id // 9
    i = well_id % 9

    # i,j to file_id
    file_id = (8 - i) * 6 + (5 - j) + 1 # plus one because file id is counted from one, not from zero
    return file_id

# for well_id in [0, 9, 53, 30]:
#     print(f'{well_id} -> {well_id_to_file_id(well_id)}')

def load_msp_by_id(plate_folder, well_id, prefix='spectrum_', do_correction=True,
                   calibration_dataset=calibration_dataset):
    data = load_msp_file(plate_folder + prefix + f'-{well_id_to_file_id(well_id)}.msp')
    if do_correction:
        data[:, 1] = apply_correction(data[:, 1], calibration_dataset=calibration_dataset)
    return data


def load_all_spectra(plate_folder, prefix='spectrum_-'):
    filelist = get_spectra_file_list(plate_folder)
    return [load_msp_by_id(plate_folder, i) for i in range(len(filelist))]


def show_all_spectra(plate_folder, prefix='spectrum_-'):
    for well_id, data in enumerate(load_all_spectra(plate_folder, prefix=prefix)):
        plt.plot(data[:, 0], data[:, 1], alpha=0.3, label=f'{well_id}')
        print(f'{well_id}: max {np.max(data[:, 1])}')
    plt.ylabel('Absorbance')
    plt.xlabel('Wavelength, nm')
    # plt.show()

# def construct_reference():
def construct_product_reference(
        data_folder,
        reference_folder,
        save_bkg_to,
        well_concentrations,
        bkg_well_id,
        ref_spectrum_id):
    reference_folder = data_folder + reference_folder
    # show_all_spectra(reference_folder)
    all_spectra = load_all_spectra(reference_folder)

    # for well_id, data in enumerate(all_spectra):
    #     if well_id >= 19 and well_id <= 25:
    #         plt.plot(data[:, 0], data[:, 1], alpha=0.3, label=f'{well_id}')
    # plt.ylabel('Absorbance')
    # plt.xlabel('Wavelength, nm')
    # plt.legend()
    # plt.show()

    # concentration in mol/L

    ref_spectrum = all_spectra[ref_spectrum_id][:, 1] - all_spectra[bkg_well_id][:, 1]
    wavelength_indices = np.arange(ref_spectrum.shape[0])
    reference_interpolator = interpolate.interp1d(wavelength_indices, ref_spectrum, fill_value='extrapolate')
    # baseline_interpolator = interpolate.interp1d(reference_wavelengths, baseline,
    #                                              fill_value='extrapolate')
    coeffs = []
    coeff_errs = []
    concentrations = []
    for well_id in well_concentrations.keys():
        concentrations.append(well_concentrations[well_id])
        target_spectrum = all_spectra[well_id][:, 1] - all_spectra[bkg_well_id][:, 1]
        def func(xs, a, b):
            return a*reference_interpolator(xs) + b
        p0 = (0.5, 0)
        bounds = ([0, -np.inf], [np.inf, np.inf])
        popt, pcov = curve_fit(func, wavelength_indices, target_spectrum,
                               p0=p0, bounds=bounds)
                               # sigma=noise_std*np.ones_like(target_spectrum),
                               # absolute_sigma=True)
        perr = np.sqrt(np.diag(pcov))
        slope = popt[0]
        slope_error = perr[0]
        coeffs.append(slope)
        coeff_errs.append(slope_error)


    coeff_to_concentration_interpolator = interpolate.interp1d(coeffs, concentrations,
                                                               fill_value='extrapolate')
    np.save(save_bkg_to, all_spectra[bkg_well_id])
    return coeff_to_concentration_interpolator, reference_interpolator, all_spectra[bkg_well_id]


def construct_product_reference_2(
        data_folder,
        reference_folder,
        save_bkg_to,
        well_concentrations,
        bkg_well_id,
        ref_spectrum_id,
        do_plot=True):
    reference_folder = data_folder + reference_folder
    # show_all_spectra(reference_folder)
    all_spectra = load_all_spectra(reference_folder)

    # if do_plot:
    #     for well_id, data in enumerate(all_spectra):
    #         if well_id >= 45:# 37:
    #             plt.plot(data[:, 0], data[:, 1] - all_spectra[bkg_well_id][:, 1], alpha=0.3, label=f'{well_id}')
    #     plt.ylabel('Absorbance')
    #     plt.xlabel('Wavelength, nm')
    #     plt.legend()
    #     plt.show()

    # concentration in mol/L

    ref_spectrum = all_spectra[ref_spectrum_id][:, 1] - all_spectra[bkg_well_id][:, 1]
    wavelength_indices = np.arange(ref_spectrum.shape[0])
    reference_interpolator = interpolate.interp1d(wavelength_indices, ref_spectrum, fill_value='extrapolate')
    # baseline_interpolator = interpolate.interp1d(reference_wavelengths, baseline,
    #                                              fill_value='extrapolate')

    # threshold_function
    # thresh_ws =        [350,  361,  406,  800]
    thresh_w_indices = [0,    25,   127, 2000]
    thresh_as =        [0.67, 0.75, 1.6,  1.6]
    threshold_interpolator = interpolate.interp1d(thresh_w_indices, thresh_as, fill_value='extrapolate')

    def refine_reference(cut_from = 400, well_id = 51, do_plot=False):
        target_spectrum = all_spectra[well_id][:, 1] - all_spectra[bkg_well_id][:, 1]
        mask = np.logical_and(target_spectrum < threshold_interpolator(wavelength_indices), wavelength_indices > cut_from)

        def func(xs, a, b):
            return a * reference_interpolator(xs) + b

        p0 = (0.5, 0)
        bounds = ([0, -np.inf], [np.inf, np.inf])
        popt, pcov = curve_fit(func, wavelength_indices[mask], target_spectrum[mask],
                               p0=p0, bounds=bounds)
        # sigma=noise_std*np.ones_like(target_spectrum),
        # absolute_sigma=True)
        perr = np.sqrt(np.diag(pcov))
        slope = popt[0]
        slope_error = perr[0]

        new_ref_spectrum = np.copy(ref_spectrum)
        new_ref_spectrum[mask] = (target_spectrum[mask] - popt[1]) / slope

        if do_plot:
            plt.plot(target_spectrum, label='data', color='C0', alpha=0.5)

            mask_illustration = np.ones_like(target_spectrum) * 4
            mask_illustration[mask] = 0
            plt.fill_between(x=wavelength_indices, y1=0, y2=mask_illustration, color='yellow', alpha=0.3)
            plt.plot(func(wavelength_indices, *popt), color='r', label='fit', alpha=0.5)
            plt.plot(func(wavelength_indices, popt[0], 0), color='C1', label='reference', alpha=0.5)
            plt.title(f'{well_id}')
            plt.legend()
            plt.show()

            plt.title(f'Refined reference, well {well_id} was used')
            plt.plot(new_ref_spectrum, color='black', alpha=0.5)
            plt.plot(ref_spectrum, color='C0', alpha=0.5)
            plt.show()

        return new_ref_spectrum, interpolate.interp1d(wavelength_indices, new_ref_spectrum, fill_value='extrapolate')

    ref_spectrum, reference_interpolator = refine_reference(cut_from=400, well_id=51)
    ref_spectrum, reference_interpolator = refine_reference(cut_from=486, well_id=50)
    ref_spectrum, reference_interpolator = refine_reference(cut_from=540, well_id=48)
    ref_spectrum, reference_interpolator = refine_reference(cut_from=581, well_id=46)

    cut_from = 115
    coeffs = []
    coeff_errs = []
    concentrations = []
    for well_id in well_concentrations.keys():
        concentrations.append(well_concentrations[well_id])
        target_spectrum = all_spectra[well_id][:, 1] - all_spectra[bkg_well_id][:, 1]
        mask = np.logical_and(target_spectrum < threshold_interpolator(wavelength_indices), wavelength_indices > cut_from)

        def func(xs, a, b):
            return a*reference_interpolator(xs) + b
        p0 = (0.5, 0)
        bounds = ([0, -np.inf], [np.inf, np.inf])
        popt, pcov = curve_fit(func, wavelength_indices[mask], target_spectrum[mask],
                               p0=p0, bounds=bounds)
                               # sigma=noise_std*np.ones_like(target_spectrum),
                               # absolute_sigma=True)
        perr = np.sqrt(np.diag(pcov))
        slope = popt[0]
        slope_error = perr[0]
        coeffs.append(slope)
        coeff_errs.append(slope_error)

        if do_plot:
            plt.plot(target_spectrum, label='data', color='C0', alpha=0.5)
            mask_illustration = np.ones_like(target_spectrum) * np.max(target_spectrum)
            mask_illustration[mask] = 0
            plt.fill_between(x=wavelength_indices, y1=0, y2=mask_illustration, color='yellow', alpha=0.3)
            plt.plot(func(wavelength_indices, *popt), color='r', label='fit', alpha=0.5)
            plt.plot(func(wavelength_indices, popt[0], 0), color='C1', label='reference', alpha=0.5)
            plt.title(f'{well_id}')
            plt.legend()
            plt.show()

    if do_plot:
        plt.loglog(coeffs, concentrations, 'o-')
        plt.show()
    coeff_to_concentration_interpolator = interpolate.interp1d(coeffs, concentrations,
                                                               fill_value='extrapolate')
    np.save(save_bkg_to, all_spectra[bkg_well_id])
    return coeff_to_concentration_interpolator, reference_interpolator, all_spectra[bkg_well_id]
# plt.plot(concentrations, coeffs, 'o-')
# plt.show()

# if __name__ == '__main__':

def process_spectra_to_concentrations(timepoint, plate_id, run_name='2022-12-07-run01',
                                      results_excel_file='multicomp-reactions\\2022-12-07-run01\\results\\v6.xlsx'):
    coeff_to_concentration_interpolator, reference_interpolator, bkg_spectrum = \
        construct_product_reference(
            data_folder='D:\\Docs\\Science\\UNIST\\Projects\\robochem\\data\\',
            reference_folder='multicomp-reactions\\2022-12-07-run01\\microspectrometer_data\\calibration\\' \
                             'product-calibration\\run-01\\',
            save_bkg_to='D:\\Docs\\Science\\UNIST\\Projects\\robochem\\data\\multicomp-reactions\\'
                        '2022-12-07-run01\\microspectrometer_data\\calibration\\bkg_spectrum.npy',
            well_concentrations= \
                {  # 19: 0.000912785,
                    20: 0.000547671,
                    21: 0.000182557,
                    22: 9.12785E-05,
                    23: 3.65114E-05,
                    24: 9.12785E-06,
                    25: 0},
            bkg_well_id=25,
            ref_spectrum_id=21)

    data_folder = 'D:\\Docs\\Science\\UNIST\\Projects\\robochem\\data\\'
    experiment_folder = data_folder + f'multicomp-reactions\\{run_name}\\' \
                                      f'microspectrometer_data\\timepoint_{timepoint:03d}\\'
    plate_folder = experiment_folder + f'plate-{plate_id:02d}\\'
    # show_all_spectra(plate_folder)
    bkg_2_id = 2
    datas = load_all_spectra(plate_folder=plate_folder)
    wavelength_indices = np.arange(datas[0].shape[0])
    baseline_2_interpolator = interpolate.interp1d(wavelength_indices, datas[bkg_2_id][:, 1],
                                                 fill_value='extrapolate')

    target_concentrations = []
    target_concentration_errors = []
    target_concentration_relerrors = []
    unmixing_errors = []
    from_id = 125
    to_id = 600 # len(wavelength_indices)

    for plate_id in [1, 2]:
        plate_folder = experiment_folder + f'plate-{plate_id:02d}\\'
        datas = load_all_spectra(plate_folder=plate_folder)
        for well_id, data in enumerate(datas):
            target_spectrum = data[:, 1] - bkg_spectrum[:, 1]

            def func(xs, a, b, c):
                return a * reference_interpolator(xs) + b*baseline_2_interpolator(xs) + c

            p0 = (0.5, 0, 0)
            bounds = ([0, -np.inf, -np.inf], [np.inf, np.inf, np.inf])
            popt, pcov = curve_fit(func,
                                   wavelength_indices[from_id:to_id],
                                   target_spectrum[from_id:to_id],
                                   p0=p0, bounds=bounds)
            # sigma=noise_std*np.ones_like(target_spectrum),
            # absolute_sigma=True)
            perr = np.sqrt(np.diag(pcov))
            slope = popt[0]
            slope_error = perr[0]
            concentration_error = (coeff_to_concentration_interpolator(slope + slope_error) - \
                                  coeff_to_concentration_interpolator(slope - slope_error) ) / 2
            target_concentrations.append(coeff_to_concentration_interpolator(slope))
            target_concentration_errors.append(concentration_error)
            target_concentration_relerrors.append(concentration_error / coeff_to_concentration_interpolator(slope))
            unmixing_errors.append(np.mean(np.abs(func(wavelength_indices[from_id:to_id], *popt) - target_spectrum[from_id:to_id])))
            # plt.plot(target_spectrum, label='data', color='C0', alpha=0.5)
            # plt.plot(func(wavelength_indices, *popt), color='r', label='fit', alpha=0.5)
            # plt.plot(func(wavelength_indices, popt[0], 0, 0), color='C1', label='product', alpha=0.5)
            # plt.legend()
            # plt.show()

    target_concentrations = np.array(target_concentrations)
    target_concentration_errors = np.array(target_concentration_errors)
    target_concentration_relerrors = np.array(target_concentration_relerrors)
    unmixing_errors = np.array(unmixing_errors)
    dataset = pd.DataFrame({'Product concentration (mol/L)': target_concentrations,
                            'Absolute standard error (mol/L)': target_concentration_errors,
                            'Unmixing error (a.u.)': unmixing_errors})
    dataset.to_excel(data_folder + results_excel_file)




def process_spectra_to_concentrations_2(timepoint, plate_id, run_name='2022-12-07-run01',
                                      results_excel_file='multicomp-reactions\\2022-12-07-run01\\results\\v6.xlsx',
                                        do_plot=True):

    coeff_to_concentration_interpolator, reference_interpolator, bkg_spectrum = \
        construct_product_reference_2(
            data_folder='D:\\Docs\\Science\\UNIST\\Projects\\robochem\\data\\',
            reference_folder='multicomp-reactions\\2022-12-14-run01\\microspectrometer_data\\'
                             'calibration\\product_calibration\\product_calibration_100uLdeep\\',
            save_bkg_to='D:\\Docs\\Science\\UNIST\\Projects\\robochem\\data\\multicomp-reactions\\'
                        '2022-12-14-run01\\microspectrometer_data\\calibration\\bkg_spectrum.npy',
            well_concentrations= \
                {46: 0.730227634,
                 47: 0.584182107,
                 48: 0.43813658,
                 49: 0.273835363,
                 50: 0.146045527,
                 51: 0.036511382,
                 52: 0.018255691,
                 53: 0.003651138,
                 19 + 18: 0.000912785,
                 20 + 18: 0.000547671,
                 21 + 18: 0.000182557,
                 22 + 18: 9.12785E-05,
                 23 + 18: 3.65114E-05,
                 24 + 18: 9.12785E-06,
                 25 + 18: 0},
            bkg_well_id=25 + 18,
            ref_spectrum_id=53, do_plot=False)

    data_folder = 'D:\\Docs\\Science\\UNIST\\Projects\\robochem\\data\\'
    experiment_folder = data_folder + f'multicomp-reactions\\{run_name}\\' \
                                      f'microspectrometer_data\\timepoint_{timepoint:03d}\\'
    plate_folder = experiment_folder + f'plate-{plate_id:02d}\\'
    # show_all_spectra(plate_folder)
    bkg_2_id = 5 # 29 # 45 38
    datas = load_all_spectra(plate_folder=plate_folder)

    # if do_plot:
    #     for well_id, data in enumerate(datas):
    #         if (well_id >= 27 and well_id<=36) or well_id == 38 or well_id == 45:
    #             plt.plot(data[:, 0], data[:, 1] - bkg_spectrum[:, 1], alpha=0.3, label=f'{well_id}')
    #     plt.ylabel('Absorbance')
    #     plt.xlabel('Wavelength, nm')
    #     plt.legend()
    #     plt.show()


    wavelength_indices = np.arange(datas[0].shape[0])
    baseline_2_interpolator = interpolate.interp1d(wavelength_indices, datas[bkg_2_id][:, 1] - bkg_spectrum[:, 1],
                                                 fill_value='extrapolate')

    thresh_w_indices = [0,    25,   127, 2000]
    thresh_as =        [0.67, 0.75, 1.6,  1.6]
    threshold_interpolator = interpolate.interp1d(thresh_w_indices, thresh_as, fill_value='extrapolate')
    target_concentrations = []
    target_concentration_errors = []
    target_concentration_relerrors = []
    unmixing_errors = []
    cut_from = 115
    # to_id = 600 # len(wavelength_indices)

    for plate_id in [1, 2]:
        plate_folder = experiment_folder + f'plate-{plate_id:02d}\\'
        datas = load_all_spectra(plate_folder=plate_folder)
        for well_id, data in enumerate(datas):
            target_spectrum = data[:, 1] - bkg_spectrum[:, 1]

            def func(xs, a, b, c):
                return a * reference_interpolator(xs) + b*baseline_2_interpolator(xs) + c

            mask = np.logical_and(target_spectrum < threshold_interpolator(wavelength_indices),
                                  wavelength_indices > cut_from)

            p0 = (0.5, 0, 0)
            bounds = ([0, -np.inf, -np.inf], [np.inf, np.inf, np.inf])
            popt, pcov = curve_fit(func,
                                   wavelength_indices[mask],
                                   target_spectrum[mask],
                                   p0=p0, bounds=bounds)
            # sigma=noise_std*np.ones_like(target_spectrum),
            # absolute_sigma=True)
            perr = np.sqrt(np.diag(pcov))
            slope = popt[0]
            slope_error = perr[0]
            concentration_error = (coeff_to_concentration_interpolator(slope + slope_error) - \
                                  coeff_to_concentration_interpolator(slope - slope_error) ) / 2
            target_concentrations.append(coeff_to_concentration_interpolator(slope))
            target_concentration_errors.append(concentration_error)
            target_concentration_relerrors.append(concentration_error / coeff_to_concentration_interpolator(slope))
            unmixing_errors.append(np.mean(np.abs(func(wavelength_indices[mask], *popt) - target_spectrum[mask])))
            if do_plot:
                plt.plot(target_spectrum, label='data', color='C0', alpha=0.5)
                plt.plot(func(wavelength_indices, *popt), color='r', label='fit', alpha=0.5)
                plt.plot(func(wavelength_indices, popt[0], 0, 0), color='C1', label='product', alpha=0.5)
                mask_illustration = np.ones_like(target_spectrum) * np.max(target_spectrum)
                mask_illustration[mask] = 0
                plt.fill_between(x=wavelength_indices, y1=0, y2=mask_illustration, color='yellow', alpha=0.3)
                plt.title(f'Well {well_id}')
                plt.legend()
                plt.show()

    target_concentrations = np.array(target_concentrations)
    target_concentration_errors = np.array(target_concentration_errors)
    target_concentration_relerrors = np.array(target_concentration_relerrors)
    unmixing_errors = np.array(unmixing_errors)
    dataset = pd.DataFrame({'Product concentration (mol/L)': target_concentrations,
                            'Absolute standard error (mol/L)': target_concentration_errors,
                            'Unmixing error (a.u.)': unmixing_errors})
    dataset.to_excel(data_folder + results_excel_file)
    return target_concentrations


data_folder = 'D:\\Docs\\Science\\UNIST\\Projects\\robochem\\data\\'

product_concentrations_vs_time = []
for timepoint in [1,2,3,4,5]:
    product_concentrations = process_spectra_to_concentrations_2(timepoint, plate_id=1, run_name='2022-12-14-run01',
                                            results_excel_file=f'multicomp-reactions\\2022-12-14-run01\\results\\v7_timepoint{timepoint}.xlsx',
                                        do_plot=False)
    product_concentrations_vs_time.append(product_concentrations)

product_concentrations_vs_time = np.array(product_concentrations_vs_time)
np.save(data_folder + 'multicomp-reactions\\2022-12-14-run01\\results\\product_vs_time.npy', product_concentrations_vs_time)


dataset = pd.DataFrame({f'Product (mol/L) at timepoint {timepoint}': product_concentrations_vs_time[timepoint-1] for timepoint in [1,2,3,4,5]})
dataset.to_excel(data_folder + 'multicomp-reactions\\2022-12-14-run01\\results\\v7_product_vs_time.xlsx')

    # plt.plot(data[:, 0], data[:, 1])
# plt.legend()
# plt.show()


# construct_reference()
# data_folder = 'D:\\Docs\\Science\\UNIST\\Projects\\robochem\\data\\'
# experiment_folder = data_folder + 'multicomp-reactions\\2022-12-07-run01\\'
# spectra_folder = experiment_folder + 'microspectrometer_data\\timepoint_001\\'
# for plate_id in [1, 2, 3]:
#     plate_folder = spectra_folder + f'plate-{plate_id:02d}\\'
#     show_all_spectra(plate_folder)
# plt.show()

# nd_index = 0
# plt.plot(wavelengths, agilent_data[nd_index], label='agilent')
# plt.plot(wavelengths, craic_data[nd_index], label='craic')
# plt.legend()
# plt.show()
# df = pd.read_csv(spectrophotometer_file, skiprows=[0], nrows=600, usecols=[2, 3])
# scalefactor = 1
# # plt.plot(df.loc[:, 'Wavelength (nm).4'], scalefactor * (df.loc[:, 'Abs.4'] - df.loc[330, 'Abs.4']))
# plt.plot(df.loc[:, 'Wavelength (nm).1'], scalefactor * (df.loc[:, 'Abs.1'] - df.loc[330, 'Abs.1']),
#          label='Ground truth (Agilent)')
#
# # plt.ylim(-0.1, 2)
# plt.ylabel('Absorbance')
# plt.xlabel('Wavelength, nm')
# plt.legend()
# plt.show()