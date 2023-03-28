import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import interpolate
from textwrap import wrap

def zeus_uncertainty_from_file(tfile, only_tip_type, do_plot=True):
    '''
    Estimate the uncertainty of the volume measurement from the data file
    Parameters
    ----------
    tfile: str
        Path to the file with the data

    only_tip_type: int
        Tip type defined by maximum volume (in microliters). Only this tip type will be loaded from the file.

    do_plot: bool
        Whether to plot the results

    Returns
    -------
    (tip_type, np.array(statistical_data), error_interpolator): tuple
    where
        tip_type: int
            Type of the tip, described by maximum volume in microliters
        statistical_data: numpy.ndarray (3xN)
            The statistical data with columns: target volume, mean measured volume, std (random error) of measured volume
        error_interpolator: scipy.interpolate.interp1d
            The interpolator for the overall error as a function of the target volume
    '''

    # This data structure is a madman's magnum opus. Observe this insanity:
    with open(tfile) as file_handler:
        data = json.load(file_handler)
        data = list(data.values())[0]
    statistical_data = []
    diffs = []
    for entry in data:
        the_only_key = list(entry.keys())[0]
        header = the_only_key.split('_')
        target_volume = int(header[-1][:-2])
        tip_type = int(header[-2][:-2])
        if tip_type != only_tip_type:
            continue
        measured_volumes = entry[the_only_key]['volume']
        # Yankai implored to remove the first point because if the weighting problem/artifact
        measured_volumes = measured_volumes[:-1]
        statistical_data.append([target_volume, np.mean(measured_volumes), np.std(measured_volumes)])
        diffs.extend([[target_volume, x - target_volume] for x in measured_volumes])
    statistical_data = np.array(statistical_data)
    df = pd.DataFrame(statistical_data, columns=['target_volume', 'measured_mean', 'measured_std'])
    df.to_csv(tfile.replace('.json', f'_processed_for_{only_tip_type}ul_tiptype.csv'), index=False)
    target_volumes, measured_volumes, measured_std = statistical_data[:, 0], statistical_data[:, 1], statistical_data[:, 2]

    # Optional plotting
    if do_plot:
        fig, ax = plt.subplots(2, 1, sharex=True)
        wrapped_filename = "\n".join(wrap(tfile,60))
        ax[0].set_title(f'Tip type: {tip_type} $\mu$L,\n file: {wrapped_filename}', wrap=True)
        ax[0].errorbar(x=target_volumes, y=measured_volumes, yerr=measured_std,
                       fmt='o-', markersize=3, capsize=5, alpha=0.5)
        ax[0].plot([np.min(target_volumes), np.max(target_volumes)],
                 [np.min(target_volumes), np.max(target_volumes)], color='black')
        ax[1].errorbar(x=target_volumes, y=measured_volumes-target_volumes, yerr=measured_std,
                       fmt='o-', markersize=5, capsize=8, alpha=0.7)
        ax[1].axhline(y=0, color='black')
        ax[1].scatter(np.array(diffs)[:, 0], np.array(diffs)[:, 1], alpha=0.2, color='C1', marker='x')
        plt.xlabel('Intended volume, $\mu$L')
        ax[1].set_ylabel('Measured minus\nintended, $\mu$L')
        ax[0].set_ylabel('Measured volume, $\mu$L')
        plt.tight_layout()
        fig.savefig(tfile.replace('.json', f'_processed_for_{only_tip_type}ul_tiptype.png'), dpi=300)
        plt.show()
    systematic_errors = measured_volumes - target_volumes
    overall_errors = np.sqrt(systematic_errors ** 2 + measured_std ** 2)
    error_interpolator = interpolate.interp1d(target_volumes, overall_errors, fill_value='extrapolate', kind='linear')
    return only_tip_type, np.array(statistical_data), error_interpolator

