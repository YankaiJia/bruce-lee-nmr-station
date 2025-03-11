from matplotlib import pyplot as plt

import tkinter as tk
from tkinter import filedialog

def plot1():
  ys_ori = {
  0:'92.03727024121508',
  1:'44.85000344605123',
  2:'21.30438829283912',
  3:'9.689694961722125',
  4:'4.404170234225603'}

  ys = [float(value) for key, value in ys_ori.items()]
  print(ys)

  xs_init = 152.4
  xs = [xs_init, xs_init/2, xs_init/4, xs_init/8, xs_init/16 ]

  yb_ori =  {0:'58.26061628299067',
  1:'29.7097988122041',
  2:'14.252173271263246',
  3:'6.550650316834435',
  4:'2.1064971663290635'}

  yb = [float(value) for key, value in yb_ori.items()]
  xb_init = 252.1
  xb = [xb_init,xb_init/2,xb_init/4,xb_init/8,xb_init/16 ]

  # plt.plot(xs, ys,'o', ls = '-')
  # plt.plot(xb, yb, 'o', ls = '-')

  # plt.xscale('log')  # Set the x-axis to logarithmic scale
  # plt.plot()
  # plt.show()


def plot2():
  import pandas as pd
  # plot csv
  path ="D:\\Dropbox\\brucelee\\data\\DPE_bromination\\_Refs\\ref_B_TEST\\205244-1D EXTENDED+-B1\\data.csv"

  df = pd.read_csv(path)
  print(df.head())
  plt.plot(df['x'], df['y'], 'o', ls = '-')
  plt.plot()
  plt.show()


def ask_folder_path():

  # Create a root window and hide it
  root = tk.Tk()
  root.withdraw()
  # Ask the user to select a folder
  folder_path = filedialog.askdirectory(title="Select a Folder")
  # Print the selected folder path
  if folder_path:
    print(f"Selected folder: {folder_path}")
  else:
    print("No folder selected")
  return folder_path

def arrange_folder_name():
  folder = ask_folder_path()
  print(folder)

  # get all the subfolders
  import os
  subfolders = [f.path for f in os.scandir(folder) if f.is_dir()]
  subfolders = [f for f in subfolders if '1D' in f]

  # rename the subfolders
  for subfolder in subfolders:
    file_path = os.path.join(subfolder, 'data.1d')
    if os.path.exists(file_path):
      # print(f"File does exist: {file_path}")
      # get modification time of the folder
      mod_time = os.path.getmtime(file_path)
      # get the date in the format yymmdd-hhmmss
      import datetime
      import time
      # date = time.strftime('%y%m%d-%H%M%S', time.localtime(mod_time))
      date = time.strftime('%y%m%d', time.localtime(mod_time))
      print(f"Date: {date}")
      ls = subfolder.split("Results\\")[-1].split('-')
      # print(ls)
      new_name = subfolder.split("Results")[0]+'/Results/'+'-'.join([str(int(ls[2])).zfill(2), ls[1], str(date), ls[0]])
      # new_name = subfolder.replace('1D', '1D EXTENDED')
      print(f"New name: {new_name}")
      os.rename(subfolder, new_name)

def rename_folder():
  # add the sring "bad_shiming" to each of the subfolders
  folder = ask_folder_path()
  print(folder)
  folder = folder + '/Results/bad_shimming_data'

  # get all the subfolders
  import os
  subfolders = [f.path for f in os.scandir(folder) if f.is_dir()]
  subfolders = [f for f in subfolders if '1D' in f]

  # rename the subfolders
  for subfolder in subfolders:
    new_name = subfolder + '_bad_shimming'
    print(f"New name: {new_name}")
    os.rename(subfolder, new_name)

rename_folder()