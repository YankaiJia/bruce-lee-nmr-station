import importlib
import os
import numpy as np
from matplotlib import pyplot as plt
from scipy.optimize import curve_fit
# import plotly.graph_objects as go
from scipy.interpolate import griddata
from mayavi import mlab

organize_run_results = importlib.import_module("misc-scripts.organize_run_results")
avs = importlib.import_module("visualize-results.animated_viewer_static")
data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'

# list_of_runs = tuple(['2024-01-29-run01',
#                       '2024-01-29-run02',
#                       '2024-01-30-run01'
#                       ])

# list_of_runs = tuple(['2024-02-16-run01',
#                       '2024-02-17-run01',
#                       '2024-02-17-run02'])

list_of_runs = tuple(['2024-03-04-run01',
                      '2024-03-04-run02'])



substances = ['c#ethyl_acetoacetate',  'c#methoxybenzaldehyde', 'c#ammonium_acetate']
substance_titles = ['Acetoacetate', 'Methoxy', 'Ammonium acetate']
# substrates = ['c#SN1OH03', 'c#HBr']

df_results = organize_run_results.join_data_from_runs([f'BPRF/{x}/' for x in list_of_runs],
                                 round_on_columns=None)

xs = df_results['c#ethyl_acetoacetate']
ys = df_results['c#methoxybenzaldehyde']
plt.scatter(xs, ys)
plt.show()

substrates = ['ethyl_acetoacetate',  'methoxybenzaldehyde', 'ammonium_acetate']
# product_name = 'bb021'
# for index, row in df_results.iterrows():
#     product_concentration = df_results.loc[index, f'pc#{product_name}']
#     coefficients_dict = {'methoxybenzaldehyde': 2, 'ethyl_acetoacetate': 1, 'ammonium_acetate': 0}
#     candidate_yields = [
#         product_concentration / (df_results.loc[index, f'c#{substrate_name}'] * coefficients_dict[substrate_name])
#         for substrate_name in substrates if substrate_name != 'ammonium_acetate']
#     df_results.loc[index, f'yield#{product_name}'] = np.max(candidate_yields)

product_name = 'dm053'
for index, row in df_results.iterrows():
    product_concentration = df_results.loc[index, f'pc#dm053']
    coefficients_dict = {'methoxybenzaldehyde': 1, 'ethyl_acetoacetate': 2, 'ammonium_acetate': 1}
    candidate_yields = [
        product_concentration / (df_results.loc[index, f'c#{substrate_name}'] * coefficients_dict[substrate_name])
        for substrate_name in substrates]
    df_results.loc[index, f'yield#{product_name}'] = np.max(candidate_yields)

# round values in substance columns to 6 significant digits
for substance in substances:
    df_results[substance] = df_results[substance].round(6)

# column_to_plot = 'yield#HRP01'

# column_to_plot = 'yield#dm37'
# df_results = df_results[df_results[column_to_plot] <= 0.285]

column_to_plot = 'yield#bb017'

# column_to_plot = 'yield#dm70'
# column_to_plot = 'yield#dm035_8_dm35_9'
# column_to_plot = 'rmse'
# column_to_plot = 'fitted_dilution_factor_2'

df_results.dropna(subset=[column_to_plot], inplace=True)
df_results = df_results[~df_results[column_to_plot].isin([np.inf, -np.inf])]
# limit the df to only where 'c#ammonium_acetate" is greater than 0.01
df_results = df_results[df_results['c#ammonium_acetate'] > 0.01]

# find the 95% perfentile of rmse, LB_stat_dil_0, LB_stat_dil_1
percentile_to_target = 0.9
rmse_95 = df_results['rmse'].quantile(percentile_to_target)
# LB_stat_dil_0_95 = df_results['LB_stat_dil_0'].quantile(percentile_to_target)
# LB_stat_dil_1_95 = df_results['LB_stat_dil_1'].quantile(percentile_to_target)

# use only df_results with values below these percentiles
df_results = df_results[df_results['rmse'] < rmse_95]
# df_results = df_results[df_results['LB_stat_dil_0'] < LB_stat_dil_0_95]
# df_results = df_results[df_results['LB_stat_dil_1'] < LB_stat_dil_1_95]


# df_results['yield#bb021'] = df_results['yield#bb021'].apply(lambda x: 0 if x<0 else x)
# df_results['yield#dm40'] = df_results['yield#dm40'].apply(lambda x: 0 if x<0 else x)
# df_results['fitted_dilution_factor_2'] = df_results['fitted_dilution_factor_2'].apply(lambda x: x/200)
# if yield is above 1, replace with 1
# df_results[column_to_plot] = df_results[column_to_plot].apply(lambda x: 1 if x>1 else x)
# negative yields are omitted
# df_results = df_results[df_results[column_to_plot] >= 0]
# df_results = df_results[df_results[column_to_plot] <= 1.3]

