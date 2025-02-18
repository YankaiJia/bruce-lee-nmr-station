import itertools as it
import numpy as np
import pandas as pd
import re
import tkinter as tk
from tkinter import filedialog

# minimum volume that can be preciously measure by the robot
min_pipettable_volume = 10

# how many times the stock solution will be diluted
DILUTION = 10
convert_uL_to_L = 0.000001



def get_folder():
    tk.Tk().withdraw()
    return filedialog.askdirectory(title="Select a Folder")

data_path = get_folder()
print(f'data_path: {data_path}')

# data_path = 'C:\\Users\\shing\\Dropbox\\robochem\\data\\DPE_bromination\\2025-01-23-run01\\OutVandC\\'

def add_columns_where_volumes_are_too_small(input_df, num, dilution_factor=DILUTION, lowest_pipettable_volume=min_pipettable_volume):
    for column in input_df.columns:
        if any(input_df[column].between(0, lowest_pipettable_volume, inclusive='neither')):
            indices_where_volume_is_too_small = input_df[column].between(0, lowest_pipettable_volume, inclusive='neither')
            new_column_name = column.split('_dil')[0] + f'_dil_x_{dilution_factor ** (num+1)}'
            input_df[new_column_name] = 0
            input_df.loc[indices_where_volume_is_too_small, [new_column_name]] = input_df[column] * dilution_factor
            input_df.loc[indices_where_volume_is_too_small, [column]] = 0
    return input_df


def add_diluted_stocks_until_volumes_are_above_limit(volumes_df, list_of_dilution_factors=None,
                                                     lowest_pipettable_volume=min_pipettable_volume, dilution_factor=DILUTION):
    if list_of_dilution_factors is None:
        list_of_dilution_factors = [dilution_factor] * 3

    for num, dilution_factor in enumerate(list_of_dilution_factors):
        volumes_df = add_columns_where_volumes_are_too_small(input_df=volumes_df, dilution_factor=dilution_factor,
                                                             lowest_pipettable_volume=lowest_pipettable_volume, num = num)
        if not any([any(volumes_df[col].between(0, min_pipettable_volume, inclusive='neither')) for col in volumes_df.columns]):
            break

    was_successful = not any([any(volumes_df[col].between(0, min_pipettable_volume, inclusive='neither')) for col in volumes_df.columns])
    return volumes_df, was_successful

def check_if_solvent_volume_is_not_negative_and_greater_than_pipettable_limit(solvent_df, min_pipettable_volume):
    was_successful1 = not any([any(solvent_df[column].between(0, min_pipettable_volume, inclusive='neither')) for column in solvent_df.columns]) and not any([any(solvent_df[column] < 0) for column in solvent_df.columns])

    return  was_successful1
excel_template = pd.read_csv( data_path + "/Volumestemplate.csv" )



list_all = [
    list(np.linspace(start=excel_template.iloc[row_id, 2],
                   stop=excel_template.iloc[row_id, 3],
                   num=excel_template.iloc[row_id, 4],
                   endpoint=True))
    for row_id in excel_template.index]
cart_product = np.array(list(it.product(*list_all, repeat=1)))

def calculate_dilution_vector(list_of_names):
    dilution_vector=[]
    for item in list_of_names:
        match = re.search(r'_dil_x_([0-9]*\.?[0-9]+)$', item)
        if match:
            dilution_vector.append(float(item.split("_dil_x_")[1]))
        else:
            dilution_vector.append(1)
    return dilution_vector
def create_the_list_with_substrates_names(list_of_names):
    list_with_names_of_substrates=[]
    for item in list_of_names:
        match = re.search(r'_dil_x_', item)
        if match:
            list_with_names_of_substrates.append(item.split("_dil_x_")[0])
        else:
            list_with_names_of_substrates.append(item)
    return list_with_names_of_substrates
def calculate_the_list_with_stock_solutions_concentrations(stock_solutions_max_concentration_df, list_with_names_of_substrates):
    list_with_molar_concentrations=[]
    for name in list_with_names_of_substrates:
        if name in stock_solutions_max_concentration_df.columns:
            list_with_molar_concentrations.append(float(stock_solutions_max_concentration_df[name].values[0]))
        else:
            list_with_molar_concentrations.append(0)
    return list_with_molar_concentrations

