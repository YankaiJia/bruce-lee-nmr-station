"""
Quantitative NMR analysis of spectral components in the 10 ppm region.

This module provides a very case-specific tool for automated peak fitting, integration, and uncertainty analysis of
NMR spectra around 10 ppm chemical shift, with the aim of quantifying 9.86 ppm peak near the main 10 ppm peak,
even when carbon-13 isotopologues produce sidebands of the main peak that overlap with 9.86 ppm peak.

The analysis employs asymmetric pseudo-Voigt lineshape based on Hardy-Lorentz-z2 lineshape with sigmoid baseline
and vertical offset.

Reference: Hardy, E. "NMR Methods for the Investigation of Structure and Transport", Chapter 7.

The core workflow implements a two-stage fitting protocol: initial single-component
lineshape optimization followed by multi-component spectral modeling including main
peak, sidebands of the main peak, and a second peak (product).

Example of usage
-------------
>>> integral1, error_of_integral1, integral2, error_of_integral2, report = get_10ppm_peak_integration('spectrum.csv')
>>> make_diagnostic_plots('spectrum.csv', report, save_fig_to_filepath='analysis.png')
>>> print(f"Main peak integral = {integral1:.3e} ± {error_of_integral1:.3e} [ppm·intensity_unit]")
>>> print(f"Secondary peak integral =  {integral2:.3e} ± {error_of_integral2:.3e} [ppm·intensity_unit]")

Author: Yaroslav I. Sobolev, yaroslav.sobolev@gmail.com, IBS Center for Algorithmic and Robotized Synthesis
"""

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
    flipping_factor = 1
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


def spectrum_function(x, center, splitting, deltappm, vmax, gamma, amplitude, asymmetry_factor, gaussian_sigma,
                      gaussian_amplitude, sigmoid_width,
                      sigmoid_amplitude, vertical_offset, sidebands_intensity, second_peak_intensity):
    """
    Complete spectral model combining main peak, its sidebands, and a secondary peak partially overlapping with one of the sidebands.

    Parameters
    ----------
    x : numpy.ndarray
        Chemical shift values (ppm) for evaluation.
    center : float
        Main peak center position (ppm).
    splitting : float
        Frequency separation between main peak and sidebands (ppm).
    deltappm : float
        Chemical shift offset of secondary peak from main peak (ppm).
    vmax : float
        Hardy lineshape maximum frequency parameter, shared across all peaks.
    gamma : float
        Hardy lineshape damping parameter, shared across all peaks.
    amplitude : float
        Amplitude for Hardy lineshape component.
    asymmetry_factor : float
        Peak asymmetry parameter, shared across all peaks. Values > 1 create rightward skew, < 1 leftward skew.
    gaussian_sigma : float
        Gaussian broadening standard deviation (ppm), shared across all peaks.
    gaussian_amplitude : float
        Gaussian component amplitude (relative), shared across all peaks.
    sigmoid_width : float
        Sigmoid background width parameter (ppm).
    sigmoid_amplitude : float
        Sigmoid background amplitude.
    vertical_offset : float
        Constant baseline offset.
    sidebands_intensity : float
        Relative intensity of symmetric sidebands around the main peak.
    second_peak_intensity : float
        Relative intensity of the secondary peak.

    Returns
    -------
    numpy.ndarray
        Intensity of total spectrum combining all peak components, evaluated at input x values.

    Notes
    -----
    **Spectral Components:**

    1. **Main Peak**: Primary resonance at `center` position with full lineshape model
    2. **Symmetric Sidebands**: Two peaks at `center ± splitting`, scaled by `sidebands_intensity`
    3. **Secondary Peak**: Additional resonance at `center - deltappm`, scaled by `second_peak_intensity`

    All peaks share the same fundamental lineshape parameters (vmax, gamma, amplitude,
    asymmetry_factor, gaussian_sigma, gaussian_amplitude) but have independent intensity
    scaling.

    """

    main_line = lineshape_function(x, center, vmax, gamma, amplitude, asymmetry_factor, gaussian_sigma,
                                   gaussian_amplitude, sigmoid_width, sigmoid_amplitude, vertical_offset)
    sidebands = (sidebands_intensity * lineshape_function(x, center - splitting, vmax, gamma, amplitude,
                                                          asymmetry_factor, gaussian_sigma, gaussian_amplitude,
                                                          sigmoid_width, sigmoid_amplitude, vertical_offset) +
                 sidebands_intensity * lineshape_function(x, center + splitting, vmax, gamma, amplitude,
                                                          asymmetry_factor, gaussian_sigma, gaussian_amplitude,
                                                          sigmoid_width, sigmoid_amplitude, vertical_offset))

    second_peak = second_peak_intensity * lineshape_function(x, center - deltappm, vmax, gamma, amplitude,
                                                             asymmetry_factor, gaussian_sigma, gaussian_amplitude,
                                                             sigmoid_width, sigmoid_amplitude, vertical_offset)

    return main_line + sidebands + second_peak


