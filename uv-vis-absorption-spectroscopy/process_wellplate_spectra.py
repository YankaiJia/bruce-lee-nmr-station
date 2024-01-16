import logging

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import pandas as pd
from scipy.signal import savgol_filter
from scipy import interpolate
from scipy.optimize import curve_fit
import matplotlib.ticker as mticker

# matplotlib.use('Agg')
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
    try:
        file_list.remove(f'{prefix}-3D.msp')  # this file contains the 2D map of absorbance at single fixed wavelength
    except ValueError:
        pass
    return [filename for filename in file_list if 'rep2' not in filename]


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


def load_raw_msp_by_id(plate_folder, well_id, prefix='spectrum_', suffix=''):
    data = load_msp_file(plate_folder + prefix + f'-{well_id_to_file_id(well_id)}{suffix}.msp')
    return data

def diluted_vials_only(list_of_vials_on_plate):
    """Returns the indices of the vials on the plate that are diluted. Every second row of the plate was not
    filled with reaction mixtures and is later used hold a diluted reaction mixture.

    Parameters
    ----------
    list_of_vials_on_plate : list
        List of vials on the plate. The order of the vials is: first row, second row, third row, etc.

    Returns
    -------
    list
        List of only those vials on the plate that are diluted.
    """
    return list_of_vials_on_plate[[i + j for i in [9, 27, 45] for j in range(9)]]

