import importlib
import logging
import os
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.ticker as mtick
from scipy.optimize import curve_fit, brentq
from scipy import interpolate

organize_run_results = importlib.import_module("misc-scripts.organize_run_results")
avs = importlib.import_module("visualize-results.animated_viewer_static")
data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'

dioxane_density = 1.034  # g/mL
dioxane_molar_mass = 88.11  # g/mol
water_molar_mass = 18.01528  # g/mol
hbr_molar_mass = 80.9119  # g/mol
acetic_acid_molar_mass = 60.05  # g/mol

def make_interpolator_of_hbr_activity(do_plot=True):
    if do_plot:
        fig2 = plt.figure(2)
    df = pd.read_csv('misc-scripts/activity_data/hbr-water-dioxane/mussini-et-al-1971-electroanalchem.csv')

    interp_dict = dict()
    for i, row in df.iterrows():
        molality = row['molality']
        xs = [int(x) for x in df.columns[1:]]
        ys = np.array(row[1:])
        if do_plot:
            plt.plot(xs, ys, 'o', label=f'{molality} mol/kg')

        def custom_fit_func(x, a, b, c, d, e):
            return a + b / (1 + np.exp(-1 * c * (x - d))) + e * x

        def produce_fit(x, y):
            lower_bounds = [-np.inf] * 5
            upper_bounds = [np.inf] * 5
            upper_bounds[4] = 0
            upper_bounds[0] = 1
            lower_bounds[0] = 0
            # upper_bounds[1] = 2
            popt, pcov = curve_fit(custom_fit_func, x, y, p0=[0, 1, 1 / 20, 70, 0], bounds=(lower_bounds, upper_bounds),
                                   maxfev=100000)
            best_f = lambda x: custom_fit_func(x, *popt)
            return best_f

        best_f = produce_fit(xs, ys)
        interp_dict[molality] = best_f
        xs2 = np.linspace(0, 100, 100)
        ys_fit = best_f(xs2)
        if do_plot:
            # plt.scatter(xs, ys)
            plt.plot(xs2, ys_fit, color='grey', linestyle='--')
            plt.ylim(0, 1)
            # plt.show()

    if do_plot:
        plt.xlabel('Dioxane mass fraction')
        plt.ylabel('HBr molal activity coefficient')
        plt.legend()
        plt.show()

    dio_mass_fracts = np.linspace(0, 100, 100)
    hbr_molalities = np.linspace(0, 1.2, 500)

    xx, yy = np.meshgrid(dio_mass_fracts, hbr_molalities)
    zz = np.zeros_like(xx)

    for i, dio_mass_frac in enumerate(dio_mass_fracts):
        ms = []
        acts = []
        for molality in interp_dict.keys():
            best_f = interp_dict[molality]
            ms.append(molality)
            acts.append(best_f(dio_mass_frac))
        if do_plot:
            plt.plot(ms, acts, 'o', label=f'{dio_mass_frac:.2f}% dioxane')

        # def custom_fit_func_2(x, a, b, c):
        #     return a + b*np.exp(-1 * c * x)

        def custom_fit_func_2(x, a, b, c):
            return a + b / (c + x)

        def produce_fit_2(x, y):
            lower_bounds = [-np.inf] * 3
            upper_bounds = [np.inf] * 3

            # upper_bounds[1] = 2
            # p0 = [0, 1, 1/0.02]
            p0 = [0, 1 / 0.04, 0.02]
            popt, pcov = curve_fit(custom_fit_func_2, x, y, p0=p0, bounds=(lower_bounds, upper_bounds),
                                   maxfev=100000)
            best_f = lambda x: custom_fit_func_2(x, *popt)
            return best_f

        best_f = produce_fit_2(ms, acts)
        xs2 = np.linspace(0, 1, 500)
        ys_fit = best_f(xs2)
        if do_plot:
            # plt.scatter(xs, ys)
            plt.plot(xs2, ys_fit, color='grey', linestyle='--')
            plt.ylim(0, 1)
            # plt.show()

        # find the indices of zz where the dio_mass_frac is xx and the molality is yy
        # then set zz to the activity
        for j, hbr_molality in enumerate(hbr_molalities):
            assert xx[j, i] == dio_mass_frac
            assert yy[j, i] == hbr_molality
            zz[j, i] = best_f(hbr_molality)

    if do_plot:
        plt.xlabel('HBr molality')
        plt.ylabel('HBr molal activity coefficient')
        plt.show()

    # make an interpolator from xx, yy and zz using interp2d
    interp2d_here = interpolate.interp2d(dio_mass_fracts, hbr_molalities, zz, kind='cubic')

    return interp2d_here


