import numpy as np
from scipy.optimize import curve_fit
import pandas as pd
import matplotlib.pyplot as plt
import ace_tools_open as tools

df = pd.read_csv('intensity_array.csv')

# Filter the DataFrame so than the 'Shift (ppm)' is between 6.1 and 6.2
df = df[(df['Shift (ppm)'] >= 6.1) & (df['Shift (ppm)'] <= 6.2)]

# plot the data
# plt.figure(figsize=(10, 6))
# plt.plot(df['Shift (ppm)'], df['Intensity'], label='Data', color='blue')
# plt.title('NMR Spectrum')
# plt.xlabel('Shift (ppm)')
# plt.ylabel('Intensity')
# plt.legend()
# plt.grid(True)
# plt.tight_layout()
# # plt.show()
# Define the pseudo-Voigt function
def pseudo_voigt(x, A, x0, gamma1, gamma2, eta):
    """Single pseudo-Voigt peak"""
    lorentz = (gamma1**2) / ((x - x0)**2 + gamma1**2)
    gauss = np.exp(-np.log(2) * ((x - x0) / gamma2)**2)
    return A * (eta * lorentz + (1 - eta) * gauss)

# Sum of two pseudo-Voigt peaks
def double_pseudo_voigt(x, A1, x01, gamma11, gamma12, eta1, A2, x02, gamma21, gamma22, eta2):
    return (pseudo_voigt(x, A1, x01, gamma11, gamma12, eta1) +
            pseudo_voigt(x, A2, x02, gamma21, gamma22, eta2))

# Extract x and y data
x_data = df['Shift (ppm)'].values
y_data = df['Intensity'].values

# Initial guesses from observed peaks
initial_guess = [
    0.1, 6.145, 0.004, 0.004, 0.4,   # A1, x01, gamma1, eta1
    0.1, 6.157, 0.004, 0.004, 0.2   # A2, x02, gamma2, eta2
]

# Fit the model
popt, _ = curve_fit(double_pseudo_voigt, x_data, y_data, p0=initial_guess)

# Generate fitted curve
x_fit = np.linspace(x_data.min(), x_data.max(), 1000)
y_fit = double_pseudo_voigt(x_fit, *popt)

# Plot original data and fitted curve
plt.figure(figsize=(10, 6))
plt.plot(x_data, y_data, label='Data', color='blue')
plt.plot(x_fit, y_fit, label='Pseudo-Voigt Fit', color='red')
plt.title('Doublet Fit Using Sum of Pseudo-Voigt Functions')
plt.xlabel('Shift (ppm)')
plt.ylabel('Intensity')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# Prepare the fitted parameters for display
fit_params = pd.DataFrame({
    'Parameter': ['A1', 'x01', 'gamma11', 'gamma12', 'eta1', 'A2', 'x02', 'gamma21', 'gamma22', 'eta2'],
    'Value': popt
})

tools.display_dataframe_to_user(name="Fitted Pseudo-Voigt Parameters", dataframe=fit_params)