class SpectraProcessor:
    """
    The only purpose of this object is to store the dataset for correcting the absorbance of CRAIC microspectrometer.
    This correction is based on dedicated experiments where certain neutral density optical filters were measured
    on the CRAIC microspectrometer and the Agilent Cary 5000, the latter instrument considered as groud truth.
    Correction is applied automatically every time a spectrum file is loaded.
    """

    def __init__(self, folder_with_correction_dataset, spectrum_data_type='craic'):
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
        self.spectrum_data_type = spectrum_data_type

        self.nanodrop_lower_cutoff_of_wavelengths = 250
        self.nanodrop_upper_cutoff_of_wavelengths = 600

    def load_nanodrop_csv_for_one_plate(self, plate_folder,
                                        ):
        """
        Loads the csv file with the Nanodrop measurements into dataframe. First column is wavelength,.
        the remaining columns are the absorbances for each sample (numerated as well/vial).

        The code can also process the nanodrop's CSV files whose nanodrop column names are, for instance, like so:
        `0_4BhYCtsRm6MY7wqCRnBh43,1_iEd9wJZKzJFfF63WizGXsJ,2_bicD5pn9i6yKwsuEwLX59r,3_cHXhtGgQtdSgyBZTx6942M, ...`
        i.e. there is a UUID added after the underscore. In principle, this commit allows for any string to be can
        be added after the underscore, it will be loaded successfully by this code.

        The code retains reverse compatibility to old nanodrop's CSV files that don't contain underscores or UUIDs.

        Returns
        -------
        nanodrop_df: pd.DataFrame
            Dataframe with the Nanodrop measurements.
        """
        nanodrop_df = pd.read_csv(plate_folder)

        # rename first column to "wavelength" and make it float type
        nanodrop_df = nanodrop_df.rename(columns={nanodrop_df.columns[0]: "wavelength"})

        # remove rows where wavelength is lower than nanodrop_lower_cutoff_of_wavelengths
        nanodrop_df = nanodrop_df[nanodrop_df["wavelength"] >= self.nanodrop_lower_cutoff_of_wavelengths]

        # remove rows where wavelength is higher than nanodrop_upper_cutoff_of_wavelengths
        nanodrop_df = nanodrop_df[nanodrop_df["wavelength"] <= self.nanodrop_upper_cutoff_of_wavelengths]

        nanodrop_df["wavelength"] = nanodrop_df["wavelength"].astype(float)

        # Remove underscore from the column names and everything after it.
        # This is because Yankai has added the UUID of each comdition into the column names -- a good idea, because
        # it allows to cross-validate the relation between spectra and the list of conditions.
        nanodrop_df.columns = nanodrop_df.columns.str.split('_').str[0]

        return nanodrop_df


    def load_single_nanodrop_spectrum(self, plate_folder, well_id):
        """
        Loads the Nanodrop spectrum for a single well.

        The code can also process the nanodrop's CSV files whose nanodrop column names are, for instance, like so:
        `0_4BhYCtsRm6MY7wqCRnBh43,1_iEd9wJZKzJFfF63WizGXsJ,2_bicD5pn9i6yKwsuEwLX59r,3_cHXhtGgQtdSgyBZTx6942M, ...`
        i.e. there is a UUID added after the underscore. In principle, this commit allows for any string to be can
        be added after the underscore, it will be loaded successfully by this code.

        The code retains reverse compatibility to old nanodrop's CSV files that don't contain underscores or UUIDs.

        Parameters
        ----------
        plate_folder: str
            Path to the folder with the Nanodrop measurements.
        well_id: int
            Number of the well.

        Returns
        -------
        nanodrop_spectrum: np.array
            Array with the Nanodrop spectrum.
        """
        nanodrop_df = self.load_nanodrop_csv_for_one_plate(plate_folder=plate_folder)
        wavelengths = nanodrop_df["wavelength"].to_numpy()
        # get the column whose names starts with well_id, but can have underscore and anything after it
        absorbances = nanodrop_df.filter(regex=f'^{well_id}_?').to_numpy().squeeze()
        nanodrop_spectrum = np.array([wavelengths, absorbances]).T
        return nanodrop_spectrum

    def load_craic_spectrum_by_id(self, plate_folder, well_id, prefix='spectrum_', do_show=False, ignore_second_repetition=False):
        spectrum = load_raw_msp_by_id(plate_folder=plate_folder, well_id=well_id, prefix=prefix)

        # if the file of the same name but suffix '_rep2' exists, then load it and apply the 'zero-dose extrapolation'
        # to correct for photobleaching
        if (not ignore_second_repetition) and \
                (os.path.isfile(plate_folder + prefix + f'-{well_id_to_file_id(well_id)}_rep2.msp')):
            try:
                spectrum_rep2 = load_raw_msp_by_id(plate_folder=plate_folder, well_id=well_id, prefix=prefix,
                                                   suffix='_rep2')
                spectrum[:, 1] = spectrum[:, 1] - 0.5*(spectrum_rep2[:, 1] - spectrum[:, 1])
            except FileNotFoundError:
                pass
        if do_show:
            plt.plot(spectrum[:, 0], spectrum[:, 1])
        spectrum[:, 1] = apply_correction(spectrum[:, 1],
                                          absorbance_correction_dataset=self.absorbance_correction_dataset)
        if do_show:
            plt.plot(spectrum[:, 0], spectrum[:, 1], label='corr')
            plt.legend()
            plt.show()
        return spectrum

    def load_msp_by_id(self, plate_folder, well_id, prefix='spectrum_', do_show=False, ignore_second_repetition=False):
        # if plate folder contains string "nanodrop", then treat the plate_folder as path to nanodrop CSV file
        if 'nanodrop' in plate_folder:
            spectrum = self.load_single_nanodrop_spectrum(plate_folder=plate_folder, well_id=well_id)
        else: # plate_folder is a folder with CRAIC spectra. Use load_craic_spectrum_by_id and pass all args
            spectrum = self.load_craic_spectrum_by_id(plate_folder=plate_folder, well_id=well_id, prefix=prefix,
                                                      do_show=do_show, ignore_second_repetition=ignore_second_repetition)
        return spectrum


    def load_all_spectra(self, plate_folder, prefix='spectrum_-'):
        if 'nanodrop' in plate_folder:
            # load the nanodrop csv file and count the columns
            nanodrop_df = self.load_nanodrop_csv_for_one_plate(plate_folder=plate_folder)
            well_id = 0
            resulting_array = []
            while str(well_id) in nanodrop_df.columns:
                resulting_array.append(self.load_msp_by_id(plate_folder, well_id))
                well_id += 1
            # make a warning if the length of resulting array is higher than 54
            if len(resulting_array) > 54:
                logging.warning(f'Warning: the number of wells is {len(resulting_array)}, '
                             f'which is higher than 54. Check the Nanodrop file.')
            return resulting_array
        else:
            filelist = get_spectra_file_list(plate_folder)
            return [self.load_msp_by_id(plate_folder, well_id) for well_id in range(len(filelist))]

    def show_all_spectra(self, plate_folder, prefix='spectrum_-', specific_well_ids=None):
        for well_id, spectrum in enumerate(self.load_all_spectra(plate_folder, prefix=prefix)):
            if specific_well_ids is None or well_id in specific_well_ids:
                plt.plot(spectrum[:, 0], spectrum[:, 1], alpha=0.3, label=f'{well_id}')
            print(f'{well_id}: max {np.max(spectrum[:, 1])}, min {np.min(spectrum[:, 1])}')
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
        if do_plot:
            plt.plot(ref_spectrum)
            plt.title('Ref spectrum')
            plt.show()

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
        # cut_from = 115
        cut_from=200
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
                                  background_model_folder,
                                  lower_limit_of_absorbance=-0.2, fig_filename='temp', do_plot=False, #lower_limit_of_absorbance=0.02
                                  upper_bounds=[np.inf, np.inf], use_line=False, cut_from = 200, ignore_abs_threshold=False,
                                  cut_to = False, ignore_pca_bkg=False, return_errors=False): #upper_bounds=[np.inf, np.inf]
        calibrants = []
        for calibrant_shortname in calibrant_shortnames:
            dict_here = dict()
            dict_here['coeff_to_concentration_interpolator'], dict_here['reference_interpolator'], dict_here[
                'bkg_spectrum'] = \
                self.load_calibration_for_one_calibrant(calibrant_shortname, calibration_folder)
            calibrants.append(dict_here.copy())

        bkg_spectrum = calibrants[0]['bkg_spectrum']
        wavelengths = bkg_spectrum[:, 0]
        target_spectrum = target_spectrum_input - bkg_spectrum[:, 1]
        wavelength_indices = np.arange(calibrants[0]['bkg_spectrum'].shape[0])

        thresh_w_indices = [0, 25, 127, 2000]
        thresh_as = [0.67, 0.75, 1.6, 1.6]
        threshold_interpolator = interpolate.interp1d(thresh_w_indices, thresh_as, fill_value='extrapolate')

        if not ignore_abs_threshold:
            mask = np.logical_and(target_spectrum < threshold_interpolator(wavelength_indices),
                                  wavelength_indices > cut_from)
        else:
            mask = wavelength_indices > cut_from

        if cut_to:
            mask = np.logical_and(mask, wavelength_indices <= cut_to)

        mask = np.logical_and(mask,
                              target_spectrum > np.min(target_spectrum) + lower_limit_of_absorbance)

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

        if len(wavelength_indices[mask]) == 0:
            print('There is no data that is within mask. Returning zeros.')
            return [0 for i in range(4)]

        ## old implementation
        # if len(calibrant_shortnames) == 2:
        #     def func(xs, a, b, c, d, e, f):
        #         return a * calibrants[0]['reference_interpolator'](xs) + b * calibrants[1]['reference_interpolator'](xs) + c \
        #                + d*xs + e * background_interpolators[0](xs) + f * background_interpolators[1](xs)
        # elif len(calibrant_shortnames) == 3:
        #     def func(xs, a1, a2, a3, c, d, e, f):
        #         return a1 * calibrants[0]['reference_interpolator'](xs) + \
        #                a2 * calibrants[1]['reference_interpolator'](xs) + \
        #                a3 * calibrants[2]['reference_interpolator'](xs)\
        #                + c + d * xs + e * background_interpolators[0](xs) + f * background_interpolators[1](xs)
        # else:
        #     raise NotImplementedError

        ## New implementation
        def func(*args):
            xs = args[0]
            c,d,e,f = args[-4:]
            calibrant_coefficients = args[1:-4]
            return sum([calibrant_coefficients[i] * calibrants[i]['reference_interpolator'](xs) for i in range(len(calibrant_coefficients))]) \
                      + c + d * xs + e * background_interpolators[0](xs) + f * background_interpolators[1](xs)

        # p0 = tuple(0.5 if upper_bounds[0] is np.inf else upper_bounds[0],
        #       0.5 if upper_bounds[1] is np.inf else upper_bounds[1],
        #       0,
        #       0,
        #       0,
        #       0)
        p0 = tuple([0.5 if upper_bound is np.inf else upper_bound for upper_bound in upper_bounds] + [0] * 4)
        if use_line:
            linebounds = [-np.inf, np.inf]
        else:
            linebounds = [-1e-15, 1e-15]

        if ignore_pca_bkg:
            bkg_comp_limit = 1e-12
        else:
            bkg_comp_limit = np.inf
        bounds = ([-1e-20] * len(calibrant_shortnames) + [-np.inf, linebounds[0], -1*bkg_comp_limit, -1*bkg_comp_limit],
                  upper_bounds + [np.inf, linebounds[1], bkg_comp_limit, bkg_comp_limit])
        popt, pcov = curve_fit(func, wavelength_indices[mask], target_spectrum[mask],
                               p0=p0, bounds=bounds)
        perr = np.sqrt(np.diag(pcov))  # errors of the fitted coefficients

        concentrations_here = [calibrants[calibrant_index]['coeff_to_concentration_interpolator'](fitted_coeff)
                               for calibrant_index, fitted_coeff in enumerate(popt[:-4])]

        fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        ax = ax1
        ax.plot(wavelengths, target_spectrum_input, label='Raw data', color='grey', alpha=0.2)
        ax.plot(wavelengths, target_spectrum, label='Data minus bkg.', color='black', alpha=0.5)
        mask_illustration = np.ones_like(target_spectrum) * np.max(target_spectrum)
        mask_illustration[mask] = 0
        ax.fill_between(x=wavelengths, y1=0, y2=mask_illustration, color='yellow', alpha=0.3,
                         label='Masked data')
        ax.plot(wavelengths, func(wavelength_indices, *popt), color='r', label='Fit', alpha=0.5)
        for calibrant_index in range(len(calibrant_shortnames)):
            cpopt = [x if i == calibrant_index else 0 for i, x in enumerate(popt)]
            ax.plot(wavelengths, func(wavelength_indices, *cpopt), label=calibrant_shortnames[calibrant_index], alpha=0.5)
        # make a list where only the third from the end item is the same as in popt, while the other ones are zero
        if use_line:
            cpopt = [x if i == len(popt) - 3 else 0 for i, x in enumerate(popt)]
            ax.plot(wavelengths, func(wavelength_indices, *cpopt), label='Line', alpha=0.5)
        if not ignore_pca_bkg:
            cpopt = [x if i == len(popt) - 2 else 0 for i, x in enumerate(popt)]
            ax.plot(wavelengths, func(wavelength_indices, *cpopt), label='Bkg. PC1', alpha=0.5)
            cpopt = [x if i == len(popt) - 1 else 0 for i, x in enumerate(popt)]
            ax.plot(wavelengths, func(wavelength_indices, *cpopt), label='Bkg. PC2', alpha=0.5)
        # plt.ylim(-0.3,
        #          np.max((func(wavelength_indices, *popt)[mask])) * 3)
        title_str = f'Concentrations:\n'
        for i in range(len(concentrations_here)):
            title_str += f'{np.array(concentrations_here)[i]:.6f} M ({calibrant_shortnames[i]})\n '
        fig1.suptitle(title_str[:-2])
        ax.set_ylabel('Absorbance')
        ax.legend()
        # Residuals subplot
        ax = ax2
        ax.plot(wavelengths[mask], target_spectrum[mask] - func(wavelength_indices[mask], *popt), color='black', alpha=0.5,
                label='residuals')
        ax.legend()
        ax.set_xlabel('Wavelength, nm')
        ax.set_ylabel('Absorbance')
        fig1.savefig(f"{fig_filename}.png")

        if do_plot:
            plt.show()
        else:
            plt.close(fig1)
            plt.close('all')
            plt.clf()

        if return_errors:
            # convert coefficient errors into concentration errors
            upper_confidence_limit = [calibrants[calibrant_index]['coeff_to_concentration_interpolator'](fitted_coeff + perr[calibrant_index])
                               for calibrant_index, fitted_coeff in enumerate(popt[:-4])]
            concentration_errors = [upper_confidence_limit[i] - concentrations_here[i] for i in range(len(concentrations_here))]
            return concentrations_here, concentration_errors

        return concentrations_here


    def concentrations_for_one_plate(self, experiment_folder, plate_folder,
                                      calibration_folder, calibrant_shortnames, calibrant_upper_bounds,
                                     background_model_folder, do_plot=False, return_all_substances=False,
                                     cut_from = 200, cut_to=False, ignore_abs_threshold=False, ignore_pca_bkg=False):
        plate_name = plate_folder.split('/')[-1]
        create_folder_unless_it_exists(experiment_folder + 'results')
        create_folder_unless_it_exists(experiment_folder + f'results/uv-vis-fits')
        # input_compositions = pd.read_csv(path_to_input_compositions_csv)
        concentrations = []
        # for index, row in input_compositions.iterrows():
        #     plate_id = index // 54
        #     well_id = index % 54
        #     print(f'{plate_id}-{well_id}')
        if 'nanodrop' in plate_folder:
            # load the nanodrop csv file and count the columns
            nanodrop_df = self.load_nanodrop_csv_for_one_plate(plate_folder=plate_folder)
            well_id = 0
            range_of_wells = []
            while str(well_id) in nanodrop_df.columns:
                range_of_wells.append(well_id)
                well_id += 1
            # make a warning if the length of resulting array is higher than 54
            if len(range_of_wells) > 54:
                logging.warning(f'Warning: the number of wells is {len(range_of_wells)}, '
                             f'which is higher than 54. Check the Nanodrop file.')
        else:
            range_of_wells = range(54)

        for well_id in range_of_wells:
            spectrum = self.load_msp_by_id(
                plate_folder=plate_folder,
                well_id=well_id)[:, 1]
            concentrations_here = self.spectrum_to_concentration(target_spectrum_input=spectrum,
                                                                 calibration_folder=calibration_folder,
                                                                 calibrant_shortnames=calibrant_shortnames,
                                                                 fig_filename=experiment_folder + f'results/uv-vis-fits/{plate_name}-well{well_id:02d}.png',
                                                                 do_plot=do_plot,
                                                                 background_model_folder=background_model_folder,
                                                                 upper_bounds=calibrant_upper_bounds, cut_from=cut_from,
                                                                 cut_to=cut_to,
                                                                 ignore_abs_threshold=ignore_abs_threshold,
                                                                 ignore_pca_bkg=ignore_pca_bkg)
            if return_all_substances:
                concentrations.append(concentrations_here)
            else:
                concentrations.append(concentrations_here[0])
        # input_compositions[calibrant_shortnames[0]] = concentrations
        # input_compositions.to_csv(
        #     data_folder + experiment_name + f'results/timepoint{timepoint_id:03d}-reaction_results.csv', index=False)
        return np.array(concentrations)


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
            experiment_folder + f'results/timepoint{timepoint_id:03d}-reaction_results.csv', index=False)
        return input_compositions


    def get_absorbance_at_single_wavelength_for_one_plate(self, plate_folder, wavelength=None, ref_wavelengths=None,
                                                          wavelength_id = 100, ref_wavelength_id=[500]):
        if not (wavelength is None):
            wavelengths = self.load_msp_by_id(plate_folder=plate_folder, well_id=0)[:, 0]
            wavelength_id = np.absolute(wavelengths - wavelength).argmin()
            ref_wavelength_id = [np.absolute(wavelengths - ref_wavelength).argmin() for ref_wavelength in ref_wavelengths]

        concentrations = []
        for well_id in range(54):
            spectrum = self.load_msp_by_id(plate_folder=plate_folder, well_id=well_id)[:, 1]
            concentrations.append(spectrum[wavelength_id] - np.mean(np.array([spectrum[ref_wav] for ref_wav in ref_wavelength_id])))
        return np.array(concentrations)


    def multispectrum_to_concentration(self, target_spectrum_inputs, calibration_folder, calibrant_shortnames,
                                  background_model_folder, dilution_factors,
                                  lower_limit_of_absorbance=-0.2, fig_filename='temp', do_plot=False, #lower_limit_of_absorbance=0.02
                                  upper_bounds=[np.inf, np.inf], use_line=False, cut_from = 200, ignore_abs_threshold=False,
                                  cut_to = False, ignore_pca_bkg=False, return_errors=False): #upper_bounds=[np.inf, np.inf]
        calibrants = []
        for calibrant_shortname in calibrant_shortnames:
            dict_here = dict()
            dict_here['coeff_to_concentration_interpolator'], dict_here['reference_interpolator'], dict_here[
                'bkg_spectrum'] = \
                self.load_calibration_for_one_calibrant(calibrant_shortname, calibration_folder)
            calibrants.append(dict_here.copy())

        bkg_spectrum = calibrants[0]['bkg_spectrum']
        wavelengths = bkg_spectrum[:, 0]
        target_spectra = [target_spectrum_input - bkg_spectrum[:, 1] for target_spectrum_input in target_spectrum_inputs]
        wavelength_indices = np.arange(calibrants[0]['bkg_spectrum'].shape[0])

        thresh_w_indices = [0, 25, 127, 2000]
        thresh_as = [0.67, 0.75, 1.6, 1.6]
        threshold_interpolator = interpolate.interp1d(thresh_w_indices, thresh_as, fill_value='extrapolate')

        if not ignore_abs_threshold:
            mask = np.logical_and(target_spectrum < threshold_interpolator(wavelength_indices),
                                  wavelength_indices > cut_from)
        else:
            mask = wavelength_indices > cut_from

        if cut_to:
            mask = np.logical_and(mask, wavelength_indices <= cut_to)

        mask = np.logical_and(mask,
                              target_spectrum > np.min(target_spectrum) + lower_limit_of_absorbance)

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

        if len(wavelength_indices[mask]) == 0:
            print('There is no data that is within mask. Returning zeros.')
            return [0 for i in range(4)]

        ## old implementation
        # if len(calibrant_shortnames) == 2:
        #     def func(xs, a, b, c, d, e, f):
        #         return a * calibrants[0]['reference_interpolator'](xs) + b * calibrants[1]['reference_interpolator'](xs) + c \
        #                + d*xs + e * background_interpolators[0](xs) + f * background_interpolators[1](xs)
        # elif len(calibrant_shortnames) == 3:
        #     def func(xs, a1, a2, a3, c, d, e, f):
        #         return a1 * calibrants[0]['reference_interpolator'](xs) + \
        #                a2 * calibrants[1]['reference_interpolator'](xs) + \
        #                a3 * calibrants[2]['reference_interpolator'](xs)\
        #                + c + d * xs + e * background_interpolators[0](xs) + f * background_interpolators[1](xs)
        # else:
        #     raise NotImplementedError

        ## New implementation
        def func(*args):
            xs = args[0]
            c,d,e,f = args[-4:]
            calibrant_coefficients = args[1:-4]
            return sum([calibrant_coefficients[i] * calibrants[i]['reference_interpolator'](xs) for i in range(len(calibrant_coefficients))]) \
                      + c + d * xs + e * background_interpolators[0](xs) + f * background_interpolators[1](xs)

        # p0 = tuple(0.5 if upper_bounds[0] is np.inf else upper_bounds[0],
        #       0.5 if upper_bounds[1] is np.inf else upper_bounds[1],
        #       0,
        #       0,
        #       0,
        #       0)


        p0 = tuple([0.5 if upper_bound is np.inf else upper_bound for upper_bound in upper_bounds] + [0] * 4)
        if use_line:
            linebounds = [-np.inf, np.inf]
        else:
            linebounds = [-1e-15, 1e-15]

        if ignore_pca_bkg:
            bkg_comp_limit = 1e-12
        else:
            bkg_comp_limit = np.inf
        bounds = ([-1e-20] * len(calibrant_shortnames) + [-np.inf, linebounds[0], -1*bkg_comp_limit, -1*bkg_comp_limit],
                  upper_bounds + [np.inf, linebounds[1], bkg_comp_limit, bkg_comp_limit])
        popt, pcov = curve_fit(func, wavelength_indices[mask], target_spectrum[mask],
                               p0=p0, bounds=bounds)
        perr = np.sqrt(np.diag(pcov))  # errors of the fitted coefficients

        concentrations_here = [calibrants[calibrant_index]['coeff_to_concentration_interpolator'](fitted_coeff)
                               for calibrant_index, fitted_coeff in enumerate(popt[:-4])]


        if return_errors:
            # convert coefficient errors into concentration errors
            upper_confidence_limit = [calibrants[calibrant_index]['coeff_to_concentration_interpolator'](fitted_coeff + perr[calibrant_index])
                               for calibrant_index, fitted_coeff in enumerate(popt[:-4])]
            concentration_errors = [upper_confidence_limit[i] - concentrations_here[i] for i in range(len(concentrations_here))]
            return concentrations_here, concentration_errors

        return concentrations_here