def cal_avg_and_std_of_volume(dicts):
    avg_here, std_here = [], []
    for dict in dicts:
        for key, value in dict.items():
            avg = np.mean(value['volume'])
            std = np.std(value['volume'])
            dict[key]['vol_avg'] = avg
            avg_here.append(round(avg, 2))
            dict[key]['vol_std'] = std
            std_here.append(round(std,2))
    print(f'avg: {avg_here}, std: {std_here}')
    return avg_here, std_here

LiquidClassIndex_precalib_22 = """
liquid parameters: GMid0001lq22uu0 0 05000 0050 00050 00250 0200 010 0 3 3 0 0 05000 00000 000 00050 040 0200 010 0032567 00
calibration_asp GEid0001gg22ck00100 00100 00200 00200 00300 00300 00500 00500 00750 00750 01000 01000 02000 02000 03000 03000 00
calibration_disp GIid0001gh22cl00100 00100 00200 00200 00300 00300 00500 00500 00750 00750 01000 01000 02000 02000 03000 03000 00
qpm_asp GSid0001gv22vv0100 0000 0015 0 0100 0000 0015 0 0100 0000 0015 1 0100 0000 0015 1 0100 0000 0015 1 0100 0005 0015 1 0100 0005 0015 1 0100 0005 0015 1 0000 0000 0000j誮
qpm_asp GWid0001gp22ww0257 0000 1 0303 0000 1 0365 0000 1 0395 0000 1 0509 0000 1 0703 0000 1 0887 0000 1 0973 0000 1 0000 0000
"""
# pipetting values obtained with the above LiquidClassIndex_precalib_22
a0 = {"DMF_300ul_10ul": {"weight": [7.32, 6.14, 7.07, 5.67, 6.06, 5.7], "volume": [7.75, 6.5, 7.49, 6.01, 6.42, 6.04], "liquid_class_index": [22, 22, 22, 22, 22, 22], "tip_type": ["300ul", "300ul", "300ul", "300ul", "300ul", "300ul"]}}
a1 = {"DMF_300ul_20ul": {"weight": [17.28, 15.64, 15.63, 15.96, 15.55, 13.46], "volume": [18.31, 16.57, 16.56, 16.91, 16.47, 14.26], "liquid_class_index": [22, 22, 22, 22, 22, 22], "tip_type": ["300ul", "300ul", "300ul", "300ul", "300ul", "300ul"]}}
a2 = {"DMF_300ul_30ul": {"weight": [24.66, 24.95, 24.91, 24.41, 24.68, 24.68], "volume": [26.12, 26.43, 26.39, 25.86, 26.14, 26.14], "liquid_class_index": [22, 22, 22, 22, 22, 22], "tip_type": ["300ul", "300ul", "300ul", "300ul", "300ul", "300ul"]}}
a3 = {"DMF_300ul_50ul": {"weight": [45.37, 42.62, 42.96, 44.39, 43.09, 43.32], "volume": [48.06, 45.15, 45.51, 47.02, 45.65, 45.89], "liquid_class_index": [22, 22, 22, 22, 22, 22], "tip_type": ["300ul", "300ul", "300ul", "300ul", "300ul", "300ul"]}}
a4 = {"DMF_300ul_75ul": {"weight": [68.43, 66.04, 67.71, 66.92, 66.78, 65.92], "volume": [72.49, 69.96, 71.73, 70.89, 70.74, 69.83], "liquid_class_index": [22, 22, 22, 22, 22, 22], "tip_type": ["300ul", "300ul", "300ul", "300ul", "300ul", "300ul"]}}
a5 = {"DMF_300ul_100ul": {"weight": [90.96, 91.27, 89.91, 91.04, 88.73, 90.56], "volume": [96.36, 96.68, 95.24, 96.44, 93.99, 95.93], "liquid_class_index": [22, 22, 22, 22, 22, 22], "tip_type": ["300ul", "300ul", "300ul", "300ul", "300ul", "300ul"]}}
a6 = {"DMF_300ul_200ul": {"weight": [185.38, 182.37, 184.76, 183.91, 183.35, 185.22], "volume": [196.38, 193.19, 195.72, 194.82, 194.23, 196.21], "liquid_class_index": [22, 22, 22, 22, 22, 22], "tip_type": ["300ul", "300ul", "300ul", "300ul", "300ul", "300ul"]}}
a7 = {"DMF_300ul_300ul": {"weight": [277.37, 278.09, 277.52, 277.37, 277.83, 277.97], "volume": [293.82, 294.59, 293.98, 293.82, 294.31, 294.46], "liquid_class_index": [22, 22, 22, 22, 22, 22], "tip_type": ["300ul", "300ul", "300ul", "300ul", "300ul", "300ul"]}}
dmf_300ul = [a0, a1, a2, a3, a4, a5, a6, a7]
# cal_avg_and_std_of_volume(dmf_300ul)
dmf_300ul_avg = [6.7, 16.51, 26.18, 46.21, 70.94, 95.77, 195.09, 294.16]
target_volume = [10, 20, 30, 50, 75, 100, 200, 300]
dmf_300ul_std = [0.68, 1.19, 0.19, 1.01, 0.94, 0.92, 1.14, 0.31]

