import importlib
import os
import numpy as np
from matplotlib import pyplot as plt
from scipy.optimize import curve_fit

organize_run_results = importlib.import_module("misc-scripts.organize_run_results")
avs = importlib.import_module("visualize-results.animated_viewer_static")
data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'

list_of_runs = tuple(['2024-01-29-run01',
                      '2024-01-29-run02',
                      '2024-01-30-run01'
                      ])

# column_to_plot = 'yield#HRP01'
# column_to_plot = 'yield#dm37'
column_to_plot = 'yield#bb017'

substances = ['c#ethyl_acetoacetate',  'c#methoxybenzaldehyde', 'c#ammonium_acetate']
substance_titles = ['Acetoacetate', 'Methoxy', 'Ammonium acetate']
# substrates = ['c#SN1OH03', 'c#HBr']

df_results = organize_run_results.join_data_from_runs([f'BPRF/{x}/' for x in list_of_runs],
                                 round_on_columns=[])

df_results.dropna(subset=[column_to_plot], inplace=True)
df_results = df_results[~df_results[column_to_plot].isin([np.inf, -np.inf])]
# if yield is above 1, replace with 1
# df_results[column_to_plot] = df_results[column_to_plot].apply(lambda x: 1 if x>1 else x)
# negative yields are omitted
df_results = df_results[df_results[column_to_plot] >= 0]
df_results = df_results[df_results[column_to_plot] <= 1]
# df_results = df_results[df_results[column_to_plot] <= 0.35]

# convert from mol/L to mM
for substrate in substances:
    df_results[substrate] = df_results[substrate].apply(lambda x: x*1000 if x>1e-10 else 0)

xs = df_results[substances[0]].to_numpy()
ys = df_results[substances[1]].to_numpy()
zs = df_results[substances[2]].to_numpy()
yields = df_results[column_to_plot].to_numpy()

print(f'Min concentrations of substrates: {[np.min(x) for x in [xs, ys, zs]]}')
print(f'Max concentrations of substrates: {[np.max(x) for x in [xs, ys, zs]]}')
print(f'Yields - min: {min(yields)}, max: {max(yields)}')

avs.plot_3d_dataset_as_cube(xs, ys, zs, yields,
                            substance_titles=substance_titles,
                            colorbar_title=column_to_plot,
                            npoints=50, sparse_npoints=7, rbf_epsilon=1,
                            rbf_smooth=0.05,
                            interpolator_choice='linear',
                            data_for_spheres='raw',
                            rbf_function='multiquadric',
                            axes_ticks_format='%.0f',
                            axes_font_factor=1.3,
                            contours=[2])