def water_activity_function(do_plot=False):
    data = np.loadtxt('misc-scripts/activity_data/water-dioxane/'
                      'kogan-fridman-kafarov-1966/data_activity_of_water_in_dioxane.txt',
                      skiprows=1, delimiter=',')
    mole_fraction = data[:, 0]
    activity = data[:, 1]

    def custom_fit_func_3(x, a, b, c, d, e):
        return a + b * np.exp(-1 * c * x) + d * x + e * x ** 2

    def produce_fit(x, y):
        popt, pcov = curve_fit(custom_fit_func_3, x, y, p0=[1, -1, 1, 1, 1], maxfev=100000)
        best_f = lambda x: custom_fit_func_3(x, *popt)
        return best_f

    best_f = produce_fit(mole_fraction, activity)
    xs = np.linspace(0, 1, 100)
    ys_fit = best_f(xs)
    if do_plot:
        plt.scatter(mole_fraction, activity)
        plt.xlabel('Water mole fraction in dioxane-water mixture')
        plt.ylabel('Water activity')
        plt.plot(xs, ys_fit)
        plt.show()
    return best_f

# x = water_activity_function(do_plot=True)

# The initial run from august
# experiment_name = 'simple-reactions/2023-08-21-run01/'
# list_of_runs = tuple([
#     '2023-08-21-run01',
#     '2023-08-22-run01',
#     '2023-08-22-run02',
#     '2023-08-28-run01',
#     '2023-08-29-run01',
#     '2023-08-29-run02'])

experiment_name = 'simple-reactions/2023-11-28-run01/'
# Christmas run
list_of_runs = tuple([
                      '2023-11-28-run01',
                      '2023-11-29-run01',
                      '2023-11-29-run02',
                      '2023-12-02-run01',
                      '2023-12-04-run01',
                      '2023-12-04-run02'])

# column_to_plot = 'HBr_relative_change'
column_to_plot = 'yield'

substances = ['c#SN1OH03', 'c#HBr', 'temperature']
substance_titles = ['Alcohol', 'HBr', 'Temperature']
substrates = ['c#SN1OH03', 'c#HBr']

df_results = organize_run_results.join_data_from_runs([f'simple-reactions/{x}/' for x in list_of_runs],
                                 round_on_columns=substances)

for i, row in df_results.iterrows():
    df_results.loc[i, 'c#H2O'] = row['c#HBr'] / 4.5 * 21.88934517
    df_results.loc[i, 'c#acetic_acid'] = row['c#HBr'] / 4.5 * 8.583416744
    df_results.loc[i, 'product_sum'] = row['pc#SN1OH03'] + row['pc#SN1Br03']

# fig1 = plt.figure(1)
# plt.scatter(df_results['c#SN1OH03'], df_results['product_sum'], alpha=0.1)
# # plot x=y line
# plt.plot([0, 0.5], [0, 0.5], '--', color='C1')
# plt.xlabel('Alcohol before reaction, M')
# plt.ylabel('Sum of product and remaining alcohol, M')
#
# fig2 = plt.figure(2)
# plt.scatter(df_results['c#SN1OH03'], df_results['pc#SN1Br03'], alpha=0.1)
# plt.xlabel('Alcohol before reaction, M')
# plt.ylabel('Bromide product, M')
# plt.plot([0, 0.5], [0, 0.5], '--', color='C1')
#
# fig3 = plt.figure(3)
# plt.scatter(df_results['c#SN1OH03'], df_results['pc#SN1OH03'], alpha=0.1)
# plt.xlabel('Alcohol before reaction, M')
# plt.ylabel('Alcohol after reaction, M')
# plt.plot([0, 0.5], [0, 0.5], '--', color='C1')
#
# fig4 = plt.figure(4)
# plt.scatter(df_results['c#HBr'], df_results['c#SN1OH03'] - df_results['pc#SN1OH03'], alpha=0.1)
# plt.xlabel('HBr before reaction, M')
# plt.ylabel('Converted alcohol after reaction, M')
# plt.plot([0, 0.5], [0, 0.5], '--', color='C1')
#
# plt.show()
#
# Compute equilibrium constant
water_activity = water_activity_function()
HBr_activity_interpolator = make_interpolator_of_hbr_activity(do_plot=False)


