import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
from itertools import product
from pathlib import Path
import csv
import random
import math

# -------- Config --------
MAX_ROWS_FOR_SHUFFLE = 2_000_000
BASE_ROW = 1  # Shift all UI rows down to make room for banner

# -------- Helpers --------
def parse_input(text, allow_empty=False):
    txt = text.strip()
    if not txt:
        if allow_empty:
            return []
        messagebox.showerror("Invalid Input", "Input cannot be empty.")
        return None
    try:
        return [float(x.strip()) for x in txt.split(',')]
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter valid numbers separated by commas.")
        return None

def active_lists():
    list_a = parse_input(entry_a.get())
    list_b = parse_input(entry_b.get())
    list_c = parse_input(entry_c.get())
    if list_a is None or list_b is None or list_c is None:
        return None, None

    list_d = parse_input(entry_d.get(), allow_empty=True)
    if list_d is None:
        return None, None

    if len(list_d) == 0:
        lists = [list_a, list_b, list_c]
        labels = ["a", "b", "c"]
    else:
        lists = [list_a, list_b, list_c, list_d]
        labels = ["a", "b", "c", "d"]

    for idx, L in enumerate(lists):
        if len(L) == 0:
            messagebox.showerror("Invalid Input", f"List {labels[idx]} is empty after parsing.")
            return None, None

    return lists, labels

def count_total(lists):
    return math.prod(len(L) for L in lists)

def preview_results(lists, limit=10):
    out_lines = []
    for i, tup in enumerate(product(*lists)):
        if i >= limit:
            break
        out_lines.append(str(tup))
    return "\n".join(out_lines)

# -------- Actions --------
def compute_product():
    lists, labels = active_lists()
    if lists is None:
        return
    total = count_total(lists)
    output_box.delete('1.0', tk.END)
    dims = " × ".join(f"{lab}({len(L)})" for lab, L in zip(labels, lists))
    output_box.insert(tk.END, f"Dimensions: {dims}\n")
    output_box.insert(tk.END, f"Total combinations: {total}\n\n")
    output_box.insert(tk.END, "First 10 results (preview):\n")
    output_box.insert(tk.END, preview_results(lists, limit=10))

def save_two_csvs():
    lists, labels = active_lists()
    if lists is None:
        return
    total = count_total(lists)
    if total == 0:
        messagebox.showerror("No Data", "No combinations to save.")
        return

    base_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        title="Save ordered grid product CSV"
    )
    if not base_path:
        return

    base_path = Path(base_path)
    shuffled_path = base_path.with_name(f"{base_path.stem}_shuffled{base_path.suffix}")
    rows = list(product(*lists))

    try:
        with base_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(labels)
            writer.writerows(rows)
    except Exception as e:
        messagebox.showerror("Save Error", f"Could not save ordered CSV:\n{e}")
        return

    if total > MAX_ROWS_FOR_SHUFFLE:
        proceed = messagebox.askyesno(
            "Large Shuffle",
            f"About to shuffle {total:,} rows in memory.\n\nContinue?"
        )
        if not proceed:
            messagebox.showinfo(
                "Saved Ordered Only",
                f"Saved ordered CSV only:\n{base_path}\n\nShuffled file skipped."
            )
            return

    try:
        shuffled_rows = rows[:]
        random.shuffle(shuffled_rows)
        with shuffled_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(labels)
            writer.writerows(shuffled_rows)
    except Exception as e:
        messagebox.showerror("Save Error", f"Could not save shuffled CSV:\n{e}")
        return

    messagebox.showinfo(
        "Saved",
        f"Saved {total} rows to:\n\n"
        f"1) {base_path}\n"
        f"2) {shuffled_path} (randomized order)"
    )

# -------- UI --------
root = tk.Tk()
root.title("Grid Product → CSV (3D/4D, Ordered + Shuffled)")

# Banner
explanation = (
    "A tool for the grid sampling of hyperspace, supporting 3 or 4 axes.\n"
    "\n"
    "Input: 3 or 4 lists of the parameters you want to sample\n"
    "Output: CSV files of ordered and shuffled grids\n"
    "Made by Yankai Jia"
)
tk.Label(
    root,
    text=explanation,
    justify="left",
    font=("Arial", 10, "bold"),
    fg="gray25",
    padx=10
).grid(row=0, column=0, columnspan=2, sticky="w", pady=(10, 6))

# Input fields (shifted by BASE_ROW)
tk.Label(root, text="List a (e.g., 1,2,3,4):").grid(row=BASE_ROW + 0, column=0, sticky='w', padx=6)
entry_a = tk.Entry(root, width=60)
entry_a.grid(row=BASE_ROW + 0, column=1, padx=6, pady=2)

tk.Label(root, text="List b (e.g., 0,1.25,2.5,3.75):").grid(row=BASE_ROW + 1, column=0, sticky='w', padx=6)
entry_b = tk.Entry(root, width=60)
entry_b.grid(row=BASE_ROW + 1, column=1, padx=6, pady=2)

tk.Label(root, text="List c (e.g., 0,0.016,0.033,0.05):").grid(row=BASE_ROW + 2, column=0, sticky='w', padx=6)
entry_c = tk.Entry(root, width=60)
entry_c.grid(row=BASE_ROW + 2, column=1, padx=6, pady=2)

tk.Label(root, text="List d (optional, leave blank to ignore):").grid(row=BASE_ROW + 3, column=0, sticky='w', padx=6)
entry_d = tk.Entry(root, width=60)
entry_d.grid(row=BASE_ROW + 3, column=1, padx=6, pady=2)

# Buttons
btn_frame = tk.Frame(root)
btn_frame.grid(row=BASE_ROW + 4, column=0, columnspan=2, pady=8)
tk.Button(btn_frame, text="Preview & Count", command=compute_product).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="Save Two CSVs (Ordered + Shuffled)", command=save_two_csvs).pack(side=tk.LEFT, padx=5)

# Output area
output_box = scrolledtext.ScrolledText(root, width=90, height=18)
output_box.grid(row=BASE_ROW + 5, column=0, columnspan=2, padx=6, pady=(0, 10))

# Prefill example
entry_a.insert(0, "1,2,3,4")
entry_b.insert(0, "0,1.25,2.5,3.75,5,6.25,7.5")
entry_c.insert(0, "0,0.016,0.033,0.05,0.066,0.083,0.1,0.15")
entry_d.insert(0, "")  # optional

root.mainloop()
