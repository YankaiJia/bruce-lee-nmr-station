# construct a linear interpolator for the NMR spectrum of Nik Compd 3

import numpy as np
from scipy.interpolate import interp1d
import os, json, pickle

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

    results_folder = run_folder + '/results'
    assert os.path.exists(results_folder), f"Results folder {results_folder} does not exist."

    # get all subfolder in the results_folder if "1D EXTENDED" is in the name
    subfolders = [f.path for f in os.scandir(results_folder) if f.is_dir() and "1D EXTENDED" in f.name]

    json_files = [os.path.join(folder, json_name) for folder in subfolders if os.path.exists(os.path.join(folder, json_name))]

    assert all(os.path.exists(file) for file in json_files), "Not all JSON files exist."

    return json_files

def convert_ndarray(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_ndarray(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_ndarray(item) for item in obj]
    else:
        return obj

# Example usage
if __name__ == "__main__":
    test_integral = 9.99932797717227e-05  # replace with an actual integral value
    concentration = get_concentration_from_integral(test_integral)
    print(f"Concentration for integral {test_integral}: {concentration}")

    folders = [
        # r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\4-Pyrrolidinopyridine\2025-05-19-run01_MeCN_4_pyrrolidinopyridine",
        # r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\4-Pyrrolidinopyridine\2025-05-19-run02_MeCN_4_pyrrolidinopyridine"
        # r"D:\\Dropbox\\brucelee\data\\NV\Final Data\MeCN\Pyridine-based nucleophiles\\4-Methyl pyridine\\2025-06-18-run01_MeCN_4_Me_Pyr\\",
        # r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methyl pyridine\2025-06-18-run02_MeCN_4_Me_Pyr\\",
        # r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\Pyridine\2025-05-15-run01_MeCN_Pyr\\",
        # r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\DMAP\2025-06-16-run01_MeCN_DMAP\\",
        # r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\DMAP\2025-06-16-run02_MeCN_DMAP\\",
        r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methyl pyridine\2025-06-18-run01_MeCN_4_Me_Pyr",
        r"D:\Dropbox\brucelee\data\NV\Final Data\MeCN\Pyridine-based nucleophiles\4-Methyl pyridine\2025-06-18-run02_MeCN_4_Me_Pyr"
    ]

    for folder in folders:
        json_files = get_all_json_files_from_one_run(folder)
        print(f"JSON files in {folder}: {json_files}")
        for json_file in json_files:
            print(f"Processing file: {json_file}")
            with open(json_file, 'r+') as file:
                dict = json.load(file)
                integral = dict['second_peak_integral']
                concentration = get_concentration_from_integral(integral)
                dict['compd3_concentration'] = concentration
                file.seek(0)
                # dict = convert_ndarray(dict)
                json.dump(dict, file, indent=4)

        print(f"Concentration for integral {integral} from {json_file}: {concentration}")