# df_results = df_results[df_results[column_to_plot] <= 2.15]
# df_results = df_results[df_results[column_to_plot] <= 0.35]
# df_results = df_results[df_results[column_to_plot] <= 0.04]

unique_ethyl_acetoacetate = df_results['c#ethyl_acetoacetate'].unique()
unique_methoxybenzaldehyde = df_results['c#methoxybenzaldehyde'].unique()


# for index, row in df_results.iterrows():
#     product_name = 'HRP02'
#     product_concentration = df_results.loc[index, f'pc#dm35_9']
#     product_error = df_results.loc[index, f'pcerr#dm35_9']
#     coefficients_dict = {'methoxybenzaldehyde': 2, 'ethyl_acetoacetate': 2, 'ammonium_acetate': 1}
#     candidate_yields = [product_concentration / (
#                 df_results.loc[index, f'c#{substrate_name}'] * coefficients_dict[substrate_name]) for
#                         substrate_name in substrates]
#     candidate_errs = [
#         product_error / (df_results.loc[index, f'c#{substrate_name}'] * coefficients_dict[substrate_name])
#         for substrate_name in substrates]
#     df_results.loc[index, f'yield#{product_name}'] = np.max(candidate_yields)
#     df_results.loc[index, f'yielderr#{product_name}'] = candidate_errs[np.argmax(candidate_yields)]
#
#     product_name = 'HRI03'
#     product_concentration = df_results.loc[index, f'pc#EAB']
#     product_error = df_results.loc[index, f'pcerr#EAB']
#     coefficients_dict = {'methoxybenzaldehyde': 0, 'ethyl_acetoacetate': 1, 'ammonium_acetate': 1}
#     candidate_yields = [product_concentration / (
#                 df_results.loc[index, f'c#{substrate_name}'] * coefficients_dict[substrate_name]) for
#                         substrate_name in substrates if substrate_name != 'methoxybenzaldehyde']
#     candidate_errs = [
#         product_error / (df_results.loc[index, f'c#{substrate_name}'] * coefficients_dict[substrate_name])
#         for substrate_name in substrates if substrate_name != 'methoxybenzaldehyde']
#     df_results.loc[index, f'yield#{product_name}'] = np.max(candidate_yields)
#     df_results.loc[index, f'yielderr#{product_name}'] = candidate_errs[np.argmax(candidate_yields)]

def get_xys_for_one_col(column_to_plot, df_results):
    xs = []
    ys = []
    zs = []
    zserr = []
    for ethyl_acetoacetate in unique_ethyl_acetoacetate:
        for methoxybenzaldehyde in unique_methoxybenzaldehyde:
            df = df_results[(df_results['c#ethyl_acetoacetate'] == ethyl_acetoacetate) &
                            (df_results['c#methoxybenzaldehyde'] == methoxybenzaldehyde) &
                            (df_results['c#ammonium_acetate'] > 0.3)]
            if len(df) > 0:
                xs.append(ethyl_acetoacetate)
                ys.append(methoxybenzaldehyde)
                # average values of column to plot
                zs.append(df[column_to_plot].median())
                zserr.append(df[column_to_plot.replace('yield', 'yielderr')].median())
            else:
                print(f'No data for {ethyl_acetoacetate} and {methoxybenzaldehyde}')

    # use griddata to interpolate to uniform xs ys grid
    plotsteps = 18
    grid_x, grid_y = np.mgrid[min(xs):max(xs):plotsteps*1j, min(ys):max(ys):plotsteps*1j]
    points = np.array([xs, ys]).T
    grid_z = griddata(points, zs, (grid_x, grid_y), method='linear')
    gridzerr = griddata(points, zserr, (grid_x, grid_y), method='linear')
    xs_for_plot = np.linspace(min(xs), max(xs), plotsteps)
    ys_for_plot = np.linspace(min(ys), max(ys), plotsteps)
    return grid_x, grid_y, grid_z, gridzerr

##### 3D PLOT
data = []

######## MAIN PRODUCTS
data.append(get_xys_for_one_col(column_to_plot = 'yield#HRP01',
                                df_results = df_results[df_results['yield#HRP01'] <= 1]))

# data.append(get_xys_for_one_col(column_to_plot = 'yield#HRP01',
#                                 df_results = df_results[df_results['yield#HRP01'] <= 1]))


