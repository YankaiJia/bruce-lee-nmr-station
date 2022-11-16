import matplotlib.pyplot as plt
import glob, os
from astropy.io import fits
import numpy as np

class LineBuilder:
    def __init__(self, line,ax,color):
        self.line = line
        self.ax = ax
        self.color = color
        self.xs = []
        self.ys = []
        self.cid = line.figure.canvas.mpl_connect('button_press_event', self)
        self.counter = 0
        self.shape_counter = 0
        self.shape = {}
        self.precision = 100

    def __call__(self, event):
        if event.inaxes!=self.line.axes: return
        if self.counter == 0:
            self.xs.append(event.xdata)
            self.ys.append(event.ydata)
        if np.abs(event.xdata-self.xs[0])<=self.precision and np.abs(event.ydata-self.ys[0])<=self.precision and self.counter != 0:
            self.xs.append(self.xs[0])
            self.ys.append(self.ys[0])
            self.ax.scatter(self.xs,self.ys,s=120,color=self.color)
            self.ax.scatter(self.xs[0],self.ys[0],s=80,color='blue')
            self.ax.plot(self.xs,self.ys,color=self.color)
            self.line.figure.canvas.draw()
            self.shape[self.shape_counter] = [self.xs,self.ys]
            self.shape_counter = self.shape_counter + 1
            self.xs = []
            self.ys = []
            self.counter = 0
        else:
            if self.counter != 0:
                self.xs.append(event.xdata)
                self.ys.append(event.ydata)
            self.ax.scatter(self.xs,self.ys,s=120,color=self.color)
            self.ax.plot(self.xs,self.ys,color=self.color)
            self.line.figure.canvas.draw()
            self.counter = self.counter + 1


def create_shape_on_image(data,cmap='jet', rangex=False, rangey=False):
    def change_shapes(shapes):
        new_shapes = {}
        for i in range(len(shapes)):
            l = len(shapes[i][1])
            new_shapes[i] = np.zeros((l,2),dtype='int')
            for j in range(l):
                new_shapes[i][j,0] = shapes[i][0][j]
                new_shapes[i][j,1] = shapes[i][1][j]
        return new_shapes
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_title('click to include shape markers (10 pixel precision to close the shape)')
    line = ax.imshow(data)
    if (rangex == False) and (rangey == False):
        ax.set_xlim(0,data[:,:,0].shape[1])
        ax.set_ylim(0,data[:,:,0].shape[0])
    else:
        ax.set_xlim(rangex[0], rangex[1])
        ax.set_ylim(rangey[0], rangey[1])
    linebuilder = LineBuilder(line,ax,'red')
    plt.gca().invert_yaxis()
    plt.show()
    new_shapes = change_shapes(linebuilder.shape)
    return new_shapes


def load_fits_image(fits_image_filename):
    image = fits.open(fits_image_filename)[0].data
    image_with_channels_as_last_axis = np.stack([image[i, :, :] for i in range(image.shape[0])], axis=2)
    return image_with_channels_as_last_axis

def image_for_show(image):
    return np.round((image - np.min(image))/(np.max(image) - np.min(image)) * 255).astype(int)

def sample_image_at_wells(image, wells, sr=20, show_roi=False):
    samples = []
    for well_id in range(wells.shape[0]):
        well = wells[well_id, :]
        # sample square with center at well and side 2*sr
        roi = image[well[1] - sr:well[1] + sr,
                    well[0] - sr:well[0] + sr, :]
        if show_roi:
            print(well_id)
            plt.imshow(image_for_show(roi))
            plt.show()
        samples.append(np.median(roi, axis=(0, 1)))
    return np.array(samples)

data_folder = 'D:\\Docs\\Science\\UNIST\\Projects\\robochem\\data\\'

experiment_folder = data_folder + 'multicomp-reactions\\2022-11-07-run01\\vis-photos\\plate_1\\FITS\\'
misc_folder = data_folder + 'multicomp-reactions\\2022-11-07-run01\\vis-photos\\plate_1\\misc\\'

def list_fit_files(experiment_folder):
    os.chdir(experiment_folder)
    file_list = []
    for file in glob.glob("*.FIT"):
        print(file)
        file_list.append(file)
    file_list.sort()
    return file_list

def well_coordinates_from_four_corner_wells(corners, N_wells = (9, 6)):
    left_wells = np.linspace(corners[0, :],
                            corners[3, :], N_wells[1])
    right_wells = np.linspace(corners[1, :],
                            corners[2, :], N_wells[1])

    wells = np.vstack((np.linspace(left_wells[row_id], right_wells[row_id], N_wells[0]) for row_id in range(N_wells[1])))
    wells = np.round(wells).astype(int)
    return wells

def show_well_locations(image, wells):
    plt.imshow(image_for_show(image))
    plt.scatter(wells[:, 0], wells[:, 1])
    plt.show()

# here it should be clicled clockwise
# corners = create_shape_on_image(image_for_show(image), rangey=(1895, 3948), rangex=(2619, 5447))[0][:-1, :]
corners = np.array([[3111, 2285],
 [5109, 2299],
 [5097, 3550],
 [3105, 3530]])

wells = well_coordinates_from_four_corner_wells(corners, N_wells=(9, 6))

# get median signal in three channes from all frames
file_list = list_fit_files(experiment_folder)
wells_in_all_frames = []
for file_id, filename in enumerate(file_list):
    image = load_fits_image(experiment_folder + file_list[file_id])
    samples = sample_image_at_wells(image, wells)
    wells_in_all_frames.append(samples)
wells_in_all_frames = np.array(wells_in_all_frames)
np.save(misc_folder + 'wells_in_all_frames.npy', wells_in_all_frames)

# get each well from the file taken at proper exposure
frame_exposures = 1 / np.array([4000, 400, 40, 4, 0.4])
upper_signal_limit = 60000
lower_signal_limit = 100
bad_signals_mask = np.logical_or(wells_in_all_frames <= lower_signal_limit,
                                 wells_in_all_frames >= upper_signal_limit)
wells_in_all_frames_persec = wells_in_all_frames / frame_exposures[:, None, None]
only_good_frames_persec = np.copy(wells_in_all_frames_persec)
only_good_frames_persec[bad_signals_mask] = np.nan
wells_final = np.nanmedian(only_good_frames_persec, axis=0)

reference_well_id = 45
absorbances = -np.log(wells_final / wells_final[reference_well_id])

plt.plot(absorbances[:, 1], absorbances[:, 2], 'o-')
plt.plot(absorbances[:, 1], absorbances[:, 0], 'o-')

plt.show()


concentrations = np.delete(np.copy(absorbances[:, 1]), reference_well_id, axis=0)
np.save(misc_folder + 'product_concentrations.npy', concentrations)


# # AUTOREAD EXPOSURE FROM EXIF FILE PROPERTIES
# import glob, os
# os.chdir(experiment_folder)
# file_list = []
# for file in glob.glob("*.TIF"):
#     print(file)
#     file_list.append(file)
#
# import exifread
#
# filename = experiment_folder + file_list[0]
#
# image = open(filename, 'rb')
# exif = exifread.process_file(image)
# exposure = exif['EXIF ExposureTime']
# exposure = exposure.values[0].num / exposure.values[0].den
# print(exposure)
#
# # IMPORT TIF
# import tifffile as tiff
# img = tiff.imread(experiment_folder + file_list[0])
# img = img.astype(float) / exposure
# plt.imshow(img[:, :, 0])
# plt.colorbar()
# plt.show()

