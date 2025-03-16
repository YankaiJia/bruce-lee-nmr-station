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
from datetime import datetime
########################

####Last fix#######
#-baseline correction added
#-Updated constrained and observed windows for peaks
###################

####Work in progress#######
#- Detecting overlaped
###########################

###########DATA#############
solvent_shift = 3.73  # ppm DCE
peak_width_50 = 0.01  # ppm at 50%

peaks_info = [  # Begining of region of itnerest, End of region of interest, expected peak number
    [5.20, 5.70],  # Substrate SM, 2H
    [4.1, 5.00],  # DCE
    [2.5, 3.05],
    [6.5, 7.0],  # Product B, 1H
    [4.45, 4.70],  # Product A, 2H
    [2.2, 2.7],  # HBr adduct
]
reference_shift = {
    "Starting material": [5.467],  # ppm
    "Product A": [4.527],  # ppm
    "Product B": [6.807],  # ppm
    "Solvent": [4.775, 4.693, 4.605],  # ppm
    "Solvent": [2.850, 2.764, 2.682],  # ppm
    "Unknown impurity SM peak 1": [6.453],  # ppm
    "Unknown impurity SM peak 2": [4.474],  # ppm
    "Unknown impurity 1": [6.523],
    "Unknown impurity 2": [5.509],  # ppm
    "Unknown impurity 3": [4.340],  # ppm
    "Unknown impurity 4": [2.549],  # ppm
    "Alcohol": [6.727],  # ppm
    "HBr adduct": [2.463],  # ppm
}

########Variables#########
threshold_amplitude = 1E-10  # Minimum threshold to be integrated



########Functions#########
def CSV_Loader(name_file, Yankai_temporary_fix=True):   #Yankai_temporary_fix: quick fix for the iunverted ppm scale

    name_file=r"{}".format(name_file)
    data = pd.read_csv(name_file, delimiter=',', names=['Shift', 'Intensity'], skiprows=1).values
    if Yankai_temporary_fix==True:
        data[::-1,1] = data[::,1]
    if False:
        plt.figure(figsize = (12, 6)) 
        plt.plot(data[:,0],data[:,1], alpha=0.9,linewidth=2.5)
        plt.xlabel('Shift (ppm)')
        plt.ylabel('Intensity')
        plt.title('Loading check')
        plt.show()
    
    return(data)

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
    return (1/np.pi) * (amp / ((x - cen)**2 + wid**2))

def sum_of_lorentzian(x, *params):
# Define a sum of Gaussians
    num_peaks =len(params) // 3
    y = np.zeros_like(x)
    
    for i in range(num_peaks):
        amp = params[i * 3]
        cen = params[i * 3 + 1]
        wid = params[i * 3 + 2]
        y += lorentzian(x, amp, cen, wid)
    
    return y

def fit_without_bounds(shift_array,intensity_array,initial_guesses,std_deviation):
        popt, covariance_matrix = curve_fit(
        sum_of_lorentzian, shift_array, intensity_array, p0=initial_guesses,
        sigma=std_deviation * np.ones_like(shift_array),
        absolute_sigma=True,
        maxfev=10000,   # Increase max function evaluations
        ftol=1e-14,     # Function tolerance (adjust for better precision)
        xtol=1e-14,     # Parameter change tolerance
        gtol=1e-14,     # Gradient tolerance
                            )
        return popt, covariance_matrix

def fit_with_bounds(shift_array,intensity_array,initial_guesses,std_deviation,lower_bounds,upper_bounds):
        popt, covariance_matrix = curve_fit(
        sum_of_lorentzian, shift_array, intensity_array, p0=initial_guesses, bounds=[lower_bounds,upper_bounds],
        sigma=std_deviation * np.ones_like(shift_array),
        absolute_sigma=True,
        maxfev=10000,   # Increase max function evaluations
        ftol=1e-14,     # Function tolerance (adjust for better precision)
        xtol=1e-14,     # Parameter change tolerance
        gtol=1e-14,     # Gradient tolerance
                            )
        return popt, covariance_matrix

def exponential_decay(x, a, b, c, d):
    return  a * np.exp(np.clip(b * (x+d), -700, 700)) + c # add clip to avoid overflow


def baseline_fit(shift_array, intensity_array, ppm_per_index, ppm_window = 0.1):
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
                                    shift_array-shift_offset,
                                    intensity_array, 
                                    p0=initial_guess,
                                    sigma=weights,
                                    maxfev=10000,   # Increase max function evaluations
                                    ftol=1e-14,     # Function tolerance 
                                    xtol=1e-14,     # Parameter change tolerance
                                    gtol=1e-14,     # Gradient tolerance
                                    )
    a_fit, b_fit, c_fit, d_fit = params



    baseline = baseline_function(shift_array-shift_offset, a_fit, b_fit, c_fit, d_fit)

    label=f'Baseline: {a_fit:.2f} * exp({b_fit:.2f} (x-{d_fit:.2f})) + {c_fit:.2f}'

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

