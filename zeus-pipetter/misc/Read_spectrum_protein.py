import glob
import pandas as pd
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')


# glob all the csv file pathes in a folder and store them in a list
csv_folder = 'D:\\Dropbox\\robochem\\data\\ELDK\\2023-01-15-run01\\nanodrop_spectra\\'
csv_file_list = glob.glob(csv_folder + '*.csv')
print(csv_file_list)

dfs = []
for csv_file in csv_file_list:
    df = pd.read_csv(csv_file)
    dfs.append(df)
for df in dfs:
    df.rename(columns={'Unnamed: 0': 'wavelength'}, inplace=True)
    df.set_index('wavelength', inplace=True)

def savgol(x, wl=9, p=5):
    return savgol_filter(x, window_length=wl, polyorder=p, mode = "interp")
# df['sav_gol'] = df['data'].apply(savgol)

# sort all the df in the dfs by the int value of the column names
for df in dfs:
    df.columns = df.columns.astype(int)
    df.sort_index(axis=1, inplace=True)
    # df = df[df.iloc[:, 0] > 300]


## plot in one fig the first five spectra for each df from the list dfs
colors = ['blue', 'pink', 'green', 'red', 'black']
titles = ["seq1-NES", "seq2-ENS", "seq3-NSE", "seq4-SNE", "seq5-ESN", "seq6-SEN"]
fig, axs = plt.subplots(2,3, figsize=(15,10))

line_name = {0:'15min', 1:'30min', 2:'45min', 3:'60min'}

for num, ax in enumerate():
        for index, df in enumerate(dfs):
            df = df.loc[290:]
            df_here = savgol_filter(df.iloc[:, 5*num:5*(num+1)].mean(axis=1), window_length=9, polyorder=5, mode = "interp")
            ax.plot(df.index, df_here, color=colors[index], alpha=1, label=line_name[index])
            # set labels
            ax.set_xlabel('Wavelength (nm)')
            ax.set_ylabel('Absorbance (AU)')
            ax.set_title(titles[num])
            ax.legend()
            #set limits
            ax.set_xlim(290, 500)
            ax.set_ylim(0.03, 0.17)
            plt.show()
        # plt.savefig('all_spectra.png')


fig1, axs1 = plt.subplots(2,3, figsize=(15,10))



