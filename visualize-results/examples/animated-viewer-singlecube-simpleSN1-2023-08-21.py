import importlib
import os
import numpy as np
from matplotlib import pyplot as plt
from scipy.optimize import curve_fit

organize_run_results = importlib.import_module("misc-scripts.organize_run_results")
avs = importlib.import_module("visualize-results.animated_viewer_static")
data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'

experiment_name = 'simple-reactions/2023-08-21-run01/'
list_of_runs = tuple([
    '2023-08-21-run01',
    '2023-08-22-run01',
    '2023-08-22-run02',
    '2023-08-28-run01',
    '2023-08-29-run01',
    '2023-08-29-run02'])
# column_to_plot = 'HBr_relative_change'
column_to_plot = 'conversion'

substances = ['c#SN1OH03', 'c#HBr', 'temperature']
substance_titles = ['Alcohol', 'HBr', 'Temperature']
substrates = ['c#SN1OH03', 'c#HBr']

df_results = organize_run_results.join_data_from_runs([f'simple-reactions/{x}/' for x in list_of_runs],
                                 round_on_columns=substances)

for i, row in df_results.iterrows():
    df_results.loc[i, 'c#H2O'] = row['c#HBr'] / 4.5 * 21.88934517
    df_results.loc[i, 'c#acetic_acid'] = row['c#HBr'] / 4.5 * 8.583416744
    df_results.loc[i, 'product_sum'] = row['pc#SN1OH03'] + row['pc#SN1Br03']

# fig1 = plt.figure(1)
# plt.scatter(df_results['c#SN1OH03'], df_results['product_sum'], alpha=0.1)
# # plot x=y line
# plt.plot([0, 0.5], [0, 0.5], '--', color='C1')
# plt.xlabel('Alcohol before reaction, M')
# plt.ylabel('Sum of product and remaining alcohol, M')
#
# fig2 = plt.figure(2)
# plt.scatter(df_results['c#SN1OH03'], df_results['pc#SN1Br03'], alpha=0.1)
# plt.xlabel('Alcohol before reaction, M')
# plt.ylabel('Bromide product, M')
# plt.plot([0, 0.5], [0, 0.5], '--', color='C1')
#
# fig3 = plt.figure(3)
# plt.scatter(df_results['c#SN1OH03'], df_results['pc#SN1OH03'], alpha=0.1)
# plt.xlabel('Alcohol before reaction, M')
# plt.ylabel('Alcohol after reaction, M')
# plt.plot([0, 0.5], [0, 0.5], '--', color='C1')
#
# fig4 = plt.figure(4)
# plt.scatter(df_results['c#HBr'], df_results['c#SN1OH03'] - df_results['pc#SN1OH03'], alpha=0.1)
# plt.xlabel('HBr before reaction, M')
# plt.ylabel('Converted alcohol after reaction, M')
# plt.plot([0, 0.5], [0, 0.5], '--', color='C1')
#
# plt.show()
#
# Compute equilibrium constant
for i, row in df_results.iterrows():
    # concentration of product
    C_RBr = row['pc#SN1Br03']/(row['pc#SN1OH03'] + row['pc#SN1Br03']) * row['c#SN1OH03']
    # concentration of water at the end of reaction
    C_H2O = row['c#H2O'] + C_RBr
    # concentration of protons at the end of reaction
    C_H_plus = row['c#HBr'] - C_RBr + row['c#acetic_acid']
    # concentration of bromide ions at the end of reaction
    C_Br_minus = row['c#HBr'] - C_RBr
    # equilibrium constant
    remaining_alcohol = row['pc#SN1OH03']/(row['pc#SN1OH03'] + row['pc#SN1Br03']) * row['c#SN1OH03']
    K_eq = (C_H_plus * C_Br_minus * remaining_alcohol) / (C_RBr * C_H2O)
    # K_eq = (C_Br_minus * remaining_alcohol) / (C_RBr * C_H2O)
    df_results.loc[i, 'K_eq'] = K_eq

column_to_plot = 'K_eq'

def smooth_across_HBr_concentrations(x, y, fraction_of_outliers=0.15, do_plot=True):

    def custom_fit_func(x, a, b, c, d):
        return a + b * np.exp(-1*c*x) + d*x

    def produce_fit(x, y):
        popt, pcov = curve_fit(custom_fit_func, x, y, p0=[1, -1, 4, 0], maxfev=100000)
        best_f = lambda x: custom_fit_func(x, *popt)
        return best_f

    # def produce_fit(x, y):
        ### Polynomial fit version
        # z = np.polyfit(x, y, 4)
        # f = np.poly1d(z)
        # return f

    x = np.array(x)
    y = np.array(y)
    if do_plot:
        plt.scatter(x, y)
    f = produce_fit(x, y)
    if do_plot:
        plt.plot(np.sort(x), f(np.sort(x)), '--', color='C1')
    # remove the 10% of the points furthest from the fit
    diff = np.abs(f(x) - y)
    indices_to_keep = np.argsort(diff)[:-int(len(diff) * fraction_of_outliers)]
    # if point with lowest x is not in the rows_having_this_alcohol_and_temperature to keep, add it
    if np.argmin(x) not in indices_to_keep:
        indices_to_keep = np.append(indices_to_keep, np.argmin(x))
    x2 = x[indices_to_keep]
    y2 = y[indices_to_keep]
    if do_plot:
        plt.scatter(x2, y2, color='C2', marker='x')
    # fit polynomial again
    f = produce_fit(x2, y2)
    if do_plot:
        plt.plot(np.sort(x), f(np.sort(x)), color='C1')
        # plt.ylim(0, 1)
        plt.show()
    return f(x)

