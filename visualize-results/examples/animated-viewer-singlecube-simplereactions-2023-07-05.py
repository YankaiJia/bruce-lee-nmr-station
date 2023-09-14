from scipy.optimize import curve_fit

from visualize_results import *
import time
from scipy.interpolate import LinearNDInterpolator
from scipy.interpolate import interp1d
organize_run_results = importlib.import_module("misc-scripts.organize_run_results")
import animated_viewer_static as avs

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'

# timepoint_id = 1
experiment_name = 'simple-reactions/2023-07-05-run01/'
# df_results = pd.read_csv(data_folder + experiment_name + f'results/timepoint{timepoint_id:03d}-reaction_results.csv')

list_of_runs = tuple([
    '2023-07-05-run01',
    '2023-07-06-run01',
    '2023-07-07-run01',
    '2023-07-10-run01',
    '2023-07-10-run02',
    '2023-07-11-run01',
    '2023-07-11-run02'])

df_results = organize_run_results.join_data_from_runs([f'simple-reactions/{x}/' for x in list_of_runs],
                                 round_on_columns=('c#SN1OH01', 'c#HBr', 'Temperature'))

# set yields to nan at the minimum of c#SN1OH01 column
df_results.loc[df_results['c#SN1OH01'].round(4) == df_results['c#SN1OH01'].round(4).min(), 'yield'] = np.nan

# set yields to nan where the temperature is 6 and yield is above 0.9
df_results.loc[(df_results['Temperature'] == 6) & (df_results['yield'] > 0.9), 'yield'] = np.nan

# remove all rows where 'yield' columns is nan
df_results.dropna(subset=['yield'], inplace=True)

df_results['yield'] = df_results['yield'].apply(lambda x: x if x>1e-10 else 0)
# df_results.drop(indices_of_outliers, inplace=True)

substances = ['c#SN1OH01', 'c#HBr', 'Temperature']
substance_titles = ['Alcohol', 'HBr', 'Temperature']
substrates = ['c#SN1OH01', 'c#HBr']

for substrate in substrates:
    df_results[substrate] = df_results[substrate].apply(lambda x: x*1000 if x>1e-10 else 0)

xs = df_results[substrates[0]].to_numpy()
ys = df_results[substrates[1]].to_numpy()
zs = df_results['Temperature'].to_numpy()

# df_results['carbocat'] = df_results['carbocat'].apply(lambda x: x * 8)
# df_results[substrates[1]] = df_results[substrates[1]].apply(lambda x: x * yscale)

xs0, ys0, zs0 = [df_results[substance].to_numpy() for substance in substances]
yields = df_results['yield'].to_numpy()

print(f'Max concentrations of substrates: {[print(max(x)) for x in [xs0, ys0, zs0]]}')
print(f'Yields - min: {min(yields)}, max: {max(yields)}')

avs.plot_3d_dataset_as_cube(xs, ys, zs, yields,
                            substance_titles=('Alcohol,\nmM', 'HBr,\nmM', 'Temperature,\n°C'),
                            colorbar_title='Conversion:',
                            npoints=50, sparse_npoints=7, rbf_epsilon=1,
                            rbf_smooth=0.05,
                            interpolator_choice='rbf',
                            data_for_spheres='interpolated',
                            rbf_function='multiquadric',
                            axes_ticks_format='%.0f',
                            axes_font_factor=1.3,
                            contours=[0.2, 0.4, 0.7, 0.85])

# df_results.loc[df_results['yield#SN1Br01s1'] < 0, 'yield#SN1Br01s1'] = 0
# df_results.loc[df_results['yield#SN1Br01s1'] > 1, 'yield#SN1Br01s1'] = 1
# df_results.loc[df_results['c#SN1OH01'].round(4) == df_results['c#SN1OH01'].round(4).min(), 'yield#SN1Br01s1'] = 0
#
# avs.plot_3d_dataset_as_cube(xs, ys, zs, df_results['yield#SN1Br01s1'].to_numpy(),
#                             substance_titles=('Alcohol,\nmM', 'HBr,\nmM', 'Temperature,\n°C'),
#                             colorbar_title='yield of SN1Br01s1',
#                             npoints=50, sparse_npoints=7, rbf_epsilon=1,
#                             rbf_smooth=0.05,
#                             interpolator_choice='rbf',
#                             data_for_spheres='interpolated',
#                             rbf_function='multiquadric',
#                             axes_ticks_format='%.0f',
#                             axes_font_factor=1.3,
#                             contours=[0.15, 0.2])


# # fit the kinetics
# xdata = np.vstack((ys0.T, zs0.T))
# ydata = yields.T
#
# def kinetics_yield(catalyst_C, temperature, a, b):
#     return (1 - np.exp(-a*catalyst_C*np.exp(-b/(temperature + 273.15))))
#
# def func(x, a, b):
#     return kinetics_yield(catalyst_C=x[0], temperature=x[1], a=a, b=b)
#
# popt, pcov = curve_fit(func, xdata, ydata, p0=[96079.4039589, 4371.26728913], ftol=1e-10)
# print(popt)
#
# npoints = 20j
# x_raw, y_raw, z_raw = np.mgrid[np.min(xs):np.max(xs):npoints,
#                       np.min(ys):np.max(ys):npoints,
#                       np.min(zs):np.max(zs):npoints]
# # flatten all arrays
# x_raw = x_raw.flatten()
# y_raw = y_raw.flatten()
# z_raw = z_raw.flatten()
# # k_raw = x_raw * y_raw * z_raw
# # k_raw = x_raw + y_raw + z_raw
#
#
# fitted_yields = kinetics_yield(y_raw, z_raw, *popt)
#
# avs.plot_3d_dataset_as_cube(x_raw, y_raw, z_raw, fitted_yields,
#                             substance_titles=('Alcohol,\nmM', 'HBr,\nmM', 'Temperature,\n°C'),
#                             colorbar_title='Conversion:',
#                             npoints=50, sparse_npoints=7, rbf_epsilon=1,
#                             rbf_smooth=0.05,
#                             interpolator_choice='linear',
#                             data_for_spheres='interpolated',
#                             rbf_function='multiquadric',
#                             axes_ticks_format='%.0f',
#                             axes_font_factor=1.3,
#                             contours=[0.2, 0.4, 0.7, 0.85])