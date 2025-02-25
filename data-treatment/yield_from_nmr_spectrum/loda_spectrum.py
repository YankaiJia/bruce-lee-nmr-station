
import nmrglue as ng
import numpy as np
import matplotlib.pyplot as plt
# load nmr raw data from a spectrum
spectrum = "C:/vscode_projects/brucelee/bruce-nmr-station/data-treatment/yield_from_nmr_spectrum"
dic,data = ng.spinsolve.read(spectrum)
# plot the spectrum
plt.plot(data)
plt.show()
# calculate the integral of the spectrum
integral = np.sum(data)
print("integral of the spectrum: ", integral)
# calculate the yield of the spectrum
yield_ = integral / 1000
print("yield of the spectrum: ", yield_)