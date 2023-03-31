import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import pandas as pd
from scipy.signal import savgol_filter
from scipy import interpolate
from scipy.optimize import curve_fit

plt.ioff()

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'
craic_folder = data_folder + 'craic_microspectrometer_measurements/absorbance/'

def create_folder_unless_it_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)


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
    file_list.remove(f'{prefix}-3D.msp')  # this file contains the 2D map of absorbance at single fixed wavelength
    return file_list


def construct_interpolators_for_absorbance_correction(
        nd_names=[0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0, 3.5, 4.0],
        nd_names_used=[0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 1.2, 1.5, 1.8, 2.5, 3.0, 3.5, 4.0],
        microspec_folder='uv-vis-absorption-spectroscopy/microspectrometer-calibration/2022-12-01/2-inch-nd-calibrations',
        folder_for_saving_interpolator_datasets='uv-vis-absorption-spectroscopy/microspectrometer-calibration/2022-12-01/interpolator-dataset/'):
    microspec_absorbances = dict()

    example_data = load_msp_file(experimental_data_filename=microspec_folder +
                                                            f'/{nd_names_used[0]:.1f}'.replace('.', 'p') + '.msp')
    craic_data = [np.zeros_like(example_data[:, 1])]
    for nd_name in nd_names_used:
        data = load_msp_file(experimental_data_filename=microspec_folder + f'/{nd_name:.1f}'.replace('.', 'p') + '.msp')
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
        agilent_data[:, wavelength_id] = np.copy(agilent_here)
        craic_data[:, wavelength_id] = np.copy(craic_here)

    np.save(folder_for_saving_interpolator_datasets + 'craic_data.npy', craic_data)
    np.save(folder_for_saving_interpolator_datasets + 'agilent_data.npy', agilent_data)


def load_dataset_for_absorbance_correction(target_folder='uv-vis-absorption-spectroscopy/microspectrometer-calibration/'
                                                         '2022-12-01/interpolator-dataset/'):
    craic_data = np.load(target_folder + 'craic_data.npy')
    agilent_data = np.load(target_folder + 'agilent_data.npy')
    return [craic_data, agilent_data]


def apply_correction(input_craic_spectrum, absorbance_correction_dataset):
    craic_data, agilent_data = absorbance_correction_dataset
    result = np.zeros_like(input_craic_spectrum)
    for wavelength_id in range(input_craic_spectrum.shape[0]):
        f = interpolate.interp1d(craic_data[:, wavelength_id], agilent_data[:, wavelength_id],
                                 fill_value='extrapolate')
        result[wavelength_id] = f(input_craic_spectrum[wavelength_id])
    return result


def well_id_to_file_id(well_id):
    '''Microspectrometer scans from bottom right corner. Each scan line goes up. Next scan line is to the left
    of the previous one. Well id is counted from top left corner in left-to-right lines, each next line below
    the previous one.'''
    # well_id to i,j. Index i is left-to-right. Index j is top-to-bottom. Both start from zero.
    j = well_id // 9
    i = well_id % 9

    # i,j to file_id
    file_id = (8 - i) * 6 + (5 - j) + 1  # plus one because file id is counted from one, not from zero
    return file_id


def load_raw_msp_by_id(plate_folder, well_id, prefix='spectrum_'):
    data = load_msp_file(plate_folder + prefix + f'-{well_id_to_file_id(well_id)}.msp')
    return data