# ########################## Compute equilibrium constant ########################################
# for i, row in df_results.iterrows():
#     # concentration of product
#     C_RBr = row['pc#SN1Br03']/(row['pc#SN1OH03'] + row['pc#SN1Br03']) * row['c#SN1OH03']
#     # concentration of water at the end of reaction
#     C_H2O = row['c#H2O'] + C_RBr
#
#     # in this section we compute the activity of water in the reaction mixture
#     dioxane_volume = row['vol#Dioxane'] + row['vol#SN1OH03']  # in microliters
#     dioxane_moles = dioxane_volume / 1000 * dioxane_density / dioxane_molar_mass
#     dioxane_molar_concentration = dioxane_moles / (500e-6)
#     solution_density_g_per_L = row['c#H2O'] * water_molar_mass + \
#                                dioxane_molar_concentration * dioxane_molar_mass + \
#                                row['c#HBr'] * hbr_molar_mass + \
#                                row['c#acetic_acid'] * acetic_acid_molar_mass
#     dioxane_mass_fraction = dioxane_molar_concentration * dioxane_molar_mass / (solution_density_g_per_L)
#
#     C_HBr_remaining = row['c#HBr'] - C_RBr
#     C_HBr_remaining_molality = C_HBr_remaining / solution_density_g_per_L * 1000
#     df_results.loc[i, 'C_HBr_remaining'] = C_HBr_remaining
#
#     HBr_activity_coefficient = HBr_activity_interpolator(dioxane_mass_fraction*100, C_HBr_remaining_molality)[0]
#     if HBr_activity_coefficient <= 1e-9:
#         HBr_activity_coefficient = 1e-9
#     print('HBr activity coefficient', HBr_activity_coefficient)
#
#     water_molar_fraction = C_H2O / (C_H2O + dioxane_molar_concentration)
#     water_activity_here = water_activity(water_molar_fraction)
#     effective_water_molar_concentration = water_activity_here * (C_H2O + dioxane_molar_concentration)
#     print(f'water mfraction {water_molar_fraction:.2f}, effective by a factor {effective_water_molar_concentration/C_H2O:.2f}')
#
#     # concentration of protons at the end of reaction
#     C_H_plus = row['c#HBr'] - C_RBr + row['c#acetic_acid']
#     # concentration of bromide ions at the end of reaction
#     C_Br_minus = row['c#HBr'] - C_RBr
#     # equilibrium constant
#     remaining_alcohol = row['pc#SN1OH03']/(row['pc#SN1OH03'] + row['pc#SN1Br03']) * row['c#SN1OH03']
#     # K_eq = (C_H_plus * C_Br_minus * remaining_alcohol) / (C_RBr * C_H2O)
#     K_eq = (C_HBr_remaining * HBr_activity_coefficient * remaining_alcohol) / (C_RBr * effective_water_molar_concentration)
#     df_results.loc[i, 'K_eq'] = K_eq

# column_to_plot = 'C_HBr_remaining'

