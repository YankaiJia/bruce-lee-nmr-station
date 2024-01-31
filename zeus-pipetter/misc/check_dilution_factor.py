import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')

# read a csv into a df
csv_71 ='D:\\Dropbox\\robochem\\data\\BPRF\\2024-01-08-run01\\nanodrop_spectra\\2024-01-10_12-51-07_UV-Vis_plate_71.csv'
csv_73 ='D:\\Dropbox\\robochem\\data\\BPRF\\2024-01-08-run01\\nanodrop_spectra\\2024-01-10_13-48-13_UV-Vis_plate_73.csv'
df_71 = pd.read_csv(csv_71)
df_73 = pd.read_csv(csv_73)

df_71.rename(columns={'Unnamed: 0': 'wavelength'}, inplace=True)
df_71.set_index('wavelength', inplace=True)
df_73.rename(columns={'Unnamed: 0': 'wavelength'}, inplace=True)
df_73.set_index('wavelength', inplace=True)

dil_1 = 21.67,
dil_2 = 213.92
dil_1, dil_2 = 45, 200
# plot df_71_v0 data against wavelength
fig, ax = plt.subplots()
ax.plot(df_71.index, df_71.iloc[:, 6]*dil_1, label='71')
ax.plot(df_73.index, df_73.iloc[:, 6]*dil_2, label='73')
ax.set_xlabel('Wavelength (nm)')
ax.set_ylabel('Absorbance (AU)')
ax.legend()
plt.show()


