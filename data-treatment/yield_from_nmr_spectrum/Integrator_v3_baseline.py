##Modules importation##
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, peak_prominences, peak_widths
from scipy.optimize import curve_fit
import statsmodels.api as sm
from numpy.polynomial.polynomial import Polynomial
import os
import json
import math
import re

# change backend for matplotlib to Qt5Agg
plt.switch_backend('TkAgg')

# get teh system path of BRUCELEE_PROJECT_DATA_PATH
BRUCELEE_PROJECT_DATA_PATH = os.environ['BRUCELEE_PROJECT_DATA_PATH']

########################
####Last fix#######
#-baseline correction added
#-Updated constrained and observed windows for peaks
###################

####Work in progress#######
#- Detecting overlaped
###########################

solvent_shift = None
peak_width_50 = None
threshold_amplitude = None
peaks_info, reference_shift = None, None

def specify_para(sol_name, outlier_type=None):

    """Specify global parameters based on the solvent name and outlier_type"""

    global solvent_shift, peak_width_50, threshold_amplitude, peaks_info, reference_shift

    if sol_name == 'DCE':
        solvent_shift = 3.73  #ppm DCE
        peak_width_50 = 0.008  #ppm at 50% #Default 0.01
        threshold_amplitude = 1E-7  # Minimum threshold to be integrated
        peaks_info = [  # Begining of region of itnerest, End of region of interest, expected peak number
            [5.20, 5.70],  # Substrate SM, 2H
            [4.1, 5.00],  # DCE
            [2.5, 3.05],  # DCE
            [6.5, 7.0],  # Product B, 1H
            [4.45, 4.70],  # Product A, 2H
            [2.2, 2.7],  # HBr adduct
            [7.80, 14],  #Acid?
        ]
        reference_shift = {
            "Starting material": [5.467],  # ppm
            "Product A": [4.527],  # ppm
            "Product B": [6.807],  # ppm
            "SolventDown": [4.775, 4.693, 4.605],  # ppm
            "SolventUp": [2.850, 2.764, 2.682],  # ppm
            "Unknown impurity SM peak 1": [6.453],  # ppm
            "Unknown impurity SM peak 2": [4.474],  # ppm
            "Unknown impurity 1": [6.523],
            "Unknown impurity 2": [5.509],  # ppm
            "Unknown impurity 3": [4.340],  # ppm
            "Unknown impurity 4": [2.549],  # ppm
            "Alcohol": [6.727],  # ppm
            "HBr_adduct": [2.463],  # ppm
            "Acid": [8.0]
        }

        if outlier_type == 'Type1':  # Type 1 outlier: Asymetric pick upshift of Product B
            print("Type1 error paras are set in if conditon!")
            # global solvent_shift, peak_width_50, threshold_amplitude, peaks_info, reference_shift


            solvent_shift = 3.73  #ppm DCE
            peak_width_50 = 0.008  #ppm at 50% #Default 0.01
            threshold_amplitude = 1E-7  # Minimum threshold to be integrated
            peaks_info = [  # Begining of region of itnerest, End of region of interest, expected peak number
                [5.20, 5.70],  # Substrate SM, 2H
                [4.1, 5.00],  # DCE
                [2.5, 3.05],  # DCE
                [6.5, 6.9],  # Product B, 1H   ############Truncate the asymetric peak for baseline fitting to take care
                [4.45, 4.70],  # Product A, 2H
                [2.2, 2.7],  # HBr adduct
                [7.80, 14],  #Acid?
            ]
            reference_shift = {
                "Starting material": [5.467],  # ppm
                "Product A": [4.527],  # ppm
                "Product B": [6.807],  # ppm
                "SolventDown": [4.775, 4.693, 4.605],  # ppm
                "SolventUp": [2.850, 2.764, 2.682],  # ppm
                "Unknown impurity SM peak 1": [6.453],  # ppm
                "Unknown impurity SM peak 2": [4.474],  # ppm
                "Unknown impurity 1": [6.523],
                "Unknown impurity 2": [5.509],  # ppm
                "Unknown impurity 3": [4.340],  # ppm
                "Unknown impurity 4": [2.549],  # ppm
                "Alcohol": [6.727],  # ppm
                "HBr_adduct": [2.463],  # ppm
                "Acid": [8.0]
            }
            #pass # change corresponding parameters
        elif outlier_type == 'Type2':  # Type 2 outlier: Asymetric pick downshift of Product B
            print("Type2 error paras are set in if conditon!")
            # global solvent_shift, peak_width_50, threshold_amplitude, peaks_info, reference_shift

            solvent_shift = 3.73  #ppm DCE
            peak_width_50 = 0.008  #ppm at 50% #Default 0.01
            threshold_amplitude = 1E-7  # Minimum threshold to be integrated
            peaks_info = [  # Begining of region of itnerest, End of region of interest, expected peak number
                [5.20, 5.70],  # Substrate SM, 2H
                [4.1, 5.00],  # DCE
                [2.5, 3.05],  # DCE
                [6.6, 7.0],  # Product B, 1H   ####Truncate the asymetric peak for baseline fitting to take care
                [4.45, 4.70],  # Product A, 2H
                [2.2, 2.7],  # HBr adduct
                [7.80, 14],  #Acid?
            ]
            reference_shift = {
                "Starting material": [5.467],  # ppm
                "Product A": [4.527],  # ppm
                "Product B": [6.807],  # ppm
                "SolventDown": [4.775, 4.693, 4.605],  # ppm
                "SolventUp": [2.850, 2.764, 2.682],  # ppm
                "Unknown impurity SM peak 1": [6.453],  # ppm
                "Unknown impurity SM peak 2": [4.474],  # ppm
                "Unknown impurity 1": [6.523],
                "Unknown impurity 2": [5.509],  # ppm
                "Unknown impurity 3": [4.340],  # ppm
                "Unknown impurity 4": [2.549],  # ppm
                "Alcohol": [6.727],  # ppm
                "HBr_adduct": [2.463],  # ppm
                "Acid": [8.0]
            }
            #pass

    elif sol_name == 'MeCN':
        solvent_shift = 1.96  # ppm ACN
        peak_width_50 = 0.008  # ppm at 50% #Default 0.01
        threshold_amplitude = 1E-7  # Minimum threshold to be integrated
        peaks_info = [  # Begining of region of itnerest, End of region of interest, expected peak number
            [7.80, 14],
            [6.5, 7.15],  
            [4.4, 4.80],  
            [3.8, 4.4],  
            [2.8, 3.3],
            [2.65,2.75]
        ]
        reference_shift = {
            "Starting material": [4.612],  # ppm
            "Product A": [3.946],  # ppm
            "Product B": [6.899],  # ppm
            "SolventDown": [2.786],  # ppm
            "SolventUp": [1.085],  # ppm
            "Unknown 1": [2.937],
            "Unknown 2": [4.645],  # ppm
            "Unknown 3": [4.201],  # ppm
            "Unknown 4": [3.946],  # ppm
            "Unknown 5": [7.029],  # ppm
            "Unknown 6": [2.366],  # ppm
            "Acid": [8.0],
            "Water": [2.13]
        }

        if outlier_type == 'Type1':  # Type 1 outlier
            pass # change corresponding parameters
        elif outlier_type == 'Type2':  # Type 2 outlier
            pass



