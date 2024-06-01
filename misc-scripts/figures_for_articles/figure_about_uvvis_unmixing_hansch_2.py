import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import importlib
from scipy import interpolate
import matplotlib.text as mtext
from scipy.optimize import curve_fit
import statsmodels.api as sm

process_wellplate_spectra = importlib.import_module("uv-vis-absorption-spectroscopy.process_wellplate_spectra")
data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'

def simpleaxis(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()


def multispectrum_to_concentration_local(sp, target_spectrum_inputs, calibration_folder, calibrant_shortnames,
                                  background_model_folder, dilution_factors,
                                  upper_limit_of_absorbance=1000, fig_filename='temp', do_plot=False, #lower_limit_of_absorbance=0.02
                                  upper_bounds=[np.inf, np.inf], use_line=False, cut_from = 200, ignore_abs_threshold=False,
                                  cut_to = False, ignore_pca_bkg=False, return_errors=False,
                                       use_linear_calibration=True, plot_calibrant_references=False,
                                       return_report=False,
                                         color_sequence=None): #upper_bounds=[np.inf, np.inf]
        calibrants = []
        for calibrant_shortname in calibrant_shortnames:
            dict_here = dict()
            dict_here['coeff_to_concentration_interpolator'], dict_here['reference_interpolator'], dict_here[
                'bkg_spectrum'] = \
                sp.load_calibration_for_one_calibrant(calibrant_shortname, calibration_folder,
                                                        use_line_fit=use_linear_calibration,
                                                        do_savgol_filtering=False)
            dict_here['concentration_to_coeff_interpolator'], _, _ = \
                sp.load_concentration_to_coeff_for_one_calibrant(calibrant_shortname, calibration_folder,
                                                                     use_line_fit=use_linear_calibration)
            calibrants.append(dict_here.copy())

        if plot_calibrant_references:
            for i, calibrant in enumerate(calibrants):
                plt.plot(220+np.linspace(0, 400, 400), calibrant['reference_interpolator'](np.linspace(0, 400, 400)),
                         label=calibrant_shortnames[i])
            plt.legend()
            plt.xlabel('Wavelength, nm')
            plt.ylabel('Absorbance')
            plt.show()

        bkg_spectrum = np.mean(np.array([calibrant['bkg_spectrum'] for calibrant in calibrants]), axis=0)
        for target_spectrum_input in target_spectrum_inputs:
            assert len(bkg_spectrum) == len(target_spectrum_input), \
                'Length of background spectrum is not the same as the length of the target spectrum.' \
                'This may be because the wavelengths are not aligned.'

        wavelengths = bkg_spectrum[:, 0]
        target_spectra = [target_spectrum_input - bkg_spectrum[:, 1] for target_spectrum_input in target_spectrum_inputs]
        wavelength_indices = np.arange(calibrants[0]['bkg_spectrum'].shape[0])

        target_spectra_wavelength_indices_masked = []
        target_spectra_amplitudes_masked = []
        for i, target_spectrum in enumerate(target_spectra):
            target_spectrum_wavelengths_masked, target_spectrum_amplitudes_masked = sp.mask_multispectrum(
                wavelength_indices, target_spectrum, cut_from, upper_limit_of_absorbance=upper_limit_of_absorbance, cut_to=cut_to)
            target_spectra_wavelength_indices_masked.append(target_spectrum_wavelengths_masked)
            target_spectra_amplitudes_masked.append(target_spectrum_amplitudes_masked)

            if len(target_spectrum_wavelengths_masked) == 0:
                print(f'There is no data that is within mask for spectrum #{i}. Returning zeros.')
                return [0 for i in range(len(calibrant_shortnames))]


        comboX = np.concatenate(target_spectra_wavelength_indices_masked)
        comboY = np.concatenate(target_spectra_amplitudes_masked)
        # sigmas is based on dilution factors
        # combo_sigmas = np.concatenate([np.ones_like(target_spectrum_amplitudes_masked) * np.sqrt(dilution_factor)
        #                                 for target_spectrum_amplitudes_masked, dilution_factor in
        #                                 zip(target_spectra_amplitudes_masked, dilution_factors)])

        indices_for_splitting = np.cumsum([len(target_spectrum_wavelengths_masked) for target_spectrum_wavelengths_masked in target_spectra_wavelength_indices_masked])[:-1]
        number_of_calibrants = len(calibrant_shortnames)
        number_of_spectra = len(target_spectrum_inputs)

        if not ignore_pca_bkg:
            background_interpolators = [interpolate.interp1d(wavelength_indices,
                                                          np.load(background_model_folder + f'component_{i}.npy'),
                                                          fill_value='extrapolate')
                                     for i in range(2)]
        else:
            background_interpolators = [interpolate.interp1d(wavelength_indices,
                                                             np.ones_like(wavelength_indices),
                                                             fill_value='extrapolate')
                                        for i in range(2)]

        def func(*args):
            xs = args[0]
            separate_spectra = np.split(xs, indices_for_splitting)
            calibrants_concentrations = args[1:number_of_calibrants + 1]
            dilutions_factors_here = [dilution_factors[0]] + list(args[number_of_calibrants + 1: number_of_calibrants + 1 + number_of_spectra - 1])
            assert len(dilutions_factors_here) == number_of_spectra
            offsets = args[number_of_calibrants + 1 + number_of_spectra - 1: number_of_calibrants + 1 + number_of_spectra - 1 + number_of_spectra]
            separate_predicted_spectra = []
            for spectrum_index, wavelengths in enumerate(separate_spectra):
                dilution_factor_for_this_spectrum = dilutions_factors_here[spectrum_index]
                calibrants_concentrations_for_this_spectrum = [x / dilution_factor_for_this_spectrum for x in calibrants_concentrations]
                calibrants_coeffs_for_this_spectrum = [np.asscalar(calibrants[i]['concentration_to_coeff_interpolator'](calibrants_concentrations_for_this_spectrum[i]))
                                                       for i in range(number_of_calibrants)]
                predicted_spectrum = sum([calibrants_coeffs_for_this_spectrum[i] * calibrants[i]['reference_interpolator'](wavelengths)
                                            for i in range(number_of_calibrants)]) \
                                        + offsets[spectrum_index]
                separate_predicted_spectra.append(predicted_spectrum)
            comboY = np.concatenate(separate_predicted_spectra)
            return comboY

        p0 = []
        lower_bounds = []
        upper_bounds = []
        for i in range(number_of_calibrants):
            p0.append(1e-3)
            lower_bounds.append(0)
            upper_bounds.append(np.inf)
        for i in range(number_of_spectra - 1):
            p0.append(dilution_factors[i+1])
            lower_bounds.append(0)
            upper_bounds.append(np.inf)
        for i in range(number_of_spectra):
            p0.append(0)
            lower_bounds.append(-np.inf)
            upper_bounds.append(np.inf)

        bounds = (lower_bounds, upper_bounds)
        popt, pcov = curve_fit(func, comboX, comboY,
                               p0=p0, bounds=bounds)
        perr = np.sqrt(np.diag(pcov))  # errors of the fitted coefficients

        concentrations_here = popt[0:number_of_calibrants]
        fitted_dilution_factors = popt[number_of_calibrants: number_of_calibrants + number_of_spectra - 1]
        fitted_offsets = popt[number_of_calibrants + number_of_spectra - 1: number_of_calibrants + number_of_spectra - 1 + number_of_spectra]


        if return_errors:
            # convert coefficient errors into concentration errors
            upper_confidence_limit = [calibrants[calibrant_index]['coeff_to_concentration_interpolator'](fitted_coeff + perr[calibrant_index])
                               for calibrant_index, fitted_coeff in enumerate(popt[:-4])]
            concentration_errors = [upper_confidence_limit[i] - concentrations_here[i] for i in range(len(concentrations_here))]
            return concentrations_here, concentration_errors


        # plot the fit vs the data

        # make number of subplots equal to number of spectra
        predicted_comboY = func(comboX, *popt)
        residual_combo = predicted_comboY - comboY

        fit_report = dict()
        fit_report['rmse'] = np.sqrt(np.mean((predicted_comboY - comboY) ** 2))

        separate_predicted_spectra = np.split(predicted_comboY, indices_for_splitting)
        separate_residuals = np.split(residual_combo, indices_for_splitting)
        # fig1, axs = plt.subplots(len(target_spectrum_inputs), 1, figsize=(10, 10), sharex=True)

        figsize = (4.5, 4.5)
        fig1, (ax1, ax1r) = plt.subplots(2, 1, figsize=figsize, sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        fig2, (ax2, ax2r) = plt.subplots(2, 1, figsize=figsize, sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        axs = (ax1, ax2)
        axsr = (ax1r, ax2r)

        for spectrum_index in range(number_of_spectra):
            axs[spectrum_index].plot(220+target_spectra_wavelength_indices_masked[spectrum_index],
                                     target_spectra_amplitudes_masked[spectrum_index],
                                     label='Data', color='black', linewidth=3, alpha=0.5)
            # axs[spectrum_index].plot(220+target_spectra_wavelength_indices_masked[spectrum_index],
            #                          separate_predicted_spectra[spectrum_index], color='black', label='Fit')
            # axs[spectrum_index].legend()


        for calibrant_index in range(len(calibrant_shortnames)):
            if calibrant_index <= 9:
                linestyle_here = '-'  # solid line
            else:
                linestyle_here = '--' # dashed line
            cpopt = popt.copy()
            for i in range(number_of_calibrants):
                if i != calibrant_index:
                    cpopt[i] = 0
            predicted_comboY = func(comboX, *cpopt)
            separate_predicted_spectra = np.split(predicted_comboY, indices_for_splitting)
            for spectrum_index in range(number_of_spectra):
                axs[spectrum_index].plot(220+target_spectra_wavelength_indices_masked[spectrum_index], separate_predicted_spectra[spectrum_index],
                                         label=calibrant_shortnames[calibrant_index], linestyle=linestyle_here, color=color_sequence[calibrant_index])
        # for spectrum_index in range(number_of_spectra):
        #     axs[spectrum_index].legend()
        plt.xlabel('Wavelength, nm')
        plt.ylabel('Absorbance')
        # fit_report['fitted_dilution_factor_2'] = fitted_dilution_factors[0]
        # # plt.legend()
        # plt.show()
        #
        # plt.figure(figsize=(5, 10))
        # pcov_to_plot = pcov[:len(calibrant_shortnames), :len(calibrant_shortnames)]
        # plt.imshow(pcov_to_plot, vmin=-1*max(np.abs(pcov_to_plot).flatten()), vmax=max(np.abs(pcov_to_plot).flatten()),
        #            cmap='RdBu_r')
        # # make tick labels from calibrant_shortnames
        # plt.yticks(range(len(calibrant_shortnames)), calibrant_shortnames)
        # plt.xticks(range(len(calibrant_shortnames)), calibrant_shortnames, rotation=90)
        # plt.colorbar(orientation='vertical', fraction=0.046)
        # plt.tight_layout()

        for spectrum_index in range(number_of_spectra):
            axsr[spectrum_index].plot(220+target_spectra_wavelength_indices_masked[spectrum_index],
                                     separate_residuals[spectrum_index], color='black',
                                     label='residuals', alpha=0.5, markersize=1)
            axsr[spectrum_index].fill_between(x=220+target_spectra_wavelength_indices_masked[spectrum_index],
                                              y1=0,
                                              y2=separate_residuals[spectrum_index], color='black',
                                              alpha=0.15)
            # axsr[spectrum_index].plot(220+target_spectra_wavelength_indices_masked[spectrum_index],
            #                          separate_predicted_spectra[spectrum_index], color='black', label='Fit')
            residuals_here = separate_residuals[spectrum_index]
            lag = 50
            lb_df = sm.stats.acorr_ljungbox(residuals_here, lags=[lag])
            # print(f'spectrum index {spectrum_index}, LB_pvalue: {lb_df.loc[lag, "lb_pvalue"]}, lag: {lag}')
            # print(lb_df)
            if len(lb_df) == 1:
                # take values from first row of dataframe lb_pvalue
                print(f"LB_pvalue_dil_{spectrum_index} : {lb_df.loc[lag, 'lb_pvalue']}, stat: {lb_df.loc[lag, 'lb_stat']}")
            else:
                print('hmmm')

        for ax in [ax1, ax2]:
            ax.set_ylim(-0.02, 0.85)
            ax.set_xlim(220, 430)
            simpleaxis(ax)

        for ax in axsr:
            ax.set_ylim(-0.019, 0.019)
            simpleaxis(ax)

        fig1.savefig(f"{fig_filename}_1.png", dpi=300)
        fig2.savefig(f"{fig_filename}_2.png", dpi=300)
        if do_plot:
            plt.show()
        else:
            plt.close(fig1)
            plt.close('all')
            plt.clf()

        if return_report:
            return concentrations_here, fit_report
        else:
            return concentrations_here


experiment_name = f'BPRF/2024-02-16-run01/nanodrop_spectra/'

sp = process_wellplate_spectra.SpectraProcessor(
    folder_with_correction_dataset='uv-vis-absorption-spectroscopy/microspectrometer-calibration/'
                                   '2022-12-01/interpolator-dataset/')
sp.nanodrop_lower_cutoff_of_wavelengths = 220

well_id = 16
substances_for_fitting = ['methoxybenzaldehyde', 'HRP01', 'ethyl_acetoacetate', 'EAB', 'bb017', 'bb021', 'dm70']#, 'dm088_4']
cut_from = 1
plate_folder = data_folder + 'BPRF/2024-02-16-run01/nanodrop_spectra/2024-02-18_17-48-07_UV-Vis_plate74.csv'
spectrum1 = sp.load_msp_by_id(
    plate_folder=plate_folder,
    well_id=well_id)[:, 1]

plate_folder = data_folder + 'BPRF/2024-02-16-run01/nanodrop_spectra/2024-02-18_18-02-42_UV-Vis_plate76.csv'
spectrum2 = sp.load_msp_by_id(
    plate_folder=plate_folder,
    well_id=well_id)[:, 1]


colors = [f'C{i}' for i in range(10)] + [f'C{i}' for i in range(10)]
# colors = ['none'] * 20
# colors[1] = 'C0'
# colors[2] = 'C1'
# colors[3] = 'C2'
# colors[5] = 'C3'
# colors[8] = 'C4'
# colors[9] = 'C5'
# colors[10] = 'C6'


concentrations = multispectrum_to_concentration_local(sp, target_spectrum_inputs=[spectrum1, spectrum2],
                                                   dilution_factors=[20, 200],
                                                   calibration_folder=data_folder + 'BPRF/2024-01-17-run01/' + 'microspectrometer_data/calibration/',
                                                   calibrant_shortnames=substances_for_fitting,
                                                   background_model_folder=data_folder + 'simple-reactions/2023-09-06-run01/microspectrometer_data/background_model/',
                                                   upper_bounds=[np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf],
                                                   do_plot=True, cut_from=cut_from, cut_to=250,
                                                   ignore_abs_threshold=False, ignore_pca_bkg=True,
                                                   plot_calibrant_references=True,
                                                   upper_limit_of_absorbance=0.95,
                                                      color_sequence=colors,
                                                   fig_filename='misc-scripts/figures/hansch-example-unmixing')



