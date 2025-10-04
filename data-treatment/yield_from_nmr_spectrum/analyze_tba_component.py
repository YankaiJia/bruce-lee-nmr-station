"""
Quantitative NMR analysis of spectral components of TBA in the 3 - 3.5 ppm region.

This module provides a very case-specific tool for automated peak fitting and integration 3 - 3.5 ppm chemical shift
of TBA with the aim of quantifying the TBA concentration.

The analysis employs asymmetric pseudo-Voigt lineshape based on Hardy-Lorentz-z2 lineshape with sigmoid baseline
and vertical offset.

Reference: Hardy, E. "NMR Methods for the Investigation of Structure and Transport", Chapter 7.

Example of usage
-------------
>>> overall_integral, report = get_tba_peak_integration(filepath='test_data/tba/data1.csv')
>>> print(f'main peak integral: {overall_integral} [ppm * intensity_unit]')
>>> print(f'RMSE of the fit: {report["rmse"]} [intensity_unit]')

Author: Yaroslav I. Sobolev, yaroslav.sobolev@gmail.com, IBS Center for Algorithmic and Robotized Synthesis
"""
import json
import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import cmath
from scipy.optimize import curve_fit
from scipy.integrate import quad
from scipy.signal import savgol_filter


def load_nmr_spectrum_from_csv(filepath):
    """
    Load NMR spectrum data from CSV file with automatic y-axis reversal.

    Reads two-column CSV data where first column contains chemical shifts (ppm) and
    second column contains intensities. The intensity column is automatically flipped on loading.

    Parameters
    ----------
    filepath : str
        Path to CSV file containing NMR spectrum data. Expected format: two columns
        with header row, comma-separated values.

    Returns
    -------
    numpy.ndarray
        Shape (n_points, 2) array with columns [chemical_shift_ppm, intensity].
        The intensity column is reversed from the input file order.

    """
    data = np.loadtxt(filepath, delimiter=',', skiprows=1)
    data[:, 1] = data[::-1, 1]  # Reverse the y-axis data
    return data


def hardy_lorentz_z2(v, vmax, gamma):
    """
    Calculate Lorentz-z2 lineshape function for NMR peak modeling. This function has been derived by
    Edme Hardy in Chapter 7 of the book "NMR Methods for the Investigation of Structure and Transport":

    .. math::

        S(\\nu)=\\frac{1}{2 \\pi i \\sqrt{\\nu_{\\max }}}\\left(\\frac{\\arctan \\sqrt{\\frac{\\nu_{\\max }}{-\\nu-\\gamma i}}}{\\sqrt{-\\nu-\\gamma i}}-\\frac{\\arctan \\sqrt{\\frac{\\nu_{\\max }}{-\\nu+\\gamma i}}}{\\sqrt{-\\nu+\\gamma i}}\\right)

    In case the LaTeX rendering does not work, the formula can be written as:
    S = 1/(2j * π * √vmax) * [atan(√(vmax/(-v - γj)))/√(-v - γj) - atan(√(vmax/(-v + γj)))/√(-v + γj)],
    where j is the imaginary unit.

    It accounds for the NMR field inhomogeneities and is used to model asymmetric lineshapes.
    It is assumed that
    1. The signal decay for the considered line in a homogeneous field is monoexponential,
    corresponding to a Lorentz line shape after Fourier transformation.
    2. The actual field has a quadratic dependence along the symmetry axis of the
    sample, leading to a resonance-frequency distribution (“spectrum”) that has to
    be calculated.
    3. The spectral contributions of 1 are broadened by the distribution of 2 or vice
    versa, corresponding to a convolution.

    Parameters
    ----------
    v : float or complex
        Frequency, in ppm
    vmax : float
        Maximum frequency parameter controlling peak shape.
    gamma : float
        Damping parameter related to line broadening.

    Returns
    -------
    float
        Intensity of the Hardy lineshape function evaluated at v.

    """
    S = 1 / (2j * np.pi * cmath.sqrt(vmax)) * (
            cmath.atan(cmath.sqrt(vmax / (-1 * v - gamma * 1j))) / cmath.sqrt(-1 * v - gamma * 1j) -
            cmath.atan(cmath.sqrt(vmax / (-1 * v + gamma * 1j))) / cmath.sqrt(-1 * v + gamma * 1j))
    return S.real


