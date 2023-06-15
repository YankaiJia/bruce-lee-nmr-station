import csv
import PySimpleGUI as sg

# use pysimplegui to get the fil path
csv_path = sg.popup_get_folder('file path', no_window=True)


with open(csv_path + '/out_volumes.csv', 'r') as input_file:
    reader = csv.reader(input_file)
    data = list(reader)

with open(csv_path + '/out_volumes_treated.csv', 'w', newline='') as output_file:
    writer = csv.writer(output_file)
    for i in range(len(data)):
        writer.writerow(data[i])
        if i % 9 == 8:
            for i in range(9):
                writer.writerow(['0'] * len(data[i]))