def model_of_yield_for_one_condition(index_in_df, target_equilibrium_constant):
    # get row of df_results with index_in_df
    row = df_results.loc[index_in_df]
    # initial concentrations of substrates, HBR, water
    c_SN1OH03 = row['c#SN1OH03']
    c_HBr = row['c#HBr']
    c_H2O = row['c#H2O']
    logging.debug(f'c_SN1OH03 {c_SN1OH03:.2e}, c_HBr {c_HBr:.2e}, c_H2O {c_H2O:.2e}')
    # if one of concentrations is zero, return zero yield
    if c_SN1OH03 == 0 or c_HBr == 0:
        return 0

    dioxane_volume = row['vol#Dioxane'] + row['vol#SN1OH03']  # in microliters
    dioxane_moles = dioxane_volume / 1000 * dioxane_density / dioxane_molar_mass
    dioxane_molar_concentration = dioxane_moles / (500e-6)
    solution_density_g_per_L = row['c#H2O'] * water_molar_mass + \
                               dioxane_molar_concentration * dioxane_molar_mass + \
                               row['c#HBr'] * hbr_molar_mass + \
                               row['c#acetic_acid'] * acetic_acid_molar_mass
    dioxane_mass_fraction = dioxane_molar_concentration * dioxane_molar_mass / (solution_density_g_per_L)

    def eq_const_function(c_prod):
        # resulting concentrations of substrates, HBR, water
        c_SN1OH03_result = c_SN1OH03 - c_prod
        c_HBr_result = c_HBr - c_prod
        c_H2O_result = c_H2O + c_prod

        # activities of substrates, HBR, water
        a_SN1OH03 = c_SN1OH03_result
        water_molar_fraction = c_H2O_result / (c_H2O_result + dioxane_molar_concentration)
        water_activity_here = water_activity(water_molar_fraction)
        maximum_possible_water_molar_concetration = 55.56
        # effective_water_molar_concentration = water_activity_here * (c_H2O_result + dioxane_molar_concentration)
        effective_water_molar_concentration = water_activity_here * c_H2O_result

        c_HBr_result_molality = c_HBr_result / solution_density_g_per_L * 1000
        # HBr_activity_coefficient = HBr_activity_interpolator(dioxane_mass_fraction * 100, c_HBr_result_molality)[0]
        HBr_activity_coefficient = 1
        return (c_HBr_result * HBr_activity_coefficient * c_SN1OH03_result) / (c_prod * effective_water_molar_concentration)

    # # plot the yield against the c_prod
    # c_prod_array = np.linspace(0, min(c_SN1OH03, c_HBr), 100)
    # eq_const_array = [eq_const_function(c_prod) for c_prod in c_prod_array]
    # plt.plot(c_prod_array, eq_const_array)
    # plt.axhline(y=target_equilibrium_constant, color='r', linestyle='-')
    # plt.xlabel('c_prod')
    # plt.ylabel('eq_const')
    # plt.show()

    # solve the equation eq_const_function(c_prod) = target_equilibrium_constant
    c_prod = brentq(lambda x: eq_const_function(x) - target_equilibrium_constant, a=0, b=min(c_SN1OH03, c_HBr))
    reaction_yield = c_prod / c_SN1OH03
    return reaction_yield

def model_of_yield_for_many_conditions(indices, target_equilibrium_constant):
    return [model_of_yield_for_one_condition(index_in_df=i,
                                             target_equilibrium_constant=target_equilibrium_constant)
            for i in indices]

predicted_yield = model_of_yield_for_one_condition(index_in_df=0, target_equilibrium_constant=1e-5)
print(f'predicted yield {predicted_yield:.2f}')

def smooth_across_HBr_concentrations(x, y, fraction_of_outliers=0.15, do_plot=True):

    def custom_fit_func(x, a, b, c, d):
        return a + b * np.exp(-1*c*x) + d*x

    def produce_fit(x, y):
        popt, pcov = curve_fit(custom_fit_func, x, y, p0=[1, -1, 4, 0], maxfev=100000)
        best_f = lambda x: custom_fit_func(x, *popt)
        return best_f

    # def produce_fit(x, y):
        ### Polynomial fit version
        # z = np.polyfit(x, y, 4)
        # f = np.poly1d(z)
        # return f

    x = np.array(x)
    y = np.array(y)
    if do_plot:
        plt.scatter(x, y)
    f = produce_fit(x, y)
    if do_plot:
        plt.plot(np.sort(x), f(np.sort(x)), '--', color='C1')
    # remove the 10% of the points furthest from the fit
    diff = np.abs(f(x) - y)
    indices_to_keep = np.argsort(diff)[:-int(len(diff) * fraction_of_outliers)]
    # if point with lowest x is not in the indices to keep, add it
    if np.argmin(x) not in indices_to_keep:
        indices_to_keep = np.append(indices_to_keep, np.argmin(x))
    x2 = x[indices_to_keep]
    y2 = y[indices_to_keep]
    if do_plot:
        plt.scatter(x2, y2, color='C2', marker='x')
    # fit polynomial again
    f = produce_fit(x2, y2)
    if do_plot:
        plt.plot(np.sort(x), f(np.sort(x)), color='C1')
        # plt.ylim(0, 1)
        plt.xlabel('Concentration of HBr')
        plt.ylabel('Allegedly, the equilibrium constant')
        plt.show()
    return f(x)

# filtering
# df_results.drop(df_results[df_results['c#HBr'] < 0.065].index, inplace=True)
# df_results.drop(df_results[df_results['yield'] > 0.96].index, inplace=True)
# df_results.drop(df_results[df_results['is_outlier'] == 1].index, inplace=True)
df_results.dropna(subset=[column_to_plot], inplace=True)
df_results = df_results[~df_results[column_to_plot].isin([np.inf, -np.inf])]
# df_results[column_to_plot] = df_results[column_to_plot].apply(lambda x: x if x > 1e-10 else 0)
# df_results[column_to_plot] = df_results[column_to_plot].apply(lambda x: x if x <= 100 else 100)