class SpectraProcessor:
    """
    The only purpose of this object is to store the dataset for correcting the absorbance of CRAIC microspectrometer.
    This correction is based on dedicated experiments where certain neutral density optical filters were measured
    on the CRAIC microspectrometer and the Agilent Cary 5000, the latter instrument considered as groud truth.
    Correction is applied automatically every time a spectrum file is loaded.
    """

    def __init__(self, folder_with_correction_dataset):
        """
        Load the dataset for correcting the absorbance of CRAIC microspectrometer.
        This correction is based on dedicated experiments where certain neutral density optical filters were measured
        on the CRAIC microspectrometer and the Agilent Cary 5000, the latter instrument considered as groud truth.
        Correction is applied automatically every time a spectrum file is loaded.

        :param folder_with_correction_dataset: path to folder having the craic_data.npy and agilent_data.npy
        :type folder_with_correction_dataset: str

        """
        self.absorbance_correction_dataset = load_dataset_for_absorbance_correction(
            target_folder=folder_with_correction_dataset)

    def load_msp_by_id(self, plate_folder, well_id, prefix='spectrum_'):
        spectrum = load_raw_msp_by_id(plate_folder=plate_folder, well_id=well_id, prefix=prefix)
        spectrum[:, 1] = apply_correction(spectrum[:, 1],
                                          absorbance_correction_dataset=self.absorbance_correction_dataset)
        return spectrum

    def load_all_spectra(self, plate_folder, prefix='spectrum_-'):
        filelist = get_spectra_file_list(plate_folder)
        return [self.load_msp_by_id(plate_folder, well_id) for well_id in range(len(filelist))]

    def show_all_spectra(self, plate_folder, prefix='spectrum_-'):
        for well_id, spectrum in enumerate(self.load_all_spectra(plate_folder, prefix=prefix)):
            plt.plot(spectrum[:, 0], spectrum[:, 1], alpha=0.3, label=f'{well_id}')
            print(f'{well_id}: max {np.max(spectrum[:, 1])}')
        plt.ylabel('Absorbance')
        plt.xlabel('Wavelength, nm')

    def show_all_spectra_for_one_calibrant(self, calibrant_shortname, calibration_sequence_df, subtract_red_end=True):
        one_calibrant_df = calibration_sequence_df.loc[calibration_sequence_df['shortname'] == calibrant_shortname]
        for index, row in one_calibrant_df.iterrows():
            spectrum = self.load_msp_by_id(
                plate_folder=data_folder + experiment_name + f"microspectrometer_data/calibration/plate-{row['plate_id']:04d}/",
                well_id=row['well_id'])
            if subtract_red_end:
                spectrum[:, 1] -= np.median(spectrum[-10:, 1])
            plt.plot(spectrum[:, 0], spectrum[:, 1], alpha=0.5,
                     label=f"{row['concentration']:.5f} M, well_id:{row['well_id']}")
        plt.legend()
        plt.show()
        return spectrum

    def show_all_extinctions_for_one_calibrant(self, calibrant_shortname, calibration_sequence_df,
                                               subtract_red_end=True):
        one_calibrant_df = calibration_sequence_df.loc[calibration_sequence_df['shortname'] == calibrant_shortname]
        background_well_df = one_calibrant_df.loc[one_calibrant_df['concentration'] == 0]
        for index, row in background_well_df.iterrows():
            background_spectrum = self.load_msp_by_id(
                plate_folder=data_folder + experiment_name + f"microspectrometer_data/calibration/plate-{row['plate_id']:04d}/",
                well_id=row['well_id'])[:, 1]
        for index, row in one_calibrant_df.iterrows():
            spectrum = self.load_msp_by_id(
                plate_folder=data_folder + experiment_name + f"microspectrometer_data/calibration/plate-{row['plate_id']:04d}/",
                well_id=row['well_id'])
            if subtract_red_end:
                spectrum[:, 1] = spectrum[:, 1] - background_spectrum
                spectrum[:, 1] -= np.mean(spectrum[-20:, 1])
            plt.semilogy(spectrum[:, 0], spectrum[:, 1] / row['concentration'], alpha=0.3,
                         label=f"{row['concentration']:.5f} M, well {row['well_id']}, plate {row['plate_id']}")
        plt.legend()
        plt.show()
        return spectrum

    def construct_reference_for_calibrant(self, calibrant_shortname,
                                          calibration_folder, ref_concentration,
                                          do_plot=True, lower_limit_of_absorbance=0.05, do_reference_refinements=True):
        create_folder_unless_it_exists(calibration_folder + 'references')
        create_folder_unless_it_exists(calibration_folder + 'background')
        create_folder_unless_it_exists(calibration_folder + f'references/{calibrant_shortname}')
        calibration_sequence_df = pd.read_csv(calibration_folder + 'calibration_sequence_dataframe.csv')
        one_calibrant_df = calibration_sequence_df.loc[calibration_sequence_df['shortname'] == calibrant_shortname]

        # make sure that only one well for this calibrant has zero concentration. Otherwise it's weird.
        assert one_calibrant_df.loc[one_calibrant_df['concentration'] == 0].shape[0] == 1
        bkg_row = one_calibrant_df.loc[one_calibrant_df['concentration'] == 0].iloc[0]
        bkg_spectrum = self.load_msp_by_id(
            plate_folder=calibration_folder + f"plate-{bkg_row['plate_id']:04d}/",
            well_id=bkg_row['well_id'])

        def load_spectrum_by_df_row(row):
            spectrum = self.load_msp_by_id(
                plate_folder=calibration_folder + f"plate-{row['plate_id']:04d}/",
                well_id=row['well_id'])
            spectrum[:, 1] -= bkg_spectrum[:, 1]
            return spectrum

        # make sure that only one well for this calibrant has concentration equal to ref_concentration
        assert one_calibrant_df.loc[one_calibrant_df['concentration'] == ref_concentration].shape[0] == 1
        ref_spectrum = load_spectrum_by_df_row(
            one_calibrant_df.loc[one_calibrant_df['concentration'] == ref_concentration].iloc[0])[:, 1]
        ref_spectrum -= np.mean(ref_spectrum[-100:])

        all_spectra = [self.load_msp_by_id(
            plate_folder=calibration_folder + f"plate-{row['plate_id']:04d}/",
            well_id=row['well_id']) for index, row in one_calibrant_df.iterrows()]

        wavelength_indices = np.arange(ref_spectrum.shape[0])
        reference_interpolator = interpolate.interp1d(wavelength_indices, ref_spectrum, fill_value='extrapolate')

        thresh_w_indices = [0, 25, 127, 2000]
        thresh_as = [0.67, 0.75, 1.6, 1.6]
        threshold_interpolator = interpolate.interp1d(thresh_w_indices, thresh_as, fill_value='extrapolate')

        concentrations = sorted(one_calibrant_df['concentration'].to_list())

        def refine_reference(cut_from, row, do_plot=True, use_first_n_points_after_masking=100):
            create_folder_unless_it_exists(calibration_folder + f'references/{calibrant_shortname}/refinements')
            target_spectrum = load_spectrum_by_df_row(row)[:, 1]
            mask_containing_entire_tail = np.logical_and(target_spectrum < threshold_interpolator(wavelength_indices),
                                                         wavelength_indices > cut_from)
            first_index_where_data_is_not_ignored = np.argmax(mask_containing_entire_tail)
            mask = np.logical_and(mask_containing_entire_tail,
                                  wavelength_indices < first_index_where_data_is_not_ignored + use_first_n_points_after_masking)

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
            new_ref_spectrum[mask_containing_entire_tail] = (target_spectrum[mask_containing_entire_tail] - popt[
                1]) / slope

            ### PLOTTING
            fig1 = plt.figure(1)
            plt.plot(target_spectrum, label='data', color='C0', alpha=0.5)

            mask_illustration = np.ones_like(target_spectrum) * 4
            mask_illustration[mask] = 0
            plt.fill_between(x=wavelength_indices, y1=0, y2=mask_illustration, color='yellow', alpha=0.3,
                             label='Data is ignored')
            plt.plot(func(wavelength_indices, *popt), color='r', label='fit', alpha=0.5)
            plt.plot(func(wavelength_indices, popt[0], 0), color='C1', label='reference', alpha=0.5)
            plt.ylim(np.min((func(wavelength_indices, *popt)[mask_containing_entire_tail])),
                     np.max((func(wavelength_indices, *popt)[mask_containing_entire_tail])) * 2)
            plt.title(
                f"conc {row['concentration']}, well {row['well_id']}, plate {row['plate_id']:04d}")
            plt.legend()
            fig1.savefig(
                calibration_folder + f"references/{calibrant_shortname}/refinements/{row['concentration']}_refinement_fit.png",
                dpi=300)
            if do_plot:
                plt.show()
            else:
                plt.clf()

            new_ref_spectrum -= new_ref_spectrum[-1]

            fig2 = plt.figure(2)
            plt.title(
                f"Refined reference, well {row['concentration']}, well {row['well_id']}, plate {row['plate_id']:04d} was used")
            plt.plot(new_ref_spectrum - np.min(new_ref_spectrum), color='black', alpha=0.5, label='new reference')
            plt.plot(ref_spectrum - np.min(new_ref_spectrum), color='C0', alpha=0.5, label='old reference')
            plt.yscale('log')
            plt.legend()
            fig2.savefig(
                calibration_folder + f"references/{calibrant_shortname}/refinements/{row['concentration']}_refined_result.png",
                dpi=300)
            if do_plot:
                plt.show()
            else:
                plt.clf()

            return new_ref_spectrum, interpolate.interp1d(wavelength_indices, new_ref_spectrum,
                                                          fill_value='extrapolate')

        if do_reference_refinements:
            for concentration in concentrations:
                if concentration <= ref_concentration:
                    # Right tail of absorption band is better only in spectra having higher concentrations than the reference
                    continue
                df_row_here = one_calibrant_df.loc[one_calibrant_df['concentration'] == concentration].iloc[0]
                ref_spectrum, reference_interpolator = refine_reference(cut_from=250, row=df_row_here, do_plot=False)

        create_folder_unless_it_exists(calibration_folder + f'references/{calibrant_shortname}/concentration_fits')
        cut_from = 115
        coeffs = []
        coeff_errs = []
        for concentration in concentrations:
            if concentration == 0:
                coeffs.append(0)
                coeff_errs.append(0)
                continue

            df_row_here = one_calibrant_df.loc[one_calibrant_df['concentration'] == concentration].iloc[0]
            target_spectrum = load_spectrum_by_df_row(df_row_here)[:, 1]
            mask = np.logical_and(target_spectrum < threshold_interpolator(wavelength_indices),
                                  wavelength_indices > cut_from)
            mask = np.logical_and(mask, target_spectrum > np.min(target_spectrum) + lower_limit_of_absorbance)

            def func(xs, a, b):
                return a * reference_interpolator(xs) + b

            p0 = (concentration / ref_concentration, 0)
            bounds = ([-1e-10, -np.inf], [np.inf, np.inf])
            popt, pcov = curve_fit(func, wavelength_indices[mask], target_spectrum[mask],
                                   p0=p0, bounds=bounds)
            # sigma=noise_std*np.ones_like(target_spectrum),
            # absolute_sigma=True)
            perr = np.sqrt(np.diag(pcov))
            slope = popt[0]
            slope_error = perr[0]
            coeffs.append(slope)
            coeff_errs.append(slope_error)

            fig1 = plt.figure(1)
            plt.plot(target_spectrum, label='data', color='C0', alpha=0.5)
            mask_illustration = np.ones_like(target_spectrum) * np.max(target_spectrum)
            mask_illustration[mask] = 0
            plt.fill_between(x=wavelength_indices, y1=0, y2=mask_illustration, color='yellow', alpha=0.3,
                             label='ignored (masked) data')
            plt.plot(func(wavelength_indices, *popt), color='r', label='fit', alpha=0.5)
            plt.plot(func(wavelength_indices, popt[0], 0), color='C1', label='reference', alpha=0.5)
            plt.ylim(-0.3,
                     np.max((func(wavelength_indices, *popt)[mask])) * 2)
            plt.title(
                f"conc {df_row_here['concentration']}, well {df_row_here['well_id']}, plate {df_row_here['plate_id']:04d}")
            plt.legend()
            fig1.savefig(
                calibration_folder + f"references/{calibrant_shortname}/concentration_fits/{df_row_here['concentration']}_fit.png")
            if do_plot:
                plt.show()
            else:
                plt.clf()

        fig3 = plt.figure(3)
        plt.loglog(coeffs, concentrations, 'o-')
        plt.xlabel('Fit coefficients')
        plt.ylabel('Concentrations, mol/liter')
        fig3.savefig(calibration_folder + f"references/{calibrant_shortname}/concentration-vs-coeff.png", dpi=300)
        if do_plot:
            plt.show()
        else:
            plt.clf()

        coeff_to_concentration_interpolator = interpolate.interp1d(coeffs, concentrations,
                                                                   fill_value='extrapolate')

        np.save(calibration_folder + f'references/{calibrant_shortname}/bkg_spectrum.npy', bkg_spectrum)
        np.save(calibration_folder + f'background//bkg_spectrum.npy', bkg_spectrum)
        np.save(calibration_folder + f'references/{calibrant_shortname}/ref_spectrum.npy', ref_spectrum)
        np.save(calibration_folder + f'references/{calibrant_shortname}/interpolator_coeffs.npy', np.array(coeffs))
        np.save(calibration_folder + f'references/{calibrant_shortname}/interpolator_concentrations.npy',
                concentrations)

        return coeff_to_concentration_interpolator, reference_interpolator, bkg_spectrum

    def load_calibration_for_one_calibrant(self, calibrant_shortname, calibration_folder):
        bkg_spectrum = np.load(calibration_folder + f'references/{calibrant_shortname}/bkg_spectrum.npy')

        coeffs = np.load(calibration_folder + f'references/{calibrant_shortname}/interpolator_coeffs.npy')
        concentrations = np.load(
            calibration_folder + f'references/{calibrant_shortname}/interpolator_concentrations.npy')
        coeff_to_concentration_interpolator = interpolate.interp1d(coeffs, concentrations,
                                                                   fill_value='extrapolate')

        ref_spectrum = np.load(calibration_folder + f'references/{calibrant_shortname}/ref_spectrum.npy')
        wavelength_indices = np.arange(ref_spectrum.shape[0])
        reference_interpolator = interpolate.interp1d(wavelength_indices, ref_spectrum, fill_value='extrapolate')
        return coeff_to_concentration_interpolator, reference_interpolator, bkg_spectrum

    def spectrum_to_concentration(self, target_spectrum_input, calibration_folder, calibrant_shortnames,
                                  lower_limit_of_absorbance=0.05, fig_filename='temp', do_plot=False,
                                  upper_bounds=[np.inf, np.inf]):
        # make sure there are two calibrants specified
        assert len(calibrant_shortnames) == 2

        calibrants = []
        for calibrant_shortname in calibrant_shortnames:
            dict_here = dict()
            dict_here['coeff_to_concentration_interpolator'], dict_here['reference_interpolator'], dict_here[
                'bkg_spectrum'] = \
                self.load_calibration_for_one_calibrant(calibrant_shortname, calibration_folder)
            calibrants.append(dict_here.copy())

        bkg_spectrum = calibrants[0]['bkg_spectrum']
        target_spectrum = target_spectrum_input - bkg_spectrum[:, 1]

        cut_from = 115
        wavelength_indices = np.arange(calibrants[0]['bkg_spectrum'].shape[0])

        thresh_w_indices = [0, 25, 127, 2000]
        thresh_as = [0.67, 0.75, 1.6, 1.6]
        threshold_interpolator = interpolate.interp1d(thresh_w_indices, thresh_as, fill_value='extrapolate')

        mask = np.logical_and(target_spectrum < threshold_interpolator(wavelength_indices),
                              wavelength_indices > cut_from)
        mask = np.logical_and(mask,
                              target_spectrum > np.min(target_spectrum) + lower_limit_of_absorbance)

        def func(xs, a, b, c):
            return a * calibrants[0]['reference_interpolator'](xs) + b * calibrants[1]['reference_interpolator'](xs) + c

        p0 = (0.5 if upper_bounds[0] is np.inf else upper_bounds[0],
              0.5 if upper_bounds[1] is np.inf else upper_bounds[1],
              0)
        bounds = ([-1e-10, -1e-10, -0.01], [upper_bounds[0], upper_bounds[1], np.inf])
        popt, pcov = curve_fit(func, wavelength_indices[mask], target_spectrum[mask],
                               p0=p0, bounds=bounds)
        perr = np.sqrt(np.diag(pcov))  # errors of the fitted coefficients

        concentrations_here = [calibrants[calibrant_index]['coeff_to_concentration_interpolator'](fitted_coeff)
                               for calibrant_index, fitted_coeff in enumerate(popt[:2])]

        fig1 = plt.figure(1)
        plt.plot(target_spectrum, label='data', color='C0', alpha=0.5)
        mask_illustration = np.ones_like(target_spectrum) * np.max(target_spectrum)
        mask_illustration[mask] = 0
        plt.fill_between(x=wavelength_indices, y1=0, y2=mask_illustration, color='yellow', alpha=0.3,
                         label='ignored (masked) data')
        plt.plot(func(wavelength_indices, *popt), color='r', label='fit', alpha=0.5)
        plt.plot(func(wavelength_indices, popt[0], 0, 0), color='C1', label=calibrant_shortnames[0], alpha=0.5)
        plt.plot(func(wavelength_indices, 0, popt[1], 0), color='C2', label=calibrant_shortnames[1], alpha=0.5)
        plt.ylim(-0.3,
                 np.max((func(wavelength_indices, *popt)[mask])) * 2)
        plt.legend()
        fig1.savefig(f"{fig_filename}.png")
        if do_plot:
            plt.show()
        else:
            plt.clf()
        return concentrations_here

    def concentrations_for_all_plates(self, timepoint_id, experiment_folder,
                                      calibration_folder,
                                      calibrant_shortnames,
                                      path_to_input_compositions_csv,
                                      calibrant_upper_bounds, do_plot=False):
        create_folder_unless_it_exists(experiment_folder + 'results')
        create_folder_unless_it_exists(experiment_folder + f'results/uv-vis-fits')
        input_compositions = pd.read_csv(path_to_input_compositions_csv)
        concentrations = []
        for index, row in input_compositions.iterrows():
            plate_id = index // 54
            well_id = index % 54
            print(f'{plate_id}-{well_id}')
            spectrum = sp.load_msp_by_id(
                plate_folder=experiment_folder + f"microspectrometer_data/timepoint_{timepoint_id:03d}/plate-{plate_id:02d}/",
                well_id=well_id)[:, 1]
            concentrations_here = self.spectrum_to_concentration(target_spectrum_input=spectrum,
                                                                 calibration_folder=calibration_folder,
                                                                 calibrant_shortnames=calibrant_shortnames,
                                                                 fig_filename=experiment_folder + f'results/uv-vis-fits/plate{plate_id:04d}-well{well_id:02d}.png',
                                                                 do_plot=do_plot,
                                                                 upper_bounds=calibrant_upper_bounds)
            concentrations.append(concentrations_here[0])
        input_compositions[calibrant_shortnames[0]] = concentrations
        input_compositions.to_csv(
            data_folder + experiment_name + f'results/timepoint{timepoint_id:03d}-reaction_results.csv', index=False)
        return input_compositions


