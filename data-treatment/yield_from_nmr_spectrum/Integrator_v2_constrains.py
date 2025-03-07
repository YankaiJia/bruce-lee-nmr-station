##Modules importation##
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, peak_prominences, peak_widths
from scipy.optimize import curve_fit
from numpy.polynomial.polynomial import Polynomial
import os
import json
from datetime import datetime
########################

###########Settings###########
solvent_shift = 3.73 #ppm DCE
peak_width_50 = 0.01 #ppm at 50%
threshold_amplitude = 1E-10  #Minimum threshold to be integrated


peaks_info = [  #Begining of region of itnerest, End of region of interest, expected peak number
[5.30, 5.60], #Substrate SM, 2H
[4.30, 5.00], #DCE    
[6.5, 7.1], # Product B, 1H
[4.45, 4.70], #Product A, 2H
[6.4, 6.6],#Unknown impurity SM peak1
[4.35, 4.55],#Unknown impurity SM peak 2
            ]
reference_shift={
    "Starting material": [5.467], #ppm
    "Product A": [4.527], #ppm
    "Product B": [6.807], #ppm
    "Solvent": [4.775, 4.693, 4.605], #ppm
    "Unknown impurity SM peak 1": [6.453],
    "Unknown impurity SM peak 2": [4.474],
                }
##########################


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

def fit_peaks(NMR_spectrum, std_deviation, estimated_peak_width_for_indexes, constrained_fit=True):
    shift_array = NMR_spectrum [:,0] 
    intensity_array = NMR_spectrum [:,1]
    peaks, _ = find_peaks(intensity_array, width=estimated_peak_width_for_indexes)
    # If no peaks are found, stop
    if len(peaks) == 0:
        print(f"Slices skipped, no peak found.")
        return [], []
    
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
        lower_bounds.extend([0, shift_array[0], 0])
        upper_bounds.extend([amp_guess*2, shift_array[-1], wid_guess*4])



    # Fit peaks
    try:
        if constrained_fit == False:
            popt, covariance_matrix = fit_without_bounds(shift_array,intensity_array,initial_guesses,std_deviation)
        else:
            popt, covariance_matrix = fit_with_bounds(shift_array,intensity_array,initial_guesses,std_deviation,lower_bounds,upper_bounds)
        errors_of_parameters = np.sqrt(np.diag(covariance_matrix))
        opti_parameter=popt.reshape(-1, 3)
        opti_parameter_error=errors_of_parameters.reshape(-1, 3) 

       
        # Generate fitted curve
        fitted_y = sum_of_lorentzian(shift_array, *popt)
        # Plot original data and fit results
        if False:
            for indice, parameter in enumerate(opti_parameter):
                print(f"\nBest parameters for peak {indice}: Scale :{parameter[0]}, Center:{parameter[1]}, Width:{parameter[2]}")

            plt.imshow(covariance_matrix, cmap='seismic', vmin=-1*np.max(np.abs(covariance_matrix)), vmax=np.max(np.abs(covariance_matrix)))
            plt.colorbar()
            plt.figure(figsize=(10, 5))
            plt.plot(shift_array, intensity_array, 'b-', label="Original Spectrum")
            plt.plot(shift_array, fitted_y, 'r--', label="Lorentzian Fit")
            plt.scatter(shift_array[peaks], intensity_array[peaks], color='green', marker='o', label="Detected Peaks")
            plt.xlabel("Shift (ppm)")
            plt.ylabel("Intensity")
            plt.legend()
            plt.title("Peak Fitting")
            plt.show()

        return opti_parameter, opti_parameter_error

    except RuntimeError:
        print("Curve fitting failed for this slice.")
        return [], []

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

def integrate_spectrum(file_name, plot_whole_spectrum=False, show_slices=False):
    # Extract the filename with extension
    filename_with_ext = os.path.basename(file_name)
    # Remove the extension
    experiment_name =os.path.basename(os.path.dirname(file_name)) #= os.path.splitext(filename_with_ext)[0]
    
    NMR_spectrum = CSV_Loader(file_name)

    if plot_whole_spectrum:
        plt.figure(figsize = (12, 6)) 
        plt.plot(NMR_spectrum[:,0],NMR_spectrum[:,1], alpha=0.9,linewidth=1)
        plt.gca().invert_xaxis() # show the plot from right to left
        plt.xlabel('Shift (ppm)')
        plt.ylabel('Intensity')
        plt.title('Whole NMR spectrum')
        plt.show()

    std_deviation=float(np.std(NMR_spectrum[-2000:,1]))
    spectral_resolution= abs(NMR_spectrum[1,0]-NMR_spectrum[0,0])
    estimated_peak_width_for_indexes = peak_width_50 /spectral_resolution

    interval_to_slice_spectrum = merge_overlapping_intervals(peaks_info)

    if False:
        print (f"\nUseful interval in NMR: {interval_to_slice_spectrum}")

    NMR_slices = extract_slices(NMR_spectrum, interval_to_slice_spectrum)


    if show_slices:
        for  indice, slice in enumerate(NMR_slices):
            plt.figure(figsize = (12, 6)) 
            plt.plot(slice[:,0],slice[:,1], alpha=0.9,linewidth=2.5)
            plt.xlabel('Shift (ppm)')
            plt.ylabel('Intensity')
            start=round(slice[0,0], 2)
            end=round(slice[-1,0], 2)
            plt.title(f'NMR slice:{indice}, {start} - {end} ppm')

            plt.figure(figsize = (12, 6)) 
            plt.plot(slice[:,1], alpha=0.9,linewidth=2.5)
            plt.xlabel('Indices')
            plt.ylabel('Intensity')
            plt.title(f'NMR slice:{indice}, {start} - {end} ppm')
        plt.show()

    results_dictionary={}

    for slice in NMR_slices:
        
        parameters, error = fit_peaks(slice, std_deviation, estimated_peak_width_for_indexes)
        
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

    return results_dictionary, experiment_name

