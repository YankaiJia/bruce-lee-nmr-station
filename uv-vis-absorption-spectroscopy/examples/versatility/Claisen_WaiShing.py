from versatility_examples import *

experiment_name = f'nanodrop-spectrometer-measurements/versatility_test/Claisen_WaiShing/'

construct_calibrant(
    cut_from=5,
    lower_limit_of_absorbance=0.007,
    concentration_column_name='concentration',
    do_plot=False,
    calibration_source_filename='2023-10-11_16-26-58_UV-Vis_methoxychalcone',
    calibrant_shortnames=['methoxychalcone'],
    ref_concentrations=[0.0002],
    max_concentrations=[0.0006],
    experiment_name=experiment_name,
)

construct_calibrant(
    cut_from=5,
    lower_limit_of_absorbance=0.007,
    concentration_column_name='concentration',
    do_plot=False,
    calibration_source_filename='2023-10-11_19-50-36_UV-Vis_anisaldehyde',
    calibrant_shortnames=['anisaldehyde', 'acetophenone'],
    ref_concentrations=[0.0002, 0.0003],
    max_concentrations=[0.001, 0.001],
    experiment_name=experiment_name,
)

sp = process_wellplate_spectra.SpectraProcessor(
    folder_with_correction_dataset='uv-vis-absorption-spectroscopy/microspectrometer-calibration/'
                                   '2022-12-01/interpolator-dataset/')
sp.nanodrop_lower_cutoff_of_wavelengths = 220
calibration_folder = data_folder + experiment_name + 'microspectrometer_data/calibration/'
process_plate(sp, dilution_factor=500,
              plate_folder=f'{data_folder}{experiment_name}2023-10-12_14-51-59_UV-Vis_crude.csv',
              well_ids=range(5),
              cut_from=5,
              cut_to=False,
              calibrant_shortnames=['methoxychalcone', 'anisaldehyde', 'acetophenone'],
              calibration_folder=calibration_folder,
              experiment_name=experiment_name,
              do_plot=True)