########Functions#########
def CSV_Loader(name_file, Yankai_temporary_fix=True):  #Yankai_temporary_fix: quick fix for the iunverted ppm scale

    name_file = r"{}".format(name_file)
    data = pd.read_csv(name_file, delimiter=',', names=['Shift', 'Intensity'], skiprows=1).values
    if Yankai_temporary_fix == True:
        data[::-1, 1] = data[::, 1]
    if False:
        plt.figure(figsize=(12, 6))
        plt.plot(data[:, 0], data[:, 1], alpha=0.9, linewidth=2.5)
        plt.xlabel('Shift (ppm)')
        plt.ylabel('Intensity')
        plt.title('Loading check')
        plt.show()

    return (data)


def merge_overlapping_intervals(peaks_info):
    # Sort intervals based on the start of the range
    peaks_info.sort(key=lambda x: x[0])

    merged_intervals = []

    for interval in peaks_info:
        start, end = interval[:2]  # Extract the first two values (range start and end)

        if not merged_intervals or merged_intervals[-1][1] < start:
            # No overlap, add as a new separate interval
            merged_intervals.append([start, end])
        else:
            # Overlapping, merge with the last interval by extending the end point
            merged_intervals[-1][1] = max(merged_intervals[-1][1], end)

    return merged_intervals