def plot_differential_absorbances_for_plate(craic_exp_name,
                                            wavelength,
                                            ref_wavelengths,
                                            ):
    """
    Plots the difference between absorbance at the target wavelength and the mean absorbance at reference wavelengths
    from ref_wavelength list.

    Parameters
    ----------
    craic_exp_name: str
        Name of the folder with CRAIC microspectrometer measurements.
    wavelength
        Target wavelength at which the absorbance is calculated.
    ref_wavelengths
        List of reference wavelengths. Mean absorbance at these wavelengths is subtracted from the absorbance at the
        target wavelength.

    Returns
    -------
    diff: np.array
        Array of differential absorbances.
    """
    sp = SpectraProcessor(folder_with_correction_dataset='uv-vis-absorption-spectroscopy/microspectrometer-calibration/'
                                                         '2022-12-01/interpolator-dataset/')
    craic_folder = data_folder + 'craic_microspectrometer_measurements/absorbance/'
    sp.show_all_spectra(craic_folder + craic_exp_name + '/')
    plt.show()
    diff = sp.get_absorbance_at_single_wavelength_for_one_plate(craic_folder + craic_exp_name + '/',
                                                                wavelength=wavelength,
                                                                ref_wavelengths=ref_wavelengths)
    diluted_indices = [i + j for i in [9, 27, 45] for j in range(9)]
    undiluted_indices = [i + j for i in [0, 18, 36] for j in range(9)]
    diff = diff[diluted_indices]
    print(f'rel.std {np.std(diff) / np.mean(diff)}')
    plt.plot(diff)
    plt.xlabel('Vial ID')
    plt.ylabel(f'Absorbance at {wavelength} nm minus absorbance at wavelengths {ref_wavelengths} nm')
    plt.title(f'{craic_exp_name}.\nRel. STD: {np.std(diff) / np.mean(diff)}')
    plt.show()
    return diff


