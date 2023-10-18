import numpy as np
import pandas as pd
import os, scipy.interpolate
import matplotlib.pyplot as plt


def get_conc_from_info(df_spectra, df_info):
    conc = []
    for i in df_spectra.columns:
        index_label = int(i)
        column_name = 'concentration'
        conc.append(df_info.loc[index_label, column_name])
    return conc



data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'+\
              'nanodrop-spectrometer-measurements\\versatility_test\\Claisen_WaiShing\\'

wavelength_start = 0
wavelength_end = 130

df_ani_and_ace = pd.read_csv(data_folder + '2023-10-11_19-50-36_UV-Vis_anisaldehyde.csv')
# select the wavelength range
df_ani_and_ace = df_ani_and_ace.loc[wavelength_start:wavelength_end,:]
# import df from txt file
df_ani_and_ace_info= pd.read_csv(data_folder + '2023-10-11_19-50-36_UV-Vis_anisaldehyde.txt', sep=',')
# make the first column as index
df_ani_and_ace_info.set_index(df_ani_and_ace_info.columns[0], inplace=True)

# set the first column as index
df_ani_and_ace.set_index(df_ani_and_ace.columns[0], inplace=True)
# set the index name to 'wavelength'
df_ani_and_ace.index.name = 'wavelength'
# remove the background
df_ani_and_ace_no_bkg = pd.DataFrame()
for i in list(df_ani_and_ace.columns):
    # print(i)
    if i != '15':
        df_ani_and_ace_no_bkg[i] = df_ani_and_ace[i] - df_ani_and_ace['15']
# get the ref spectrum  for each compound
df_ani = df_ani_and_ace_no_bkg[['5','6','7','8','9']].copy()
list_ani_conc = get_conc_from_info(df_ani,df_ani_and_ace_info)

df_ace = df_ani_and_ace_no_bkg[['10','11','12','13','14']].copy()
list_ani_conc = get_conc_from_info(df_ace,df_ani_and_ace_info)


df_methoxy_original = pd.read_csv(data_folder + '2023-10-11_16-26-58_UV-Vis_methoxychalcone.csv')
df_methoxy_original = df_methoxy_original.loc[wavelength_start:wavelength_end,:]

df_methoxy_original_info = pd.read_csv(data_folder + '2023-10-11_16-26-58_UV-Vis_methoxychalcone.txt', sep=',')
# set the first column as index
df_methoxy_original.set_index(df_methoxy_original.columns[0], inplace=True)
# set the index name to 'wavelength'
df_methoxy_original.index.name = 'wavelength'
# remove the background
df_methoxy_no_bkg = pd.DataFrame()
for i in list(df_methoxy_original.columns):
    # print(i)
    if i != '4':
        df_methoxy_no_bkg[i] = df_methoxy_original[i] - df_methoxy_original['4']

df_methoxy = df_methoxy_no_bkg
list_methoxy_conc = get_conc_from_info(df_methoxy,df_methoxy_original_info)


# the three reference spectra are: df_ani, df_ace, df_methoxy

intp_ani = scipy.interpolate.interp1d(list_ani_conc, df_ani, bounds_error=False, fill_value="extrapolate")
intp_ace = scipy.interpolate.interp1d(list_ani_conc, df_ace, bounds_error=False, fill_value="extrapolate")
intp_methoxy = scipy.interpolate.interp1d(list_methoxy_conc, df_methoxy, bounds_error=False, fill_value="extrapolate")

ref_ani = intp_ani(0.00015)
ref_ace = intp_ace(0.00015)
ref_methoxy = intp_methoxy(0.00015)

# plot df_ani, df_ace, df_methoxy
plt.figure()
plt.plot(df_ani.index, df_ani, label='Anisaldehyde')
plt.plot(df_ace.index, df_ace, label='Acetophenone')
plt.plot(df_methoxy.index, df_methoxy, label='Methoxychalcone')
plt.xlabel('Wavelength (nm)')
plt.ylabel('Absorbance')

# plot ref_ani, ref_ace, ref_methoxy
plt.plot(df_ani.index,ref_ani, label='Anisaldehyde at 0.00015 M')
plt.plot(df_ace.index,ref_ace, label='Acetophenone at 0.00015 M')
plt.plot(df_methoxy.index, ref_methoxy, label='Methoxychalcone at 0.00015 M')
plt.xlabel('Wavelength (nm)')
plt.ylabel('Absorbance')
plt.legend()
# plt.show()

df_crude = pd.read_csv(data_folder + '2023-10-12_14-51-59_UV-Vis_crude.csv')
# set the first column as index
df_crude.set_index(df_crude.columns[0], inplace=True)

df_crude0 = df_crude.loc[220:350,'0']
df_crude1 = df_crude.loc[220:350,'1']

from sklearn.linear_model import LinearRegression
concentration = []
model = LinearRegression(fit_intercept=False, positive=True)

ref = pd.DataFrame([ref_methoxy,ref_ani,ref_ace])
ref = ref.T

model.fit(ref, df_crude1)

a = model.coef_
print(a)

