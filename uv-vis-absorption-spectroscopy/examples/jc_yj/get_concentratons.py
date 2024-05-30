import importlib
import numpy as np
import pandas as pd

process_wellplate_spectra = importlib.import_module("uv-vis-absorption-spectroscopy.process_wellplate_spectra")

data_folder = 'D:/Docs/Science/UNIST/Projects/useless-random-shit/nanodrop_spectra/'
sp = process_wellplate_spectra.SpectraProcessor(folder_with_correction_dataset=data_folder + 'interpolator-dataset/')
sp.nanodrop_lower_cutoff_of_wavelengths = 220
calibrant_shortnames=['STYRENE', 'EPOX', 'ALDE']
plate_path = data_folder + 'test_experiment_1/2023-09-12-PBAS-sample.csv'
concentrations_here = sp.concentrations_for_one_plate(experiment_folder=data_folder + 'test_experiment_1/',
                                                      plate_folder=plate_path,
                                                      calibration_folder=data_folder + 'test_experiment_1/' + 'microspectrometer_data/calibration/',
                                                      calibrant_shortnames=calibrant_shortnames,
                                                      background_model_folder=data_folder + 'test_experiment_1/microspectrometer_data/background_model/',
                                                      calibrant_upper_bounds=[np.inf, np.inf, np.inf],
                                                      do_plot=True, return_all_substances=True,
                                                      cut_from=2, cut_to=80,
                                                      ignore_abs_threshold=True, ignore_pca_bkg=True)
for well_id, concentrations in enumerate(concentrations_here):
    for i, calibrant_shortname in enumerate(calibrant_shortnames):
        print(f'well: {well_id}, {calibrant_shortname}: {concentrations[i]}')

# use numpy.savetxt() to save concentrations_here to csv file with column names equal to calibrant_shortnames
np.savetxt(data_folder + 'test_experiment_1/concentrations.csv', concentrations_here,
           delimiter=',', header=','.join(calibrant_shortnames), comments='')