# all the rows where 'yield#bb017' is above 1 replace with 1
# df_results['yield#bb017'] = df_results['yield#bb017'].apply(lambda x: 1 if x>1 else x)
# df_results['yield#bb017'] = df_results['yield#bb017']/1.06
data.append(get_xys_for_one_col(column_to_plot = 'yield#bb017',
                                df_results = df_results[df_results['yield#bb017'] <= 1.55]))

# data.append(get_xys_for_one_col(column_to_plot = 'yield#dm053',
#                                 df_results = df_results))


# surfcolors = [(31/255, 119/255, 180/255), (1, 127/255, 14/255)]
surfcolors = [tuple(np.array((33, 64, 154))/255), tuple(np.array((243, 185, 26))/255)]
yieldmax = 100

# ########## intermediates:
# data.append(get_xys_for_one_col(column_to_plot = 'yield#dm40',
#                                 df_results = df_results[df_results['yield#dm40'] <= 1]))
# data.append(get_xys_for_one_col(column_to_plot = 'yield#bb021',
#                                 df_results = df_results[df_results['yield#bb021'] <= 1]))
# surfcolors = [(44/255, 160/255, 44/255), (214/255, 39/255, 40/255)]
# yieldmax = 15

mlab.figure(size=(1024, 1224), bgcolor=(1, 1, 1), fgcolor=(0.2, 0.2, 0.2))



for dataset_id, data_point in enumerate(data):
    grid_x, grid_y, grid_z, gridzerr = data_point
    print(f'min z: {np.min(grid_z)}, max z: {np.max(grid_z)}')
    grid_x *= 1000
    grid_y *= 1000
    grid_z *= 100

    xs0 = (grid_x - np.min(grid_x)) / (np.max(grid_x) - np.min(grid_x))
    ys0 = (grid_y - np.min(grid_y)) / (np.max(grid_y) - np.min(grid_y))
    # zs0 = (grid_z - np.min(grid_z)) / (np.max(grid_z) - np.min(grid_z))
    zs0 = grid_z/yieldmax
    max_xs0 = np.max(xs0)
    max_ys0 = np.max(ys0)
    max_zs0 = np.max(zs0)

    print(f'zs0 range: {np.min(zs0)} - {np.max(zs0)}')

    # use mayavi mlab surf
    # mlab.figure(bgcolor=(1, 1, 1))
    # plot = mlab.surf(xs0, ys0, zs0, color=surfcolors[dataset_id])
    plot = mlab.points3d(xs0, ys0, zs0, color=surfcolors[dataset_id], scale_factor=0.08)
    # plot = mlab.surf(xs0, ys0, zs0, color=surfcolors[dataset_id], extent=[np.min(xs0), np.max(xs0),
    #                                                                          np.min(ys0), np.max(ys0),
    #                                                                          0, 1],
    #                  opacity=1)
# set(plot,'FaceColor',[1 0 0],'FaceAlpha',0.5)
# mlab.colorbar()
# mlab.xlabel('c#ethyl_acetoacetate')
# mlab.ylabel('c#methoxybenzaldehyde')
# mlab.show()

plot.actor.actor.property.ambient = 0
# for i in range(3):
#     start = np.array([np.min(xs0), np.min(ys0), np.min(zs0)])
#     end = np.array([np.min(xs0), np.min(ys0), np.min(zs0)])
#     end[i] = list([max_xs0, max_ys0, max_zs0])[i]
#     arr = Arrow_From_A_to_B(start[0], start[1], start[2], end[0], end[1], end[2])
# arr_temp = Arrow_From_A_to_B(np.max(xs0), np.min(ys0), np.min(zs0),
#                                   np.max(xs0), np.min(ys0), np.max(zs0))
# plot = mlab.surf(xs0, ys0, (zs0-np.min(zs0))/(np.max(zs0)-np.min(zs0)), color=surfcolors[dataset_id], opacity=0)

plot = mlab.surf(xs0, ys0, (zs0-np.min(zs0))/(np.max(zs0)-np.min(zs0)), color=surfcolors[dataset_id])

sparse_npoints=4
ax1 = mlab.axes(color=(0.5, 0.5, 0.5), nb_labels=sparse_npoints, ranges=[np.min(grid_x), np.max(grid_x),
                                                                         np.min(grid_y), np.max(grid_y),
                                                                         0, np.max(grid_z)])
substance_titles = ['Acetoacetate', 'Methoxy', 'Yield, %']
substance_titles = ['']*3
mlab.xlabel(f'{substance_titles[0]}')
mlab.ylabel(f'{substance_titles[1]}')
mlab.zlabel(f'{substance_titles[2]}')