# pipetting values obtained with the calibrated curve
a0_after_calib = {'DMF_300ul_10.0ul': {'weight': [5.6, 5.65, 6.48, 5.57, 6.22], 'volume': [5.932203389830509, 5.985169491525425, 6.864406779661018, 5.90042372881356, 6.588983050847458], 'liquid_class_index': [22, 22, 22, 22, 22], 'tip_type': ['300ul', '300ul', '300ul', '300ul', '300ul']}}
a1_after_calib = {'DMF_300ul_20.0ul': {'weight': [15.15, 15.08, 14.6, 14.91, 14.75], 'volume': [16.048728813559322, 15.974576271186441, 15.466101694915254, 15.79449152542373, 15.625], 'liquid_class_index': [22, 22, 22, 22, 22], 'tip_type': ['300ul', '300ul', '300ul', '300ul', '300ul']}}
a2_after_calib = {'DMF_300ul_30.0ul': {'weight': [25.86, 23.73, 24.84, 24.82, 24.6], 'volume': [27.39406779661017, 25.137711864406782, 26.3135593220339, 26.292372881355934, 26.059322033898308], 'liquid_class_index': [22, 22, 22, 22, 22], 'tip_type': ['300ul', '300ul', '300ul', '300ul', '300ul']}}
a3_after_calib = {'DMF_300ul_50.0ul': {'weight': [42.51, 41.96, 43.13, 44.52, 43.16], 'volume': [45.03177966101695, 44.449152542372886, 45.6885593220339, 47.16101694915255, 45.720338983050844], 'liquid_class_index': [22, 22, 22, 22, 22], 'tip_type': ['300ul', '300ul', '300ul', '300ul', '300ul']}}
a4_after_calib = {'DMF_300ul_75.0ul': {'weight': [63.64, 66.24, 65.26, 65.27, 66.55], 'volume': [67.41525423728814, 70.16949152542372, 69.1313559322034, 69.14194915254237, 70.49788135593221], 'liquid_class_index': [22, 22, 22, 22, 22], 'tip_type': ['300ul', '300ul', '300ul', '300ul', '300ul']}}
a5_after_calib = {'DMF_300ul_100.0ul': {'weight': [90.62, 89.03, 88.38, 90.66, 89.12], 'volume': [95.99576271186442, 94.3114406779661, 93.62288135593221, 96.03813559322035, 94.40677966101696], 'liquid_class_index': [22, 22, 22, 22, 22], 'tip_type': ['300ul', '300ul', '300ul', '300ul', '300ul']}}
a6_after_calib = {'DMF_300ul_200.0ul': {'weight': [182.04, 181.02, 181.36, 180.81, 178.22], 'volume': [192.83898305084745, 191.7584745762712, 192.11864406779662, 191.53601694915255, 188.79237288135593], 'liquid_class_index': [22, 22, 22, 22, 22], 'tip_type': ['300ul', '300ul', '300ul', '300ul', '300ul']}}
a7_after_calib = {'DMF_300ul_300.0ul': {'weight': [273.79, 273.47, 275.17, 274.62, 275.01], 'volume': [290.03177966101697, 289.6927966101695, 291.49364406779665, 290.91101694915255, 291.3241525423729], 'liquid_class_index': [22, 22, 22, 22, 22], 'tip_type': ['300ul', '300ul', '300ul', '300ul', '300ul']}}
dmf_300ul_after_calib = [a0_after_calib, a1_after_calib, a2_after_calib, a3_after_calib, a4_after_calib, a5_after_calib, a6_after_calib, a7_after_calib]
# cal_avg_and_std_of_volume(dmf_300ul_after_calib)
dmf_300ul_after_calib_avg = [6.25, 15.78, 26.24, 45.61, 69.27, 94.88, 191.41, 290.69]
dmf_300ul_after_calib_std = [0.4, 0.22, 0.72, 0.91, 1.08, 0.97, 1.38, 0.71]
"""
The above result means that the more I calibration the more inaccurate the result is. So the order is wrong, which is weired.
So I change the order of target volume and measured volume as follows.
"""
a00 = {"DMF_300ul_200.0ul": {"weight": [190.63, 191.66], "volume": [201.94, 203.03], "liquid_class_index": [22, 22], "tip_type": ["300ul", "300ul"]}}
a11 = {"DMF_300ul_100.0ul": {"weight": [95.58, 97.62], "volume": [101.25, 103.41], "liquid_class_index": [22, 22], "tip_type": ["300ul", "300ul"]}}
a22 = {"DMF_300ul_75.0ul": {"weight": [72.4, 72.28], "volume": [76.69, 76.57], "liquid_class_index": [22, 22], "tip_type": ["300ul", "300ul"]}}
a33 = {"DMF_300ul_50.0ul": {"weight": [50.24, 49.3], "volume": [53.22, 52.22], "liquid_class_index": [22, 22], "tip_type": ["300ul", "300ul"]}}
a44 = {"DMF_300ul_30.0ul": {"weight": [30.77, 31.03], "volume": [32.6, 32.87], "liquid_class_index": [22, 22], "tip_type": ["300ul", "300ul"]}}
a55 = {"DMF_300ul_20.0ul": {"weight": [20.4, 22.09], "volume": [21.61, 23.4], "liquid_class_index": [22, 22], "tip_type": ["300ul", "300ul"]}}
a66 = {"DMF_300ul_10.0ul": {"weight": [11.74, 12.41], "volume": [12.44, 13.15], "liquid_class_index": [22, 22], "tip_type": ["300ul", "300ul"]}}
"""
Result: the volume has small error (~1%) at high volume, but the error is large (~20%) at low volume.
Next: redo the calibration at low volume.
"""

