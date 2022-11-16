from astropy.io import fits
import matplotlib.pyplot as plt
import numpy as np

fits_image_filename = 'D:\\Docs\\Science\\UNIST\\Projects\\robochem\\data\\multicomp-reactions\\2022-11-07-run01\\' \
                      'vis-photos\\color_testing\\FITS\\NNN_1981_0004.FIT'

def load_fits_image(fits_image_filename):
    image = fits.open(fits_image_filename)[0].data
    image_with_channels_as_last_axis = np.stack([image[i, :, :] for i in range(image.shape[0])], axis=2)
    return image_with_channels_as_last_axis

image = load_fits_image(fits_image_filename)#[4100:4220, 2825:3000, :]
plt.imshow(image[:, :, 1])
plt.show()

exposures = [1/x for x in [400, 200, 100, 50, 25, 25]]
means = []
for file_id in range(1, 7, 1):
    fits_image_filename = 'D:\\Docs\\Science\\UNIST\\Projects\\robochem\\data\\multicomp-reactions\\2022-11-07-run01\\' \
                          'vis-photos\\color_testing\\FITS\\NNN_1981_{0:04d}.FIT'.format(file_id)
    image = load_fits_image(fits_image_filename)[4100:4220, 2825:3000, :]
    means.append(np.mean(image[:, :], axis=(0, 1)))
means = np.array(means)
for i in range(3):
    plt.plot(exposures, means[:, i], 'o-')
plt.show()