def calculate_the_amount_of_material_nessesery_for_reactions(molecular_mas_df, list_with_names_of_substrates):
    list_of_molecular_weight = []
    for name in list_with_names_of_substrates:
        if name in molecular_mas_df.columns:
            list_of_molecular_weight.append(float(molecular_mas_df[name].values[0]))
        else:
            list_of_molecular_weight.append(0)
    return list_of_molecular_weight

# conc_df unit [mol/L]
concentrations_df = pd.DataFrame(data=cart_product, columns=excel_template['short_name'])
number_of_moles = concentrations_df * (excel_template.iloc[0, 9])
stock_solutions_max_concentration = list(
    excel_template.iloc[:, 3] * excel_template.iloc[0, 9] / excel_template.iloc[:, 6])
volumes_df = pd.DataFrame((number_of_moles).div(stock_solutions_max_concentration))
volumes_df, is_successful = add_diluted_stocks_until_volumes_are_above_limit(volumes_df=volumes_df,
                                                                             list_of_dilution_factors=[DILUTION] * 5)
solvent_df = pd.DataFrame(data=((volumes_df.sum(axis = 1) - (excel_template.iloc[0, 9])) * [-1]), columns=[excel_template.iloc[0, 8]])
volumes_for_pipetter_df = pd.concat([volumes_df, solvent_df], axis=1)
is_successful1 = check_if_solvent_volume_is_not_negative_and_greater_than_pipettable_limit(solvent_df=solvent_df,
                                                                                 min_pipettable_volume=min_pipettable_volume)
volumes_sum_df = pd.DataFrame(data=volumes_for_pipetter_df.sum(axis=0), dtype=float).transpose()
molecular_mas_df = pd.DataFrame(data=list(excel_template['molecular_weight']), index=excel_template['short_name'], columns=['molecular_weight']).transpose()
stock_solutions_max_concentration_df=pd.DataFrame(stock_solutions_max_concentration, index=[concentrations_df.columns], columns=['C']).transpose()
list_of_names = list(volumes_for_pipetter_df.columns)
dilution_vector = calculate_dilution_vector(list_of_names=list_of_names)
list_with_names_of_substrates = create_the_list_with_substrates_names(list_of_names=list_of_names)
list_with_molar_concentrations = calculate_the_list_with_stock_solutions_concentrations(stock_solutions_max_concentration_df=stock_solutions_max_concentration_df, list_with_names_of_substrates=list_with_names_of_substrates)
list_of_molecular_weight = calculate_the_amount_of_material_nessesery_for_reactions(molecular_mas_df=molecular_mas_df, list_with_names_of_substrates=list_with_names_of_substrates)
stock_solutions_concentration_df=pd.DataFrame(data=list_with_molar_concentrations, index=[volumes_for_pipetter_df.columns]).transpose().div(dilution_vector)
molecular_mass_all_df=pd.DataFrame(data=list_of_molecular_weight, index=[volumes_for_pipetter_df.columns]).transpose()
mass_for_stock_solutions_df= stock_solutions_concentration_df.mul(volumes_sum_df, level=0).mul(molecular_mass_all_df, level=0) * convert_uL_to_L
material_for_reactions_df=pd.concat([molecular_mass_all_df, stock_solutions_concentration_df, molecular_mass_all_df, mass_for_stock_solutions_df], axis=0, ignore_index=True)
material_for_reactions_df.iloc[0]=volumes_sum_df.iloc[0]
mi = ['Volumes_sum_[uL]', 'C_Stock_Solutions_[mol/L]', 'Molecular_Weight_[g/mol]', 'Mass_of_a_Substance_[g]']
material_for_reactions_df['Labels']=mi


def generate_files_from_dfs(data_path, is_random=False):

    volumes_for_pipetter_df.to_csv(data_path + "/out_volumes.csv")
    concentrations_df.to_csv(data_path + "/out_concentrations.csv")

    if is_random:
        volumes_for_pipetter_df_shuffled = volumes_for_pipetter_df.sample(frac=1, random_state=0)
        volumes_for_pipetter_df_shuffled.to_csv(data_path + "/out_volumes_shuffled.csv")


# Move the last column 'Labels' to the first column
material_for_reactions_df = material_for_reactions_df[[material_for_reactions_df.columns[-1]] + list(material_for_reactions_df.columns[:-1])]
material_for_reactions_df.to_csv(data_path + "/out_material.csv")
generate_files_from_dfs(data_path, is_random= True)

print(f'All_substrates_volumes_are_pipettable: {is_successful}')
print(f'You_are_below_total_volume_and_solvent_volume_is_pipettable: {is_successful1}')

