axes_ticks_format='%.0f'
axes_font_factor=1.3
# substance_titles = ['Acetoacetate', 'Methoxy', 'Ammonium acetate']
# mlab.outline(plot)
# cb = mlab.colorbar(object=plot, title=colorbar_title, orientation='horizontal', nb_labels=5)
# cb.scalar_bar.unconstrained_font_size = True
# cb.label_text_property.font_size = 19
ax1.axes.font_factor = axes_font_factor
ax1.axes.label_format = axes_ticks_format
ax1.axes.corner_offset = 0.05

scene = mlab.get_engine().scenes[0]

# scene.scene.camera.position = [2.5924475454278446, 4.014092072475744, 3.196806857037632]
# scene.scene.camera.focal_point = [0.5, 0.5, 0.5]
# scene.scene.camera.view_angle = 30.0
# scene.scene.camera.view_up = [-0.3157787130206195, -0.4521410923093301, 0.834177581242967]
# scene.scene.camera.clipping_range = [3.1635435457316055, 7.0953401952622475]
# scene.scene.camera.compute_view_plane_normal()

scene.scene.camera.position = [3.5022834678305252, 6.509322279608751, 4.250526934007179]
scene.scene.camera.focal_point = [0.5206201337277889, 0.4916610289365053, 0.5019663814455271]
scene.scene.camera.view_angle = 30.0
scene.scene.camera.view_up = [-0.21520257220714775, -0.4373014770797476, 0.8731868477360951]
scene.scene.camera.clipping_range = [5.8418018839435515, 10.04878256955108]
scene.scene.camera.compute_view_plane_normal()

# scene.scene.light_manager.lights[1].intensity = 0
# scene.scene.light_manager.lights[2].intensity = 0
# scene.scene.light_manager.lights[3].intensity = 0
# camera_light = scene.scene.light_manager.lights[0]
# camera_light.elevation = 47
# camera_light.azimuth = -5.0
scene.scene.render()

mlab.savefig('misc-scripts/figures/hansch-mainprod.obj')

mlab.show()


data = []
data.append(get_xys_for_one_col(column_to_plot = 'yield#HRP01',
                                df_results = df_results[df_results['yield#HRP01'] <= 1]))
# df_results['yield#bb017'] = df_results['yield#bb017'].apply(lambda x: 1 if x>1 else x)
data.append(get_xys_for_one_col(column_to_plot = 'yield#bb017',
                                df_results = df_results[df_results['yield#bb017'] <= 10.55]))

# data.append(get_xys_for_one_col(column_to_plot = 'yield#HRP02',
#                                 df_results = df_results[df_results['yield#bb017'] <= 10.55]))

# data.append(get_xys_for_one_col(column_to_plot = 'yield#HRI03',
#                                 df_results = df_results[df_results['yield#bb017'] <= 10.55]))
# data.append(get_xys_for_one_col(column_to_plot = 'yield#dm40',
#                                 df_results = df_results[df_results['yield#dm40'] <= 1]))
# data.append(get_xys_for_one_col(column_to_plot = 'yield#bb021',
#                                 df_results = df_results[df_results['yield#bb021'] <= 1]))

# make figure with double x axes
fig = plt.figure(figsize=(4,2.5), dpi=300)
ax1 = fig.add_subplot(111)
ax2 = ax1.twiny()

def tick_function(X):
    V = 110 - X
    return ["%.0f" % z for z in V]

labels = ['HRP01', 'HRP04']
colors = [f'C{i}' for i in range(4)]
colors[1] = 'gold'
for id, d in enumerate(data):
    # iterate over unique x and find z where y=x
    xs, ys, zs, zserr = d
    xxs = []
    zzs = []
    # for x in np.unique(xs):

    # find indices of ys where xs==ys==x
    indices = np.where(np.isclose(xs+ys, 110/1000))
    # find z where xs==ys==x
    z = zs[indices]
    x = xs[indices]
    # ax1.plot(110 - x*1000, z*100, label=labels[id], color=colors[id])
    # plot with zserr errorbars
    ax1.errorbar(110 - x*1000, z*100, yerr=zserr[indices]*100, fmt='o-', label=labels[id], color=colors[id],
                 alpha=0.5, capsize=3, capthick=1, elinewidth=1, markersize=3)

ax1.set_xlim(10, 100)
ax1Ticks = ax1.get_xticks()
ax2Ticks = ax1Ticks
ax2.set_xticks(ax2Ticks)
ax2.set_xbound(ax1.get_xbound())
ax2.set_xticklabels(tick_function(ax2Ticks))

ax2.set_xlabel("EAA, mM")
ax1.set_xlabel('Aldehyde, mM')

ax1.set_ylabel('Yield, %')
ax1.legend()

plt.show()