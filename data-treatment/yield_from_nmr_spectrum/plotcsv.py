"""
x	y
-2.965308524	154.6875
-2.964996	157.4737244
-2.964683476	176.0453491
-2.964370953	205.0615082
-2.964058429	231.6642914
-2.963745905	241.1613617
-2.963433381	225.7540741
-2.963120858	189.363678
-2.962808334	145.2499847
-2.96249581	109.6538696
-2.962183286	94.35472107
-2.961870763	101.1089554
-2.961558239	121.4014359
-2.961245715	142.9307861
-2.960933191	156.3302002
-2.960620667	160.1993408

"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def plot_csv(file_path):
    """
    Reads a CSV file and plots the data using seaborn.

    Parameters:
    file_path (str): The path to the CSV file.
    """
    # Read the CSV file
    df = pd.read_csv(file_path)

    # Set the style for seaborn
    sns.set_style("whitegrid")

    # Create a line plot
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df, x='x', y='y')

    # Set the title and labels
    plt.title('NMR Spectrum Data')
    plt.xlabel('Chemical Shift (ppm)')
    plt.ylabel('Intensity')

    # Show the plot
    plt.show()

file_path = r"D:\Dropbox\brucelee\data\IDO_ring_opening\NMR_spectra\run01-12_06_2025\plate_95_3OMe_32_testing\1\data.csv"
plot_csv(file_path)