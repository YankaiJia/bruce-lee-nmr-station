import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def lorentzian(x, amp, cen, wid):
    # Define a Lorentzian function
    return (1 / np.pi) * (amp / ((x - cen) ** 2 + wid ** 2))


def sum_of_lorentzian(x, *params):
    # Define a sum of Gaussians
    num_peaks = len(params) // 3
    y = np.zeros_like(x)

    for i in range(num_peaks):
        amp = params[i * 3]
        cen = params[i * 3 + 1]
        wid = params[i * 3 + 2]
        y += lorentzian(x, amp, cen, wid)

    return y

x_vals = np.linspace(-20, 20, 500)
y_vals = sum_of_lorentzian(x_vals, 1.0, 0.0, 1.0, 0.5, 6.0, 0.8,0.9, 12, 0.5)
# plot the result
plt.plot(x_vals, y_vals, label='Sum of Lorentzians')

ydata = y_vals + 0.01 * np.random.normal(size=x_vals.size)  # Adding some noise

plt.plot(x_vals, ydata, 'b-', label='Noisy data')
# plt.show()

# find peak for ydata
from scipy.signal import find_peaks
peaks, _ = find_peaks(ydata, width=5, height=0.2)
print("Peaks found at:", peaks)

initial_guesses = []
for peak in peaks:
    amp_guess = ydata[peak]  # Peak height
    cen_guess = x_vals[peak]  # Peak center
    wid_guess = 5  # Initial width guess (adjust as needed)
    initial_guesses.extend([amp_guess, cen_guess, wid_guess])

print("Initial guesses for parameters:", initial_guesses)

popt, pcov = curve_fit(sum_of_lorentzian, x_vals, ydata, p0=initial_guesses)
print("Optimal parameters:", popt)

plt.plot(x_vals, sum_of_lorentzian(x_vals, *popt), 'r-',)

plt.show()