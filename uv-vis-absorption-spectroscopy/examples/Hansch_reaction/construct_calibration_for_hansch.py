import importlib
import os
calibrator = importlib.import_module("uv-vis-absorption-spectroscopy.calibrator")
data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'

experiment_name = f'BPRF/2024-01-17-run01/'
cut_from = 5

## Without CARY
# calibrator.construct_calibrant(
#     cut_from=cut_from,
#     lower_limit_of_absorbance=0.007,
#     concentration_column_name='concentration',
#     do_plot=True,
#     calibration_source_filename='calibrations/2024-01-21_14-53-09_UV-Vis_main_product',
#     calibrant_shortnames=['HRP01'],
#     ref_concentrations=[0.0003],
#     max_concentrations=[0.015],
#     min_concentrations=[0.00004],
#     experiment_name=experiment_name,
#     upper_limit_of_absorbance=0.7557,
#     do_reference_stitching=True,
#     bkg_multiplier=0
# )

# # With CARY
# calibrator.construct_calibrant(
#     cut_from=cut_from,
#     lower_limit_of_absorbance=0.007,
#     concentration_column_name='concentration',
#     do_plot=True,
#     calibration_source_filename='calibrations/2024-01-21_14-53-09_UV-Vis_main_product',
#     calibrant_shortnames=['HRP01'],
#     ref_concentrations=[0.0003],
#     max_concentrations=[0.015],
#     min_concentrations=[0.00004],
#     experiment_name=experiment_name,
#     upper_limit_of_absorbance=0.7557,
#     do_reference_stitching=False,
#     bkg_multiplier=1,
#     do_smoothing_at_low_absorbance=None,
#     forced_reference_from_agilent_cary_file=data_folder + experiment_name + 'calibrations/spectrophotometer_data/Hantzsch-ester-HRP01/HRP01_400ug_per_20mL_repeat1.csv',
#     cary_column_name='HRP01_0.4mg_per_20_mL_repeat1',
# )

# calibrator.construct_calibrant(
#     cut_from=cut_from,
#     lower_limit_of_absorbance=0.007,
#     concentration_column_name='concentration',
#     do_plot=True,
#     calibration_source_filename='calibrations/2024-01-16_18-28-35_UV-Vis_starting_materials',
#     calibrant_shortnames=['methoxybenzaldehyde'],
#     ref_concentrations=[0.0005],
#     max_concentrations=[1],
#     min_concentrations=[4e-5],
#     experiment_name=experiment_name,
#     upper_limit_of_absorbance=0.95,
#     do_reference_stitching=True
# )

# calibrator.construct_calibrant(
#     cut_from=cut_from,
#     lower_limit_of_absorbance=0.007,
#     concentration_column_name='concentration',
#     do_plot=True,
#     calibration_source_filename='calibrations/2024-01-16_18-28-35_UV-Vis_starting_materials',
#     calibrant_shortnames=['ethyl_acetoacetate'],
#     ref_concentrations=[0.006],
#     max_concentrations=[0.015],
#     min_concentrations=[0],
#     experiment_name=experiment_name,
#     upper_limit_of_absorbance=0.95,
#     do_reference_stitching=True,
#     cut_to=None
# )

# calibrator.construct_calibrant(
#     cut_from=cut_from,
#     lower_limit_of_absorbance=0.007,
#     concentration_column_name='concentration',
#     do_plot=True,
#     calibration_source_filename='calibrations/2024-01-16_13-38-39_UV-Vis_Knoevenagel',
#     calibrant_shortnames=['dm40_12'],
#     ref_concentrations=[0.0003],
#     max_concentrations=[1],
#     min_concentrations=[0.00025],
#     experiment_name=experiment_name,
#     upper_limit_of_absorbance=0.95,
#     do_reference_stitching=True,
#     cut_to=None,
#     # custom_bkg_spectrum_npy_file=data_folder + 'BPRF/2024-01-17-run01/microspectrometer_data/calibration/references/HRP01/bkg_spectrum.npy',
#     custom_bkg_spectrum_npy_file=data_folder + 'BPRF/2024-01-17-run01/microspectrometer_data/calibration/references/methoxybenzaldehyde/bkg_spectrum.npy',
# )