# round concentrations "c#SN1OH03" and "c#HBr" to 6 decimal places
df_results['c#SN1OH03'] = df_results['c#SN1OH03'].round(6)
df_results['c#HBr'] = df_results['c#HBr'].round(6)

# # iterate over unique values of "c#SN1OH03" and "temperature" and smooth the data across the 'c#HBr' values
# for alcohol_concentration in df_results['c#SN1OH03'].unique():
#     for temperature in df_results['temperature'].unique():
#         print(f'c#SN1OH03 = {alcohol_concentration}, temperature = {temperature}')
#         indices = (df_results['c#SN1OH03'] == alcohol_concentration) & \
#                                                    (df_results['temperature'] == temperature)
#         df_results.loc[indices, column_to_plot] = \
#             smooth_across_HBr_concentrations(df_results.loc[indices, 'c#HBr'],
#                                              df_results.loc[indices, column_to_plot]
#                                              )

def fit_kinetic_model(indices_here, do_plot=False):

    def produce_fit(x, y):
        popt, pcov = curve_fit(model_of_yield_for_many_conditions, x, y, p0=[1e-2],
                               max_nfev=100000, bounds=([0], [np.inf]),
                               loss='soft_l1', f_scale=0.05)
        best_f = lambda x: model_of_yield_for_many_conditions(x, *popt)
        return best_f, popt[0]

    # def produce_fit(x, y):
        ### Polynomial fit version
        # z = np.polyfit(x, y, 4)
        # f = np.poly1d(z)
        # return f
    # make unique values of the alcohol concentrations for indices_here
    unique_alcohol_concentrations = df_results.loc[indices_here, 'c#SN1OH03'].unique()
    # sort it
    unique_alcohol_concentrations = np.sort(unique_alcohol_concentrations)
    # make a list of colors based on the id of the alcohol concentration
    colors = [f'C{i}' for i in range(len(unique_alcohol_concentrations))]
    colors_to_plot = df_results.loc[indices_here, 'c#SN1OH03'].apply(lambda x: colors[np.where(unique_alcohol_concentrations == x)[0][0]])
    xs_to_plot = df_results.loc[indices_here, 'c#HBr']
    measured_yields = df_results.loc[indices_here, 'yield']
    # plt.scatter(xs_to_plot, measured_yields, color='yellow', marker='o')
    f, keq_fit = produce_fit(indices_here, measured_yields)
    if do_plot:
        plt.scatter(xs_to_plot, measured_yields, color=colors_to_plot, alpha=0.5)
        for c_alc in unique_alcohol_concentrations:
            color_here = colors[np.where(unique_alcohol_concentrations == c_alc)[0][0]]
            # find df_indices among indices_here where alcolhol concentration is c_alc
            indices_where_mask_is_true = df_results.loc[indices_here, 'c#SN1OH03'] == c_alc
            # sort indices by HBr concentration
            xs_here = df_results.loc[indices_here[indices_where_mask_is_true], 'c#HBr']
            ys_here = f(indices_here[indices_where_mask_is_true])
            # sort xs and ys by increasing xs
            xs_here, ys_here = zip(*sorted(zip(xs_here, ys_here)))
            plt.plot(xs_here, ys_here, color=color_here, label=f'{c_alc:.3f} M')
        # plt.scatter(xs_to_plot, ys_to_plot, color=colors_to_plot, marker='x')
        plt.ylabel('Yield')
        plt.xlabel('Initial concentration of HBr')
        plt.legend(title="Starting alcohol\nconcentration")

    return keq_fit

# # iterate over unique values of "c#SN1OH03" and "temperature" and smooth the data across the 'c#HBr' values
# for temperature in df_results['temperature'].unique():
#     for alcohol_concentration in df_results['c#SN1OH03'].unique():
#         print(f'Fitting model at c#SN1OH03 = {alcohol_concentration}, temperature = {temperature}')
#         mask = (df_results['c#SN1OH03'] == alcohol_concentration) & \
#                                                    (df_results['temperature'] == temperature)
#         indices_where_mask_is_true = df_results[mask].index.to_numpy()
#         fit_kinetic_model(indices_where_mask_is_true, do_plot=True)