"""
with the following parameters where "01000 02000 02000 02000" is used, the interpolation is correct. That means with this parameter,
whatever volume I pipette between 100ul and 200ul, the pipetter will try to pipette 200ul.
calibration_asp GEid0001gg22ck00100 00067 00200 00165 00300 00262 00500 00462 00750 00709 01000 02000 02000 02000 03000 02942
"""
## with the following parameters the precision is good.
# this is the result: [10.7, 20.38, 32.64, 50.7, 75.75, 100.85, 200.39, 299.67]
parameters_used = """
2023-03-15 01:09:09,555 - main.zeus.ZeusModule - INFO - liquid parameters: GMid0001lq22uu0 0 05000 0050 00050 00250 0200 010 0 3 3 0 0 05000 00000 000 00050 040 0200 010 0032573 00
2023-03-15 01:09:10,089 - main.zeus.ZeusModule - INFO - calibration_asp GEid0001gg22ck00090 00100 00185 00200 00280 00300 00470 00500 00715 00750 00960 01000 01955 02000 03000 03050 00
2023-03-15 01:09:10,634 - main.zeus.ZeusModule - INFO - calibration_disp GIid0001gh22cl00090 00100 00185 00200 00280 00300 00470 00500 00715 00750 00960 01000 01955 02000 03000 03050 00
2023-03-15 01:09:11,178 - main.zeus.ZeusModule - INFO - qpm_asp GSid0001gv22vv0100 0000 0015 0 0100 0000 0015 0 0100 0000 0015 1 0100 0000 0015 1 0100 0000 0015 1 0100 0005 0015 1 0100 0005 0015 1 0100 0005 0015 1 0000 0000 0000j誮
2023-03-15 01:09:11,710 - main.zeus.ZeusModule - INFO - qpm_asp GWid0001gp22ww0257 0000 1 0303 0000 1 0365 0000 1 0395 0000 1 0509 0000 1 0703 0000 1 0887 0000 1 0973 0000 1 0000 0000
"""





