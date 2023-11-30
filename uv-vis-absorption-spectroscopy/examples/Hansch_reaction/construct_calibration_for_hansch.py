import importlib
import os
calibrator = importlib.import_module("uv-vis-absorption-spectroscopy.calibrator")
data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'

experiment_name = f'BPRF/2023-11-08-run01/'
cut_from = 5

calibrator.construct_calibrant(
    cut_from=cut_from,
    lower_limit_of_absorbance=0.007,
    concentration_column_name='concentration',
    do_plot=True,
    calibration_source_filename='calibrations/2023-11-17_15-11-58_UV-Vis_substrates_product2',
    calibrant_shortnames=['HRP01', 'methoxybenzaldehyde'],
    ref_concentrations=[0.0005, 0.0005],
    max_concentrations=[1, 1],
    experiment_name=experiment_name,
)

calibrator.construct_calibrant(
    cut_from=cut_from,
    lower_limit_of_absorbance=0.007,
    concentration_column_name='concentration',
    do_plot=True,
    calibration_source_filename='calibrations/2023-11-07_16-59-16_UV-Vis_substrates',
    calibrant_shortnames=['ethyl_acetoacetate'],
    ref_concentrations=[0.004],
    max_concentrations=[1],
    experiment_name=experiment_name,
    custom_bkg_spectrum_npy_file=data_folder + 'BPRF/2023-11-08-run01/microspectrometer_data/calibration/background/bkg_spectrum.npy'
)
