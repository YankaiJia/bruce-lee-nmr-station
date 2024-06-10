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

def plot_yield_map(path):
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
def plot_kinetics_plot(folder):

    csv_folder = folder + '\\kinetics_data'
    csv_files = [f.path for f in os.scandir(csv_folder) if f.is_file() and f.path.endswith('.csv')]

    for num, csv_file in enumerate(csv_files):
        col_names = ['a', 'b', 'a2', 'ab', 'b2', 'a2b', 'ab2', 'a2b2']
        df = pd.read_csv(csv_file)
        # make 8 subplots for each species
        fig, axs = plt.subplots(1, 8, figsize=(20, 9))
        for index, col_name in enumerate(col_names):
            axs[index].plot(df[col_name])
            axs[index].set_title(col_name)
            axs[index].set_xlabel('t')

        a0 = df['a'][0]
        b0 = df['b'][0]
        product_final = df['a2b2'][len(df['a2b2']) - 1]
        # if a0 or bo is 0, then the yield is 0
        if np.isclose(a0, 0) or np.isclose(b0, 0):
            ab_yield = 0
        else:
            ab_yield = 2 * product_final / min(a0, b0)

        fig.suptitle(f'\n a0 = {round(a0,2)}, b0 = {round(b0,2)}, '
                     f'a2b2_final = {round(product_final,2)}, a2b2_yield = {round(ab_yield,2)} \n',
                     fontsize=20)

        # Save the plot
        png_file = csv_file.replace('.csv', '.png')
        plt.savefig(png_file, dpi= 100)
        print(f'num: {num} csv_file: {csv_file}')

if __name__ == "__main__":

    folder = "F:\\reaction_network_simulation_a2b2_1_0.1"

    # plot_yield_map(folder)

    # get all the subfolders int the folder
    subfolders = [f.path for f in os.scandir(folder) if f.is_dir()]

    for subfolder in subfolders:
        plot_kinetics_plot(subfolder)
    # plot_kinetics_plot(folder)






