# vectorize the Hardy-Lorentz-z2 function for efficient evaluation over arrays
hardy_lorentz_z2_vectorized = np.vectorize(hardy_lorentz_z2)


def lineshape_function(x, center, vmax, gamma, amplitude,
                       asymmetry_factor, gaussian_sigma, gaussian_amplitude, sigmoid_width, sigmoid_amplitude,
                       vertical_offset):
    """
    Composite NMR lineshape function combining Hardy-Lorentz-z2, Gaussian curve, and sigmoid baseline, and baseline offset.
    Asymmetry is controlled by the asymmetry_factor parameter, which skews the peak shape relative to the peak center.

    Parameters
    ----------
    x : numpy.ndarray
        Chemical shift values (ppm) for evaluation.
    center : float
        Peak center position (ppm).
    vmax : float
        Hardy lineshape maximum frequency parameter.
    gamma : float
        Hardy lineshape damping parameter.
    amplitude : float
        Hardy lineshape amplitude.
    asymmetry_factor : float
        Peak asymmetry parameter. Values > 1 create rightward skew, < 1 leftward skew.
    gaussian_sigma : float
        Standard deviation of Gaussian broadening component (ppm).
    gaussian_amplitude : float
        Amplitude of Gaussian broadening component.
    sigmoid_width : float
        Width parameter for sigmoid background component (ppm).
    sigmoid_amplitude : float
        Amplitude of sigmoid background component.
    vertical_offset : float
        Constant baseline offset.

    Returns
    -------
    numpy.ndarray
        Composite lineshape evaluation at input x values.

    Notes
    -----
    **Component Functions:**

    1. **Hardy-Lorentz Core**: Provides the fundamental resonance lineshape with
       natural asymmetry from the Hardy Z2 formulation
    2. **Asymmetry Correction**: Applies differential scaling to positive and negative
       frequency offsets with respect to center (x_relative = x - center)
    3. **Gaussian Broadening**: Adds symmetric broadening from instrumental effects
    4. **Sigmoid Background**: Models gradual baseline variations across the spectral region, with sigmoid centered on
         the peak center and controlled by sigmoid_width and sigmoid_amplitude.
    5. **Vertical Offset**: Accounts for constant baseline displacement

    """
    # if x is a numpy array, apply the function element-wise
    flipping_factor = -1
    # asymmetry_factor controls asymmetric skew of the x axis
    x_relative = x - center
    # multiply positive x_relative by asymmetry_factor, and negative by 1/asymmetry_factor
    x_relative = np.where(x_relative >= 0, x_relative * asymmetry_factor, x_relative / asymmetry_factor)
    res = amplitude * hardy_lorentz_z2_vectorized(flipping_factor * x_relative, vmax, gamma)
    gaussian = amplitude * gaussian_amplitude * np.exp(-(x_relative ** 2) / (2 * (gaussian_sigma ** 2)))
    res += gaussian
    # addition of sigmoid background centered at center
    # sigmoid_background = sigmoid_amplitude / (1 + np.exp(-(x - center) / sigmoid_width))
    sigmoid_background = sigmoid_amplitude * 2 / np.pi * np.arctan(np.pi / 2 * x_relative / sigmoid_width)
    res += sigmoid_background + vertical_offset
    return res