if __name__ == '__main__':

    sp = SpectraProcessor(folder_with_correction_dataset='uv-vis-absorption-spectroscopy/microspectrometer-calibration/'
                                                         '2022-12-01/interpolator-dataset/')
    experiment_name = 'multicomp-reactions/2023-01-18-run01/'

    # ##### This constructs the calibration for the product 'IIO029A' and saves for later. Do not rerun unless you know what you do. #######
    # sp.construct_reference_for_calibrant(calibrant_shortname='IIO029A',
    #                                      calibration_folder=data_folder + experiment_name + 'microspectrometer_data/calibration/',
    #                                      ref_concentration=0.00011,
    #                                      do_plot=True, do_reference_refinements=True)

    # #### This constructs the calibration for the substrate 'ald001' and saves for later. Do not rerun unless you know what you do. #######
    # sp.construct_reference_for_calibrant(calibrant_shortname='ald001',
    #                                      calibration_folder=data_folder + experiment_name + 'microspectrometer_data/calibration/',
    #                                      ref_concentration=0.0384048,
    #                                      do_plot=True, do_reference_refinements=True)

    ##### This extracts concentrations from unknown reaction mixtures. You can rerun this. Do rerun this with different experiments in the future. #####
    reaction_results = sp.concentrations_for_all_plates(timepoint_id=1,
                                                        experiment_folder=data_folder + experiment_name,
                                                        calibration_folder=data_folder + experiment_name + 'microspectrometer_data/calibration/',
                                                        calibrant_shortnames=['IIO029A', 'ald001'],
                                                        calibrant_upper_bounds=[np.inf, 2],
                                                        path_to_input_compositions_csv=data_folder + experiment_name + 'input_compositions/' + '20230110RF029_concentrations_in_reaction_mixtures.csv',
                                                        do_plot=False)

    ### MISC SKETCHES -- IGNORE THESE: #########
    # calibration_sequence_df = pd.read_csv(data_folder + experiment_name + 'microspectrometer_data/calibration/calibration_sequence_dataframe.csv')
    # sp.show_all_spectra_for_one_calibrant(calibrant_shortname='IIO029A', calibration_sequence_df=calibration_sequence_df)