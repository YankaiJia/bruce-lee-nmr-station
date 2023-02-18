import matplotlib.pyplot as plt
import json
import numpy as np
import statistics

with open('../data/Weighted_values_for_calibration_index21_1000ul.json') as json_file:
    liquid_class_table_para = json.load(json_file)

# for i in liquid_class_table_para:
#     liquid_class_table_para[i]['volume'] = [i /0.888 for i in liquid_class_table_para[i]['data']]
#     liquid_class_table_para[i]['avg'] = sum([i /0.888 for i in liquid_class_table_para[i]['data']]) / len([i /0.888 for i in liquid_class_table_para[i]['data']])
#     liquid_class_table_para[i]['std'] = statistics.stdev([i /0.888 for i in liquid_class_table_para[i]['data']])
#     print([i /0.888 for i in liquid_class_table_para[i]['data']])

# with open('data/Weighted_values_for_calibration_index25_1000ul.json', 'w', encoding='utf-8') as f:
#     json.dump(liquid_class_table_para, f, ensure_ascii=False, indent=4)

def ast(weighted_values= liquid_class_table_para):

    target_volume = []
    dispensed_volume = []
    std = []
    for i in liquid_class_table_para:
        print(i)
        print(i[:-2])
        target_volume.append(int(i[:-2]))
        dispensed_volume.append(liquid_class_table_para[i]['avg'])
        std.append(liquid_class_table_para[i]['std'])
    print(target_volume)
    print(dispensed_volume)
    print(std)

    plt.errorbar(target_volume, dispensed_volume, std, linestyle = 'None', marker = '^',  capsize=4, elinewidth=2, markersize = 6)
    plt.plot(target_volume,target_volume, marker = '.', markersize = 6)
    plt.xlabel("Target volume (uL) ")
    plt.ylabel("Dispensed volume (uL)")

    plt.savefig( 'data/index_21.jpg', dpi = 1200)
    # plt.ylim(190, 210)
    plt.show()

    return "done!"

ast()