def integrate_one_folder(master_path, is_save_json=False):
    
        ########Variables#########
        total_result_dictionary = {}
        list_experiment_loaded = []
        ##########################

        if master_path is not None:
            # Initialize list to store full paths of matching folders
            matching_folders = []

            # Define the target folder name
            target_folder = "Results"

            # Check if "Results" folder exists
            results_path = os.path.join(master_path, target_folder)
            # print(f'results_path: {results_path}')
            if os.path.isdir(results_path):  # Ensure "Results" is a directory
                # print(f"'{target_folder}' folder found at: {results_path}")

                # Iterate through subfolders inside "Results"
                for folder in os.listdir(results_path):
                    folder_path = os.path.join(results_path, folder)
                    # print(f'folder_path: {folder_path}')
                    
                    # Check if it's a directory and contains "1D EXTENDED"
                    if os.path.isdir(folder_path) and "1D EXTENDED" in folder:
                        folder_path_extended=folder_path+"\\data.csv"
                        matching_folders.append(folder_path_extended)
                        print(folder_path_extended, end="\n\n")

            file_list = matching_folders
        # sort the list according to the first two digits of the file name
        file_list.sort(key=lambda x: int(x.split('\\')[-2].split("-")[0]))

        # Iterate through CSV from the list to fit and obtain absolute area
        for file_name in file_list:
            print(f"\nProcessing: {file_name}")
            experiment_dictionary, experiment_name=integrate_spectrum(file_name,
                                                                    plot_whole_spectrum=False,
                                                                    show_slices=False)
            list_experiment_loaded.append(experiment_name)
            print(f"\n{experiment_name}: {experiment_dictionary}")
            # total_result_dictionary.update({experiment_name : experiment_dictionary}) 
            total_result_dictionary[experiment_name] = experiment_dictionary


        # Get current date in YYYY-MM-DD format
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Define full JSON file path
        path_to_json = results_path
        # json_filename = os.path.join(path_to_json, f"Fitting_results_{current_date}.json")
        json_filename = os.path.join(path_to_json, "integration_results.json")

        # Save dictionary as JSON
        if is_save_json:
            with open(json_filename, "w") as json_file:
                json.dump(total_result_dictionary, json_file, indent=4)

        # Define the text file path
        text_filename = os.path.join(path_to_json, f"reaction_name_list.txt")

        # Save list to text file (each entry on a new line)
        if is_save_json:
            with open(text_filename, "w") as text_file:
                text_file.write("\n".join(list_experiment_loaded))  # Write each list item on a new line

            print(f"\nResults saved to: {path_to_json}")

if __name__ == "__main__":

    
    #####File location########
    file_list =[
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_S\215822-1D EXTENDED+-S1\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_S\220953-1D EXTENDED+-S2\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_S\222125-1D EXTENDED+-S3\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_S\223650-1D EXTENDED+-S4\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_S\224823-1D EXTENDED+-S5\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\005141-1D EXTENDED+- 12\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\005805-1D EXTENDED+- 13\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_B\205244-1D EXTENDED+-B1\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_B\210416-1D EXTENDED+-B2\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_B\211549-1D EXTENDED+-B3\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_B\213119-1D EXTENDED+-B4\data.csv",
        r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data\ref_B\214250-1D EXTENDED+-B5\data.csv"
        ]
    path_to_json=r"c:\Users\UNIST\Desktop\Louis Korea\Yasemin-Yankai NMR\Data"   #Path where resutls are saved

    master_path_ls = \
    ["D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-02-19-run02_normal_run\\",
    # "D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-03-01-run01_normal_run",
    # "D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-03-03-run01_normal_run",
    # "D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-03-03-run02_normal_run"
    ]

    # master_path_ls = ['D:\\Dropbox\\brucelee\\data\\DPE_bromination\\_Refs\\ref_S\\']

    # master_path=None #Example of automated generated file_list: r"C:\Users\UNIST\Dropbox\brucelee\data\DPE_bromination\2025-03-03-run01_normal_run" 
    for master_path in master_path_ls:
    ##########################

        integrate_one_folder(master_path)