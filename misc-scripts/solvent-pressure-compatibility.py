import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

data_folder = 'D:\\Docs\\Science\\UNIST\\Projects\\robochem\\data\\'

target_file = data_folder + 'solvent-pressure-compatibility/with-septa.txt'

data = np.loadtxt(target_file, skiprows=2)
with open(target_file) as f:
    first_line = f.readline()
    headers = first_line.split('\t')

data2 = dict()
for i in range(data.shape[0]):
    data2[f'{data[i, 0]:.0f}°'] = [x for x in data[i, 2:]]

# data2 = {'Quantity': [320, 450, 300, 120, 280],
#         'Price': [800, 250, 1200, 150, 300]
#         }
df = pd.DataFrame(data2, columns=data2.keys(), index=headers[2:])

plot = df.plot.barh(figsize=(10, 3), color=['C0', 'C2', 'C1'])
fig = plot.get_figure()
plt.xlim(0, 25)
plt.title('Cap with septa')
plt.ylabel('Solvent')
plt.xlabel('Loss, μL/hour')
plt.tight_layout()
fig.savefig('figures/solvent-pressure-compatibility-with-septa.png')
plt.show()

target_file = data_folder + 'solvent-pressure-compatibility/solid-cap.txt'

data = np.loadtxt(target_file, skiprows=2)
with open(target_file) as f:
    first_line = f.readline()
    headers = first_line.split('\t')

data2 = dict()
for i in range(data.shape[0]):
    data2[f'{data[i, 0]:.0f}°'] = [x for x in data[i, 2:]]

# data2 = {'Quantity': [320, 450, 300, 120, 280],
#         'Price': [800, 250, 1200, 150, 300]
#         }
df = pd.DataFrame(data2, columns=data2.keys(), index=headers[2:])

plot = df.plot.barh(figsize=(10, 3), color=['C0', 'C2', 'C1'])
fig = plot.get_figure()
plt.xlim(0, 25)
plt.title('Solid cap')
plt.ylabel('Solvent')
plt.xlabel('Loss, μL/hour')
plt.tight_layout()
fig.savefig('figures/solvent-pressure-compatibility-solid-cap.png')
plt.show()