def extract_slices(nmr_data, merged_intervals):
    """
    Extracts slices from the 2D numpy array based on merged intervals.

    Parameters:
    - nmr_data: 2D numpy array where first column is NMR SHIFT and second column is Intensity
    - merged_intervals: List of merged intervals [[start1, end1], [start2, end2], ...]

    Returns:
    - List of numpy arrays, each representing a slice
    """
    slices = []

    for start, end in merged_intervals:
        # Extract rows where NMR SHIFT falls within the interval
        mask = (nmr_data[:, 0] >= start) & (nmr_data[:, 0] <= end)
        slice_data = nmr_data[mask]
        slices.append(slice_data)

    return slices


def lorentzian(x, amp, cen, wid):
    # Define a Lorentzian function
    return (1 / np.pi) * (amp / ((x - cen) ** 2 + wid ** 2))


def sum_of_lorentzian(x, *params):
    # Define a sum of Gaussians
    num_peaks = len(params) // 3
    y = np.zeros_like(x)

    for i in range(num_peaks):
        amp = params[i * 3]
        cen = params[i * 3 + 1]
        wid = params[i * 3 + 2]
        y += lorentzian(x, amp, cen, wid)

    return y


def fit_without_bounds(shift_array, intensity_array, initial_guesses, std_deviation):
    popt, covariance_matrix = curve_fit(
        sum_of_lorentzian, shift_array, intensity_array, p0=initial_guesses,
        sigma=std_deviation * np.ones_like(shift_array),
        absolute_sigma=True,
        maxfev=10000,  # Increase max function evaluations
        ftol=1e-14,  # Function tolerance (adjust for better precision)
        xtol=1e-14,  # Parameter change tolerance
        gtol=1e-14,  # Gradient tolerance
    )
    return popt, covariance_matrix


def fit_with_bounds(shift_array, intensity_array, initial_guesses, std_deviation, lower_bounds, upper_bounds):
    popt, covariance_matrix = curve_fit(
        sum_of_lorentzian, shift_array, intensity_array, p0=initial_guesses, bounds=[lower_bounds, upper_bounds],
        sigma=std_deviation * np.ones_like(shift_array),
        absolute_sigma=True,
        maxfev=10000,  # Increase max function evaluations
        ftol=1e-14,  # Function tolerance (adjust for better precision)
        xtol=1e-14,  # Parameter change tolerance
        gtol=1e-14,  # Gradient tolerance
    )
    return popt, covariance_matrix


def exponential_decay(x, a, b, c, d):
    return a * np.exp(np.clip(b * (x + d), -700, 700)) + c  # add clip to avoid overflow


def baseline_fit(shift_array, intensity_array, ppm_per_index, ppm_window=0.1):
    indices_to_keep = int(ppm_window / ppm_per_index)
    shift_offset = shift_array[0]

    if False:
        # Plot data and fitted curve
        plt.plot(shift_array, intensity_array, label='Data', color='Black')
        plt.axvline(shift_array[indices_to_keep], color='blue', linestyle='--', label='Ignored Region Start')
        plt.axvline(shift_array[-indices_to_keep], color='blue', linestyle='--', label='Ignored Region End')
        plt.legend()
        plt.xlabel('Shift (ppm)')
        plt.ylabel('Intensity')
        plt.title('Baseline fitting')
        plt.show()

    # Define weights 
    weights = np.ones_like(intensity_array)  # Default all weights = 1

    # Mask data
    weights[indices_to_keep:-indices_to_keep] = 100

    # Select baseline function

    baseline_function = exponential_decay
    initial_guess = [
        np.max(intensity_array) - np.min(intensity_array),  # A_guess (Amplitude)
        -0.1 if intensity_array[0] > intensity_array[-1] else 0.1,  # B_guess (Decay/Growth)
        np.min(intensity_array),  # C_guess (Offset)
        shift_array[np.argmax(np.gradient(intensity_array))]  # D_guess (Delay point)
    ]

    params, covariance = curve_fit(baseline_function,
                                   shift_array - shift_offset,
                                   intensity_array,
                                   p0=initial_guess,
                                   sigma=weights,
                                   maxfev=10000,  # Increase max function evaluations
                                   ftol=1e-14,  # Function tolerance
                                   xtol=1e-14,  # Parameter change tolerance
                                   gtol=1e-14,  # Gradient tolerance
                                   )
    a_fit, b_fit, c_fit, d_fit = params

    baseline = baseline_function(shift_array - shift_offset, a_fit, b_fit, c_fit, d_fit)

    label = f'Baseline: {a_fit:.2f} * exp({b_fit:.2f} (x-{d_fit:.2f})) + {c_fit:.2f}'

    if False:
        # Plot data and fitted curve
        plt.plot(shift_array, intensity_array, label='Data', color='Black')
        plt.plot(shift_array, baseline, label=label, color='red')
        plt.legend()
        plt.xlabel('Shift (ppm)')
        plt.ylabel('Intensity')
        plt.title('Baseline fitting')
        plt.show()

    return baseline