LiquidClassIndex_precalib_24 = """
liquid parameters: GMid0001lq24uu0 0 05000 0020 00030 00300 0200 010 0 3 3 0 0 05000 00000 000 00030 040 0200 010 0032567 00
calibration_asp GEid0001gg24ck00030 00030 00040 00040 00050 00050 00080 00080 00100 00100 00200 00200 00300 00300 00500 00500 00
calibration_disp GIid0001gh24cl00030 00030 00040 00040 00050 00050 00080 00080 00100 00100 00200 00200 00300 00300 00500 00500 00
qpm_asp GSid0001gv24vv0219 0000 0015 0 0219 0000 0015 0 0219 0000 0015 0 0127 0000 0015 0 0693 0000 0015 1 0585 0000 0015 1 0502 0000 0015 1 0363 0000 0015 1 0000 0000 0000j誮
qpm_asp GWid0001gp24ww0435 0000 1 0515 0000 1 0433 0000 1 0513 0000 1 0599 0000 1 0711 0000 1 0803 0000 1 0967 0000 1 0000 0000
"""

# pipetting values obtained with the above LiquidClassIndex_precalib_24
b0 = {"DMF_50ul_50.0ul": {"weight": [43.72, 46.76, 46.72, 46.53, 46.53, 46.31, 46.45, 46.46, 47.07, 46.74], "volume": [46.31, 49.53, 49.49, 49.29, 49.29, 49.06, 49.21, 49.22, 49.86, 49.51], "liquid_class_index": [24, 24, 24, 24, 24, 24, 24, 24, 24, 24], "tip_type": ["50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul"]}}
b1 = {"DMF_50ul_30.0ul": {"weight": [28.77, 28.17, 28.5, 28.28, 27.93, 28.43, 27.68, 28.1, 27.9, 27.88], "volume": [30.48, 29.84, 30.19, 29.96, 29.59, 30.12, 29.32, 29.77, 29.56, 29.53], "liquid_class_index": [24, 24, 24, 24, 24, 24, 24, 24, 24, 24], "tip_type": ["50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul"]}}
b2 = {"DMF_50ul_20.0ul": {"weight": [19.18, 18.61, 18.47, 18.37, 18.35, 18.06, 19.1, 18.65, 18.67, 18.33], "volume": [20.32, 19.71, 19.57, 19.46, 19.44, 19.13, 20.23, 19.76, 19.78, 19.42], "liquid_class_index": [24, 24, 24, 24, 24, 24, 24, 24, 24, 24], "tip_type": ["50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul"]}}
b3 = {"DMF_50ul_10.0ul": {"weight": [9.33, 8.99, 9.83, 9.55, 8.81, 9.33, 9.41, 9.53, 9.21, 9.12], "volume": [9.88, 9.52, 10.41, 10.12, 9.33, 9.88, 9.97, 10.1, 9.76, 9.66], "liquid_class_index": [24, 24, 24, 24, 24, 24, 24, 24, 24, 24], "tip_type": ["50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul"]}}
b4 = {"DMF_50ul_8.0ul": {"weight": [7.33, 7.6, 6.9, 6.87, 7.55, 7.38, 7.22, 7.37, 7.21, 7.53], "volume": [7.76, 8.05, 7.31, 7.28, 8.0, 7.82, 7.65, 7.81, 7.64, 7.98], "liquid_class_index": [24, 24, 24, 24, 24, 24, 24, 24, 24, 24], "tip_type": ["50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul"]}}
b5 = {"DMF_50ul_5.0ul": {"weight": [4.63, 4.55, 4.35, 3.95, 4.28, 4.81, 4.21, 4.66, 4.49, 4.38], "volume": [4.9, 4.82, 4.61, 4.18, 4.53, 5.1, 4.46, 4.94, 4.76, 4.64], "liquid_class_index": [24, 24, 24, 24, 24, 24, 24, 24, 24, 24], "tip_type": ["50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul"]}}
b6 = {"DMF_50ul_4.0ul": {"weight": [3.59, 3.64, 3.42, 3.49, 3.54, 3.76, 3.5, 3.94, 3.23, 3.61], "volume": [3.8, 3.86, 3.62, 3.7, 3.75, 3.98, 3.71, 4.17, 3.42, 3.82], "liquid_class_index": [24, 24, 24, 24, 24, 24, 24, 24, 24, 24], "tip_type": ["50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul"]}}
b7 = {"DMF_50ul_3.0ul": {"weight": [2.86, 3.23, 2.82, 2.58, 2.91, 3.51, 2.94, 3.11, 3.14, 2.91], "volume": [3.03, 3.42, 2.99, 2.73, 3.08, 3.72, 3.11, 3.29, 3.33, 3.08], "liquid_class_index": [24, 24, 24, 24, 24, 24, 24, 24, 24, 24], "tip_type": ["50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul", "50ul"]}}
dmf_50ul = [b0, b1, b2, b3, b4, b5, b6, b7]
# cal_avg_and_std_of_volume(dmf_50ul)
dmf_50ul_avg = [49.08, 29.84, 19.68, 9.86, 7.73, 4.69, 3.78, 3.18]
dmf_50ul_std = [0.95, 0.34, 0.35, 0.3, 0.25, 0.25, 0.19, 0.26]

