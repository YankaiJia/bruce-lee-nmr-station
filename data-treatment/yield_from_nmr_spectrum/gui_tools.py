# use tkinter to creat a window to ask user to select the folder and return the path
import tkinter as tk
from tkinter import filedialog
import os

def select_folder():

    root = tk.Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory(title='Select the "brucelee" directory')
    return folder_selected

if __name__ == "__main__":
    data_dir = select_folder()
    print(data_dir)