# calibrator.construct_calibrant(
#     cut_from=cut_from,
#     lower_limit_of_absorbance=0.007,
#     concentration_column_name='concentration',
#     do_plot=True,
#     calibration_source_filename='calibrations/2024-01-16_13-38-39_UV-Vis_Knoevenagel',
#     calibrant_shortnames=['dm40_10'],
#     ref_concentrations=[0.0003],
#     max_concentrations=[1],
#     min_concentrations=[1e-4],
#     experiment_name=experiment_name,
#     upper_limit_of_absorbance=0.95,
#     do_reference_stitching=True,
#     cut_to=None,
#     custom_bkg_spectrum_npy_file=data_folder + 'BPRF/2024-01-17-run01/microspectrometer_data/calibration/references/HRP01/bkg_spectrum.npy',
#     bkg_multiplier=0
# )

# calibrator.construct_calibrant(
#     cut_from=cut_from,
#     lower_limit_of_absorbance=0.007,
#     concentration_column_name='concentration',
#     do_plot=True,
#     calibration_source_filename='calibrations/2023-12-20_17-51-07_UV-Vis_side_prod',
#     calibrant_shortnames=['dm35_8'],
#     ref_concentrations=[0.0003],
#     max_concentrations=[1],
#     min_concentrations=[4.5e-5],
#     experiment_name=experiment_name,
#     upper_limit_of_absorbance=0.95,
#     do_reference_stitching=True,
#     cut_to=None,
#     bkg_multiplier=1
#     # custom_bkg_spectrum_npy_file=data_folder + 'BPRF/2024-01-17-run01/microspectrometer_data/calibration/references/HRP01/bkg_spectrum.npy'
# )

# calibrator.construct_calibrant(
#     cut_from=cut_from,
#     lower_limit_of_absorbance=0.007,
#     concentration_column_name='concentration',
#     do_plot=True,
#     calibration_source_filename='calibrations/2023-12-20_17-51-07_UV-Vis_side_prod',
#     calibrant_shortnames=['dm35_9'],
#     ref_concentrations=[0.0003],
#     max_concentrations=[1],
#     min_concentrations=[4.5e-5],
#     experiment_name=experiment_name,
#     upper_limit_of_absorbance=0.95,
#     do_reference_stitching=True,
#     cut_to=None
#     # custom_bkg_spectrum_npy_file=data_folder + 'BPRF/2024-01-17-run01/microspectrometer_data/calibration/references/HRP01/bkg_spectrum.npy'
# )

# calibrator.construct_calibrant(
#     cut_from=cut_from,
#     lower_limit_of_absorbance=0.007,
#     concentration_column_name='concentration',
#     do_plot=True,
#     calibration_source_filename='calibrations/2023-12-20_17-51-07_UV-Vis_side_prod',
#     calibrant_shortnames=['dm36'],
#     ref_concentrations=[0.0005],
#     max_concentrations=[0.00075],
#     min_concentrations=[4.5e-5],
#     experiment_name=experiment_name,
#     upper_limit_of_absorbance=0.95,
#     do_reference_stitching=True,
#     cut_to=None
#     # custom_bkg_spectrum_npy_file=data_folder + 'BPRF/2024-01-17-run01/microspectrometer_data/calibration/references/HRP01/bkg_spectrum.npy'
# )

# calibrator.construct_calibrant(
#     cut_from=cut_from,
#     lower_limit_of_absorbance=0.007,
#     concentration_column_name='concentration',
#     do_plot=True,
#     calibration_source_filename='calibrations/2023-12-20_17-51-07_UV-Vis_side_prod',
#     calibrant_shortnames=['dm37'],
#     ref_concentrations=[0.0005],
#     max_concentrations=[1],
#     min_concentrations=[2.5e-5],
#     experiment_name=experiment_name,
#     upper_limit_of_absorbance=0.95,
#     do_reference_stitching=False,
#     cut_to=None,
#     forced_reference_from_agilent_cary_file=data_folder + experiment_name + 'calibrations/spectrophotometer_data/Hantzsch_dm37/dm37.csv',
#     cary_column_name='dm_37_SBW1nm_repeat2',
#     do_smoothing_at_low_absorbance=None
#     # custom_bkg_spectrum_npy_file=data_folder + 'BPRF/2024-01-17-run01/microspectrometer_data/calibration/references/HRP01/bkg_spectrum.npy'
# )

# calibrator.construct_calibrant(
#     cut_from=cut_from,
#     lower_limit_of_absorbance=0.007,
#     concentration_column_name='concentration',
#     do_plot=True,
#     calibration_source_filename='calibrations/2024-01-16_14-33-10_UV-Vis_dm053',
#     calibrant_shortnames=['dm053'],
#     ref_concentrations=[0.0003],
#     max_concentrations=[1],
#     min_concentrations=[0.00004],
#     experiment_name=experiment_name,
#     upper_limit_of_absorbance=0.95,
#     do_reference_stitching=True,
#     cut_to=None
#     # custom_bkg_spectrum_npy_file=data_folder + 'BPRF/2024-01-17-run01/microspectrometer_data/calibration/references/HRP01/bkg_spectrum.npy'
# )


