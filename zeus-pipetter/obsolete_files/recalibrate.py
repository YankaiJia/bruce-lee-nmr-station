'''
Using the validation measurements performed with current calibration curve, calculate a new calibration curve to
be loaded in Zeus.
'''

import os
import numpy as np
import pandas as pd
from scipy import interpolate
import matplotlib.pyplot as plt
import importlib

calibration_data = importlib.import_module("calibration_data")

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'

def recalibrate_from_old_string_and_new_measurements(current_calibration_curve_command_string,
                                                     processed_measurement_files_list, tip_type, do_plot=False):
    """
    Recalibrate the pipette based on the current calibration curve command and new measurements.

    Parameters
    ----------
    current_calibration_curve_command_string: str
        String returned from the Zeus command 'GE'

    processed_measurement_files_list: list of str
        One or more paths to the processed measurement files (CSV, output of uncertainty_estimation.py method
        zeus_uncertainty_from_file)

    tip_type: int or str
        Examples are 50, 300, '50uL', '300uL'

    do_plot: bool
        Whether to plot the measurements and the resampled values

    Returns
    -------
    new_command: str
        The new calibration curve command to be loaded in Zeus
    """
    if type(tip_type) == str:
        assert tip_type[-2:] == 'ul' or tip_type[-2:] == 'uL'
        tip_type = int(tip_type[:-2])

    index_where_data_starts = current_calibration_curve_command_string.index('ck') + 2
    command_prefix = current_calibration_curve_command_string[:index_where_data_starts]
    curve_datapoints = current_calibration_curve_command_string[index_where_data_starts:].split(' ')[:16]
    curve_input_volumes = [int(x) / 10 for x in curve_datapoints[::2]]  # in uL
    curve_output_volumes = [int(x) / 10 for x in curve_datapoints[1::2]]  # in uL

    # Load measurement data and resample it at points used as input to current calibration curve
    resampled_point_lists_from_all_files = []
    for filename in processed_measurement_files_list:
        if filename.endswith('.json'):
            # process this file into three-column csv first
            _, __, ___ = \
                calibration_data.zeus_uncertainty_from_file(filename, only_tip_type=tip_type, do_plot= True)
            # this method will save it to the same folder with a different name, with suffix having tip type.
            # So now we load from it into pandas dataframe:
            measurement_data = pd.read_csv(filename.replace('.json', f'_processed_for_{tip_type}ul_tiptype.csv'))
        elif filename.endswith('.csv'):
            measurement_data = pd.read_csv(filename)
        # resample measurement means at curve input volumes
        measured_volumes_at_curve_input_volumes = interpolate.interp1d(measurement_data['target_volume'].values,
                                                                       measurement_data['measured_mean'].values,
                                                                       fill_value='extrapolate')(curve_input_volumes)
        resampled_point_lists_from_all_files.append(np.copy(measured_volumes_at_curve_input_volumes))
        if do_plot:
            plt.plot(measurement_data['target_volume'].values, measurement_data['measured_mean'].values, 'o-',
                     label='measurements')
            plt.plot(curve_input_volumes, measured_volumes_at_curve_input_volumes, 'o', label='resampled measurements')
            plt.legend()
            plt.show()
    resampled_point_lists_from_all_files = np.array(resampled_point_lists_from_all_files)
    measured_volumes_at_curve_input_volumes_averaged_over_files = np.mean(resampled_point_lists_from_all_files, axis=0)

    # replace the input volumes of curve with resampled measurements
    new_command = command_prefix + ' '.join([f'{int(round(x * 10)):05d} {int(round(curve_output_volumes[i] * 10)):05d}'
                                             for i, x in
                                             enumerate(measured_volumes_at_curve_input_volumes_averaged_over_files)])
    return new_command


