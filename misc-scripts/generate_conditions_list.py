import shortuuid
import pandas as pd
import numpy as np

excel_template = 'D:/Docs/Dropbox/robochem/data/BPRF/2024-03-04-run01/misc/2024-03-04-template.xlsx'
output_excel_file = 'D:/Docs/Dropbox/robochem/data/BPRF/2024-03-04-run01/2024-03-04-run01.xlsx'

# open first worksheet from excel, foll columns with numbers and save back to the same excel file
df = pd.read_excel(excel_template, sheet_name=0)

# add 54*6 new rows with same values in all columns
for i in range(54*6-1):
    df = df.append(df.iloc[0], ignore_index=True)

# change the values of the 'plate_barcode' column to i + 20
for i in range(6):
    for j in range(54):
        df.loc[i*54+j, 'plate_barcode'] = i + 20
        df.loc[i * 54 + j, 'plate_barcodes_for_dilution'] = i + 30
        df.loc[i * 54 + j, 'plate_barcodes_for_dilution_2'] = i + 40

# copy index values to "local_index' and 'global_index' column
df['local_index'] = df.index
df['global_index'] = df.index

# fill column 'uuid' with shortuuid.uuid()
df['uuid'] = df['uuid'].apply(lambda x: shortuuid.uuid())


colname_x = 'vol#methoxybenzaldehyde'
colname_y = 'vol#ethyl_acetoacetate'
colname_z = 'vol#ammonium_acetate'
colname_ethanol = 'vol#Ethanol'
row_indexer = 0
randomized_list_of_rows = np.random.permutation(df.index)
for xs in np.linspace(15, 150, 18):
    for ys in np.linspace(15, 150, 18):
        row_index_here = randomized_list_of_rows[row_indexer]
        df.loc[row_index_here, colname_x] = xs
        df.loc[row_index_here, colname_y] = ys
        df.loc[row_index_here, colname_z] = 150
        df.loc[row_index_here, 'global_index'] = row_indexer
        ethanol = 500 - xs - ys - 150
        df.loc[row_index_here, colname_ethanol] = ethanol
        row_indexer += 1


# save to the same excel file, to the
df.to_excel(output_excel_file, index=False)