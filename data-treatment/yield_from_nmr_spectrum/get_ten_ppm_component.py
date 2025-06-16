import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import cmath
from scipy.optimize import curve_fit
from scipy.integrate import quad
from scipy.signal import savgol_filter

def load_nmr_spectrum_from_csv(filepath):
    data = np.loadtxt(filepath, delimiter=',', skiprows=1)
    data[:, 1] = data[::-1, 1]  # Reverse the y-axis data
    return data

def plot_nmr_spectrum(data, title='NMR Spectrum', xlabel='Chemical Shift (ppm)', ylabel='Intensity'):
    plt.plot(data[:, 0], data[:, 1] - np.min(data[:, 1]), 'o', color='black', alpha=0.5, markersize=1)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    # make log scale for y-axis
    plt.yscale('log')
    plt.grid()
    plt.gca().invert_xaxis()  # Invert x-axis for chemical shift

# Edme Hardy lineshape function from Chapter 7 of the book "NMR Methods for the Investigation of Structure and Transport"
def hardy_lorentz_z2(v, vmax, gamma):
    S = 1/(2j * np.pi * cmath.sqrt(vmax)) * (
            cmath.atan(cmath.sqrt(vmax/(-1 * v - gamma * 1j)))/cmath.sqrt(-1 * v - gamma * 1j) -
            cmath.atan(cmath.sqrt(vmax/(-1* v + gamma * 1j)))/cmath.sqrt(-1 * v + gamma * 1j))
    return S.real

hardy_lorentz_z2_vectorized = np.vectorize(hardy_lorentz_z2)

def lineshape_function(x, center, vmax, gamma, amplitude,
                       asymmetry_factor, gaussian_sigma, gaussian_amplitude, sigmoid_width, sigmoid_amplitude, vertical_offset):
    # if x is a numpy array, apply the function element-wise
    flipping_factor = 1
    # asymmetry_factor controls asymmetric skew of the x axis
    x_relative = x - center
    # multiply positive x_relative by asymmetry_factor, and negative by 1/asymmetry_factor
    x_relative = np.where(x_relative >= 0, x_relative * asymmetry_factor, x_relative / asymmetry_factor)
    res = amplitude * hardy_lorentz_z2_vectorized(flipping_factor*x_relative, vmax, gamma)
    gaussian = gaussian_amplitude * np.exp(-(x_relative ** 2) / (2 * (gaussian_sigma ** 2)))
    res += gaussian
    # addition of sigmoid background centered at center
    # sigmoid_background = sigmoid_amplitude / (1 + np.exp(-(x - center) / sigmoid_width))
    sigmoid_background = sigmoid_amplitude * 2/np.pi * np.arctan(np.pi/2*x_relative / sigmoid_width)
    res += sigmoid_background + vertical_offset
    return res


# model for the entire spectrum
def spectrum_function(x, center, splitting, deltappm, vmax, gamma, amplitude, asymmetry_factor, gaussian_sigma, gaussian_amplitude, sigmoid_width,
                       sigmoid_amplitude, vertical_offset, sidebands_intensity, second_peak_intensity):

    main_line = lineshape_function(x, center, vmax, gamma, amplitude, asymmetry_factor, gaussian_sigma, gaussian_amplitude, sigmoid_width, sigmoid_amplitude, vertical_offset)
    sidebands = (sidebands_intensity * lineshape_function(x, center - splitting, vmax, gamma, amplitude,
                                   asymmetry_factor, gaussian_sigma, gaussian_amplitude, sigmoid_width, sigmoid_amplitude, vertical_offset) +
                 sidebands_intensity * lineshape_function(x, center + splitting, vmax, gamma, amplitude,
                                    asymmetry_factor, gaussian_sigma, gaussian_amplitude, sigmoid_width, sigmoid_amplitude, vertical_offset))

    second_peak = second_peak_intensity * lineshape_function(x, center - deltappm, vmax, gamma, amplitude,
                                   asymmetry_factor, gaussian_sigma, gaussian_amplitude, sigmoid_width, sigmoid_amplitude, vertical_offset)

    return main_line + sidebands + second_peak