def fit_peaks(NMR_spectrum, std_deviation,
              estimated_peak_width_for_indexes,
              shift_tolerance=0.02,
              constrained_fit=True,
              baseline_correction=True,
              is_show_plot=False
              ):
    shift_array = NMR_spectrum[:, 0]
    intensity_array = NMR_spectrum[:, 1]
    intensity_array_original = intensity_array.copy()
    ppm_step = shift_array[1] - shift_array[0]
    warning_string = None
    peaks, _ = find_peaks(intensity_array, width=estimated_peak_width_for_indexes)
    # If no peaks are found, stop
    if len(peaks) == 0:
        print(f"Slices skipped, no peak found.")
        return [], [], None, []

    if False:
        print(f"{len(peaks)} found in slice: {round(shift_array[0], 2)} - {round(shift_array[-1], 2)} ppm.")

    # Get initial guesses for peak parameters (amplitude, center, width)
    initial_guesses = []

    lower_bounds = []
    upper_bounds = []

    for peak in peaks[:]:
        if intensity_array[peak] > 0:
            amp_guess = intensity_array[peak]  # Peak height
        else:
            amp_guess = std_deviation
        cen_guess = shift_array[peak]  # Peak center
        wid_guess = peak_width_50  # Initial width guess (adjust as needed)
        initial_guesses.extend([amp_guess, cen_guess, wid_guess])
        lower_bounds.extend([0, cen_guess - shift_tolerance, 0])
        upper_bounds.extend([amp_guess * 2, cen_guess + shift_tolerance, wid_guess * 4])

    if baseline_correction == True:

        try:
            baseline = baseline_fit(shift_array, intensity_array, ppm_step)
        except:
            print("Baseline could not be corrected, attempt with reduced window...")
            try:
                baseline = baseline_fit(shift_array, intensity_array, ppm_step, ppm_window=0.05)
            except:
                warning_string = "Baseline difficult to fit"
                try:
                    baseline = baseline_fit(shift_array, intensity_array, ppm_step, ppm_window=0.025)
                except:
                    print("Baseline could not be fitted")
                    warning_string = "Baseline could not be fitted"
                    baseline = np.zeros_like(intensity_array)
        finally:
            intensity_array -= baseline

    # Fit peaks
    fig = []
    try:
        #Fitting
        if constrained_fit == False:
            popt, covariance_matrix = fit_without_bounds(shift_array, intensity_array, initial_guesses, std_deviation)
        else:
            popt, covariance_matrix = fit_with_bounds(shift_array, intensity_array, initial_guesses, std_deviation,
                                                      lower_bounds, upper_bounds)
        errors_of_parameters = np.sqrt(np.diag(covariance_matrix))
        opti_parameter = popt.reshape(-1, 3)
        opti_parameter_error = errors_of_parameters.reshape(-1, 3)

        # Generate fitted curve
        fitted_y = sum_of_lorentzian(shift_array, *popt)

        max_residuals = np.max(intensity_array - sum_of_lorentzian(shift_array, *popt))
        if max_residuals > 0.1 and warning_string == None:
            warning_string = "Strong residual: a peak might have been not fitted"

        # Plot original data and fit results
        # for indice, parameter in enumerate(opti_parameter):
        #     print(
        #         f"\nBest parameters for peak {indice}:  Scale :{parameter[0]}  Center:{parameter[1]}  Width:{parameter[2]}")

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))  # Two subplots (1 row, 2 columns)
        # ---- Subplot 1: Covariance Matrix ----
        ax1 = axes[0]
        cax = ax1.imshow(covariance_matrix, cmap='seismic',
                         vmin=-1 * np.max(np.abs(covariance_matrix)),
                         vmax=np.max(np.abs(covariance_matrix)))
        fig.colorbar(cax, ax=ax1)
        ax1.set_title("Covariance Matrix")
        # ---- Subplot 2: Spectral Data and Fitting Results ----
        ax2 = axes[1]
        ax2.plot(shift_array, intensity_array_original, color='black', label="Original Spectrum")
        ax2.plot(shift_array, fitted_y + baseline, 'r--', label="Lorentzian Fit")
        ax2.plot(shift_array, baseline, 'b--', label="Baseline Fit")
        ax2.plot(shift_array, intensity_array_original - fitted_y, color='silver', label="Residuals")
        ax2.scatter(shift_array[peaks], intensity_array_original[peaks], color='green', marker='o',
                    label="Detected Peaks")
        ax2.set_xlabel("Shift (ppm)")
        ax2.set_ylabel("Intensity")
        ax2.legend()
        ax2.set_title("Peak Fitting")

        if is_show_plot:
            plt.tight_layout()  # Adjust spacing between plots
            plt.show()
        else:
            plt.close(fig)

        return opti_parameter, opti_parameter_error, warning_string, fig

    except RuntimeError:
        print("Curve fitting failed for this slice.")
        return [], [], ["Fit failed"], 0