if __name__ == '__main__':

    sp = SpectraProcessor(folder_with_correction_dataset='uv-vis-absorption-spectroscopy/microspectrometer-calibration/'
                                                         '2022-12-01/interpolator-dataset/')
    sp.nanodrop_lower_cutoff_of_wavelengths = 220
    x = sp.load_nanodrop_csv_for_one_plate(plate_folder=data_folder + 'BPRF/2024-01-08-run01/nanodrop_spectra/2024-01-10_12-51-07_UV-Vis_plate_71.csv')

    # well_id = 44
    # substances_for_fitting = ['methoxybenzaldehyde', 'HRP01', 'dm35_8', 'dm35_9', 'dm36', 'dm37', 'dm40_12', 'dm40_10', 'EAB']
    # cut_from = 5
    # # Condition 154
    # plate_folder = data_folder + 'BPRF/2023-12-27-run01_200/nanodrop_spectra/2023-12-29_13-50-21_UV-Vis_plate_67.csv'
    # spectrum1 = sp.load_msp_by_id(
    #     plate_folder=plate_folder,
    #     well_id=well_id)[:, 1]
    #
    # plate_folder = data_folder + 'BPRF/2023-12-27-run01_100/nanodrop_spectra/2023-12-29_14-38-46_UV-Vis_plate_73.csv'
    # spectrum2 = sp.load_msp_by_id(
    #     plate_folder=plate_folder,
    #     well_id=well_id)[:, 1]
    #
    # # concentrations = sp.spectrum_to_concentration(target_spectrum_input=spectrum2,
    # #                                                    calibration_folder=data_folder + 'BPRF/2023-11-08-run01/' + 'microspectrometer_data/calibration/',
    # #                                                    calibrant_shortnames=substances_for_fitting,
    # #                                                    background_model_folder=data_folder + 'simple-reactions/2023-09-06-run01/microspectrometer_data/background_model/',
    # #                                                    upper_bounds=[np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf],
    # #                                                    do_plot=True, cut_from=cut_from,
    # #                                                    ignore_abs_threshold=True, ignore_pca_bkg=True)
    #
    # concentrations = sp.multispectrum_to_concentration(target_spectrum_input=[spectrum1, spectrum2],
    #                                                    dilution_factors=[2, 1],
    #                                                    calibration_folder=data_folder + 'BPRF/2023-11-08-run01/' + 'microspectrometer_data/calibration/',
    #                                                    calibrant_shortnames=substances_for_fitting,
    #                                                    background_model_folder=data_folder + 'simple-reactions/2023-09-06-run01/microspectrometer_data/background_model/',
    #                                                    upper_bounds=[np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf],
    #                                                    do_plot=True, cut_from=cut_from,
    #                                                    ignore_abs_threshold=True, ignore_pca_bkg=True)

    # sp.load_single_nanodrop_spectrum(plate_folder=data_folder + 'simple-reactions/2023-08-21-run01/nanodrop_spectra/2023-08-23_23-50-41_plate_51.csv',
    #                                  well_id=0)


    # process_run_by_shortname(run_name)
    # plot_differential_absorbances_for_plate(
    #         craic_exp_name='2023-06-14_21-11-36__plate0000036__four-dye-dil-2023-06-13-run01',
    #         wavelength=420,
    #         ref_wavelengths=[525]
    #         )

    # ##### =================================== 2023-01-18-run01 ========================================================
    # experiment_name = 'multicomp-reactions/2023-01-18-run01/'
    # # ##### This constructs the calibration for the product 'IIO029A' and saves for later. Do not rerun unless you know what you do. #######
    # # sp.construct_reference_for_calibrant(calibrant_shortname='IIO029A',
    # #                                      calibration_folder=data_folder + experiment_name + 'microspectrometer_data/calibration/',
    # #                                      ref_concentration=0.00011,
    # #                                      do_plot=True, do_reference_refinements=True)
    #
    # # #### This constructs the calibration for the substrate 'ald001' and saves for later. Do not rerun unless you know what you do. #######
    # # sp.construct_reference_for_calibrant(calibrant_shortname='ald001',
    # #                                      calibration_folder=data_folder + experiment_name + 'microspectrometer_data/calibration/',
    # #                                      ref_concentration=0.0384048,
    # #                                      do_plot=True, do_reference_refinements=True)
    #
    # ##### This extracts concentrations from unknown reaction mixtures. You can rerun this. Do rerun this with different experiments in the future. #####
    # reaction_results = sp.concentrations_for_all_plates(timepoint_id=1,
    #                                                     experiment_folder=data_folder + experiment_name,
    #                                                     calibration_folder=data_folder + experiment_name + 'microspectrometer_data/calibration/',
    #                                                     calibrant_shortnames=['IIO029A', 'ald001'],
    #                                                     calibrant_upper_bounds=[np.inf, 2],
    #                                                     path_to_input_compositions_csv=data_folder + experiment_name + 'input_compositions/' + '20230110RF029_concentrations_in_reaction_mixtures.csv',
    #                                                     do_plot=False)

    ##### =================================== 2023-03-20-run01 ========================================================
    # dilution_factor = 200
    # experiment_name = 'multicomp-reactions/2023-03-20-run01/'
    # # ##### This constructs the calibration for the product 'IIO029A' and saves for later. Do not rerun unless you know what you do. #######
    # # sp.construct_reference_for_calibrant(calibrant_shortname='IIO029A',
    # #                                      calibration_folder=data_folder + 'multicomp-reactions/2023-01-18-run01/' + 'microspectrometer_data/calibration/',
    # #                                      ref_concentration=0.00011,
    # #                                      do_plot=True, do_reference_refinements=True)
    #
    # # #### This constructs the calibration for the substrate 'ald001' and saves for later. Do not rerun unless you know what you do. #######
    # # sp.construct_reference_for_calibrant(calibrant_shortname='ald001',
    # #                                      calibration_folder=data_folder + 'multicomp-reactions/2023-01-18-run01/' + 'microspectrometer_data/calibration/',
    # #                                      ref_concentration=0.0192096,
    # #                                      do_plot=True, do_reference_refinements=False)
    #
    # craic_folder = data_folder + 'craic_microspectrometer_measurements/absorbance/'
    # df = pd.read_csv(craic_folder + 'database_about_these_folders.csv')
    # df = df.loc[df['exp_name'] == '-'].copy().reset_index()
    #
    # concentrations_df = pd.read_csv(data_folder + experiment_name + 'outVandC/' + 'outCRF038202303201421.csv')
    #
    # # make sure that number of rows in concentrations dataframe is number of rows in df times 27 experiments per plate
    # assert len(concentrations_df.index) == len(df.index) * 27
    #
    # # add a column for the product concentration, fill it with zeros, then fill with measured values
    # concentrations_df['IIO029A'] = concentrations_df['ptsa'] * 0
    # for index, row in df.iterrows():
    #     concentrations_here = sp.concentrations_for_one_plate(experiment_folder=data_folder + experiment_name,
    #                                                           plate_folder=craic_folder + row['folder'] + '/',
    #                                                           calibration_folder=data_folder + 'multicomp-reactions/2023-01-18-run01/' + 'microspectrometer_data/calibration/',
    #                                                           calibrant_shortnames=['IIO029A', 'ald001'],
    #                                                           background_model_folder=data_folder + 'multicomp-reactions/2023-03-20-run01/microspectrometer_data/background_model/',
    #                                                           calibrant_upper_bounds=[np.inf, 1e-10],
    #                                                           do_plot=False)
    #     diluted_vials = diluted_vials_only(concentrations_here) * dilution_factor
    #     concentrations_df.at[index * 27:(index + 1) * 27 - 1, 'IIO029A'] = diluted_vials
    #
    # concentrations_df.to_csv(data_folder + experiment_name + 'results/' + 'product_concentration.csv', index=False)
    #
    # substrates = ['ald001', 'am001', 'ic001']
    # concentrations_df['yield'] = concentrations_df['IIO029A'] * 0
    # for index, row in concentrations_df.iterrows():
    #     substrate_concentrations_min = min([concentrations_df.at[index, substrate] for substrate in substrates])
    #     yield_here = concentrations_df.at[index, 'IIO029A'] / substrate_concentrations_min
    #     concentrations_df.at[index, 'yield'] = yield_here
    #
    # concentrations_df.to_csv(data_folder + experiment_name + 'results/' + 'product_concentration.csv', index=False)

    # craic_folder = data_folder + 'craic_microspectrometer_measurements/absorbance/'
    # sp.show_all_spectra(craic_folder + '2023-05-23_01-14-40__plate0000018__simple-reactions-2023-05-22-run01_calibration/')
    # sp.show_all_spectra(
    #     craic_folder + '2023-05-23_01-36-33__plate0000019__simple-reactions-2023-05-22-run01_calibration/')
    # sp.show_all_spectra(craic_folder + '2023-05-23_01-51-15__plate0000020__simple-reactions-2023-05-22-run01_calibration/')

    # sp.show_all_spectra(craic_folder + '2023-07-05_19-25-51__plate0000057__simple_reactions_2023-07-05-run01_dil/')
    # sp.show_all_spectra(craic_folder + '2023-07-05_18-02-13__plate0000054__simple_reactions_2023-07-05-run01/')
    # sp.show_all_spectra(craic_folder + '2023-07-05_18-02-13__plate0000054__simple_reactions_2023-07-05-run01/')
    # sp.show_all_spectra(craic_folder + '2023-07-05_18-02-13__plate0000054__simple_reactions_2023-07-05-run01/')
    # sp.show_all_spectra(craic_folder + '2023-06-15_15-49-38__plate0000037__pure-dmf-bkg-test/', specific_well_ids=range(10))
    # plt.legend()

    # sp.show_all_spectra(craic_folder + '2023-07-10_23-38-15__plate0000055__simple_reaction_2023-07-10_run02/')
    # sp.show_all_spectra(
    #     craic_folder + '2023-06-13_14-42-05__plate0000040__multicomponent-reactions-2023-06-13-pigments/')
    # sp.show_all_spectra(craic_folder + '2023-05-23_01-51-15__plate0000020__simple-reactions-2023-05-22-run01_calibration/')
    # plt.show()
    # wavelengths = sp.load_msp_by_id(craic_folder + '2023-04-08_16-06-36__plate0000021__2023-04-07-run01-diluted/', well_id=0)[:, 0]
    # pass

    # conc = sp.get_absorbance_at_single_wavelength_for_one_plate(craic_folder + '2023-04-08_16-06-36__plate0000021__2023-04-07-run01-diluted/',
    #                                                             wavelength_id=98,
    #                                                             ref_wavelength_id=198)

    ###################### SIMPLE SN1 REACTIONS ######################

    # plate_folder = data_folder + 'nanodrop-spectrometer-measurements/reference_for_simple_SN1/2023-09-07_22-46-02_E1_ref_and_etoh_hbr_aac.csv'
    # # # sp.show_all_spectra(data_folder + 'simple-reactions/2023-08-21-run01/nanodrop_spectra/2023-08-23_23-50-41_plate_51.csv',
    # # #                     specific_well_ids=range(10))
    # sp.show_all_spectra(plate_folder, specific_well_ids=range(7, 14, 1))
    # plt.legend()
    # plt.show()


    # run_name = 'simple-reactions/2023-08-21-run01/'
    # concentrations_here = sp.concentrations_for_one_plate(experiment_folder=data_folder + run_name,
    #                                                       plate_folder=data_folder + 'simple-reactions/2023-08-21-run01/nanodrop_spectra/2023-08-23_23-52-13_plate_51.csv',
    #                                                       calibration_folder=data_folder + 'simple-reactions/2023-08-21-run01/' + 'microspectrometer_data/calibration/',
    #                                                       calibrant_shortnames=['SN1Br03', 'SN1OH03', 'HBr'],
    #                                                       background_model_folder=data_folder + 'simple-reactions/2023-08-21-run01/microspectrometer_data/background_model/',
    #                                                       calibrant_upper_bounds=[np.inf, np.inf, np.inf],
    #                                                       do_plot=True, return_all_substances=True,
    #                                                       cut_from=50, cut_to=False,
    #                                                       ignore_abs_threshold=True)
    # print(concentrations_here)

    ###################### E1 REACTIONS ######################

    # run_name = 'simple-reactions/2023-09-06-run01/'
    # concentrations_here = sp.concentrations_for_one_plate(experiment_folder=data_folder + run_name,
    #                                                       plate_folder=data_folder + 'simple-reactions/2023-09-06-run01/nanodrop_spectra/2023-09-06_20-29-24_plate_50.csv',
    #                                                       calibration_folder=data_folder + 'simple-reactions/2023-09-06-run01/' + 'microspectrometer_data/calibration/',
    #                                                       calibrant_shortnames=['E1DB02', 'E1OH02'],
    #                                                       background_model_folder=data_folder + 'simple-reactions/2023-09-06-run01/microspectrometer_data/background_model/',
    #                                                       calibrant_upper_bounds=[np.inf, np.inf],
    #                                                       do_plot=True, return_all_substances=True,
    #                                                       cut_from=50, cut_to=False,
    #                                                       ignore_abs_threshold=True, ignore_pca_bkg=True)
    # print(concentrations_here)

    # ## JC
    # sp.nanodrop_lower_cutoff_of_wavelengths = 230
    # plate_folder = 'D:/Docs/Science/UNIST/Projects/useless-random-shit/nanodrop_spectra/' + 'raw_calibration_data/2023-09-11-PBAS-reference.csv'
    # sp.show_all_spectra(plate_folder)
    # plt.legend()
    # plt.show()