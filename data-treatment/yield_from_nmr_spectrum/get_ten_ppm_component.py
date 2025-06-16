import numpy as np
import matplotlib.pyplot as plt
import cmath
from scipy.optimize import curve_fit

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
                       vmax2, gamma2, amplitude2, sigmoid_width, sigmoid_amplitude, vertical_offset):
    # if x is a numpy array, apply the function element-wise
    flipping_factor = 1
    # vmax2 controls asymmetric skew of the x axis
    x_relative = x - center
    # multiply positive x_relative by vmax2, and negative by 1/vmax2
    x_relative = np.where(x_relative >= 0, x_relative * vmax2, x_relative / vmax2)
    res = amplitude * hardy_lorentz_z2_vectorized(flipping_factor*x_relative, vmax, gamma)
    gaussian = amplitude2 * np.exp(-(x_relative ** 2) / (2 * (gamma2 ** 2)))
    res += gaussian
    # addition of sigmoid background centered at center
    # sigmoid_background = sigmoid_amplitude / (1 + np.exp(-(x - center) / sigmoid_width))
    sigmoid_background = sigmoid_amplitude * 2/np.pi * np.arctan(np.pi/2*x_relative / sigmoid_width)
    res += sigmoid_background + vertical_offset
    return res


# model for the entire spectrum
def spectrum_function(x, center, splitting, deltappm, vmax, gamma, amplitude, vmax2, gamma2, amplitude2, sigmoid_width,
                       sigmoid_amplitude, vertical_offset, sidebands_intensity, second_peak_intensity):

    main_line = lineshape_function(x, center, vmax, gamma, amplitude, vmax2, gamma2, amplitude2, sigmoid_width, sigmoid_amplitude, vertical_offset)
    sidebands = (sidebands_intensity * lineshape_function(x, center - splitting, vmax, gamma, amplitude,
                                   vmax2, gamma2, amplitude2, sigmoid_width, sigmoid_amplitude, vertical_offset) +
                 sidebands_intensity * lineshape_function(x, center + splitting, vmax, gamma, amplitude,
                                    vmax2, gamma2, amplitude2, sigmoid_width, sigmoid_amplitude, vertical_offset))

    second_peak = second_peak_intensity * lineshape_function(x, center - deltappm, vmax, gamma, amplitude,
                                   vmax2, gamma2, amplitude2, sigmoid_width, sigmoid_amplitude, vertical_offset)

    return main_line + sidebands + second_peak

def get_10ppm_peak_integration(filepath, do_plot=False, instrumental_rms_error=0.0020):
    nmr_data = load_nmr_spectrum_from_csv(filepath)
    # crop the data between 9 and 11 ppm
    min_ppm = 9.25
    max_ppm = 11
    cropped_data = nmr_data[(nmr_data[:, 0] >= min_ppm) & (nmr_data[:, 0] <= max_ppm)]
    ppm_of_the_maximum = cropped_data[np.argmax(cropped_data[:, 1]), 0]
    height_of_the_maximum = np.max(cropped_data[:, 1])

    if do_plot:
        plot_nmr_spectrum(cropped_data, title='Cropped NMR Spectrum (9-11 ppm)')
        plt.show()

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
                           bounds=(lower_bounds, upper_bounds), verbose=2, jac='3-point', x_scale=x_scale,
                           gtol=1e-9)

    print("Fitted parameters:", popt)
    print(f'Length of popt: {len(popt)}')

    if do_plot:
        fitted_intensity = fit_lineshape(vs, *popt)
        plt.plot(vs, fitted_intensity, label='Fitted Lineshape Function', color='blue')
        plt.plot(cropped_data[:, 0], cropped_data[:, 1], 'o', color='black', alpha=0.5, markersize=1, label='Cropped Data')
        # reverse the x-axis for chemical shift
        plt.gca().invert_xaxis()
        plt.legend()
        plt.show()

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

    # xtol=1e-8, x_scale=x_scale, gtol=1e-9)

    print("Fitted parameters for the full spectrum:", popt)
    perr = np.sqrt(np.diag(pcov))
    print(f'Fitted second peak amplitude with error {popt[-1]} ± {perr[-1]/popt[-1]:.2%} %')

    if do_plot:
        # Plot the fitted spectrum function
        vs = np.linspace(min_ppm, max_ppm, 1000)
        fitted_spectrum = spectrum_function(vs, *popt)
        plt.plot(vs, fitted_spectrum, label='Fitted Spectrum Function', color='blue')
        plt.plot(cropped_data[:, 0], cropped_data[:, 1], 'o', color='black', alpha=0.5, markersize=1, label='Cropped Data')
        # reverse the x-axis for chemical shift
        plt.gca().invert_xaxis()
        plt.legend()
        plt.show()


    # get RMSD of the residual
    n_last_points = 30
    residuals = cropped_data[-n_last_points:, 1] - spectrum_function(cropped_data[-n_last_points:, 0], *popt)
    rms_error = np.std(residuals)
    print(f'RMS residual: {rms_error}')

if __name__ == '__main__':
    get_10ppm_peak_integration(filepath='test_data/data1.csv', do_plot=True)
