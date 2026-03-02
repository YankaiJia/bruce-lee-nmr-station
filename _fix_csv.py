import pandas as pd
import glob

files = glob.glob("data/**/out_concentrations.csv", recursive=True)
fixed, skipped = [], []

for f in files:
    df = pd.read_csv(f)
    first_col = df.columns[0]
    if str(first_col).startswith("Unnamed") or first_col == "":
        df.rename(columns={first_col: "global_index"}, inplace=True)
        df.to_csv(f, index=False)
        fixed.append(f)
    else:
        skipped.append((f, first_col))

print(f"Fixed: {len(fixed)}, Skipped: {len(skipped)}")
for f in fixed:
    print("  FIXED:", f)
for f, c in skipped:
    print(f"  OK [{c}]:", f)