# calibrator.construct_calibrant(
#     cut_from=cut_from,
#     lower_limit_of_absorbance=0.007,
#     concentration_column_name='concentration',
#     do_plot=True,
#     calibration_source_filename='calibrations/2024-02-02_14-06-53_UV-Vis_dm070',
#     calibrant_shortnames=['dm70'],
#     ref_concentrations=[0.00128],
#     max_concentrations=[1],
#     min_concentrations=[0.00017],
#     experiment_name=experiment_name,
#     upper_limit_of_absorbance=0.95,
#     do_reference_stitching=True,
#     cut_to=None
#     # custom_bkg_spectrum_npy_file=data_folder + 'BPRF/2024-01-17-run01/microspectrometer_data/calibration/references/HRP01/bkg_spectrum.npy'
# )

# calibrator.construct_calibrant(
#     cut_from=cut_from,
#     lower_limit_of_absorbance=0.007,
#     concentration_column_name='concentration',
#     do_plot=True,
#     calibration_source_filename='calibrations/2023-12-26_15-14-38_UV-Vis_ethylaminobutenoate',
#     calibrant_shortnames=['EAB'],
#     ref_concentrations=[0.0005],
#     max_concentrations=[0.00085],#[0.00085],
#     min_concentrations=[0],
#     experiment_name=experiment_name,
#     upper_limit_of_absorbance=0.95,
#     do_reference_stitching=True,
#     cut_to=None,
#     bkg_multiplier=1,
#     do_smoothing_at_low_absorbance=0.03
#     # custom_bkg_spectrum_npy_file=data_folder + 'BPRF/2024-01-17-run01/microspectrometer_data/calibration/references/HRP01/bkg_spectrum.npy'
# )

# calibrator.construct_calibrant(
#     cut_from=cut_from,
#     lower_limit_of_absorbance=0.007,
#     concentration_column_name='concentration',
#     do_plot=True,
#     calibration_source_filename='calibrations/2024-01-22_12-37-31_UV-Vis_bb017',
#     calibrant_shortnames=['bb017'],
#     ref_concentrations=[0.0003],
#     max_concentrations=[1],
#     min_concentrations=[0],
#     experiment_name=experiment_name,
#     upper_limit_of_absorbance=0.95,
#     do_reference_stitching=True,
#     cut_to=None,
#     do_smoothing_at_low_absorbance=0.03,
#     bkg_multiplier=1
#     # custom_bkg_spectrum_npy_file=data_folder + 'BPRF/2024-01-17-run01/microspectrometer_data/calibration/references/HRP01/bkg_spectrum.npy'
# )

# calibrator.construct_calibrant(
#     cut_from=cut_from,
#     lower_limit_of_absorbance=0.007,
#     concentration_column_name='concentration',
#     do_plot=True,
#     calibration_source_filename='calibrations/2024-01-29_15-09-06_UV-Vis_bb021',
#     calibrant_shortnames=['bb021'],
#     ref_concentrations=[0.0003],
#     max_concentrations=[1],
#     min_concentrations=[0],
#     experiment_name=experiment_name,
#     upper_limit_of_absorbance=0.95,
#     do_reference_stitching=True,
#     cut_to=None,
#     custom_bkg_spectrum_npy_file=data_folder + 'BPRF/2024-01-17-run01/microspectrometer_data/calibration/references/HRP01/bkg_spectrum.npy',
# )

# calibrator.construct_calibrant(
#     cut_from=cut_from,
#     lower_limit_of_absorbance=0.007,
#     concentration_column_name='concentration',
#     do_plot=True,
#     calibration_source_filename='calibrations/2024-02-28_21-35-56_UV-Vis_dm088_4',
#     calibrant_shortnames=['dm088_4'],
#     ref_concentrations=[0.0003],
#     max_concentrations=[1],
#     min_concentrations=[0],
#     experiment_name=experiment_name,
#     upper_limit_of_absorbance=0.95,
#     do_reference_stitching=True,
#     cut_to=None,
#     bkg_multiplier=1
#     # custom_bkg_spectrum_npy_file=data_folder + 'BPRF/2024-01-17-run01/microspectrometer_data/calibration/references/HRP01/bkg_spectrum.npy'
# )