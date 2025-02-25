
import nmrglue as ng
import numpy as np
import matplotlib.pyplot as plt
# load nmr raw data from a spectrum
spectrum = "C:/vscode_projects/brucelee/bruce-nmr-station/data-treatment/yield_from_nmr_spectrum"
dic,data = ng.spinsolve.read(spectrum + '/acqu.par')
# read csv file by numpy
data = np.loadtxt(spectrum + '/data.csv', delimiter=',')
print(data)