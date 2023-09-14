import csv

with open('outV_0331.csv', 'r') as input_file:
    reader = csv.reader(input_file)
    data = list(reader)

with open('outV_0331_treated.csv', 'w', newline='') as output_file:
    writer = csv.writer(output_file)
    for i in range(len(data)):
        writer.writerow(data[i])
        if i % 9 == 8:
            for i in range(9):
                writer.writerow(['0'] * len(data[i]))