def fit_peaks(NMR_spectrum, std_deviation, estimated_peak_width_for_indexes, constrained_fit=True, baseline_correction=True):
    shift_array = NMR_spectrum [:,0] 
    intensity_array = NMR_spectrum [:,1]
    intensity_array_original = intensity_array.copy()
    ppm_step = shift_array[1]-shift_array[0]
    warning_string=None
    peaks, _ = find_peaks(intensity_array, width=estimated_peak_width_for_indexes)
    # If no peaks are found, stop
    if len(peaks) == 0:
        print(f"Slices skipped, no peak found.")
        return [], [], None
    
    if False:
        print(f"{len(peaks)} found in slice: {round(shift_array[0],2)} - {round(shift_array[-1],2)} ppm.")
    
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
        lower_bounds.extend([0, cen_guess-0.03, 0])
        upper_bounds.extend([amp_guess*2, cen_guess+0.03, wid_guess*4])

    if baseline_correction == True:
        try:
            baseline = baseline_fit(shift_array, intensity_array, ppm_step)
        except:
            print("Baseline could not be corrected, attempt with reduced window...")
            try:
                baseline = baseline_fit(shift_array, intensity_array, ppm_step,ppm_window = 0.05)
            except:
                warning_string = "Baseline difficult to fit"
                try:
                    baseline = baseline_fit(shift_array, intensity_array, ppm_step,ppm_window = 0.025)
                except:
                    print("Baseline could not be fitted")
                    warning_string = "Baseline could not be fitted"
                    baseline=np.zeros_like(intensity_array)
        finally:
            intensity_array -= baseline

    # Fit peaks
    try:
        #Fitting
        if constrained_fit == False:
            popt, covariance_matrix = fit_without_bounds(shift_array,intensity_array,initial_guesses,std_deviation)
        else:
            popt, covariance_matrix = fit_with_bounds(shift_array,intensity_array,initial_guesses,std_deviation,lower_bounds,upper_bounds)
        errors_of_parameters = np.sqrt(np.diag(covariance_matrix))
        opti_parameter=popt.reshape(-1, 3)
        opti_parameter_error=errors_of_parameters.reshape(-1, 3) 

        # Generate fitted curve
        fitted_y = sum_of_lorentzian(shift_array, *popt)

        # #Autocorrelation test
        # residuals = intensity_array - sum_of_lorentzian(shift_array, *popt)
        # lag = int(estimated_peak_width_for_indexes)*2
        # lb_df = sm.stats.acorr_ljungbox(residuals, lags=[lag])
        # if len(lb_df) == 1:
        #     # take values from first row of dataframe lb_pvalue
        #     print(f"LB_pvalue : {lb_df.loc[lag, 'lb_pvalue']}, stat: {lb_df.loc[lag, 'lb_stat']}")
        # else:
        #     print('hmmm')

        max_residuals =np.max(intensity_array - sum_of_lorentzian(shift_array, *popt))
        if max_residuals >0.1 and warning_string==None:
            warning_string = "Strong residual, a peak might have been not fitted"
        # Plot original data and fit results
        if False:
            for indice, parameter in enumerate(opti_parameter):
                print(f"\nBest parameters for peak {indice}: Scale :{parameter[0]}, Center:{parameter[1]}, Width:{parameter[2]}")

            plt.imshow(covariance_matrix, cmap='seismic', vmin=-1*np.max(np.abs(covariance_matrix)), vmax=np.max(np.abs(covariance_matrix)))
            plt.colorbar()
            plt.figure(figsize=(10, 5))
            plt.plot(shift_array, intensity_array_original, color='black', label="Original Spectrum")
            plt.plot(shift_array, fitted_y+baseline, 'r--', label="Lorentzian Fit")
            plt.plot(shift_array, baseline, 'b--', label="Baseline Fit")
            plt.plot(shift_array, intensity_array_original-fitted_y, color='silver', label="Residuals")
            plt.scatter(shift_array[peaks], intensity_array_original[peaks], color='green', marker='o', label="Detected Peaks")
            plt.xlabel("Shift (ppm)")
            plt.ylabel("Intensity")
            plt.legend()
            plt.title("Peak Fitting")
            plt.show()

        return opti_parameter, opti_parameter_error, warning_string

    except RuntimeError:
        print("Curve fitting failed for this slice.")
        return [], [], ["Fit failed"]

def integration_peak (amp, cen, wid):
    return (amp/(wid))

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