def get_10ppm_peak_integration(filepath, instrumental_rms_error=0.0020, verbose=2):
    nmr_data = load_nmr_spectrum_from_csv(filepath)
    # crop the data between 9 and 11 ppm
    min_ppm = 9.25
    max_ppm = 11
    cropped_data = nmr_data[(nmr_data[:, 0] >= min_ppm) & (nmr_data[:, 0] <= max_ppm)]
    ppm_of_the_maximum = cropped_data[np.argmax(cropped_data[:, 1]), 0]
    height_of_the_maximum = np.max(cropped_data[:, 1])

    min_ppm = ppm_of_the_maximum - (9.96666016 - 9.6)
    max_ppm = ppm_of_the_maximum + (9.96666016 - 9.6)

    cropped_data = nmr_data[(nmr_data[:, 0] >= min_ppm) & (nmr_data[:, 0] <= max_ppm)]

    # # Example of using the lineshape function
    vs = np.linspace(min_ppm, max_ppm, 1000)
    center = ppm_of_the_maximum

    fit_lineshape = lineshape_function

    lower_bounds = [min_ppm, 0, 0, 0, 0, 0, 0, 0.0001, 0, -0.014]
    upper_bounds = [max_ppm, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, 0.3, 0.01, 0.014]

    p0 = [center, 5.68877297e-26, 9.64055154e-03, 3.63118454e-02/2.2*height_of_the_maximum,
          9.36311714e-01, 5.10908742e-03, 9.06158610e-01/2.2*height_of_the_maximum,
          1.93666225e-03, 2.44896635e-03, -1.30129103e-03]

    x_scale = p0[:]
    x_scale[0] = 0.05  # Set the center to the maximum ppm value
    x_scale = np.abs(np.array(x_scale))

    popt, pcov = curve_fit(fit_lineshape, cropped_data[:, 0], cropped_data[:, 1],
                           p0=p0,
                           bounds=(lower_bounds, upper_bounds), verbose=verbose, jac='3-point', x_scale=x_scale,
                           gtol=1e-9)

    if verbose == 2:
        print("Fitted parameters:", popt)
        print(f'Length of popt: {len(popt)}')

    # ## PLOT FOR DEBUGGING ONLY
    # fitted_intensity = fit_lineshape(vs, *popt)
    # plt.plot(vs, fitted_intensity, label='Fitted Lineshape Function', color='blue')
    # plt.plot(cropped_data[:, 0], cropped_data[:, 1], 'o', color='black', alpha=0.5, markersize=1, label='Cropped Data')
    # # reverse the x-axis for chemical shift
    # plt.gca().invert_xaxis()
    # plt.legend()
    # plt.show()

    splitting_p0 = 1.48721827e-01
    delta_ppm_p0 = 1.42794971e-01

    min_ppm = ppm_of_the_maximum - (9.96666016 - 9.6)
    max_ppm = ppm_of_the_maximum + (9.96666016 - 9.6)
    cropped_data = nmr_data[(nmr_data[:, 0] >= min_ppm) & (nmr_data[:, 0] <= max_ppm)]

    lower_bounds = [min_ppm, 0.7*splitting_p0, 0.7*delta_ppm_p0, 0, 0, 0, 0, 0, 0, 0.0001, 0, -0.014, 0, 0]
    upper_bounds = [max_ppm, 1.3*splitting_p0, 1.3*delta_ppm_p0, np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, 0.3, 0.01, 0.014, np.inf, np.inf]

    # inherit the p0 from the popt
    # from the previous fit
    # to use as initial guess for the full spectrum fit
    # but modify the splitting and deltappm parameters
    # to be more flexible
    # and allow for sidebands and second peak intensity
    p0 = [popt[0]] + [splitting_p0, delta_ppm_p0] + list(popt[1:]) + [0.01, 0.01]
    x_scale = p0[:]
    x_scale[0] = 0.05  # Set the center to the maximum ppm value
    x_scale = np.abs(np.array(x_scale))

    popt, pcov = curve_fit(spectrum_function, cropped_data[:, 0], cropped_data[:, 1],
                            p0=p0,
                            bounds=(lower_bounds, upper_bounds), verbose=2, jac='3-point',
                            maxfev=10000, method='trf', x_scale=x_scale,
                            sigma=instrumental_rms_error*np.ones_like(cropped_data[:, 0]),
                            absolute_sigma=True, ftol=1e-11, xtol=1e-9)

    perr = np.sqrt(np.diag(pcov))
    if verbose == 2:
        print("Fitted parameters for the full spectrum:", popt)
        print(f'Fitted second peak amplitude with error {popt[-1]} ± {perr[-1]/popt[-1]:.2%} %')

    # get RMSD of the residual
    n_last_points = 30
    residuals = cropped_data[-n_last_points:, 1] - spectrum_function(cropped_data[-n_last_points:, 0], *popt)
    rms_error = np.std(residuals)
    if verbose == 2:
        print(f'RMS residual: {rms_error}')

    # make a pure spectrum of the second peak, without the background sigmoid ahd vertical shift
    # Optimal parameters are:
    center, splitting, deltappm, vmax, gamma, amplitude, asymmetry_factor, gaussian_sigma, gaussian_amplitude, sigmoid_width, sigmoid_amplitude, vertical_offset, sidebands_intensity, second_peak_intensity = popt
    second_peak_intensity_uncertainty = perr[-1]

    second_peak_partial = lambda x: second_peak_intensity * lineshape_function(x, center - deltappm, vmax, gamma, amplitude,
                                                             asymmetry_factor, gaussian_sigma, gaussian_amplitude, sigmoid_width,
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
        print(f'Second peak integral: ({second_peak_integral} ± {second_peak_integral_uncertainty} ) [ppm * intensity_unit]')

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
        'second_peak_intensity_uncertainty' : second_peak_intensity_uncertainty,
        'second_peak_integral': second_peak_integral,
        'second_peak_integral_uncertainty': second_peak_integral_uncertainty,
        'optimized_parameters': popt,
        'optimized_parameters_errors': perr,
        'residuals_rms': rms_error,
    }

    return second_peak_integral, second_peak_integral_uncertainty, dictionary_to_return