def get_10ppm_peak_integration(filepath, instrumental_rms_error=0.0020, verbose=2):
    """
    Quantify the NMR peaks around 10ppm through automated peak fitting and integration.

    Performs comprehensive analysis of NMR spectra in the 9-11 ppm region to determine
    the integrated intensity of a specific secondary peak. The function implements a
    two-stage fitting protocol: initial single-peak NMR lineshape optimization followed by full
    multi-component spectral modeling, culminating in precise numerical integration
    of the target component.

    The analysis workflow:

    1. **Data preprocessing**: Load spectrum and isolate 9-11 ppm region
    2. **Peak detection**: Locate the location of the signal maximum intensity to use as initial guess
    3. **Single-peak fitting**: Initial parameter estimation of the NMR lineshape model
    4. **Multi-component fitting**: Full spectral model including main peak, sidebands, and secondary peak
    5. **Component integration**: Numerical integration of the best-fit secondary peak
    6. **Uncertainty propagation**: Calculate integration uncertainty from fitting errors

    Parameters
    ----------
    filepath : str
        Path to CSV file containing NMR spectrum data. Expected format: two columns
        [chemical_shift_ppm, intensity] with single header row.
    instrumental_rms_error : float, optional
        Estimated RMS noise level for weighted fitting. Default 0.0020. Used to
        calculate parameter uncertainties. Noise is assumed to be homoscedactic.
    verbose : int, optional
        Verbosity level for diagnostic output. 0: silent, 2: detailed.
        Default 2 makes printing of the curve_fit progress and fitted parameters.

    Returns
    -------
    main_peak_integral : float
        Integral of the main peak. Units are [ppm * intensity_unit].
        Calculated by numerical integration of the best-fit main peak model.
    main_peak_integral_uncertainty : float
        Uncertainty in the integral of the main peak, propagated from fitting parameter errors. Units are [ppm * intensity_unit].
    second_peak_integral : float
        Integral of the secondary peak. Units are [ppm * intensity_unit].
        Calculated by numerical integration of the best-fit secondary peak model.
    second_peak_integral_uncertainty : float
        Uncertainty in the integral of the secondary peak, propagated from fitting parameter errors. Units are [ppm * intensity_unit].
    dictionary_to_return : dict
        Dictionary of complete analysis results containing:

        **Fitted Parameters:**
        - 'center': Main peak position (ppm)
        - 'splitting': Sideband separation from main peak (ppm)
        - 'deltappm': Secondary peak offset from main peak (ppm)
        - 'vmax', 'gamma': Hardy-Lorentz-z2 lineshape parameters
        - 'amplitude': Hardy-Lorentz-z2 lineshape amplitude
        - 'asymmetry_factor': Peak asymmetry parameter
        - 'gaussian_sigma', 'gaussian_amplitude': Gaussian broadening parameters
        - 'sigmoid_width', 'sigmoid_amplitude': Background parameters
        - 'vertical_offset': Baseline offset
        - 'sidebands_intensity': Relative sideband intensity
        - 'second_peak_intensity': Relative secondary peak intensity

        **Analysis Results:**
        - 'second_peak_intensity_uncertainty': Fitting uncertainty for secondary peak amplitude
        - 'second_peak_integral': Integral of the secondary peak. Units are [ppm * intensity_unit].
        - 'second_peak_integral_uncertainty': Uncertainty in the secondary peak integral. Units are [ppm * intensity_unit].
        - 'optimized_parameters': Complete parameter array from fitting
        - 'optimized_parameters_errors': Parameter uncertainty array
        - 'residuals_rms': RMS of the residuals from final fit. Units are intensity units.


    Examples
    --------
    >>> # Basic analysis with default settings
    >>> main_peak_integral, main_peak_integral_uncertainty, secondary_peak_integral, secondary_peak_integral_uncertainty, report = get_10ppm_peak_integration('sample_nmr.csv')
    >>> print(f"Main peak integral: {main_peak_integral:.3e} ± {main_peak_integral_uncertainty:.3e}")
    >>> print(f"Secondary peak integral: {econdary_peak_integral:.3e} ± {secondary_peak_integral_uncertainty:.3e}")

    >>> # Quiet analysis for batch processing: it does not print anything
    >>> main_peak_integral, main_peak_integral_uncertainty, secondary_peak_integral, secondary_peak_integral_uncertainty, report = get_10ppm_peak_integration('sample_nmr.csv', verbose=0)
    """
    nmr_data = load_nmr_spectrum_from_csv(filepath)
    # crop the data between 9 and 11 ppm
    min_ppm = 9.25
    max_ppm = 11
    cropped_data = nmr_data[(nmr_data[:, 0] >= min_ppm) & (nmr_data[:, 0] <= max_ppm)]
    ppm_of_the_maximum = cropped_data[np.argmax(cropped_data[:, 1]), 0]
    height_of_the_maximum = np.max(cropped_data[:, 1])
    if verbose == 2:
        print(f"Maximum intensity found at {ppm_of_the_maximum:.4f} ppm with height {height_of_the_maximum:.4f}")

    min_ppm = ppm_of_the_maximum - (9.96666016 - 9.6)
    max_ppm = ppm_of_the_maximum + (9.96666016 - 9.6)

    cropped_data = nmr_data[(nmr_data[:, 0] >= min_ppm) & (nmr_data[:, 0] <= max_ppm)]

    # The two-stage fitting approach improves convergence reliability:
    #
    # Stage 1: Fitting a single asymmetric pseudo-Voigt based on Hardy-Lorentz0-z2 lineshape with sigmoid baseline
    # provides robust initial parameter estimates of the NMR lineshape
    # Stage 2: Full multi-component model with parameters' initial guess based on Stage 1 results
    center = ppm_of_the_maximum
    fit_lineshape = lineshape_function
    lower_bounds = [min_ppm, 0, 0, 0, 0, 0, 0, 0.0001, 0, -0.014]
    upper_bounds = [max_ppm, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, 0.3, 0.01, 0.014]

    p0 = [center, 5.68877297e-26, 9.64055154e-03, 3.63118448e-02 / 2.1 * height_of_the_maximum,
          9.36311714e-01, 5.10908742e-03, 2.49549047e+01,
          1.93666225e-03, 2.44896635e-03, -1.30129103e-03]

    x_scale = p0[:]
    x_scale[0] = 0.05  # Set the center to the maximum ppm value
    x_scale = np.abs(np.array(x_scale))

    popt, pcov = curve_fit(fit_lineshape, cropped_data[:, 0], cropped_data[:, 1],
                           p0=p0,
                           bounds=(lower_bounds, upper_bounds), verbose=verbose, jac='3-point', x_scale=x_scale,
                           gtol=1e-9, maxfev=10000)
    best_fit_center = popt[0]

    if verbose == 2:
        print("Fitted parameters:", popt)
        print(f'Length of popt: {len(popt)}')

    # ## PLOT FOR DEBUGGING ONLY
    # vs = np.linspace(min_ppm, max_ppm, 1000)
    # fitted_intensity = fit_lineshape(vs, *popt)
    # plt.plot(vs, fitted_intensity, label='Fitted Lineshape Function', color='blue')
    # plt.plot(cropped_data[:, 0], cropped_data[:, 1], 'o', color='black', alpha=0.5, markersize=1, label='Cropped Data')
    # # reverse the x-axis for chemical shift
    # plt.gca().invert_xaxis()
    # plt.legend()
    # plt.show()


    # Critical parameters are constrained based on empirical analysis:
    # - Splitting bounds: 0.7-1.3 × 0.148 ppm (typical coupling constant range)
    # - deltappm bounds: 0.7-1.3 × 0.143 ppm (characteristic chemical shift difference)
    splitting_p0 = 1.48721827e-01
    delta_ppm_p0 = 1.42794971e-01


    # if the center of the most intense peak identified above is closer to 9.96666016 than to (9.96666016 - 1.48721827e-01)
    # then assume that we have fitted the main peak. Otherwise, assume we have fitted secondary peak
    if np.abs(best_fit_center - (9.96666016 - delta_ppm_p0)) < np.abs(best_fit_center - 9.96666016):
        strongest_peak_is_main = False
        main_peak_guess = best_fit_center + delta_ppm_p0
        if verbose == 2:
            print(f"Assuming the strongest peak at {best_fit_center:.4f} ppm is the secondary peak.")
    else:
        strongest_peak_is_main = True
        main_peak_guess = best_fit_center
        if verbose == 2:
            print(f"Assuming the strongest peak at {best_fit_center:.4f} ppm is the main peak.")

    min_ppm = main_peak_guess - (9.96666016 - 9.6)
    max_ppm = main_peak_guess + (9.96666016 - 9.6)
    cropped_data = nmr_data[(nmr_data[:, 0] >= min_ppm) & (nmr_data[:, 0] <= max_ppm)]

    lower_bounds = [main_peak_guess - 0.05, 0.7 * splitting_p0, 0.7 * delta_ppm_p0, 0, 0, 0, 0, 0, 0, 0.0001, 0, -0.014, 0, 0]
    upper_bounds = [main_peak_guess + 0.05, 1.3 * splitting_p0, 1.5 * delta_ppm_p0, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf,
                    0.3, 0.01, 0.014, 1, np.inf]

    # inherit the p0 from the popt
    # from the previous fit
    # to use as initial guess for the full spectrum fit
    # but modify the splitting and deltappm parameters
    # to be more flexible
    # and allow for sidebands and second peak intensity
    if strongest_peak_is_main:
        p0 = [main_peak_guess] + [splitting_p0, delta_ppm_p0] + list(popt[1:]) + [0.01, 0.01]
    else:
        p0 = [main_peak_guess] + [splitting_p0, delta_ppm_p0] + list(popt[1:]) + [0.01, 10]
    x_scale = p0[:]
    x_scale[0] = 0.05  # Set the center to the maximum ppm value
    x_scale = np.abs(np.array(x_scale))

    popt, pcov = curve_fit(spectrum_function, cropped_data[:, 0], cropped_data[:, 1],
                           p0=p0,
                           bounds=(lower_bounds, upper_bounds), verbose=2, jac='3-point',
                           maxfev=10000, method='trf', x_scale=x_scale,
                           sigma=instrumental_rms_error * np.ones_like(cropped_data[:, 0]),
                           absolute_sigma=True, ftol=1e-11, xtol=1e-9)

    perr = np.sqrt(np.diag(pcov))
    if verbose == 2:
        print("Fitted parameters for the full spectrum:", popt)
        print(f'Fitted second peak amplitude with error {popt[-1]} ± {perr[-1] / popt[-1]:.2%} %')

    # get RMSD of the residual
    n_last_points = 30
    residuals = cropped_data[-n_last_points:, 1] - spectrum_function(cropped_data[-n_last_points:, 0], *popt)
    rms_error = np.std(residuals)
    if verbose == 2:
        print(f'RMS residual: {rms_error}')
        
    # Optimal parameters are:
    (center, splitting, deltappm, vmax, gamma, amplitude, asymmetry_factor, gaussian_sigma, gaussian_amplitude,
     sigmoid_width, sigmoid_amplitude, vertical_offset, sidebands_intensity, second_peak_intensity) = popt
    second_peak_intensity_uncertainty = perr[-1]
    main_peak_amplitude_uncertainty = perr[5]
        
    # The main peak integration isolates the pure lineshape component by setting
    # sigmoid_amplitude=0 and vertical_offset=0, then using the remaining best-fit parameters to numerically integrate
    # the secondary peak lineshape (best-fitted) over the region
    # ±2 ppm around the main peak center using adaptive quadrature with
    # convergence tolerance of 1e-10.
    main_peak_partial = lambda x: lineshape_function(x, center, vmax, gamma,
                                                     amplitude,
                                                     asymmetry_factor, gaussian_sigma,
                                                     gaussian_amplitude, sigmoid_width,
                                                     sigmoid_amplitude=0,
                                                     vertical_offset=0)
    integration_halfwidth = 2
    integration_result = quad(main_peak_partial,
                              center - integration_halfwidth,
                              center + integration_halfwidth,
                              limit=1000, points=[center],
                              epsabs=1e-10)
    main_peak_integral, main_peak_integration_error = integration_result
    main_peak_integral_uncertainty = main_peak_amplitude_uncertainty / amplitude * main_peak_integral
    if verbose == 2:
        print(
            f'main peak integral: ({main_peak_integral} ± {main_peak_integral_uncertainty} ) [ppm * intensity_unit]')
        

    # The secondary peak integration isolates the pure lineshape component by setting
    # sigmoid_amplitude=0 and vertical_offset=0, then using the remaining best-fit parameters to numerically integrate
    # the secondary peak lineshape (best-fitted) over the region
    # ±2 ppm around the secondary peak center using adaptive quadrature with
    # convergence tolerance of 1e-10.



    # Partial application of the lineshape function for the second peak
    second_peak_partial = lambda x: second_peak_intensity * lineshape_function(x, center - deltappm, vmax, gamma,
                                                                               amplitude,
                                                                               asymmetry_factor, gaussian_sigma,
                                                                               gaussian_amplitude, sigmoid_width,
                                                                               sigmoid_amplitude=0,
                                                                               vertical_offset=0)
    integration_halfwidth = 2
    integration_result = quad(second_peak_partial,
                              center - deltappm - integration_halfwidth,
                              center - deltappm + integration_halfwidth,
                              limit=1000, points=[center - deltappm],
                              epsabs=1e-10)
    second_peak_integral, second_peak_integration_error = integration_result
    second_peak_integral_uncertainty = second_peak_intensity_uncertainty / second_peak_intensity * second_peak_integral
    if verbose == 2:
        print(
            f'Second peak integral: ({second_peak_integral} ± {second_peak_integral_uncertainty} ) [ppm * intensity_unit]')

    dictionary_to_return = {
        'center': center,
        'splitting': splitting,
        'deltappm': deltappm,
        'vmax': vmax,
        'gamma': gamma,
        'amplitude': amplitude,
        'asymmetry_factor': asymmetry_factor,
        'gaussian_sigma': gaussian_sigma,
        'gaussian_amplitude': gaussian_amplitude,
        'sigmoid_width': sigmoid_width,
        'sigmoid_amplitude': sigmoid_amplitude,
        'vertical_offset': vertical_offset,
        'sidebands_intensity': sidebands_intensity,
        'second_peak_intensity': second_peak_intensity,
        'second_peak_intensity_uncertainty': second_peak_intensity_uncertainty,
        'second_peak_integral': second_peak_integral,
        'second_peak_integral_uncertainty': second_peak_integral_uncertainty,
        'optimized_parameters': popt,
        'optimized_parameters_errors': perr,
        'residuals_rms': rms_error,
    }

    return main_peak_integral, main_peak_integral_uncertainty, second_peak_integral, second_peak_integral_uncertainty, dictionary_to_return


