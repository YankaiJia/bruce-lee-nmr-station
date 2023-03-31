import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from scipy.interpolate import splev, splrep
from savitzky_golay_werrors import savgol_filter_werror
data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'

def filter_layouts(array, threshold, verbose=True):
    diff = np.diff(array)
    for i, x in enumerate(array):
        if i == 0 or i == len(array) - 1:
            continue
        difference_to_previos_point = diff[i-1]
        difference_to_next_point = diff[i]
        if abs(difference_to_previos_point) > threshold and abs(difference_to_next_point) > threshold and \
                np.sign(difference_to_next_point) != np.sign(difference_to_previos_point):
            array[i] = (array[i-1] + array[i+1]) / 2
            if verbose:
                print(f'Point {i} with value {x} was filtered out.')
    return array


# take care of rounding errors
def round_to_nearest(df_new, df_reference, column_names):
    for column_name in column_names:
        new_values = df_new[column_name].to_numpy()
        unique_values_from_reference_df = df_reference[column_name].unique()
        for i, new_value in enumerate(new_values):
            for unique_value_from_reference in unique_values_from_reference_df:
                if np.isclose(new_value, unique_value_from_reference):
                    new_values[i] = unique_value_from_reference
        df_new[column_name] = new_values
    return df_new


def join_data_from_runs(experiment_names, round_on_columns=('ic001', 'am001', 'ald001', 'ptsa')):
    df_result = pd.read_csv(data_folder + experiment_names[0] + f'results/product_concentration.csv')
    df_result.drop('Unnamed: 0', inplace=True, axis=1)
    for experiment_name in experiment_names[1:]:
        df_temporary = pd.read_csv(data_folder + experiment_name + f'results/product_concentration.csv')
        df_temporary.drop('Unnamed: 0', inplace=True, axis=1)
        df_temporary = round_to_nearest(df_temporary, df_result, round_on_columns)
        df_result = df_result.append(df_temporary, ignore_index=True)
    return df_result


def make_spline(xs, ys, yerr, layout_threshold=4, more_error_savgol=0.4, more_error_spline=0.2,
                spline_smoothing_factor=6, do_plot=False):
    ys = filter_layouts(ys, threshold=layout_threshold)
    ys_sg = savgol_filter_werror(ys, window_length=5, degree=2, error=yerr + more_error_savgol)
    if do_plot:
        plt.plot(xs, ys_sg, color='gold', linewidth=4, alpha=0.5)
    tck = splrep(xs, ys_sg, s=spline_smoothing_factor, w=1 / (yerr + more_error_spline))
    return tck


def plot_one_point_across_catalyst_range(df_data, param_values_by_index, label=None, color=None,
                                         column_names=('ic001', 'am001', 'ald001'),
                                         catalyst_name='ptsa', column_to_plot='yield', relative_std=0.146,
                                         withspline=True):
    target = {column_name: sorted(df_data[column_name].unique())[param_values_by_index[i]]
              for i, column_name in enumerate(column_names)}
    indices = df_data[(df_data[column_names[0]] == target[column_names[0]]) &
                      (df_data[column_names[1]] == target[column_names[1]]) &
                      (df_data[column_names[2]] == target[column_names[2]])].index
    if column_to_plot == 'yield':
        scale_factor = 100
    xs = df_data[catalyst_name].to_numpy()[indices]
    ys = df_data[column_to_plot].to_numpy()[indices] * scale_factor
    yerr = df_data[column_to_plot].to_numpy()[indices] * scale_factor * relative_std
    if color is None:
        plt.errorbar(xs, ys, yerr=yerr, linestyle='None', marker='o', capsize=3, label=label, alpha=0.5)
    else:
        plt.errorbar(xs, ys, yerr=yerr, linestyle='None', marker='o', capsize=3, label=label, alpha=0.5, color=color)

    if withspline:
        tck = make_spline(xs, ys, yerr, do_plot=True)
        xs_new = np.linspace(np.min(xs), np.max(xs), 100)
        ys_new = splev(xs_new, tck)
        plt.plot(xs_new, ys_new, color='black', linewidth=5, alpha=0.3)

    plt.xlabel(f'{catalyst_name} (catalyst) concentration, mol/L')
    if column_to_plot == 'yield':
        plt.ylabel('Yield, %')


if __name__ == '__main__':
    df_results = join_data_from_runs(['multicomp-reactions/2023-03-20-run01/',
                                      'multicomp-reactions/2023-03-29-run01/'])

    substances = ['ic001','am001','ald001','ptsa']
    product = 'IIO029A'

    substrate_cs = []
    for substance in substances:
        substrate_cs.append(df_results[substance].to_numpy())

    xs0, ys0, zs0, cats = substrate_cs

    for substance in substances:
        print(f'{substance} min: {np.min(df_results[substance].to_numpy())}')
        print(f'{substance} max: {np.max(df_results[substance].to_numpy())}')
        print(f'{substance} unique: {sorted(df_results[substance].unique())}')

    minimal_concentration_of_substrates = np.min(np.array([xs0, ys0, zs0]))

    unique_cats = sorted(list(set(list(cats))))
    print(f'Unique cats: {unique_cats}')

    # plot_one_point_across_catalyst_range(df_results, (2, 0, 2), label='Corner A')
    # plot_one_point_across_catalyst_range(df_results, (2, 2, 0), label='Corner B')
    # plot_one_point_across_catalyst_range(df_results, (2, 1, 1), label='Between corners', color='grey')

    plot_one_point_across_catalyst_range(df_results, (2, 10, 5), label='Repeated point', color='red')
    plt.show()
    for ald in [0, 5, 10]:
        plot_one_point_across_catalyst_range(df_results, (2, 10, ald), label=f'Repeated point, ald{ald}')
        plt.show()
    for am in [0, 5, 10]:
        plot_one_point_across_catalyst_range(df_results, (2, am, 5), label=f'Repeated point, am{am}')
        plt.show()
    plt.legend()
    plt.xlabel('PTSA (catalyst) concentration, mol/L')
    plt.ylabel('Yield, %')
    plt.tight_layout()
    plt.show()