def simpleaxis(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()

def make_diagnostic_plots(filepath, report_dictionary, save_fig_to_filepath=None,
                          figsize=(12, 10), min_ppm = 9.25, max_ppm = 11, do_show=True, custom_title=None):
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
    ax.plot(cropped_data[:, 0], cropped_data[:, 1] - np.min(cropped_data[:, 1]), 'o', color='black', alpha=0.3, markersize=1)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_yscale('log')
    ax.invert_xaxis()  # Invert x-axis for chemical shift
    simpleaxis(ax)

    # Plot the fitted spectrum function
    ax = axs[1, 0]
    vs = np.linspace(min_ppm, max_ppm, 1000)
    popt = report_dictionary['optimized_parameters']
    fitted_spectrum = spectrum_function(vs, *popt)
    ax.plot(vs, fitted_spectrum, label='Fitted model', color='C0')
    ax.plot(cropped_data[:, 0], cropped_data[:, 1], 'o', color='black', alpha=0.5, markersize=1, label='Data')
    # reverse the x-axis for chemical shift
    ax.set_title('Comparison of fit and data')
    ax.set_xlim(report_dictionary['center'] - report_dictionary['deltappm']*2,
                  report_dictionary['center'] + report_dictionary['deltappm']*2)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.invert_xaxis()  # Invert x-axis for chemical shift
    ax.legend()
    simpleaxis(ax)

    # Plot the fitted spectrum function, zoomed
    ax = axs[0, 1]
    vs = np.linspace(min_ppm, max_ppm, 1000)
    popt = report_dictionary['optimized_parameters']
    fitted_spectrum = spectrum_function(vs, *popt)
    ax.plot(vs, fitted_spectrum, color='C0')
    ax.plot(cropped_data[:, 0], cropped_data[:, 1], 'o', color='black', alpha=0.5, markersize=1)
    # reverse the x-axis for chemical shift
    ax.set_title('Comparison of fit and data, zoomed')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xlim(report_dictionary['center'] - report_dictionary['deltappm']*1.3,
                  report_dictionary['center'] + report_dictionary['deltappm']*1.3)

    # make log scale for y-axis
    ax.invert_xaxis()  # Invert x-axis for chemical shift

    # fill between the fitted spectrum minus pure spectrum of the second peak
    (center, splitting, deltappm, vmax, gamma, amplitude, asymmetry_factor, gaussian_sigma, gaussian_amplitude,
     sigmoid_width, sigmoid_amplitude, vertical_offset, sidebands_intensity, second_peak_intensity) = popt
    pure_spectrum_of_second_peak = second_peak_intensity * lineshape_function(vs, center - deltappm, vmax, gamma, amplitude,
                                                             asymmetry_factor, gaussian_sigma, gaussian_amplitude, sigmoid_width,
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
    ax_residuals.plot(cropped_data[:, 0], residuals, 'o', color='black', alpha=0.5, markersize=2, label=f'Raw (rms={report_dictionary["residuals_rms"]:.5f})')
    ax_residuals.axhline(0, color='red', linestyle='--', linewidth=1, label='Zero Line')
    # plot the savgol smoothed residuals with window 15
    smoothed_residuals = savgol_filter(residuals, window_length=15, polyorder=2)
    ax_residuals.plot(cropped_data[:, 0], smoothed_residuals, alpha=0.5, color='C2', label='Smoothed')
    ax_residuals.set_title('Residuals')
    ax_residuals.set_xlabel('Chemical Shift (ppm)')
    ax_residuals.set_ylabel('Residual Intensity')
    ax_residuals.legend()
    ax_residuals.set_xlim(report_dictionary['center'] - report_dictionary['deltappm']*2,
                  report_dictionary['center'] + report_dictionary['deltappm']*2)
    ax_residuals.invert_xaxis()  # Invert x-axis for chemical shift
    simpleaxis(ax_residuals)

    # add a vertical histogram of the residuals distribution on the right side of the residuals plot
    ax_hist = ax5
    ax_hist.hist(residuals, bins=30, orientation='horizontal', color='gray', alpha=0.4)
    ax_hist.set_xlabel('')
    ax_hist.set_yticks([])
    ax_hist.set_xticks([])
    simpleaxis(ax_hist)
    ax_hist.spines['bottom'].set_visible(False)

    if custom_title is not None:
        fig.suptitle(custom_title, fontsize=16)

    plt.tight_layout()

    if save_fig_to_filepath is not None:
        plt.savefig(save_fig_to_filepath, dpi=300, bbox_inches='tight')

    if do_show:
        plt.show()
    else: # clear figure and delete it
        plt.clf()
        plt.close(fig)


if __name__ == '__main__':
    filepath = 'test_data/data.csv'
    second_peak_integral, second_peak_integral_uncertainty, report_dictionary = get_10ppm_peak_integration(filepath=filepath)
    make_diagnostic_plots(filepath, report_dictionary, save_fig_to_filepath='test_data/diagnostic_plot.png')
    plt.show()