if __name__ == '__main__':
    # print(recalibrate_from_old_string_and_new_measurements(
    #     current_calibration_curve_command_string='GEid0001gg22ck00090 00100 00185 00200 00290 00300 00470 00500 00715 00750 00960 01000 01955 02000 03000 03050 00 ',
    #     processed_measurement_files_list=[data_folder + \
    #                                       'multicomp-reactions/2023-03-20-run01/pipetter_io/measured_volumes/' \
    #                                       'calibration_results_2023_03_27_02_49_50ul_and_300ul_processed_for_300ul_tiptype.csv',
    #                                       data_folder + \
    #                                       'multicomp-reactions/2023-03-20-run01/pipetter_io/measured_volumes/' \
    #                                       'calibration_results_2023_03_26_15_18_300ul_processed_for_300ul_tiptype.csv'
    #                                       ],
    #     tip_type=300))

    # print(recalibrate_from_old_string_and_new_measurements(
    #     current_calibration_curve_command_string='GEid0001gg22ck00090 00100 00185 00200 00290 00300 00470 00500 00715 00750 00960 01000 01955 02000 03000 03050 00 ',
    #     processed_measurement_files_list=[data_folder + \
    #                                       'multicomp-reactions/2023-03-20-run01/pipetter_io/measured_volumes/' \
    #                                       'calibration_results_2023_03_27_02_49_50ul_and_300ul.json',
    #                                       data_folder + \
    #                                       'multicomp-reactions/2023-03-20-run01/pipetter_io/measured_volumes/' \
    #                                       'calibration_results_2023_03_26_15_18_300ul.json'
    #                                       ],
    #     tip_type=300))

    # calibration curves used before 2023-03-29
    calib_string_300ul = 'GEid0001gg22ck00090 00100 00185 00200 00290 00300 00470 00500 00715 00750 00960 01000 01955 02000 03000 03050 00 '
    calib_string_1000ul = 'GEid0001gg23ck00098 00100 00196 00200 00494 00500 00983 01000 01973 02000 04961 05000 07433 07500 10000 10120 00 '
    calib_string_50ul = 'GEid0001gg24ck00076 00080 00101 00100 00119 00120 00147 00150 00192 00200 00243 00250 00296 00300 00500 00507 00 '

    # before re-calibration
    measured_volumes_300ul = [data_folder + 'multicomp-reactions/2023-03-20-run01/pipetter_io/measured_volumes/'
                                           'calibration_results_2023_03_26_15_18_300ul.json',
                            data_folder + 'multicomp-reactions/2023-03-20-run01/pipetter_io/measured_volumes/'
                                          'calibration_results_2023_03_27_02_49_50ul_and_300ul_processed_for_300ul_tiptype.csv'
                             ]
    measured_volumes_1000ul = [data_folder + 'multicomp-reactions/2023-03-20-run01/pipetter_io/measured_volumes/' \
                                           'calibration_results_2023_03_28_20_54_1000ul.json']
    measured_volumes_50ul = [data_folder + 'multicomp-reactions/2023-03-20-run01/pipetter_io/measured_volumes/'
                                          'calibration_results_2023_03_26_02_13_50ul.json',

                            data_folder + 'multicomp-reactions/2023-03-20-run01/pipetter_io/measured_volumes/'
                                          'calibration_results_2023_03_27_02_49_50ul_and_300ul_processed_for_50ul_tiptype.csv'
                             ]
    # after re-calibration
    measured_volumes_300ul_after_recalib = [data_folder + 'multicomp-reactions/2023-03-20-run01/pipetter_io/measured_volumes/'
                                            'calibration_results_2023_03_29_01_13_300ul_recalib.json']
    measured_volumes_1000ul_after_recalib = [data_folder + 'multicomp-reactions/2023-03-20-run01/pipetter_io/measured_volumes/' \
                                             'calibration_results_2023_03_28_20_54_1000ul.json']
    measured_volumes_50ul_after_recalib = [data_folder + 'multicomp-reactions/2023-03-20-run01/pipetter_io/measured_volumes/'
                                           'calibration_results_2023_03_29_03_08_50ul_recalib.json',

                             data_folder + 'multicomp-reactions/2023-03-20-run01/pipetter_io/measured_volumes/'
                                           'calibration_results_2023_03_27_02_49_50ul_and_300ul_processed_for_50ul_tiptype.csv'
                             ]

    print(recalibrate_from_old_string_and_new_measurements(
        current_calibration_curve_command_string= calib_string_300ul,
        processed_measurement_files_list=measured_volumes_300ul_after_recalib,
        tip_type=300, do_plot=True))