def simpleaxis(ax):
    """
    Apply minimal axis styling by removing top and right spines.

    Removes the top and right border lines from matplotlib axes to create
    a cleaner, less cluttered appearance following modern plotting conventions e.g. by Nature journals.
    Repositions tick marks to the remaining visible axes.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Matplotlib axes object to modify.

    """
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()


def make_diagnostic_plots(filepath, report_dictionary, save_fig_to_filepath=None,
                          figsize=(12, 10), min_ppm=9.25, max_ppm=11, do_show=True, custom_title=None):
    """
    Generate comprehensive diagnostic plots for NMR peak fitting analysis by the `get_10ppm_peak_integration()` function.

    Creates a multi-panel figure displaying raw data, fitted models, residual analysis,
    and component visualization to assess the quality and reliability of the automated
    peak fitting and integration workflow.

    When `do_show=False`, the function automatically clears and closes the figure
    to prevent memory accumulation in batch processing workflows. Figures are
    saved at high-resolution (300 DPI) in PNG format if `save_fig_to_filepath` is provided.

    Optionally, custom title (`custom_title` parameter) can be set for each figure to aid in sample identification or
    batch processing workflows.

    The diagnostic layout includes:

    1. **Raw spectrum**: Log-scale intensity plot showing the full spectral region
    2. **Fit comparison**: Linear-scale overlay of data and fitted model
    3. **Zoomed fit**: Detailed view focused on the peak region of interest
    4. **Component visualization**: Highlighted secondary peak integration area
    5. **Residual analysis**: Fitting residuals with smoothed trend analysis
    6. **Residual distribution**: Histogram of residual values for noise assessment

    Parameters
    ----------
    filepath : str
        Path to CSV file containing the original NMR spectrum data.
    report_dictionary : dict
        Results dictionary from `get_10ppm_peak_integration()` containing fitted
        parameters and analysis results.
    save_fig_to_filepath : str or None, optional
        Full path for saving the diagnostic figure. If None, figure is not saved.
        Recommended format: PNG with 300 DPI for publication quality.
    figsize : tuple of float, optional
        Figure dimensions (width, height) in inches. Default (12, 10) provides
        good balance between detail and screen/print readability.
    min_ppm : float, optional
        Minimum chemical shift for plot range (ppm). Default 9.25.
    max_ppm : float, optional
        Maximum chemical shift for plot range (ppm). Default 11.
    do_show : bool, optional
        Whether to display the figure interactively. Default True. Set False
        for batch processing or when only saving figures.
    custom_title : str or None, optional
        Custom figure title to override the default. Useful for sample identification
        or batch processing workflows.

    Notes
    -----
    **Panel Layout:**

    The figure uses a 2×3 GridSpec layout with variable column widths:
    ```
    >>> # Layout structure:
    >>> [Raw Spectrum    ][  Zoomed Fit View   ]
    >>> [Fit Comparison  ][Residuals][Hist]
    ```

    Examples
    --------
    >>> # Interactive analysis with popup matplotlib display (`plt.show()`)
    >>> main_peak_integral, main_peak_integral_uncertainty, secondary_peak_integral, secondary_peak_integral_uncertainty, report = get_10ppm_peak_integration('sample.csv')
    >>> make_diagnostic_plots('sample.csv', report,
    ...                      save_fig_to_filepath='sample_analysis.png')

    >>> # Batch processing without invoking interactive display
    >>> for filepath in spectrum_files:
    ...     main_peak_integral, main_peak_integral_uncertainty, secondary_peak_integral, secondary_peak_integral_uncertainty, report = get_10ppm_peak_integration(filepath, verbose=0)
    ...     # ...here you may want to use integral values for further processing...
    ...     # And then you save diagnostic plots for each file, like so:
    ...     output_path = filepath.replace('.csv', '_diagnostic.png')
    ...     make_diagnostic_plots(filepath, report, save_fig_to_filepath=output_path,
    ...                          do_show=False, custom_title=f'Input file: {filepath}')
    """
    popt = report_dictionary['optimized_parameters']
    (center, splitting, deltappm, vmax, gamma, amplitude, asymmetry_factor, gaussian_sigma, gaussian_amplitude,
     sigmoid_width, sigmoid_amplitude, vertical_offset, sidebands_intensity, second_peak_intensity) = popt

    nmr_data = load_nmr_spectrum_from_csv(filepath)
    # crop the data between 9 and 11 ppm
    cropped_data = nmr_data[(nmr_data[:, 0] >= min_ppm) & (nmr_data[:, 0] <= max_ppm)]

    fig = plt.figure(figsize=figsize)
    gs = GridSpec(2, 3, width_ratios=[3, 3, 1], height_ratios=[1, 1], wspace=0.3)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[1, 0])
    ax3 = fig.add_subplot(gs[0, 1:])
    ax4 = fig.add_subplot(gs[1, 1])
    ax5 = fig.add_subplot(gs[1, 2])
    axs = np.array([[ax1, ax3], [ax2, ax4]])

    title = 'Raw NMR spectrum in log scale'
    xlabel = 'Chemical Shift (ppm)'
    ylabel = 'Intensity'
    ax = axs[0, 0]
    ax.plot(cropped_data[:, 0], cropped_data[:, 1] - np.min(cropped_data[:, 1]), 'o', color='black', alpha=0.3,
            markersize=1)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_yscale('log')
    ax.invert_xaxis()  # Invert x-axis for chemical shift
    simpleaxis(ax)

    # Plot the fitted spectrum function
    ax = axs[1, 0]
    vs = np.linspace(min_ppm, max_ppm, 1000)
    fitted_spectrum = spectrum_function(vs, *popt)
    ax.plot(vs, fitted_spectrum, label='Fitted model', color='C0')
    ax.plot(cropped_data[:, 0], cropped_data[:, 1], 'o', color='black', alpha=0.5, markersize=1, label='Data')

    # plot the area between the first peak and the fitted spectrum
    main_peak_shape = lineshape_function(vs, center, vmax, gamma,
                       amplitude,
                       asymmetry_factor, gaussian_sigma,
                       gaussian_amplitude, sigmoid_width,
                       sigmoid_amplitude=0,
                       vertical_offset=0)
    ax.fill_between(x=vs, y1=fitted_spectrum - main_peak_shape, y2=fitted_spectrum, color='gold', alpha=0.25,
                    label='Main peak\ncontribution')

    # reverse the x-axis for chemical shift
    ax.set_title('Comparison of fit and data')
    ax.set_xlim(report_dictionary['center'] - report_dictionary['deltappm'] * 2,
                report_dictionary['center'] + report_dictionary['deltappm'] * 2)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.invert_xaxis()  # Invert x-axis for chemical shift
    ax.legend()
    simpleaxis(ax)

    # Plot the fitted spectrum function, zoomed
    ax = axs[0, 1]
    vs = np.linspace(min_ppm, max_ppm, 1000)
    ax.plot(vs, fitted_spectrum, color='C0')
    ax.plot(cropped_data[:, 0], cropped_data[:, 1], 'o', color='black', alpha=0.5, markersize=1)
    # reverse the x-axis for chemical shift
    ax.set_title('Comparison of fit and data, zoomed')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xlim(report_dictionary['center'] - report_dictionary['deltappm'] * 1.3,
                report_dictionary['center'] + report_dictionary['deltappm'] * 1.3)

    # make log scale for y-axis
    ax.invert_xaxis()  # Invert x-axis for chemical shift

    # fill between the fitted spectrum minus pure spectrum of the second peak

    pure_spectrum_of_second_peak = second_peak_intensity * lineshape_function(vs, center - deltappm, vmax, gamma,
                                                                              amplitude,
                                                                              asymmetry_factor, gaussian_sigma,
                                                                              gaussian_amplitude, sigmoid_width,
                                                                              sigmoid_amplitude=0,
                                                                              vertical_offset=0)
    ax.fill_between(x=vs, y1=fitted_spectrum - pure_spectrum_of_second_peak, y2=fitted_spectrum, color='C1', alpha=0.5,
                    label='Shaded area of the second peak\n' + f'({report_dictionary["second_peak_integral"]:.3e} ± {report_dictionary["second_peak_integral_uncertainty"]:.3e} ) [ppm·intensity_unit]')
    ax.legend()
    mask = (cropped_data[:, 0] < center - 0.09) | (cropped_data[:, 0] > center + 0.09)
    ax.set_ylim(np.min(cropped_data[mask, 1]) * 0.8,
                np.max(cropped_data[mask, 1]) * 1.2)
    simpleaxis(ax)

    # plot the residuals, and add a small vertical histogram of its distribution vertically on the right
    residuals = cropped_data[:, 1] - spectrum_function(cropped_data[:, 0], *popt)
    ax_residuals = ax4
    ax_residuals.plot(cropped_data[:, 0], residuals, 'o', color='black', alpha=0.5, markersize=2,
                      label=f'Raw (rms={report_dictionary["residuals_rms"]:.5f})')
    ax_residuals.axhline(0, color='red', linestyle='--', linewidth=1, label='Zero line')
    # plot the savgol smoothed residuals with window 15
    smoothed_residuals = savgol_filter(residuals, window_length=15, polyorder=2)
    ax_residuals.plot(cropped_data[:, 0], smoothed_residuals, alpha=0.5, color='C2', label='Smoothed')
    ax_residuals.set_title('Residuals')
    ax_residuals.set_xlabel('Chemical Shift (ppm)')
    ax_residuals.set_ylabel('Residual Intensity')
    ax_residuals.legend()
    ax_residuals.set_xlim(report_dictionary['center'] - report_dictionary['deltappm'] * 2,
                          report_dictionary['center'] + report_dictionary['deltappm'] * 2)
    ax_residuals.invert_xaxis()  # Invert x-axis for chemical shift
    simpleaxis(ax_residuals)

    # add a vertical histogram of the residuals distribution on the right side of the residuals plot
    ax_hist = ax5
    ax_hist.hist(residuals, bins=30, orientation='horizontal', color='gray', alpha=0.4, density=True)

    # plot the gaussian fit to the histogram
    hist_data = np.histogram(residuals, bins=30)
    bin_centers = 0.5 * (hist_data[1][:-1] + hist_data[1][1:])
    mean = np.mean(residuals)
    std_dev = np.std(residuals)
    gaussian_fit = np.exp(-(bin_centers - mean) ** 2 / (2 * std_dev ** 2)) / (std_dev * np.sqrt(2 * np.pi))
    ax_hist.plot(gaussian_fit, bin_centers, alpha=0.4, color='black', label='Gaussian fit to histogram')
    ax_hist.set_xlabel('')
    ax_hist.set_yticks([])
    ax_hist.set_xticks([])
    simpleaxis(ax_hist)
    ax_hist.spines['bottom'].set_visible(False)

    if custom_title is not None:
        fig.suptitle(custom_title, fontsize=16)

    if save_fig_to_filepath is not None:
        plt.savefig(save_fig_to_filepath, dpi=300, bbox_inches='tight')

    if do_show:
        plt.show()
    else:  # clear figure and delete it
        plt.clf()
        plt.close(fig)