def get_tba_peak_integration(filepath,
                             instrumental_rms_error=0.002,
                             verbose=True,
                             is_save_fiting_img=True,
                             is_save_report_to_json=True,
                             is_override_previous_run=False):
    """
    Quantify the NMR peaks of TBA around 2 - 3.5 ppm through automated peak fitting and integration.
    """


    print(f"Working on tba fitting for: {filepath}")

    if not is_override_previous_run:
        json_path = os.path.splitext(filepath)[0] + '_tba_fitting_intg.json'  # replace the file extension to json
        if os.path.exists(json_path):
            print('Already calculated!')
            return

    nmr_data = load_nmr_spectrum_from_csv(filepath)

    p0 = [3.72940090e+00, 1.85526572e-11, 8.08781799e-03, 4.69128724e+00,
          9.60115796e-01, 4.78635372e-03, -6.59256725e+00, 2.98970894e-01,
          1.42645144e-12, 1.40000000e-02]

    popt = p0

    min_ppm = 2.9776
    max_ppm = 3.35
    cropped_data = nmr_data[(nmr_data[:, 0] >= min_ppm) & (nmr_data[:, 0] <= max_ppm)]

    location_of_ppm_of_the_maximum_within_cropped_data = cropped_data[np.argmax(cropped_data[:, 1]), 0]

    default_max_location = 3.14288072
    shift_from_default = location_of_ppm_of_the_maximum_within_cropped_data - default_max_location

    # shift the min_ppm and max_ppm and redo the cropping
    min_ppm = 2.9776
    max_ppm = 3.5
    min_ppm = min_ppm + shift_from_default
    max_ppm = max_ppm + shift_from_default
    cropped_data = nmr_data[(nmr_data[:, 0] >= min_ppm) & (nmr_data[:, 0] <= max_ppm)]

    default_max_intensity = 0.33874780
    height_of_the_maximum_within_cropped_data = np.max(cropped_data[:, 1])
    scale_wrt_default = height_of_the_maximum_within_cropped_data / default_max_intensity

    single_peak_params = popt[:]

    n_bands = 8
    n_amplitudes = n_bands

    def spectrum_function(*args):
        x = args[0]
        gaussian_sigma, gaussian_a, offset = args[1:4]
        gamma, asymmetry, gsig = args[4:7]
        centers = args[7:7 + n_bands]  # Splitting values for sidebands
        amplitudes = args[7 + n_bands:7 + n_bands + n_amplitudes]
        gaussian_shape = gaussian_a * np.exp((x - 3.3) / gaussian_sigma) + offset
        overall_shape = np.copy(gaussian_shape)

        for i in range(len(centers)):
            center = centers[i]
            amplitude = amplitudes[i]
            lineshape_params = single_peak_params[:]  # Use the parameters from the single peak fit
            lineshape_params[0] = center  # Set the center to the current center
            lineshape_params[2] = gamma  # Set the gamma to the current gamma
            lineshape_params[4] = asymmetry  # Set the asymmetry to the current asymmetry
            lineshape_params[5] = gsig  # Set the gaussian sigma to the current gaussian sigma

            overall_shape += amplitude * lineshape_function(x, *lineshape_params)

        return overall_shape

    initial_guess = [
        0.10739204296083842,
        0.033370661727045156,
        0.023568352637486713,
        0.013922698758690368,
        0.9902472498854916,
        0.006390097208053115,
        3.345094042912188,
        3.3118771313544073,
        3.280093339947063,
        3.2559132676196447,
        3.227159057606013,
        3.2018030704502873,
        3.176785392064779,
        3.1409792798988736,
        0.002278573951209147,
        0.0008666172113703162,
        0.0016120180035724642,
        0.0022755746631087357,
        0.0010319803840434332,
        0.001232902638637008,
        0.0009188870739039915,
        0.0035823143502777665,
    ]

    # shift the ppms in initial guess by shift_from_default
    initial_guess[6:6 + n_bands] = [c + shift_from_default for c in initial_guess[6:6 + n_bands]]

    # scale the amplitudes
    initial_guess[6 + n_bands:] = [a * scale_wrt_default for a in initial_guess[6 + n_bands:]]

    # shift the exponent by modifying the gaussian_a
    gaussian_sigma = initial_guess[0]
    new_gaussian_a = initial_guess[1] / np.exp(shift_from_default / gaussian_sigma)
    initial_guess[1] = new_gaussian_a

    ## UNCOMMENT IF DEGUGGING
    # # Don't fit yet, just plot initial guess over the cropped data
    # vs = np.linspace(min_ppm, max_ppm, 1000)
    # initial_shape = spectrum_function(*([vs] + initial_guess))
    # plt.plot(vs, initial_shape, label='Initial Guess Spectrum Function', color='red')
    # plt.plot(cropped_data[:, 0], cropped_data[:, 1], 'o', color='black', alpha=0.5, markersize=1, label='Cropped Data')
    # # reverse the x-axis for chemical shift
    # plt.gca().invert_xaxis()
    # plt.legend()
    # plt.show()

    # set the bounds of center positions to no more than delta_position away from initial guess of centers
    delta_position = -1 * (initial_guess[7] - initial_guess[6]) * 4
    lower_bounds = [0.0, 0.0, -np.inf] + \
                   [0, 0, 0] + \
                   [c - delta_position for c in initial_guess[6:6 + n_bands]] + \
                   [0.0] * n_amplitudes
    upper_bounds = [np.inf, np.inf, np.inf] + \
                   [np.inf, 10, np.inf] + \
                   [c + delta_position for c in initial_guess[6:6 + n_bands]] + \
                   [np.inf] * n_amplitudes

    x_scale = initial_guess
    # x_scale[0] = 0.05  # Set the center to the maximum ppm value
    x_scale = np.abs(np.array(x_scale))

    try:
        popt, pcov = curve_fit(spectrum_function, cropped_data[:, 0], cropped_data[:, 1],
                               p0=initial_guess,
                               bounds=(lower_bounds, upper_bounds), verbose=verbose, jac='3-point',
                               maxfev=600, method='trf', x_scale=x_scale,
                               sigma=instrumental_rms_error * np.ones_like(cropped_data[:, 0]),
                               absolute_sigma=True, ftol=1e-8, xtol=1e-8)

    except RuntimeError:  # if the fit fails, we will retry with relaxed tolerances
        print('Maximum number of iterations reached on full spectrum fit. Retrying with relaxed tolerances.')
        pass
        popt, pcov = curve_fit(spectrum_function, cropped_data[:, 0], cropped_data[:, 1],
                               p0=initial_guess,
                               bounds=(lower_bounds, upper_bounds), verbose=2, jac='3-point',
                               maxfev=600, method='trf', x_scale=x_scale,
                               sigma=instrumental_rms_error * np.ones_like(cropped_data[:, 0]),
                               absolute_sigma=True, ftol=1e-5, xtol=1e-5)

    # compute the RMSE error between fit and data
    fitted_intensity = spectrum_function(*([cropped_data[:, 0]] + list(popt)))
    rmse = np.sqrt(np.mean((cropped_data[:, 1] - fitted_intensity) ** 2))


    ## UNCOMMENT IF DEGUGGING
    # # print the fitted parameters and save them to a text file in which they look like python list in python code
    # print("Fitted parameters for full spectrum:", popt)
    # print(f'Length of popt: {len(popt)}')
    # # save the fitted parameters to a file
    # with open('fitted_parameters.txt', 'w') as f:
    #     f.write('fitted_parameters = [\n')
    #     for param in popt:
    #         f.write(f'    {param},\n')
    #     f.write(']\n')

    if is_save_fiting_img:
        # plot the results of the fit
        vs = np.linspace(min_ppm, max_ppm, 1000)
        fitted_intensity = spectrum_function(*([vs] + list(popt)))
        plt.plot(vs, fitted_intensity, label='Fitted spectrum', color='gray')
        plt.plot(cropped_data[:, 0], cropped_data[:, 1], 'o', color='black', alpha=0.5, markersize=1, label='Data')

        colors = ['C1', 'C0']
        # plot axvlines for the centers of the peaks
        for i in range(n_bands):
            center = popt[6 + i]
            color_here = colors[i % len(colors)]
            plt.axvline(center, color=color_here, linestyle='--', label=f'Line {i+1}: {center:.4f} ppm')

        for i in range(n_bands):
            # plot separate lineshapes, one for each center
            center = popt[6 + i]
            amplitude_here = popt[6 + n_bands + i]
            lineshape_params = single_peak_params[:]  # Use the parameters from the single peak fit
            lineshape_params[0] = center  # Set the center to the current center
            lineshape_params[2] = popt[3]  # Set the gamma to the current gamma
            lineshape_params[4] = popt[4]  # Set the asymmetry to the current asymmetry
            lineshape_params[5] = popt[5]  # Set the gaussian sigma to the current gaussian sigma
            lineshape_intensity = amplitude_here * lineshape_function(vs, *lineshape_params)
            # do a fillbetween for the lineshape
            color_here = colors[i % len(colors)]
            plt.fill_between(vs, lineshape_intensity, alpha=0.1, color=color_here)
        # plot the Gaussian shape
        gaussian_sigma = popt[0]
        gaussian_a = popt[1]
        offset = popt[2]
        gaussian_shape = gaussian_a * np.exp((vs-3.3)/gaussian_sigma) + offset
        plt.plot(vs, gaussian_shape, label='Exponential\nbackground', color='C2')

        # reverse the x-axis for chemical shift
        plt.gca().invert_xaxis()
        plt.legend()
        plt.xlabel('Chemical shift (ppm)')
        plt.ylabel('Intensity')
        # plt.show()
        img_path = os.path.splitext(filepath)[0] + '.png' # replace the file extension to png
        os.makedirs(os.path.dirname(img_path), exist_ok=True) # make sure the dir exist
        plt.savefig(img_path)

    # The main peak integration isolates the pure lineshape component by setting
    # sigmoid_amplitude=0 and vertical_offset=0, then using the remaining best-fit parameters to numerically integrate
    # the spectrum (best-fitted) over the region
    # ±0.7 ppm around the center using adaptive quadrature with
    # convergence tolerance of 1e-10.
    def fit_spectrum_without_baseline(x):
        opts = ['_'] + list(popt)
        gamma, asymmetry, gsig = opts[4:7]
        centers = opts[7:7 + n_bands]  # Splitting values for sidebands
        amplitudes = opts[7 + n_bands:7 + n_bands + n_amplitudes]

        overall_shape = np.zeros_like(x)

        for i in range(len(centers)):
            center = centers[i]
            amplitude = amplitudes[i]
            # lineshape_params_here
            lineshape_params = single_peak_params[:]  # Use the parameters from the single peak fit
            lineshape_params[0] = center  # Set the center to the current center
            lineshape_params[2] = gamma  # Set the gamma to the current gamma
            lineshape_params[4] = asymmetry  # Set the asymmetry to the current asymmetry
            lineshape_params[5] = gsig  # Set the gaussian sigma to the current gaussian sigma

            # setting sigmoid_amplitude=0, vertical_offset=0 because we are not interested in the integration of the baseline
            lineshape_params[-1] = 0  # Set sigmoid_amplitude to 0
            lineshape_params[-2] = 0  # Set vertical_offset to 0

            overall_shape += amplitude * lineshape_function(x, *lineshape_params)

        return overall_shape

    # center is the mean of centers
    centers = popt[6:6 + n_bands]
    center = np.mean(centers)
    integration_halfwidth = 0.7

    ### UNCOMMENT IF DEGUGGING
    # # plot the fit_spectrum_without_baseline
    # vs = np.linspace(center - integration_halfwidth, center + integration_halfwidth, 1000)
    # fitted_intensity_without_baseline = fit_spectrum_without_baseline(vs)
    # plt.fill_between(x=vs, y1=0, y2=fitted_intensity_without_baseline, label='Fitted spectrum without baseline',
    #                  color='C0', alpha=0.5)
    # plt.plot(cropped_data[:, 0], cropped_data[:, 1], 'o', color='black', alpha=0.5, markersize=1, label='Data')
    # plt.show()

    integration_result = quad(fit_spectrum_without_baseline,
                              center - integration_halfwidth,
                              center + integration_halfwidth,
                              limit=1000, points=[centers],
                              epsabs=1e-10)
    overall_integral, integration_error = integration_result

    report = dict()
    # add RMSE to the report
    report['rmse'] = rmse

    # Add the fit parameters into the dictionary, use proper names as keys
    report['fit_parameters'] = {
        'gaussian_sigma': popt[0],
        'gaussian_amplitude': popt[1],
        'sigmoid_width': popt[2],
        'sigmoid_amplitude': popt[3],
        'asymmetry_factor': popt[4],
        'gamma': popt[5],
        'vertical_offset': popt[6],
    }

    # add line centers and amplitudes to the report
    report['line_centers'] = popt[7:7 + n_bands].tolist()
    report['line_amplitudes'] = popt[7 + n_bands:7 + n_bands + n_amplitudes].tolist()

    # add integral to the report
    report['overall_integral'] = overall_integral

    if is_save_report_to_json:
        # save result to json
        json_path = os.path.splitext(filepath)[0] + '_tba_fitting_intg.json'  # replace the file extension to json
        with open(json_path, "w") as json_file:
            json.dump(report, json_file, indent=4)

    # return main_peak_integral, main_peak_integral_uncertainty, dictionary_to_return
    return overall_integral, report


