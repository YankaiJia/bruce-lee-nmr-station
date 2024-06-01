import pickle
import os
import matplotlib.pyplot as plt

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'
experiment_name = 'multicomp-reactions/2023-03-31-run01/'
with open(data_folder + experiment_name + 'results/unique_cats.pickle', 'rb') as f:
    unique_cats = pickle.load(f)
fig = plt.figure(1)
for i, cat in enumerate(unique_cats):
    text = f'Catalyst (p-Toluenesulfonic acid): {cat*1000:3.1f} mM'
    print(text)
    plt.title(text)
    fig.savefig(f'D:/Docs/Dropbox/robochem/data/multicomp-reactions/2023-03-31-run01/results/title-frames/{i:05d}.png', dpi=300)