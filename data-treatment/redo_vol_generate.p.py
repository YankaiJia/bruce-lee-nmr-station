import re
import pandas as pd

entries = [
    r"D:\Dropbox\brucelee\data\DPE_bromination\2025-02-19-run02_normal_run\Results\15-1D EXTENDED+-250227-205458",
    r"D:\Dropbox\brucelee\data\DPE_bromination\2025-03-03-run01_normal_run\Results\ 0-1D EXTENDED+-20250304-133718",
    r"D:\Dropbox\brucelee\data\DPE_bromination\2025-03-03-run01_normal_run\Results\ 32-1D EXTENDED+-20250304-171713",
    r"D:\Dropbox\brucelee\data\DPE_bromination\2025-03-03-run01_normal_run\Results\ 34-1D EXTENDED+-20250304-173002",
    r"D:\Dropbox\brucelee\data\DPE_bromination\2025-03-03-run01_normal_run\Results\ 40-1D EXTENDED+-20250304-181232",
    r"D:\Dropbox\brucelee\data\DPE_bromination\2025-03-03-run02_normal_run\Results\ 30-1D EXTENDED+-20250305-003728",
    r"D:\Dropbox\brucelee\data\DPE_bromination\2025-03-03-run02_normal_run\Results\ 33-1D EXTENDED+-20250305-005641",
    r"D:\Dropbox\brucelee\data\DPE_bromination\2025-03-05-run01_normal_run\Results\ 10-1D EXTENDED+-20250306-213536",
    r"D:\Dropbox\brucelee\data\DPE_bromination\2025-03-05-run01_normal_run\Results\ 23-1D EXTENDED+-20250306-230259",
    r"D:\Dropbox\brucelee\data\DPE_bromination\2025-03-05-run01_normal_run\Results\ 45-1D EXTENDED+-20250307-014127",
    r"D:\Dropbox\brucelee\data\DPE_bromination\2025-03-12-run01_better_shimming\Results\ 2-1D EXTENDED+-20250313-152853",
    r"D:\Dropbox\brucelee\data\DPE_bromination\2025-03-12-run01_better_shimming\Results\ 8-1D EXTENDED+-20250313-161133",
    r"D:\Dropbox\brucelee\data\DPE_bromination\2025-03-12-run01_better_shimming\Results\ 40-1D EXTENDED+-20250313-205448",
    r"D:\Dropbox\brucelee\data\DPE_bromination\2025-03-12-run01_better_shimming\Results\ 43-1D EXTENDED+-20250313-211803"
]
run_names = [ entry.split("Results\\")[0] for entry in entries ]
excel_names = [
    '2025-02-19-run02.xlsx',
    '2025-03-03-run01.xlsx',
    '2025-03-03-run01.xlsx',
    '2025-03-03-run01.xlsx',
    '2025-03-03-run01.xlsx',
    '2025-03-03-run02.xlsx',
    '2025-03-03-run02.xlsx',
    '2025-03-05-run01.xlsx',
    '2025-03-05-run01.xlsx',
    '2025-03-05-run01.xlsx',
    '2025-03-12-run01.xlsx',
    '2025-03-12-run01.xlsx',
    '2025-03-12-run01.xlsx',
    '2025-03-12-run01.xlsx'
]

excels = [a+"\\"+b for a, b in zip(run_names, excel_names)]
print(excels)
vial_ids = []

# in each of the entries, get the number before "-1D EXTENDED"
for i, entry in enumerate(entries):
    match = re.search(r'(\d+)-1D EXTENDED', entry)
    if match:
        number = match.group(1)
        vial_ids.append(number)
    else:
        print(f"Entry {i+1}: No match found")

df_out = pd.DataFrame()

for i in range(len(entries)):
    # read the excel into pd
    df = pd.read_excel(excels[i])
    # print(df.head())
    index = vial_ids[i]
    # get the row where the local index matches the index
    row = df[df['local_index'] == int(index)]
    print(row)
    # append the row to df_out
    if not row.empty:
        df_out = pd.concat([df_out, row], ignore_index=True)
    else:
        print(f"No data found for local index {index} in {excels[i]}")

# save df_out to a new excel file
output_file = r"D:\Dropbox\brucelee\data\DPE_bromination\redo_vol_generate.xlsx"
df_out.to_excel(output_file, index=False)