if __name__ == '__main__':
    ## Example usage
    # filepath = 'test_data/tba/data1.csv'
    # overall_integral, report = get_tba_peak_integration(filepath=filepath)
    # print(f'main peak integral: {overall_integral} [ppm * intensity_unit]')
    # print(f'RMSE of the fit: {report["rmse"]} [intensity_unit]')

    tbabr3_path = r"D:\Dropbox\brucelee\data\DPE_bromination"
    folder_list = [
                   # r'\2025-04-15-run01_DCE_TBABr3_normal',
                   # r'\2025-04-15-run02_DCE_TBABr3_normal',
                   # r'\2025-04-15-run03_DCE_TBABr3_normal',
                   # r'\2025-04-15-run04_DCE_TBABr3_normal',
                    r"\2025-04-22-run01_DCE_TBABr3_normal",
                    r"\2025-09-11-run01_DCE_TBABr3_add",
                    r"\2025-09-11-run02_DCE_TBABr3_add",
                   ]
    run_folder_paths = [tbabr3_path+folder_name for folder_name in folder_list]

    data_dir_ls = []
    data_file_ls = []

    for run_folder_path in run_folder_paths:
        result_folder = run_folder_path + r'\Results'
        # Iterate through subfolders inside "Results", and get all csv data files
        for folder in os.listdir(result_folder):
            folder_path = os.path.join(result_folder, folder)

            if "1D EXTENDED" in folder_path:
                data_dir_ls.append(folder_path)
                data_file = folder_path + "\\data.csv"
                if not os.path.isfile(data_file):
                    raise FileNotFoundError(f"Error! Data file not found in: {folder_path}")
                data_file_ls.append(data_file)

    # for data_file in data_file_ls:
    #     # perform fitting here
    #     get_tba_peak_integration(data_file)

    import os
    from concurrent.futures import ProcessPoolExecutor
    max_workers = 16
    with ProcessPoolExecutor(max_workers) as executor:
        executor.map(get_tba_peak_integration, data_file_ls)