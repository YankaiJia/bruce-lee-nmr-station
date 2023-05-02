from visualize_results import *
from scipy.interpolate import Rbf, LinearNDInterpolator

df_results = join_data_from_runs(['multicomp-reactions/2023-03-20-run01/',
                                  'multicomp-reactions/2023-03-29-run01/',
                                  'multicomp-reactions/2023-03-31-run01/',
                                  'multicomp-reactions/2023-04-11-run01/'])
# 'multicomp-reactions/2023-03-29-run01/'])
do_plot = True
substances = ['ic001', 'am001', 'ald001', 'ptsa']
product = 'IIO029A'
catalyst_name = 'ptsa'
relative_std = 0.146

# here I drop two first columns from df_results pandas dataframe because they are not needed
# for the interpolation

indices_of_outliers = [901, 909, 917]
df_results.drop(indices_of_outliers, inplace=True)

substrate_cs = []
for substance in substances:
    substrate_cs.append(df_results[substance].to_numpy())

xs0, ys0, zs0, cats = substrate_cs
ks0 = df_results['yield'].to_numpy()

for substance in substances:
    print(f'{substance} min: {np.min(df_results[substance].to_numpy())}')
    print(f'{substance} max: {np.max(df_results[substance].to_numpy())}')
    print(f'{substance} unique: {sorted(df_results[substance].unique())}')


minimal_concentration_of_substrates = np.min(np.array([xs0, ys0, zs0]))

unique_cats = sorted(list(set(list(cats))))
print(f'Unique cats: {unique_cats}')

npoints_over_catalyst_range = 500
new_cats = np.linspace(df_results[catalyst_name].min(), df_results[catalyst_name].max(), npoints_over_catalyst_range)

df_combinations = df_results.groupby(['ic001', 'am001', 'ald001']).size().reset_index().rename(columns={0:'count'})

df_interpolated = df_results.drop(df_results.index)
df_interpolated.drop([product], axis=1, inplace=True)
for index, row in df_combinations.iterrows():
    print(f'Index: {index}')
    print(row)
    # find all the rows from df_results that have this combination of concentrations
    df_this_combination = df_results[(df_results['ic001'] == row['ic001']) &
                                (df_results['am001'] == row['am001']) &
                                (df_results['ald001'] == row['ald001'])]
    # if there is only one row in df_this_combination, then there is no need to interpolate
    if len(df_this_combination) == 1:
        df_temporary = df_interpolated.drop(df_interpolated.index)
        df_temporary.loc[0] = [row['ald001'], df_this_combination['ptsa'].to_numpy()[0], row['am001'], row['ic001'],
                               df_this_combination['yield'].to_numpy()[0]]
        df_interpolated = df_interpolated.append(df_temporary, ignore_index=True)
        continue

    if index == 18:
        df_this_combination['yield'] = df_this_combination['yield'] * 18.6/10.7

    if index == 29:
        df_this_combination['yield'] = df_this_combination['yield'] * 12.5/8.8

    catalyst_concentration_limits_here = df_this_combination['ptsa'].min(), df_this_combination['ptsa'].max()

    # For catalyst concentrations where this combination was not measured,
    # make RBF interpolation from nearby points in substrate space
    if do_plot:
        plt.errorbar(df_this_combination['ptsa'].to_numpy(), df_this_combination['yield'].to_numpy(),
                     yerr=df_this_combination['yield'].to_numpy() * relative_std, linestyle='None',
                     marker='o', capsize=3, label='data', alpha=0.5, color='C0')
    xnew = row['ic001']
    ynew = row['am001']
    znew = row['ald001']
    for catalyst_concentration in unique_cats:
        if catalyst_concentration < catalyst_concentration_limits_here[0] or catalyst_concentration > catalyst_concentration_limits_here[1]:
            mask = (cats == catalyst_concentration)
            xs = xs0[mask]
            ys = ys0[mask]
            zs = zs0[mask]
            ks = ks0[mask]

            # # RBF version
            # rbf4 = Rbf(xs, ys, zs, ks, epsilon=0.04, smooth=0.8)  # function="thin_plate"
            # wnew = rbf4(xnew, ynew, znew)

            # Linead ND version
            interp_here = LinearNDInterpolator((xs, ys, zs), ks)
            wnew = float(interp_here((xnew, ynew, znew)))
            if wnew < 0:
                wnew = 0
            # append one row to df_this_combination with wnew as yield and catalyst_concentration as ptsa
            df_temporary = df_interpolated.drop(df_interpolated.index)
            df_temporary.loc[0] = [row['ald001'], catalyst_concentration, row['am001'], row['ic001'], wnew]
            df_this_combination = df_this_combination.append(df_temporary, ignore_index=True)
    assert df_this_combination['ptsa'].min() == unique_cats[0]
    assert df_this_combination['ptsa'].max() == unique_cats[-1]
    catalyst_concentration_limits_here = df_this_combination['ptsa'].min(), df_this_combination['ptsa'].max()

    # make interpolator of yields over catalyst concentrations
    xs = df_this_combination['ptsa'].to_numpy()
    ys = df_this_combination['yield'].to_numpy()
    yerr = df_this_combination['yield'].to_numpy() * relative_std
    if do_plot:
        plt.errorbar(xs, ys, yerr=yerr, linestyle='None', marker='x', capsize=3, label='data', alpha=0.5, color='C1')
    # tck = make_spline(xs, ys, yerr, do_plot=do_plot, spline_smoothing_factor=0.05)
    tck = make_spline(xs, ys, yerr, do_plot=do_plot, spline_smoothing_factor=0.08)
    if do_plot:
        xs_new = np.linspace(np.min(xs), np.max(xs), 100)
        ys_new = splev(xs_new, tck)
        plt.plot(xs_new, ys_new, color='black', linewidth=5, alpha=0.3)

    xs_new = new_cats[np.where((new_cats >= catalyst_concentration_limits_here[0]) & (new_cats <= catalyst_concentration_limits_here[1]))]
    ys_new = splev(xs_new, tck)
    df_temporary = df_interpolated.drop(df_interpolated.index)
    for i, ptsa_new in enumerate(xs_new):
        df_temporary.loc[i] = [row['ald001'], ptsa_new, row['am001'], row['ic001'], ys_new[i]]
    df_interpolated = df_interpolated.append(df_temporary, ignore_index=True)
    if do_plot:
        plt.show()

# save to file
run_name = 'multicomp-reactions/2023-03-31-run01/'
df_interpolated.to_csv(data_folder + run_name + f'results/interpolated_product_concentration.csv', index=False)
