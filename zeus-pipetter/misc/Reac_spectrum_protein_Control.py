import glob
import pandas as pd
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')
from matplotlib import rc_params

# glob all the csv file pathes in a folder and store them in a list
csv_folder = 'D:\\Dropbox\\robochem\\data\\BORG\\2024-01-17-run01\\nanodrop_spectra\\'
csv_file = glob.glob(csv_folder + '*.csv')

dfs = []
# this is for control
for csv in csv_file:
    df_here = pd.read_csv(csv)
    # change the first column name and set it as index
    df_here.rename(columns={'Unnamed: 0': 'wavelength'}, inplace=True)
    df_here.set_index('wavelength', inplace=True)
    dfs.append(df_here)

df_control, df_EtOH_100mM, df_EtOH_10mM = dfs[0], dfs[1], dfs[2]
df_control_abs340, df_EtOH_100mM_abs340, df_EtOH_10mM_abs340 = \
    df_control.loc[340], df_EtOH_100mM.loc[340], df_EtOH_10mM.loc[340]


# plot controls in one fig
colors = rc_params()['axes.prop_cycle'].by_key()['color']
fig, axs = plt.subplots(1,3, figsize=(16,6))
titles=['Control(0-6)', 'Sample(9)', 'Sample(10)']
axs.flatten()[0].plot(list(range(6)),df_control_abs340.iloc[0:6], color=colors[0], marker='o', label='15min', )
axs.flatten()[0].plot(list(range(6)),df_control_abs340.iloc[6:12], color=colors[1], marker='v', label='30min', )
axs.flatten()[0].plot(list(range(6)),df_control_abs340.iloc[12:18], color=colors[2], marker='<', label='60min', )
axs.flatten()[0].set_xlabel('Samples')
axs.flatten()[0].set_ylabel('Absorbance@340nm(AU)')
axs.flatten()[0].title.set_text('Control exp')

axs.flatten()[0].set_ylim(-0.005, 0.17)
axs.flatten()[0].legend()

# plot samples with 100mM EtOH
seq1_15min = df_EtOH_100mM_abs340.loc['0-15min':'3-15min'].mean()
seq1_30min = df_EtOH_100mM_abs340.loc['0-30min':'3-30min'].mean()
seq1_60min = df_EtOH_100mM_abs340.loc['0-60min':'3-60min'].mean()
seq2_15min = df_EtOH_100mM_abs340.loc['4-15min':'7-15min'].mean()
seq2_30min = df_EtOH_100mM_abs340.loc['4-30min':'7-30min'].mean()
seq2_60min = df_EtOH_100mM_abs340.loc['4-60min':'7-60min'].mean()
seq3_15min = df_EtOH_100mM_abs340.loc['8-15min':'11-15min'].mean()
seq3_30min = df_EtOH_100mM_abs340.loc['8-30min':'11-30min'].mean()
seq3_60min = df_EtOH_100mM_abs340.loc['8-60min':'11-60min'].mean()
seq4_15min = df_EtOH_100mM_abs340.loc['12-15min':'15-15min'].mean()
seq4_30min = df_EtOH_100mM_abs340.loc['12-30min':'15-30min'].mean()
seq4_60min = df_EtOH_100mM_abs340.loc['12-60min':'15-60min'].mean()
seq5_15min = df_EtOH_100mM_abs340.loc['16-15min':'19-15min'].mean()
seq5_30min = df_EtOH_100mM_abs340.loc['16-30min':'19-30min'].mean()
seq5_60min = df_EtOH_100mM_abs340.loc['16-60min':'19-60min'].mean()
seq6_15min = df_EtOH_100mM_abs340.loc['21-15min':'22-15min'].mean()
seq6_30min = df_EtOH_100mM_abs340.loc['21-30min':'23-30min'].mean()
seq6_60min = df_EtOH_100mM_abs340.loc['21-60min':'23-60min'].mean()

axs.flatten()[1].plot([15,30,60],[seq1_15min,seq1_30min,seq1_60min], color=colors[0], marker='o', label='seq1_100mM')
axs.flatten()[1].plot([15,30,60],[seq2_15min,seq2_30min,seq2_60min], color=colors[1], marker='v', label='seq2_100mM')
axs.flatten()[1].plot([15,30,60],[seq3_15min,seq3_30min,seq3_60min], color=colors[2], marker='<', label='seq3_100mM')
axs.flatten()[1].plot([15,30,60],[seq4_15min,seq4_30min,seq4_60min], color=colors[3], marker='>', label='seq4_100mM')
axs.flatten()[1].plot([15,30,60],[seq5_15min,seq5_30min,seq5_60min], color=colors[4], marker='^', label='seq5_100mM')
axs.flatten()[1].plot([15,30,60],[seq6_15min,seq6_30min,seq6_60min], color=colors[5], marker='s', label='seq6_100mM')
axs.flatten()[1].set_ylim(0.08, 0.17)
axs.flatten()[1].set_xlabel('Time(min)')
# axs.flatten()[1].set_ylabel('Absorbance@340nm(AU)')
axs.flatten()[1].title.set_text('Seq test 100mM')
axs.flatten()[1].legend()

