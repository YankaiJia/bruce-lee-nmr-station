import numpy as np
from dataclasses import dataclass
import matplotlib.pyplot as plt
import  pandas as pd

excel_filename = '20230203RFcalibration_spec.xlsx'
df = pd.read_excel(excel_filename, sheet_name='Sheet1', usecols='A:J')

# define a data class for storage of compound
@dataclass
class CompoundForCalibartion():

    shortname: str
    fullname: str
    date_source: str
    date_now: str
    bottle_id: str
    stock_concentration: float
    solvent: str
    max_concentration: float
    min_concentration: float
    volume_for_each_point: float = 0.5 # unit in mL
    num_of_calibration_dot: int = 20
    is_background: bool = True



def compound_list_from_dataframe(df = df) -> list:
    compound_list = []
    # print(df)
    for i in range(len(df.index)):
        compound = CompoundForCalibartion(
                    shortname = df.loc[i]['shortname'],
                    fullname = df.loc[i]['fullname'],
                    date_source  = df.loc[i]['date_source'],
                    date_now  = df.loc[i]['date_now'],
                    bottle_id = df.loc[i]['bottle_id'],
                    stock_concentration = df.loc[i]['stock_concentration_[mol/l]'],
                    solvent = df.loc[i]['solvent'],
                    max_concentration = df.loc[i]['max_concentration'],
                    min_concentration = df.loc[i]['min_concentration']
        )
        compound_list.append(compound)
    return compound_list

def build_df_from_compound_list(compound_list = compound_list_from_dataframe(),
                                         points_in_first_part=[10, 3, 10, 10],
                                         points_in_second_part=[4, 3, 4, 4],
                                         cut_off_percentage=0.6,
                                         total_volume_in_bottle=500,
                                         number_of_bottles_per_plate=54):

    shortnames_of_all_compounds = [compound.shortname for compound in compound_list]
    assert len(points_in_first_part) == len(shortnames_of_all_compounds)
    assert len(points_in_second_part) == len(shortnames_of_all_compounds)
    list_of_rows = []
    composition_id = 0
    for compound_index, compound in enumerate(compound_list):
        arr1 = list(np.linspace(start = compound.max_concentration, stop =compound.max_concentration * cut_off_percentage,
                                num =points_in_first_part[compound_index], dtype= float))
        arr2 = list(np.geomspace(start = compound.max_concentration * (1 - cut_off_percentage),
                                stop = compound.min_concentration,
                                num =points_in_second_part[compound_index], dtype= float))
        list_of_concentrations_in_bottles = arr1 + arr2
        if compound.is_background:
            list_of_concentrations_in_bottles.append(0)
        dictionary_template = {'shortname':compound.shortname,
                               'fullname':compound.fullname,
                               'date_source':compound.date_source,
                               'solvent':compound.solvent,
                               'concentration':0,
                               'bottle_id':0,
                               'plate_id':0,
                               f'{compound.solvent}':0}
        for shortname in shortnames_of_all_compounds:
            dictionary_template[shortname] = 0

        for concentration in list_of_concentrations_in_bottles:
            dictionary_for_this_row = dictionary_template.copy()
            dictionary_for_this_row['concentration'] = concentration
            dictionary_for_this_row['bottle_id'] = composition_id % number_of_bottles_per_plate
            dictionary_for_this_row['plate_id'] = composition_id // number_of_bottles_per_plate
            volume_of_compound_to_be_pipetted = total_volume_in_bottle * concentration / compound.stock_concentration
            volume_of_solvent_to_be_pipetted = total_volume_in_bottle - volume_of_compound_to_be_pipetted
            dictionary_for_this_row[compound.shortname] = volume_of_compound_to_be_pipetted
            dictionary_for_this_row[compound.solvent] = volume_of_solvent_to_be_pipetted
            list_of_rows.append(dictionary_for_this_row.copy())
            composition_id += 1

        df_output = pd.DataFrame(list_of_rows)
        print(df.sum(axis = 0))

    print(f'Total volumes that will be needed:\n {df_output.sum(axis=0)[-len(shortnames_of_all_compounds)-1:]}')
    df_output.to_csv('calibration_uvvis\\df_output.csv')
    return df_output

def plot_calibration_dots():
    list = build_df_from_compound_list
    plt.plot(list[0] , marker = 'o')
    plt.plot(list[1], marker = '*')
    plt.show()

def main():
    # assembly_compund_list()
    # geom_space()
    # plot_calibration_dots()
    pp = build_df_from_compound_list()


if __name__ == "__main__":
    main()