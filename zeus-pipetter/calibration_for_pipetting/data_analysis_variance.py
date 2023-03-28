import json
import matplotlib.pyplot as plt
import statistics


def get_volume_dict(path):
   # Load the data from the JSON file
   with open(path) as f:
      data =  json.load(f)

   volume_dict = {}

   for key, value in data.items():
      print(key, value)
      measurement_list = value
      for data_list in measurement_list:
         for key, value in data_list.items():
           volume_dict[key]= value['volume']
   return volume_dict


# path for 50ul tips measurements
path_50ul = 'calibration_results\\calibration_results_2023_03_26_02_13.json'
path_300ul = 'calibration_results\\calibration_results_2023_03_26_15_18.json'

volume_50ul_dict = get_volume_dict(path_50ul)

volume_300ul_dict = get_volume_dict(path_300ul)

for key, value in volume_300ul_dict.items():

   volumes = value[1:]
   volumes_avg = statistics.mean(volumes)
   volumes_std = statistics.stdev(volumes)
   print(f'Average volume for {key} is {volumes_avg} with a standard deviation of {volumes_std}')

   # print(key, value)
   plt.hist(volumes, bins=10, range = (volumes_avg-volumes_std*5, volumes_avg+volumes_std*5))
   plt.xlabel('weight')
   plt.ylabel('Person count')
   plt.legend( loc='upper right', title = key)
   plt.show()
