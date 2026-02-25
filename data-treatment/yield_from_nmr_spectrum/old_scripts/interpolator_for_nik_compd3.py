# construct a linear interpolator for the NMR spectrum of Nik Compd 3

import numpy as np
from scipy.interpolate import interp1d
import os, json, pickle
import pandas as pd
import re


def load_integral_json_file(file):
    """Load the integral from a JSON file."""
    with open(file, 'r') as f:
        data = json.load(f)
        integral = data['second_peak_integral']
    return integral

data_folder = r"D:\Dropbox\brucelee\data\NV\Final Data\Calibrations\MeCN\Mixture_compd2_and_compd3"

# get all the subfolders in the data folder
subfolders = [f.path for f in os.scandir(data_folder) if f.is_dir()]
json_files = [folder+'\hardy_fitting_report.json' for folder in subfolders]
fitted_integrals = [load_integral_json_file(file) for file in json_files]
exp_concentrations = [3, 8, 12, 50]

# create a linear interpolator to get the concentration from the integral
interpolator = interp1d(fitted_integrals, exp_concentrations, bounds_error=False, fill_value='extrapolate')

# save the interpolator to pickle file
pickle_file_path = os.path.join(data_folder, 'interpolator_for_nik_compd3.pkl')
with open(pickle_file_path, 'wb') as file:
    pickle.dump(interpolator, file)

# an example of how to use the interpolator
def get_concentration_from_integral(integral):
    """Get the concentration from the integral using the interpolator."""
    return float(interpolator(integral))

def get_all_json_files_from_one_run(run_folder, json_name='hardy_fitting_report.json'):

    results_folder = run_folder + '/Results'
    assert os.path.exists(results_folder), f"Results folder {results_folder} does not exist."

    # get all subfolder in the results_folder if "1D EXTENDED" is in the name
    subfolders = [f.path for f in os.scandir(results_folder) if f.is_dir() and "1D EXTENDED" in f.name]

    json_files = [os.path.join(folder, json_name) for folder in subfolders if os.path.exists(os.path.join(folder, json_name))]

    assert all(os.path.exists(file) for file in json_files), "Not all JSON files exist."

    return json_files

def filter_json_files(json_list_before_filter):

    json_list_after_filter = []
    for json_file in json_list_before_filter:
        with open(json_file, 'r') as file:
            data = json.load(file)
            # calculate the coefficient of variation (cv)
            cv = 0 if data["second_peak_intensity"]==0 else data['second_peak_intensity_uncertainty']/data["second_peak_intensity"]
            if cv < 0.5:
                json_list_after_filter.append(json_file)

    return json_list_after_filter


def convert_ndarray(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_ndarray(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_ndarray(item) for item in obj]
    else:
        return obj

def generate_csv_with_vol_and_conc_and_spectrum_names(run_folder, conc_global_index_csv=
                                   r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\conc_with_global_index.csv"):
    print(f"Generating CSV with volume and concentration for run folder: {run_folder}")
    df_conc_with_global_index = pd.read_csv(conc_global_index_csv)

    # note: conc, excel, results
    results_folder = run_folder + r'/Results/'
    assert os.path.exists(results_folder), f"Results folder {results_folder} does not exist."

    # get excel for this run
    excel_name = re.search(r"\b\d{4}-\d{2}-\d{2}-run\d{2}", run_folder).group()
    excel_file = os.path.join(run_folder, f"{excel_name}.xlsx")
    assert os.path.exists(excel_file), f"Excel file {excel_file} does not exist."
    df_excel = pd.read_excel(excel_file, sheet_name='reactions_with_run_info')
    # only keep the columns if 'index' or 'vol#' in the name
    df_excel = df_excel[[col for col in df_excel.columns if 'index' in col or 'vol#' in col]]

    # merge df_excel with df_conc_with_global_index by 'global_index'
    df_vol_and_conc = pd.merge(df_excel, df_conc_with_global_index, on='global_index', how='left')

    # put this run's results into a df
    spectrum_names = [f.name for f in os.scandir(results_folder) if f.is_dir() and "1D EXTENDED" in f.name]
    spectrum_index = [ int(f.split('-1D')[0]) for f in spectrum_names]
    df_results = pd.DataFrame({
        'local_index': spectrum_index,
        'spectrum_name': spectrum_names,
        'run_folder': [run_folder] * len(spectrum_names)
    })
    # merge df_results with df_vol_and_conc by 'local_index'
    df_vol_and_conc_and_spectrum_names = pd.merge(df_vol_and_conc, df_results, on='local_index', how='left')
    # sort by 'local_index'
    df_vol_and_conc_and_spectrum_names.sort_values(by='local_index', inplace=True)

    # save the dataframe to a CSV file
    csv_file = os.path.join(run_folder, 'run_info.csv')
    df_vol_and_conc_and_spectrum_names.to_csv(csv_file, index=False)
    return df_vol_and_conc_and_spectrum_names

# Example usage
if __name__ == "__main__":
    test_integral = 9.99932797717227e-05  # replace with an actual integral value
    concentration = get_concentration_from_integral(test_integral)
    print(f"Concentration for integral {test_integral}: {concentration}")

    folders = [
        # r"D:\Dropbox\brucelee\data\NV\Fin al Data\MeCN\4-Pyrrolidinopyridine\2025-05-19-run01_MeCN_4_pyrrolidinopyridine",
        # r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\4-Pyrrolidinopyridine\2025-05-19-run02_MeCN_4_pyrrolidinopyridine"
        # r"D:\\Dropbox\\brucelee\data\\NV\Final Data\MeCN\Pyridine-based nucleophiles\\4-Methyl pyridine\\2025-06-18-run01_MeCN_4_Me_Pyr\\",
        # r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methyl pyridine\2025-06-18-run02_MeCN_4_Me_Pyr\\",
        # r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\Pyridine\2025-05-15-run01_MeCN_Pyr\\",
        # r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\DMAP\2025-06-16-run01_MeCN_DMAP\\",
        # r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\DMAP\2025-06-16-run02_MeCN_DMAP\\",
        # r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methyl pyridine\2025-06-18-run01_MeCN_4_Me_Pyr",
        # r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methyl pyridine\2025-06-18-run02_MeCN_4_Me_Pyr"
        r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methoxy pyridine\2025-06-22-run01_MeCN_4_Methoxy_Pyr",
        r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methoxy pyridine\2025-06-22-run02_MeCN_4_Methoxy_Pyr",

    ]

    df = generate_csv_with_vol_and_conc_and_spectrum_names(folders[0])  # example usage of generate_csv_with_vol_and_conc

    raise ValueError("This script is not meant to be run directly. Please use the main function to process specific folders.")

    for folder in folders:
        json_files = get_all_json_files_from_one_run(folder) # put all json results together
        json_files = filter_json_files(json_files) # filter out files with high coefficient of variation
        print(f"JSON files in {folder}: {json_files}")
        for json_file in json_files:

            print(f"Processing file: {json_file}")
            with open(json_file, 'r+') as file:
                dict = json.load(file)
                integral = dict['second_peak_integral']
                concentration = get_concentration_from_integral(integral)
                dict['compd3_concentration'] = concentration
                file.seek(0)
                json.dump(dict, file, indent=4)

        print(f"Concentration for integral {integral} from {json_file}: {concentration}")