# filtering
df_results.drop(df_results[df_results['c#HBr'] < 0.065].index, inplace=True)
df_results.drop(df_results[df_results['yield'] > 0.96].index, inplace=True)
df_results.drop(df_results[df_results['is_outlier'] == 1].index, inplace=True)
df_results.dropna(subset=[column_to_plot], inplace=True)
df_results = df_results[~df_results[column_to_plot].isin([np.inf, -np.inf])]
df_results[column_to_plot] = df_results[column_to_plot].apply(lambda x: x if x > 1e-10 else 0)
df_results[column_to_plot] = df_results[column_to_plot].apply(lambda x: x if x <= 100 else 100)

# round concentrations "c#SN1OH03" and "c#HBr" to 6 decimal places
df_results['c#SN1OH03'] = df_results['c#SN1OH03'].round(6)
df_results['c#HBr'] = df_results['c#HBr'].round(6)

# iterate over unique values of "c#SN1OH03" and "temperature" and smooth the data across the 'c#HBr' values
for alcohol_concentration in df_results['c#SN1OH03'].unique():
    for temperature in df_results['temperature'].unique():
        print(f'c#SN1OH03 = {alcohol_concentration}, temperature = {temperature}')
        rows_having_this_alcohol_and_temperature = (df_results['c#SN1OH03'] == alcohol_concentration) & \
                                                   (df_results['temperature'] == temperature)
        df_results.loc[rows_having_this_alcohol_and_temperature, column_to_plot] = \
            smooth_across_HBr_concentrations(df_results.loc[rows_having_this_alcohol_and_temperature, 'c#HBr'],
                                             df_results.loc[rows_having_this_alcohol_and_temperature, column_to_plot]
                                             )

# convert from mol/L to mM
for substrate in substrates:
    df_results[substrate] = df_results[substrate].apply(lambda x: x*1000 if x>1e-10 else 0)

xs = df_results[substrates[0]].to_numpy()
ys = df_results[substrates[1]].to_numpy()
zs = df_results['temperature'].to_numpy()
yields = df_results[column_to_plot].to_numpy()

print(f'Min concentrations of substrates: {[np.min(x) for x in [xs, ys, zs]]}')
print(f'Max concentrations of substrates: {[np.max(x) for x in [xs, ys, zs]]}')
print(f'Yields - min: {min(yields)}, max: {max(yields)}')

avs.plot_3d_dataset_as_cube(xs, ys, zs, yields,
                            substance_titles=('Alcohol,\nmM', 'HBr,\nmM', 'Temperature,\n°C'),
                            colorbar_title=column_to_plot,
                            npoints=50, sparse_npoints=7, rbf_epsilon=1,
                            rbf_smooth=0.05,
                            interpolator_choice='linear',
                            data_for_spheres='raw',
                            rbf_function='multiquadric',
                            axes_ticks_format='%.0f',
                            axes_font_factor=1.3,
                            contours=[0.2, 0.4, 0.55, 0.7, 0.85])





# df_results.loc[df_results['yield#SN1Br01s1'] < 0, 'yield#SN1Br01s1'] = 0
# df_results.loc[df_results['yield#SN1Br01s1'] > 1, 'yield#SN1Br01s1'] = 1
# df_results.loc[df_results['c#SN1OH01'].round(4) == df_results['c#SN1OH01'].round(4).min(), 'yield#SN1Br01s1'] = 0
#
# avs.plot_3d_dataset_as_cube(xs, ys, zs, df_results['yield#SN1Br01s1'].to_numpy(),
#                             substance_titles=('Alcohol,\nmM', 'HBr,\nmM', 'temperature,\n°C'),
#                             colorbar_title='yield of SN1Br01s1',
#                             npoints=50, sparse_npoints=7, rbf_epsilon=1,
#                             rbf_smooth=0.05,
#                             interpolator_choice='rbf',
#                             data_for_spheres='interpolated',
#                             rbf_function='multiquadric',
#                             axes_ticks_format='%.0f',
#                             axes_font_factor=1.3,
#                             contours=[0.15, 0.2])

