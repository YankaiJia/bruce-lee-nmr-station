from numpy import arange, pi, cos, sin

from traits.api import HasTraits, Range, Instance, \
        on_trait_change
from traitsui.api import View, Item, Group
from mayavi.core.api import PipelineBase
from mayavi.core.ui.api import MayaviScene, SceneEditor, \
                MlabSceneModel
import pandas as pd
from scipy.interpolate import Rbf
import numpy as np
import os

def create_folder_unless_it_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'
experiment_name = 'multicomp-reactions/2023-01-18-run01/'
timepoint_id = 1
df_results = pd.read_csv(data_folder + experiment_name + f'results/timepoint{timepoint_id:03d}-reaction_results.csv')

print(df_results.max())

substances = ['ic001','amine','ald001','pTSA']
product = 'IIO029A'

substrate_cs = []
for substance in substances:
    substrate_cs.append(df_results[substance].to_numpy())

xs0, ys0, zs0, cats = substrate_cs

for x in [xs0, ys0, zs0]:
    print(max(x))

unique_cats = sorted(list(set(list(cats))))
print(f'Unique cats: {unique_cats}')

product_concentrations = df_results[product].to_numpy()

yields = []
for index, row in df_results.iterrows():
    lowest_concentration_of_substrate_here = min(row[substance] for substance in substances[:-1])
    yield_here = row[product] / lowest_concentration_of_substrate_here
    yields.append(yield_here)
yields = np.array(yields)

ks0 = yields
print(max(ks0))
print(min(ks0))

max_ks0 = np.max(ks0)
max_xs0 = np.max(xs0)
max_ys0 = np.max(ys0)
max_zs0 = np.max(zs0)

all_wnews = []
all_points = []
for cat_here in unique_cats:
    mask = (cats == cat_here)
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

    # v5
    # rbf4 = Rbf(xs, ys, zs, ks, epsilon=0.12 /0.79 * 9.926E-02, smooth=0.02) # function="thin_plate"
    # rbf4 = Rbf(xs, ys, zs, ks, epsilon=0.12 / 0.79 * 9.926E-02 * 10, smooth=0.00001)  # function="thin_plate"
    rbf4 = Rbf(xs, ys, zs, ks, epsilon=0.04, smooth=0.00001)  # function="thin_plate"

    # mlab.points3d(xs, ys, zs, ks)
    # mlab.show()

    ti = np.linspace(0, max_ks0, 10)
    # xnew, ynew, znew = np.meshgrid(ti, ti, ti)
    npoints = 30j
    xnew, ynew, znew = np.mgrid[0:max_xs0:npoints, 0:max_ys0:npoints, 0:max_zs0:npoints]
    wnew = rbf4(xnew, ynew, znew)
    wnew[wnew<0] = 0
    all_wnews.append(wnew)

    # ks[:] = 0.005
    all_points.append((xs, ys, zs, ks))


def curve(n_mer):
    return all_wnews[n_mer], all_points[n_mer]


class MyModel(HasTraits):
    pTSA_concentration_id    = Range(0, len(unique_cats)-1, 1, )#mode='spinner')

    scene = Instance(MlabSceneModel, ())
    scene.background = (1, 1, 1)

    plot = Instance(PipelineBase)


    # When the scene is activated, or when the parameters are changed, we
    # update the plot.
    @on_trait_change('pTSA_concentration_id,scene.activated')
    def update_plot(self):
        wnew, the_points = curve(self.pTSA_concentration_id)
        if self.plot is None:
            self.plot = self.scene.mlab.contour3d(xnew, ynew, znew, wnew, contours=5, opacity=0.5, vmin=0, vmax=max_ks0,
                                  colormap='summer')


            # 7.95508836282453e-05
            # 0.000160386113793563
            # 0.00012190439571993896

            # cont.actor.actor.scale = (0.35, 0.35, 0.35)
            ax1 = self.scene.mlab.axes(color=(0.5, 0.5, 0.5), nb_labels=4)
            self.scene.foreground = (0.2, 0.2, 0.2)
            self.scene.mlab.xlabel(f'{substances[0]}')
            self.scene.mlab.ylabel(f'{substances[1]}')
            self.scene.mlab.zlabel(f'{substances[2]}')
            self.scene.mlab.outline(self.plot)
            self.texthere = self.scene.mlab.text3d(max_xs0*0.15, max_ys0*1.3, max_zs0/2, 'Catalyst', scale=0.005)
            # mlab.axes.label_text_property.font_size = 12
            self.vslice = self.scene.mlab.volume_slice(xnew, ynew, znew, wnew, plane_orientation='x_axes', opacity=0.5,
                                                       vmin=0, vmax=max_ks0)#, colormap='summer')
            self.scene.background = (1, 1, 1)
            cb = self.scene.mlab.colorbar(object=self.vslice, title="Yield")
            cb.scalar_bar.unconstrained_font_size = True
            cb.label_text_property.font_size = 15
            # self.scene.children[1].children[0].scalar_lut_manager.title_text_property.font_size = 6
            ax1.axes.font_factor = 0.83
            # ax2 = self.scene.mlab.axes(color=(0.5, 0.5, 0.5), nb_labels=4)
            # ax2.axes.font_factor = 0.83
            xs, ys, zs, ks = the_points
            self.plot_points = self.scene.mlab.points3d(xs, ys, zs, ks, vmin=0, vmax=max_ks0)
                                  # colormap='summer')
        else:
            self.plot.mlab_source.trait_set(x=xnew, y=ynew, z=znew, scalars=wnew)
            self.vslice.mlab_source.trait_set(x=xnew, y=ynew, z=znew, scalars=wnew)
            xs, ys, zs, ks = the_points
            self.plot_points.mlab_source.trait_set(x=xs, y=ys, z=zs, scalars=ks)
            self.texthere.text = f'Catalyst (pTSA) {unique_cats[self.pTSA_concentration_id]:.3f} mol/L'
            self.texthere.vector_text.update()
            create_folder_unless_it_exists(data_folder + experiment_name + f'results/4d-viewer-frames')
            self.scene.mlab.savefig(data_folder + experiment_name + f'results/4d-viewer-frames/{self.pTSA_concentration_id:05d}.png')



    # The layout of the dialog created
    view = View(Item('scene', editor=SceneEditor(scene_class=MayaviScene),
                     height=250, width=300, show_label=False),
                Group(
                        '_', 'pTSA_concentration_id',
                     ),
                resizable=True,
                )

my_model = MyModel()
my_model.configure_traits()