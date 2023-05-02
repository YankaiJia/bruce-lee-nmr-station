import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from scipy.interpolate import splev, splrep
from savitzky_golay_werrors import savgol_filter_werror
data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'


def simpleaxis(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()

def filter_layouts(array, threshold, verbose=True):
    """
    Points that are further away from the previous and next point than the threshold
    are replaced by the mean of the previous and the next point.

    Parameters
    ----------
    array: ndarray
        1D array of values to be filtered.

    threshold: float
        The threshold for filtering.

    verbose: bool
        Whether to print out which points were filtered out.

    Returns
    -------
    array: np.array
        The filtered array.

    """
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


def round_to_nearest(df_new, df_reference, column_names):
    """
    Round the values in the new dataframe to the nearest values in the reference dataframe.
    For example, if column in reference dataframe has values [0.1, 0.2, 0.3] and the new dataframe has values
    [5, 8, 11, 0.099999999999999999998, 11, 0.2000000000000000001, 0.35], the new dataframe values will be rounded to
    [5, 8, 11, 0.1, 0.2, 0.3. 11. 0.2, 0.35]
    and returned.

    Parameters
    ----------
    df_new: pd.DataFrame
        The dataframe with the new values that may be slightly different from the reference values due to rounding
        errors.

    df_reference: pd.DataFrame
        The dataframe with the reference values.

    column_names: list of str
        Only these columns will be changed in the new dataframe. Columns of same names are compared between
        the dataframes.

    Returns
    -------
    df_new: pd.DataFrame
        The dataframe with the new values rounded to the nearest values in the reference dataframe.
    """
    for column_name in column_names:
        new_values = df_new[column_name].to_numpy()
        unique_values_from_reference_df = df_reference[column_name].unique()
        for i, new_value in enumerate(new_values):
            for unique_value_from_reference in unique_values_from_reference_df:
                if np.isclose(new_value, unique_value_from_reference):
                    new_values[i] = unique_value_from_reference
        df_new[column_name] = new_values
    return df_new


def join_data_from_runs(run_names, round_on_columns=('ic001', 'am001', 'ald001', 'ptsa')):
    """
    Loads the `results/product_concentration.csv` from multiple runs and joins them into one dataframe.

    Parameters
    ----------
    run_names: list
        The names of the runs whose results will be loaded and joined. These names are the names of the subfolders
        of the data folder.

    round_on_columns
        The columns that will be rounded to the nearest values in the reference dataframe. This is done to avoid
        rounding errors when joining the dataframes.

    Returns
    -------
    df_result: pd.DataFrame
        The dataframe with the joined data. The sequence of the rows is the same as the sequence of the runs.
    """
    df_result = pd.read_csv(data_folder + run_names[0] + f'results/product_concentration.csv')
    df_result.drop('Unnamed: 0', inplace=True, axis=1)
    for run_name in run_names[1:]:
        df_temporary = pd.read_csv(data_folder + run_name + f'results/product_concentration.csv')
        df_temporary.drop('Unnamed: 0', inplace=True, axis=1)
        df_temporary = round_to_nearest(df_temporary, df_result, round_on_columns)
        df_result = df_result.append(df_temporary, ignore_index=True)
    return df_result


def make_spline(xs, ys, yerr, layout_threshold=0.04, more_error_savgol=0.4, more_error_spline=0.2,
                spline_smoothing_factor=6, do_plot=False):
    """
    Filts spline to the data. Intended for plots of yield across all the catalyst values for specific
    combination of concentrations of substrates other than the catalyst.

    It applies the weighted Savitsky-Golay filter to the data, then first the weighted spline to the smoothed data.
    Weight are determined by the supplied yerr values, which should be the measurement uncertainty of individual
    datapoints.

    Parameters
    ----------
    xs: ndarray
        1D array of x values. E.g. catalyst concentrations.

    ys: ndarray
        1D array of y values to which the spline will be fitted. E.g.: reaction yields.

    yerr: ndarray
        The errors of the y values.

    layout_threshold: float
        The threshold for filtering the data for layouts. See the filter_layouts function above.

    more_error_savgol: float
        The additional error to be added to the yerr when smoothing the data with weighted Savitsky-Golay filter.

    more_error_spline: float
        The additional error to be added to the yerr when smoothing the data with weighted spline applied after
        Savitsky-Golay filter.

    spline_smoothing_factor:
        The smoothing factor for the spline. See the factor s in the scipy.interpolate.splrep function.

    do_plot: bool
        If True, the smoothed data will be plotted.

    Returns
    -------
        tck: tuple
            The spline parameters. See the scipy.interpolate.splrep function.
    """
    permurations_that_sort_xs = xs.argsort()
    xs = xs[permurations_that_sort_xs]
    ys = ys[permurations_that_sort_xs]
    ys = filter_layouts(ys, threshold=layout_threshold)
    ys_sg = savgol_filter_werror(ys, window_length=5, degree=2, error=yerr + more_error_savgol)
    if do_plot:
        plt.plot(xs, ys_sg, color='gold', linewidth=4, alpha=0.5)
    tck = splrep(xs, ys_sg, s=spline_smoothing_factor, w=1 / (yerr + more_error_spline))
    return tck


def plot_one_point_across_catalyst_range(df_data, param_values_by_index, label=None, color=None,
                                         column_names=('ic001', 'am001', 'ald001'),
                                         catalyst_name='ptsa', column_to_plot='yield', relative_std=0.146,
                                         withspline=True, factor=1, spline_color='black', plot_points=True,
                                         plot_savgol=True, spline_alpha=0.3, spline_linewidth=5):
    """
    Plots data across the catalyst range for a specific combination of non-catalyst substrate concentrations
    (and perhaps other parameters) defined by the indices in lists if unique values of the parameters.

    For example, if param_values_by_data=(2, 0, 1) and column_names=('ic001', 'am001', 'ald001')
    then the function will plot the data from the dataset where the column `ic001` has the third unique value
    from the sorted list of unique values of column `ic001`, the column `am001` has the first unique value, and
    the column `ald001` has the second unique value.

    Parameters
    ----------
    df_data: pd.DataFrame
        The dataframe with the data to be plotted. The dataframe should have the columns catalyst_name,
        column_to_plot, and all the columns in `column_names` list (or tuple).

    param_values_by_index: tuple
        The indices of the unique values of the parameters that will be used to select the data to be plotted.

    label: str
        The label of the plot. If None, the label will be the values of the parameters that were used to select
        the data to be plotted.

    color: str
        The color of the plot. If None, the color will be the default color of the plot.

    column_names: tuple
        The names of the columns that will be used to select the data to be plotted. The length of the list
        should be the same as the length of the `param_values_by_index` list.

    catalyst_name: str
        The name of the column that contains the catalyst concentrations.

    column_to_plot:
        The name of the column that contains the data to be plotted. For example, the yield of the reaction.

    relative_std:
        The relative standard deviation of the data to be plotted. This is used to determine the error bars.

    withspline:
        If True, the spline will be plotted on top of the data. See the make_spline function above.
    """
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

    if label is None:
        label = f'{column_names}: {param_values_by_index}'

    if plot_points:
        if color is None:
            plt.errorbar(xs, ys, yerr=yerr, linestyle='None', marker='o', capsize=3, label=label, alpha=0.5)
        else:
            plt.errorbar(xs, ys, yerr=yerr, linestyle='None', marker='o', capsize=3, label=label, alpha=0.5, color=color)

    if withspline:
        tck = make_spline(xs, ys, yerr, do_plot=plot_savgol, spline_smoothing_factor=4)
        xs_new = np.linspace(np.min(xs), np.max(xs), 100)
        ys_new = splev(xs_new, tck) * factor
        plt.plot(xs_new, ys_new, color=spline_color, linewidth=spline_linewidth, alpha=spline_alpha)

    plt.xlabel(f'{catalyst_name} (catalyst) concentration, mol/L')
    if column_to_plot == 'yield':
        plt.ylabel('Yield, %')


if __name__ == '__main__':
    df_results = join_data_from_runs(['multicomp-reactions/2023-03-20-run01/',
                                      'multicomp-reactions/2023-03-29-run01/',
                                      'multicomp-reactions/2023-03-31-run01/'])

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

    fig = plt.figure(figsize=(3,2.6))
    plot_one_point_across_catalyst_range(df_results, (-1, 0, -1), label='Corner A', plot_points=False, plot_savgol=False, spline_color='C3', spline_alpha=0.6, spline_linewidth=3)
    plot_one_point_across_catalyst_range(df_results, (-1, -1, 0), label='Corner B', plot_points=False, plot_savgol=False, spline_color='C0', spline_alpha=0.6, spline_linewidth=3,
                                         factor=1.35)

    # # plot_one_point_across_catalyst_range(df_results, (2, 1, 1), label='Between corners', color='grey')
    # plot_one_point_across_catalyst_range(df_results, (3, 5, 7), label='Outlier A', withspline=True)
    # plt.show()

    # plot_one_point_across_catalyst_range(df_results, (2, 10, 5), label='Repeated point', color='red')
    # plt.show()
    # for ald in [0, 5, 10]:
    #     plot_one_point_across_catalyst_range(df_results, (2, 10, ald), label=f'Repeated point, ald{ald}')
    #     plt.show()
    # for am in [0, 5, 10]:
    #     plot_one_point_across_catalyst_range(df_results, (2, am, 5), label=f'Repeated point, am{am}')
    #     plt.show()
    simpleaxis(plt.gca())
    # plt.legend()
    plt.xlabel('Acid concentration [mol/L]')
    plt.ylabel('Yield [%]')
    plt.tight_layout()
    fig.savefig('yield_vs_acid.png', dpi=300)
    plt.show()