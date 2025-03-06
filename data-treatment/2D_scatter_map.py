import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Load data from file
file_path = 'C:/Users/shing/Dropbox/robochem/data/DPE_bromination/2025-01-23-run01/Results/Plot_TBABr_125mM.csv'  # Replace with your file's path
# file_path = 'C:/Users/shing/Dropbox/robochem/data/DPE_bromination/2025-01-17-run01/results/mole_fraction_of_B_equiv.csv'  # Replace with your file's path
# file_path = 'C:/Users/shing/Dropbox/robochem/data/DPE_bromination/2025-01-17-run01/mole_fraction_of_B.csv'  # Replace with your file's path
# file_path = 'C:/Users/shing/Dropbox/robochem/data/DPE_bromination/2025-01-17-run01/mole_fraction_of_C.csv'  # Replace with your file's path
data = pd.read_csv(file_path)

# Extract columns
a = data['[Br2]0 (mM)']  # Column for variable a
b = data['[DPE]0 (mM)']  # Column for variable b
X = data['Selectivity of B']  # Column for color-coded variable X

# Define axis labels as variables
x_label = '[S]$_0$ (mM)'  # X-axis label
y_label = '[Br$_2$]$_0$ (mM)'  # Y-axis label with LaTeX formatting
# y_label = 'Equiv. of Br$_2$'  # Y-axis label with LaTeX formatting
colorbar_label = 'Selectivity of B'

# Scatter plot
plt.figure(figsize=(6, 5))
scatter = plt.scatter(b, a, c=X, cmap='viridis', s=100, edgecolor='k', vmin=0.5, vmax=1)
plt.colorbar(scatter, label=colorbar_label)
plt.xlabel(x_label, fontsize=14)
plt.ylabel(y_label, fontsize=14)
# plt.title(r'Scatter plot of [B]$_{\text{f}}$ / ([A]$_{\text{f}}$ + [B]$_{\text{f}}$ + [C]$_{\text{f}}$)', fontsize=14)
plt.title(r'Selectivity of B when [TBABr]0 = 125 mM', fontsize=14)

# Set minimum and maximum values for axes
plt.xlim(50, 200)  # Set x-axis limits (min=0, max=50)
plt.ylim(50, 200)  # Set y-axis limits (min=-10, max=100)

# Set custom tick intervals
x_interval = 50  # Set desired interval for x-axis
y_interval = 50  # Set desired interval for y-axis

# Apply intervals to the axes
ax = plt.gca()  # Get current axes
ax.xaxis.set_major_locator(ticker.MultipleLocator(x_interval))
ax.yaxis.set_major_locator(ticker.MultipleLocator(y_interval))
ax.xaxis.set_minor_locator(ticker.MultipleLocator(x_interval/2))
ax.yaxis.set_minor_locator(ticker.MultipleLocator(y_interval/2))

plt.show()