def integrate_spectrum(file_name):
    # Extract the filename with extension
    filename_with_ext = os.path.basename(file_name)
    # Remove the extension
    experiment_name =os.path.basename(os.path.dirname(file_name)) #= os.path.splitext(filename_with_ext)[0]
    
    NMR_spectrum = CSV_Loader(file_name)
    std_deviation=float(np.std(NMR_spectrum[-2000:,1]))
    spectral_resolution= abs(NMR_spectrum[1,0]-NMR_spectrum[0,0])
    estimated_peak_width_for_indexes = peak_width_50 /spectral_resolution

    interval_to_slice_spectrum = merge_overlapping_intervals(peaks_info)

    if False:
        print (f"\nUseful interval in NMR: {interval_to_slice_spectrum}")

    NMR_slices = extract_slices(NMR_spectrum, interval_to_slice_spectrum)

    if False:
        for  indice, slice in enumerate(NMR_slices):
            plt.figure(figsize = (12, 6)) 
            plt.plot(slice[:,0],slice[:,1], alpha=0.9,linewidth=2.5)
            plt.xlabel('Shift (ppm)')
            plt.ylabel('Intensity')
            start=round(slice[0,0], 2)
            end=round(slice[-1,0], 2)
            plt.title(f'NMR slice:{indice}, {start} - {end} ppm')

        plt.show()

    results_dictionary={}
    results_dictionary["Warning"] = {}
    for slice in NMR_slices:
        
        parameters, error, warning_string = fit_peaks(slice, std_deviation, estimated_peak_width_for_indexes)
        
        # Iterate through fitted peak parameters
        for parameter in parameters:
            if parameter[0]<threshold_amplitude:
                continue
            fitted_center = parameter[1]  # Extract the center of the fitted peak
            peak_area = integration_peak(*parameter) *1000 # Compute peak area

            # Find the closest matching reference shift
            closest_product, closest_shift = find_closest_reference(fitted_center, reference_shift)
            
            # Append the peak area instead of overwriting
            if closest_product=='Solvent' or 'impurity' in closest_product: #Do not report solvent and impurities
                continue
            else:
                if closest_product in results_dictionary:
                    results_dictionary[closest_product] += peak_area  # Cumulate for multiplet
                else:
                    results_dictionary[closest_product] = peak_area  # Create new list

            if warning_string is not None:
                results_dictionary["Warning"][closest_product]=warning_string 

    return results_dictionary, experiment_name

def analyze_one_run_folder(master_path):

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
        experiment_dictionary, experiment_name = integrate_spectrum(file_name)
        list_experiment_loaded.append(experiment_name)
        print(f"\n{experiment_name}: {experiment_dictionary}")
        total_result_dictionary.update({experiment_name : experiment_dictionary})

    # Save dictionary as JSON
    json_filename = os.path.join(results_path, f"fitting_results.json")
    with open(json_filename, "w") as json_file:
        json.dump(total_result_dictionary, json_file, indent=4)

    # Save list to text file (each entry on a new line)
    text_filename = os.path.join(results_path, f"fitting_list.txt")
    with open(text_filename, "w") as text_file:
        text_file.write("\n".join(list_experiment_loaded))  # Write each list item on a new line

if __name__ == "__main__":



    ##TEST###
    file_list = [
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\005141-1D EXTENDED+- 12\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\005805-1D EXTENDED+- 13\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_S\215822-1D EXTENDED+-S1\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_S\220953-1D EXTENDED+-S2\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_S\222125-1D EXTENDED+-S3\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_S\223650-1D EXTENDED+-S4\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_S\224823-1D EXTENDED+-S5\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_B\205244-1D EXTENDED+-B1\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_B\210416-1D EXTENDED+-B2\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_B\211549-1D EXTENDED+-B3\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_B\213119-1D EXTENDED+-B4\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_B\214250-1D EXTENDED+-B5\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\Problematic spectra\26-1D EXTENDED+-20250304-163445\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\Problematic spectra\43-1D EXTENDED+-20250304-185249\data.csv"
    ]
    ###Problematic samples
    # file_list =[r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\Problematic spectra\26-1D EXTENDED+-20250304-163445\data.csv",r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\Problematic spectra\43-1D EXTENDED+-20250304-185249\data.csv"]
    ###

    # path_to_json = r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data"  # Path where resutls are saved

    master_path_ls = [
        'D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-02-19-run02_normal_run\\',
        'D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-03-01-run01_normal_run\\',
        'D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-03-03-run01_normal_run\\',
        'D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-03-03-run02_normal_run\\',
        'D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-03-05-run01_normal_run\\',
        'D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-03-12-run01_better_shimming\\',
        ]



    for path in master_path_ls:
        if path:
            analyze_one_run_folder(path)