def integration_peak(amp, cen, wid):
    return (amp / (wid))


def find_closest_reference(fitted_center, reference_dict):
    """
    Find the closest reference shift in the dictionary for a given fitted peak center.
    
    - fitted_center: The peak center from the fitted parameters.
    - reference_dict: Dictionary of reference shifts.

    Returns:
    - The name of the closest product/material.
    - The corresponding reference shift.
    """
    closest_product = None
    closest_shift = None
    min_difference = float('inf')  # Initialize with a very large value

    for product, shifts in reference_dict.items():
        for shift in shifts:  # Handle multiple reference shifts per product
            difference = abs(fitted_center - shift)
            if difference < min_difference:
                min_difference = difference
                closest_product = product
                closest_shift = shift

    return closest_product, closest_shift


def replot_fittings(figures, is_show_plot=False, dir=None):
    num_figs = len(figures)

    if num_figs == 0:
        print("No figures to plot.")
        return None

    num_cols = 3
    num_rows = math.ceil(num_figs / num_cols)

    # Create the figure with the correct number of rows and columns
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(4 * num_cols, 4 * num_rows))
    fig.suptitle(dir, fontsize=12, fontweight="bold")

    # Flatten axes array for easy indexing
    axes = axes.flatten()

    # Iterate over stored figures and plot on the new shared figure
    for i, fig_old in enumerate(figures):
        for ax_old in fig_old.axes:  # Extract each axis from the stored figure
            for line in ax_old.get_lines():  # Extract line plots
                axes[i].plot(line.get_xdata(), line.get_ydata(), label=line.get_label())

                # set title for each subplot
                useful_peaks = ["Starting material", "Product A", "Product B", "HBr_adduct", "Acid"]
                reference_shift_here = {k: reference_shift[k] for k in useful_peaks}
                x_min, x_max = ax_old.get_xlim()  # Get the x-axis limits
                for key, value in reference_shift_here.items():
                    if x_min <= value[0] <= x_max:
                        axes[i].set_title(key)

            # axes[i].set_title(ax_old.get_title())
            axes[i].set_xlabel(ax_old.get_xlabel())
            axes[i].set_ylabel(ax_old.get_ylabel())
            if axes[i].has_data():  # Only add legend if data exists
                axes[i].legend()

    # Hide any unused subplots (if the last row is not full)
    for j in range(num_figs, len(axes)):
        axes[j].axis("off")  # Instead of fig.delaxes(), just hide the extra axes

    plt.tight_layout()

    if is_show_plot:
        plt.show(block=True)  # Show only the combined figure and block execution
    else:
        plt.close(fig)  # Close the figure without showing it

    return fig


