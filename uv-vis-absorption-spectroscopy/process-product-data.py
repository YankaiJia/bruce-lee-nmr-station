import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import pandas as pd
from scipy.signal import savgol_filter
from scipy import interpolate
from scipy.optimize import curve_fit
from mayavi import mlab
from scipy.interpolate import Rbf
from mpl_toolkits.mplot3d import Axes3D


# plt.ioff()

data_folder = 'D:\\Docs\\Science\\UNIST\\Projects\\robochem\\data\\'

excel_filename = data_folder + 'multicomp-reactions\\2022-12-14-run01\\input_compositions\\compositions.xlsx'
df_conc = pd.read_excel(excel_filename,
                   sheet_name='Sheet1', usecols='I,J,K,L,M')
df_plates = df_conc.iloc[:]

stock_concentrations = {'aldehyde': 0.794065682,
                        'pTSA':1.193398979,
                        'amine':2.387782168,
                        'Isocyano':2.38104247}
substances = ['DMF', 'aldehyde', 'amine', 'Isocyano', 'pTSA']

substrate_cs = []
for substance in substances[1:]:
    substrate_cs.append(df_plates[substance + '.1'].to_numpy() * stock_concentrations[substance] / 100)

xs0, ys0, zs0, cats = substrate_cs

for x in [xs0, ys0, zs0]:
    print(max(x))

unique_cats = sorted(list(set(list(cats))))

product_concentrations_vs_time = np.load(data_folder + 'multicomp-reactions\\2022-12-14-run01\\results\\product_vs_time.npy', allow_pickle=True).T
ks = []
# product_concentrations_vs_time.shape[0]
for i in range(105):
    # if i>10:
    #     continue
    # ts = np.array([0, 10, 20, 30])
    # cs = np.insert(product_concentrations_vs_time[i, :-2], 0, 0)
    ts = np.array([10, 20, 30])
    cs = product_concentrations_vs_time[i, :-2]
    # plt.plot(ts, cs, 'o-')
    # plt.show()
    slope = np.polyfit(ts, cs, 1)[0]
    ks.append(slope)
ks0 = np.array(ks)

print(max(ks0))
print(min(ks0))

cat_here = unique_cats[0]
mask = cats == cat_here
xs = xs0[mask]
ys = ys0[mask]
zs = zs0[mask]
ks = ks0[mask]

# dataset = pd.DataFrame({'Product concentration (mol/L)': target_concentrations,
#                         'Absolute standard error (mol/L)': target_concentration_errors,
#                         'Unmixing error (a.u.)': unmixing_errors})
#
# # dataset = pd.DataFrame({f'Product (mol/L) at timepoint {timepoint}': product_concentrations_vs_time[timepoint-1] for timepoint in [1,2,3,4,5]})
# dataset.to_excel(data_folder + 'multicomp-reactions\\2022-12-14-run01\\results\\v7_product_vs_time.xlsx')


# fig1 = plt.figure()
# ax1=fig1.gca(projection='3d')
# sc1=ax1.scatter(xs, ys, zs, c=ks, cmap=plt.viridis())
# plt.colorbar(sc1)
# ax1.set_xlabel('X')
# ax1.set_ylabel('Y')
# ax1.set_zlabel('Z')
# plt.show()

rbf4 = Rbf(xs, ys, zs, ks, epsilon=0.12, smooth=0.02) # function="thin_plate"
ti = np.linspace(0, 0.35, 10)
# xnew, ynew, znew = np.meshgrid(ti, ti, ti)
npoints = 30j
xnew, ynew, znew = np.mgrid[0:0.35:npoints, 0:0.35:npoints, 0:0.35:npoints]
wnew = rbf4(xnew, ynew, znew)

mlab.figure(size = (1024,768),\
            bgcolor = (1,1,1), fgcolor = (0.5, 0.5, 0.5))
contours0 = np.linspace(0, 0.00041189502561095185, 6)
contours = contours0
print('AAA')
print(np.max(wnew))
# contours = []
# for contour in contours0:
#     if contour > np.min(wnew) and contour < np.max(wnew):
#         contours.append(contour)
cont = mlab.contour3d(xnew, ynew, znew, wnew, contours=6, opacity=0.5, vmin=0, vmax=0.000160386113793563,
                      colormap='summer')

# 7.95508836282453e-05
# 0.000160386113793563
# 0.00012190439571993896

# cont.actor.actor.scale = (0.35, 0.35, 0.35)
ax1 = mlab.axes(color=(1,1,1), nb_labels=4)
mlab.xlabel(f'{substances[1]}')
mlab.ylabel(f'{substances[2]}')
mlab.zlabel(f'{substances[3]}')
mlab.outline(cont)
# mlab.axes.label_text_property.font_size = 12
ax1.axes.font_factor=0.83
mlab.volume_slice(xnew, ynew, znew, wnew, plane_orientation='x_axes', opacity=0.5)
mlab.show()