do_plot = False
keq_fits = []
temperatures = df_results['temperature'].unique()
temperatures = np.sort(temperatures)
for temperature in temperatures:
    print(f'Fitting model at temperature = {temperature}')
    mask = (df_results['temperature'] == temperature)
    indices_where_mask_is_true = df_results[mask].index.to_numpy()
    keq_fit = fit_kinetic_model(indices_where_mask_is_true, do_plot=True)
    keq_fits.append(keq_fit)
    if do_plot:
        plt.title(f'Temperature {temperature} °C')
        plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        plt.ylabel('Yield w.r.t. alcohol')
        plt.xlabel('Starting concentration of HBr, M')
        plt.gcf().savefig(f'{data_folder}simple-reactions/2023-11-28-run01/results/kinetics/figures/temperature_{temperature}C.png', dpi=300)
        plt.show()

xs = 1000/(273.15 + temperatures)
ys = -1*np.log(keq_fits)

# remove last points from xs and ys
xs = xs[:-1]
ys = ys[:-1]

plt.scatter(xs, ys)
# fit line and get slope and intersept
z = np.polyfit(xs, ys, 1)
f = np.poly1d(z)
print(f'Intercept {f[0]}, slope {f[1]}')
R_gas = 8.31446261815324 # J/(K*mol)
print(f'Delta S {f[0] * R_gas} J/(K*mol), delta H {-1 * f[1] * R_gas} kJ/mol')
plt.plot(xs, f(xs), '--')
plt.xlabel('1000/T, K$^{-1}$')
plt.ylabel('ln K')

# plot data of the last point
xs = 1000/(273.15 + temperatures)
ys = -1*np.log(keq_fits)
plt.scatter(xs[-1], ys[-1], color='red', marker='x')

plt.show()

# Computing the best-fit yields for the whole dataframe
for temperature in temperatures:
    # find the best-fit K_eq for this temperature
    logK = -1 * f(1000/(273.15 + temperature))
    K_eq = np.exp(logK)

    print(f'Fitting model at temperature = {temperature}')
    mask = (df_results['temperature'] == temperature)
    indices_where_mask_is_true = df_results[mask].index.to_numpy()
    for df_index in indices_where_mask_is_true:
        df_results.loc[df_index, 'yield_model'] = model_of_yield_for_one_condition(df_index, K_eq)

column_to_plot = 'yield_model'

# convert from mol/L to mM
for substrate in substrates:
    df_results[substrate] = df_results[substrate].apply(lambda x: x*1000 if x>1e-10 else 0)

xs = df_results[substrates[0]].to_numpy()
ys = df_results[substrates[1]].to_numpy()
zs = df_results['temperature'].to_numpy()
yields = df_results[column_to_plot].to_numpy()

print(f'Min concentrations of substrates: {[np.min(x) for x in [xs, ys, zs]]}')
print(f'Max concentrations of substrates: {[np.max(x) for x in [xs, ys, zs]]}')
print(f'Yields - min: {min(yields)}, max: {max(yields)}')

avs.plot_3d_dataset_as_cube(xs, ys, zs, yields,
                            substance_titles=('Alcohol,\nmM', 'HBr,\nmM', 'Temperature,\n°C'),
                            colorbar_title=column_to_plot,
                            npoints=50, sparse_npoints=6, rbf_epsilon=1,
                            rbf_smooth=0.05,
                            interpolator_choice='rbf',
                            data_for_spheres='interpolated',
                            rbf_function='multiquadric',
                            axes_ticks_format='%.0f',
                            axes_font_factor=1.5,
                            contours=[0.1, 0.5, 0.85, 0.97], contour_opacity=0.7) # [0.2, 0.4, 0.55, 0.7, 0.85]


# df_results.loc[df_results['yield#SN1Br01s1'] < 0, 'yield#SN1Br01s1'] = 0
# df_results.loc[df_results['yield#SN1Br01s1'] > 1, 'yield#SN1Br01s1'] = 1
# df_results.loc[df_results['c#SN1OH01'].round(4) == df_results['c#SN1OH01'].round(4).min(), 'yield#SN1Br01s1'] = 0
#
# avs.plot_3d_dataset_as_cube(xs, ys, zs, df_results['yield#SN1Br01s1'].to_numpy(),
#                             substance_titles=('Alcohol,\nmM', 'HBr,\nmM', 'temperature,\n°C'),
#                             colorbar_title='yield of SN1Br01s1',
#                             npoints=50, sparse_npoints=7, rbf_epsilon=1,
#                             rbf_smooth=0.05,
#                             interpolator_choice='rbf',
#                             data_for_spheres='interpolated',
#                             rbf_function='multiquadric',
#                             axes_ticks_format='%.0f',
#                             axes_font_factor=1.3,
#                             contours=[0.15, 0.2])