def integrate_spectrum(file_name, is_save_plot=True, is_show_plot=False):
    # get the dir path of the file
    file_dir = os.path.dirname(file_name)
    # Remove the extension
    experiment_name = os.path.basename(os.path.dirname(file_name))  #= os.path.splitext(filename_with_ext)[0]

    NMR_spectrum = CSV_Loader(file_name)
    std_deviation = float(np.std(NMR_spectrum[-2000:, 1]))
    spectral_resolution = abs(NMR_spectrum[1, 0] - NMR_spectrum[0, 0])
    estimated_peak_width_for_indexes = peak_width_50 / spectral_resolution

    interval_to_slice_spectrum = merge_overlapping_intervals(peaks_info)

    if False:  # for debugging
        print(f"\nUseful interval in NMR: {interval_to_slice_spectrum}")

    NMR_slices = extract_slices(NMR_spectrum, interval_to_slice_spectrum)

    if False:  # for debugging
        for indice, slice in enumerate(NMR_slices):
            plt.figure(figsize=(12, 6))
            plt.plot(slice[:, 0], slice[:, 1], alpha=0.9, linewidth=2.5)
            plt.xlabel('Shift (ppm)')
            plt.ylabel('Intensity')
            start = round(slice[0, 0], 2)
            end = round(slice[-1, 0], 2)
            plt.title(f'NMR slice:{indice}, {start} - {end} ppm')

        plt.show()

    results_dictionary = process_nmr_peaks(
        NMR_slices,
        std_deviation,
        estimated_peak_width_for_indexes,
        threshold_amplitude,
        reference_shift,
        fit_peaks,
        integration_peak,
        find_closest_reference,
        file_dir,
        is_save_plot,
        is_show_plot,
    )

    return results_dictionary, experiment_name


def process_nmr_peaks(
        NMR_slices,
        std_deviation,
        estimated_peak_width_for_indexes,
        threshold_amplitude,
        reference_shift,
        fit_peaks_func,
        integration_peak_func,
        find_closest_reference_func,
        file_dir,
        is_save_plot=True,
        is_show_plot=False
):
    """
    Processes NMR peaks from slices and assigns each product the closest matching peak.
    Adds a warning if some peaks are not used in the final assignment.

    Returns:
    - results_dictionary: dictionary of product to peak area, with warnings if any
    """

    all_peaks = []
    figures = []

    for slice in NMR_slices:
        parameters, error, warning_string, fig = fit_peaks_func(slice, std_deviation, estimated_peak_width_for_indexes)

        if fig:
            figures.append(fig)

        for parameter in parameters:
            if parameter[0] < threshold_amplitude:
                continue

            fitted_center = parameter[1]
            peak_area = integration_peak_func(*parameter) * 1000

            closest_product, closest_shift = find_closest_reference_func(fitted_center, reference_shift)

            if 'SolventDown' in closest_product or 'SolventUp' in closest_product:
                continue

            all_peaks.append({
                'product': closest_product,
                'center': fitted_center,
                'area': peak_area,
                'parameter': parameter,
                'amplitude': parameter[0],
                'warning': warning_string
            })

    # Assign closest peak to each product
    closest_peaks = {}
    for peak in all_peaks:
        prod = peak['product']
        center = peak['center']
        ref_center = reference_shift[prod]
        distance = abs(center - ref_center)

        if prod not in closest_peaks or distance < abs(closest_peaks[prod]['center'] - ref_center):
            closest_peaks[prod] = peak

    results_dictionary = {'Warning': {}}
    for prod, peak in closest_peaks.items():
        results_dictionary[prod] = peak['area']
        if peak['warning'] is not None:
            results_dictionary['Warning'][prod] = peak['warning']

    # Extract unmatched peaks (above-threshold, not assigned)
    assigned_peak_ids = {id(peak) for peak in closest_peaks.values()}

    unmatched_peaks = [
        f"center={round(peak['center'], 3)} ppm    area={peak['area']}"
        for peak in all_peaks
        if id(peak) not in assigned_peak_ids and peak['amplitude'] >= threshold_amplitude
    ]

    if unmatched_peaks:
        results_dictionary['Warning']['UnmatchedPeaks'] = unmatched_peaks

    fig_combined = replot_fittings(figures, is_show_plot=is_show_plot, dir=file_dir)

    if is_save_plot and fig_combined:
        fig_combined.savefig(file_dir + "\\fitting_results.png")

    return results_dictionary


