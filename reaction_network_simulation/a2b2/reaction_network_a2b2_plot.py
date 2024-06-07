import concurrent.futures
import itertools
import os
import random

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd


matplotlib.use('Agg')
import plotly.graph_objects as go
import seaborn as sns


def treat_csv_files_in_one_folder(csvs):

    for csv in csvs:

        df = pd.read_csv(csv)
        X = df['a_init']
        Y = df['b_init']
        Z = df['a2b2_yield']

        # generate 2 2d grids for the x & y bounds
        x, y = np.meshgrid(X, Y)





        # use pcolormesh to plot the heatmap
        fig, ax = plt.subplots()
        c = ax.pcolormesh(x, y, Z)
        ax.set_xlabel('A0')
        ax.set_ylabel('B0')
        fig.colorbar(c, ax=ax)
        plt.savefig(csv.replace('.csv', '.png'))

        plt.show()

if __name__ == "__main__":

    folder = "F:\\reaction_network_simulation_a2b2_1_0.1"

    ## list all the subfolder in the folder
    subfolders = [f.path for f in os.scandir(folder) if f.is_dir()]

    ## get all the csv files in the subfolders without going into the subfolders
    for index, subfolder in enumerate(subfolders):

        print(f"Index: {index} Subfolder: {subfolder}")

        # if there are png files in the subfolder, delete them
        png_here = [f.path for f in os.scandir(subfolder) if f.is_file() and f.path.endswith('.png')]
        for png in png_here:
            os.remove(png)

        csv_here = [f.path for f in os.scandir(subfolder) if f.is_file() and f.path.endswith('.csv')]

        for csv in csv_here:
            # Check if the CSV file exists
            if not os.path.exists(csv):
                print(f"File {csv} does not exist.")
                continue

            df = pd.read_csv(csv)

            X = df['a_init']
            Y = df['b_init']
            Z = df['a2b2_yield']

            # reshape X, Y, Z to 50 * 50 matrix
            X = X.values.reshape(50, 50)
            Y = Y.values.reshape(50, 50)
            Z = Z.values.reshape(50, 50)

            # Plot the heatmap
            fig, ax = plt.subplots()
            c = ax.pcolormesh(X, Y, Z)
            ax.set_xlabel('A0')
            ax.set_ylabel('B0')
            fig.colorbar(c, ax=ax)

            # Save the plot and check if the file is created
            png_file = csv.replace('.csv', '.png')
            plt.savefig(png_file)






















