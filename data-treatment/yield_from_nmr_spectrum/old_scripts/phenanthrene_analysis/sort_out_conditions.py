import os
from pathlib import Path
import pandas as pd

"""This module is for renaming of the folders so that it including the global index information."""

root_dir = r'D:\Dropbox\brucelee\data\DPE_bromination\2025-11-10-phenanthrene_results'

# get all subfolders if the str 'WS-Phen' is in the folder path
spectrum_folder_path = [d for d in Path(root_dir).iterdir() if d.is_dir() and "WS-Phen" in str(d)]

excel1 = root_dir + r'\2025-11-09-run01.xlsx'
excel2 = root_dir + r'\2025-11-09-run02.xlsx'
excel3 = root_dir + r'\2025-11-09-run03.xlsx'

df1 = pd.read_excel(excel1)
df2 = pd.read_excel(excel2)
df3 = pd.read_excel(excel3)

df1 = df1[['local_index', 'global_index']]
df2 = df2[['local_index', 'global_index']]
df3 = df3[['local_index', 'global_index']]

df1['run_id'] = ['run01'] * len(df1)
df2['run_id'] = ['run02'] * len(df2)
df3['run_id'] = ['run03'] * len(df3)

df_all = pd.concat([df1, df2, df3], ignore_index=True, sort=False)

for idx, row in df_all.iterrows():
    # print(idx, row)
    for path in spectrum_folder_path:
        local_index = int(str(path).split('-')[-1])
        if (row['run_id'] in str(path)) and (row['local_index'] == local_index):
            if 'global_index' not in str(path):
                # print(f'mathing here: {path}')
                # rename by staring with global_index_xx
                new_folder_name = f"global_index_{row['global_index']}_" + path.name
                print(new_folder_name)
                new_path = path.parent / new_folder_name
                print(path)
                print(new_path)
                os.rename(path, new_path)
            else:
                print(f'global_index is already in the folder path: {path}')