def analyze_one_run_folder(master_path,
                           sol_name='DCE',
                           outliers=None,  # Example: {33:'Type1', 43:'Type2'}
                           is_show_plot=False):

    total_result_dictionary = {}
    list_experiment_loaded = []
    data_dir_ls = []
    data_file_ls = []

    results_path = os.path.join(master_path, "Results")
    if not os.path.isdir(results_path):  # Ensure "Results" is a directory
        raise FileNotFoundError(f"Error! Results folder not found in: {master_path}")

    # Iterate through subfolders inside "Results"
    for folder in os.listdir(results_path):
        folder_path = os.path.join(results_path, folder)
        if "1D EXTENDED" in folder_path:
            data_dir_ls.append(folder_path)
            data_file = folder_path + "\\data.csv"
            if not os.path.isfile(data_file):
                raise FileNotFoundError(f"Error! Data file not found in: {folder_path}")
            data_file_ls.append(data_file)

    # Iterate through CSV from the list to fit and obtain absolute area
    for file_name in data_file_ls:

        # Specify global parameters based on the solvent name and outlier_type
        if not outliers:
            specify_para(sol_name)
        else:
            print(file_name)
            # Extract vial number by regex
            vial_name_here = re.search(r'(\d+)-1D', file_name).group(1)
            vial_name_here = int(vial_name_here)
            if vial_name_here in outliers.keys():
                specify_para(sol_name, outliers[vial_name_here])
                print('##########Outlier type specified for vial##########:', file_name)
            else:
                specify_para(sol_name)
        ###################################

        experiment_dictionary, experiment_name = integrate_spectrum(file_name, is_save_plot=True,
                                                                    is_show_plot=is_show_plot)
        list_experiment_loaded.append(experiment_name)
        print(f"\n{experiment_name}: {experiment_dictionary}")
        total_result_dictionary.update({experiment_name: experiment_dictionary})

    # Save dictionary as JSON
    json_filename = os.path.join(results_path, f"fitting_results.json")
    with open(json_filename, "w") as json_file:
        json.dump(total_result_dictionary, json_file, indent=4)

    # Save list to text file (each entry on a new line)
    text_filename = os.path.join(results_path, f"fitting_list.txt")
    with open(text_filename, "w") as text_file:
        text_file.write("\n".join(list_experiment_loaded))  # Write each list item on a new line


if __name__ == "__main__":

    data_dir = BRUCELEE_PROJECT_DATA_PATH
    print(BRUCELEE_PROJECT_DATA_PATH)
    # run folder structure: [run_folder, run_sol, run_outliers]
    run_folders = [
                #["\\DPE_bromination\\2025-02-19-run02_normal_run\\", 'DCE', None],
                #["\\DPE_bromination\\2025-03-01-run01_normal_run\\", 'DCE', None],
                #["\\DPE_bromination\\2025-03-03-run01_normal_run\\", 'DCE', {46: 'Type1', 47: 'Type2'}],
                ["\\DPE_bromination\\2025-03-03-run01_normal_runTEST\\", 'DCE', {46: 'Type1', 47: 'Type2'}],
                #["\\DPE_bromination\\2025-03-03-run02_normal_run\\", 'DCE', None],
                #["\\DPE_bromination\\2025-03-05-run01_normal_run\\", 'DCE', None],
                #["\\DPE_bromination\\2025-03-12-run01_better_shimming\\", 'DCE', None]
                ]

    for run_folder in run_folders:
        run_dir = data_dir + run_folder[0]
        run_sol = run_folder[1]
        run_outliers = run_folder[2]

        analyze_one_run_folder(run_dir, run_sol, run_outliers,is_show_plot=False)

    print("All runs processed successfully.")