seq1_15min_10mM = df_EtOH_10mM_abs340.loc[['24-15min', '26-15min','27-15min']].mean()
seq1_30min_10mM = df_EtOH_10mM_abs340.loc[['24-30min', '26-30min','27-30min']].mean()
seq1_60min_10mM = df_EtOH_10mM_abs340.loc[['24-60min', '26-60min','27-60min']].mean()
seq2_15min_10mM = df_EtOH_10mM_abs340.loc['28-15min':'31-15min'].mean()
seq2_30min_10mM = df_EtOH_10mM_abs340.loc['28-30min':'31-30min'].mean()
seq2_60min_10mM = df_EtOH_10mM_abs340.loc['28-60min':'31-60min'].mean()
seq3_15min_10mM = df_EtOH_10mM_abs340.loc['32-15min':'35-15min'].mean()
seq3_30min_10mM = df_EtOH_10mM_abs340.loc['32-30min':'35-30min'].mean()
seq3_60min_10mM = df_EtOH_10mM_abs340.loc['32-60min':'35-60min'].mean()
seq4_15min_10mM = df_EtOH_10mM_abs340.loc['36-15min':'39-15min'].mean()
seq4_30min_10mM = df_EtOH_10mM_abs340.loc['36-30min':'39-30min'].mean()
seq4_60min_10mM = df_EtOH_10mM_abs340.loc['36-60min':'39-60min'].mean()
seq5_15min_10mM = df_EtOH_10mM_abs340.loc['40-15min':'43-15min'].mean()
seq5_30min_10mM = df_EtOH_10mM_abs340.loc['40-30min':'43-30min'].mean()
seq5_60min_10mM = df_EtOH_10mM_abs340.loc['40-60min':'43-60min'].mean()
seq6_15min_10mM = df_EtOH_10mM_abs340.loc['45-15min':'47-15min'].mean()
seq6_30min_10mM = df_EtOH_10mM_abs340.loc['45-30min':'46-30min'].mean()
seq6_60min_10mM = df_EtOH_10mM_abs340.loc['45-60min':'47-60min'].mean()
axs.flatten()[2].plot([15,30,60],[seq1_15min_10mM,seq1_30min_10mM,seq1_60min_10mM], color=colors[0], marker='o', label='seq1_10mM')
axs.flatten()[2].plot([15,30,60],[seq2_15min_10mM,seq2_30min_10mM,seq2_60min_10mM], color=colors[1], marker='v', label='seq2_10mM')
axs.flatten()[2].plot([15,30,60],[seq3_15min_10mM,seq3_30min_10mM,seq3_60min_10mM], color=colors[2], marker='<', label='seq3_10mM')
axs.flatten()[2].plot([15,30,60],[seq4_15min_10mM,seq4_30min_10mM,seq4_60min_10mM], color=colors[3], marker='>', label='seq4_10mM')
axs.flatten()[2].plot([15,30,60],[seq5_15min_10mM,seq5_30min_10mM,seq5_60min_10mM], color=colors[4], marker='^', label='seq5_10mM')
axs.flatten()[2].plot([15,30,60],[seq6_15min_10mM,seq6_30min_10mM,seq6_60min_10mM], color=colors[5], marker='s', label='seq6_10mM')

axs.flatten()[2].set_ylim(0.04, 0.10)
axs.flatten()[2].set_xlabel('Time(min)')
# axs.flatten()[2].set_ylabel('Absorbance@340nm(AU)')
axs.flatten()[2].title.set_text('Seq test 10mM')

axs.flatten()[2].legend()

# save fig
plt.savefig('D:\\Dropbox\\robochem\\data\\BORG\\2024-01-17-run01\\all_exp.png')

plt.show()




#
# ## plot 7 controls in one fig
# colors = rc_params()['axes.prop_cycle'].by_key()['color']
# fig, axs = plt.subplots(1,3, figsize=(16,6))
# df_abs = df.loc[340]
#
# titles=['Control(0-6)', 'Sample(9)', 'Sample(10)']
# axs.flatten()[0].plot(list(range(7)),df_abs.iloc[0:7], color=colors[0], marker='o')
# axs.flatten()[0].plot(list(range(7)),df_abs.iloc[8:15], color=colors[1], marker='v')
# axs.flatten()[0].set_xlabel('Samples')
# axs.flatten()[0].set_ylabel('Absorbance@340nm(AU)')
#
# sample_9 =df_abs.loc['9_0':'9_25']
# axs.flatten()[1].plot([0.5*i for i in list(range(len(sample_9)))],sample_9, color=colors[2], marker='o')
# sample_10 =df_abs.loc['10_0':'10_20']
# axs.flatten()[2].plot([0.5*i for i in list(range(len(sample_10)))],sample_10, color=colors[2], marker='o')
# axs.flatten()[1].set_xlabel('Time(min)')
# axs.flatten()[2].set_xlabel('Time(min)')
#
# for i in [0,1,2]:
#     axs.flatten()[i].set_title(titles[i])
#     # set limits
#     axs.flatten()[i].set_ylim(-0.005, 0.17)

# save fig
# plt.savefig('D:\\Dropbox\\robochem\\data\\BORG\\2024-01-16-run01\\control_exp.png')
# plt.show()