LiquidClassIndex_precalib_23 = """
liquid parameters: GMid0001lq23uu0 0 05000 0050 00080 00400 0200 010 0 3 3 0 0 05000 00000 000 00050 080 0200 010 0032579 00
calibration_asp GEid0001gg23ck00100 00100 00200 00200 00500 00500 01000 01000 02000 02000 05000 05000 07500 07500 10000 10000 00
calibration_disp GIid0001gh23cl00100 00100 00200 00200 00500 00500 01000 01000 02000 02000 05000 05000 07500 07500 10000 10000 00
qpm_asp GSid0001gv23vv0522 0002 0015 0 0330 0002 0015 0 0771 0002 0015 1 0737 0005 0015 1 0713 0005 0015 1 0687 0005 0015 1 0671 0005 0015 1 0655 0005 0015 1 0000 0000 0000j誮
qpm_asp GWid0001gp23ww0229 0000 1 0255 0000 1 0285 0000 1 0299 0000 1 0331 0000 1 0357 0000 1 0355 0000 1 0379 0000 1 0000 0000
"""

c0 = {"DMF_1000ul_10.0ul": {"weight": [9.55, 9.12, 9.27, 9.35, 9.24, 9.38, 9.12, 9.25, 9.39, 9.63], "volume": [10.12, 9.66, 9.82, 9.9, 9.79, 9.94, 9.66, 9.8, 9.95, 10.2], "liquid_class_index": [23, 23, 23, 23, 23, 23, 23, 23, 23, 23], "tip_type": ["1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul"]}}
c1 = {"DMF_1000ul_20.0ul": {"weight": [19.37, 18.36, 18.42, 18.32, 18.83, 18.27, 18.56, 18.25, 18.27, 18.36], "volume": [20.52, 19.45, 19.51, 19.41, 19.95, 19.35, 19.66, 19.33, 19.35, 19.45], "liquid_class_index": [23, 23, 23, 23, 23, 23, 23, 23, 23, 23], "tip_type": ["1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul"]}}
c2 = {"DMF_1000ul_50.0ul": {"weight": [47.37, 46.66, 46.82, 46.28, 46.56, 46.32, 46.65, 46.45, 46.47, 47.1], "volume": [50.18, 49.43, 49.6, 49.03, 49.32, 49.07, 49.42, 49.21, 49.23, 49.89], "liquid_class_index": [23, 23, 23, 23, 23, 23, 23, 23, 23, 23], "tip_type": ["1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul"]}}
c3 = {"DMF_1000ul_100.0ul": {"weight": [90.34, 91.78, 93.78, 93.02, 93.06, 93.03, 93.15, 93.57, 93.17, 93.28], "volume": [95.7, 97.22, 99.34, 98.54, 98.58, 98.55, 98.68, 99.12, 98.7, 98.81], "liquid_class_index": [23, 23, 23, 23, 23, 23, 23, 23, 23, 23], "tip_type": ["1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul"]}}
c4 = {'DMF_1000ul_200.0ul': {'weight': [190.46, 185.81, 186.53, 186.69, 186.6, 185.24, 185.67, 185.06, 185.17, 185.91], 'volume': [201.75, 196.83, 197.59, 197.76, 197.67, 196.23, 196.68, 196.04, 196.15, 196.94], 'liquid_class_index': [23, 23, 23, 23, 23], 'tip_type': ['1000ul', '1000ul', '1000ul', '1000ul', '1000ul']}}
c5 = {"DMF_1000ul_500.0ul": {"weight": [469.5, 468.88, 468.4, 468.3, 468.36, 467.82, 467.19, 468.41, 468.45, 468.32], "volume": [497.35, 496.69, 496.19, 496.08, 496.14, 495.57, 494.9, 496.2, 496.24, 496.1], "liquid_class_index": [23, 23, 23, 23, 23, 23, 23, 23, 23, 23], "tip_type": ["1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul"]}}
c6 = {"DMF_1000ul_750.0ul": {"weight": [700.87, 702.23, 703.09, 702.34, 702.13, 701.53, 701.38, 700.36, 701.62, 701.25], "volume": [742.45, 743.89, 744.8, 744.0, 743.78, 743.15, 742.99, 741.91, 743.24, 742.85], "liquid_class_index": [23, 23, 23, 23, 23, 23, 23, 23, 23, 23], "tip_type": ["1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul", "1000ul"]}}
c7 = {'DMF_1000ul_1000.0ul': {'weight': [930.64, 933.09, 934.47, 934.14, 933.5, 929.34, 931.21, 931.55, 932.55, 932.49], 'volume': [985.84, 988.44, 989.90, 989.55, 988.87, 984.47, 986.45, 986.81, 987.87, 987.81], 'liquid_class_index': [23, 23, 23, 23, 23], 'tip_type': ['1000ul', '1000ul', '1000ul', '1000ul', '1000ul']}}
dmf_1000ul = [c0, c1, c2, c3, c4, c5, c6, c7]
# cal_avg_and_std_of_volume(dmf_1000ul)
dmf_1000ul_avg = [9.88, 19.6, 49.44, 98.32, 197.36, 496.15, 743.31, 987.6]
dmf_1000ul_std = [0.17, 0.35, 0.35, 1.02, 1.58, 0.6, 0.79, 1.62]






# # round the volume to 2 decimal places
# def round_volume_to_2_decimals(dicts):
#     for dict in dicts:
#         for key, value in dict.items():
#
#             value['volume'] = [round(x, 2) for x in value['volume']]
#
#     return dicts
#
# d = round_volume_to_2_decimals(dicts)
#
# # save d to a json file
# with open('data.json', 'w') as f:
#     json.dump(d, f)

