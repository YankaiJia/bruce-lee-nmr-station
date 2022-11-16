import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

data_folder = 'D:\\Docs\\Science\\UNIST\\Projects\\robochem\\data\\'
experiment_folder = data_folder + 'multicomp-reactions\\2022-11-07-run01\\'
compositions_file = experiment_folder + 'input_compositions\\compositions.xlsx'
df = pd.read_excel(compositions_file, usecols='B,C,D,E')
df_one_plate = df.head(53)

product_concentrations = np.load(experiment_folder + 'vis-photos\\plate_1\\misc\\product_concentrations.npy')
df_one_plate['product'] = product_concentrations.tolist()
df_one_plate.to_excel(experiment_folder + 'results/output_excel.xlsx')



