import numpy as np
from mayavi import mlab


x, y, z = np.ogrid[-5:5:64j, -5:5:64j, -5:5:64j]

k = 0.7
scalars = x * x * 0.5 + (y+k*x) * (y+k*x) + z * z * 2.0

mlab.contour3d(scalars, contours=[9.6], opacity=0.5,
                                  colormap='summer')
obj = mlab.volume_slice(scalars, plane_orientation='x_axes')

mlab.show()