def generate_mock_data_for_testing():
    ### make a simulated spectrum where secondary peak is stronger than the main peak
    splitting_p0 = 1.48721827e-01
    delta_ppm_p0 = 1.42794971e-01
    p0 = [9.96666016, splitting_p0, delta_ppm_p0, 5.68877297e-26, 9.64055154e-03, 0.1*3.63118448e-02,
          9.36311714e-01, 5.10908742e-03, 2.49549047e+01,
          1.93666225e-03, 0.1*2.44896635e-03, -1.30129103e-03, 0.03, 10]
    nmr_data = load_nmr_spectrum_from_csv(filepath)
    vs = nmr_data[:, 0]
    simulated = spectrum_function(vs, *p0)
    # add noise of 0.002 to the simulated data
    noise = np.random.normal(0, 0.002, size=simulated.shape)
    simulated += noise
    # save to csv
    simulated_data = np.column_stack((vs, simulated[::-1]))
    np.savetxt('test_data/data3.csv', simulated_data, delimiter=',', header='ppm,intensity', comments='')

if __name__ == '__main__':
    # # # # # Example usage
    filepath = 'test_data/data1.csv'
    main_peak_integral, main_peak_integral_uncertainty, second_peak_integral, second_peak_integral_uncertainty, report_dictionary = get_10ppm_peak_integration(
        filepath=filepath)
    make_diagnostic_plots(filepath, report_dictionary, save_fig_to_filepath='test_data/diagnostic_plot.png')
    plt.show()
