'''Takes in the run_info.csv file, adds certain time delay to the finishing time and makes a table.
This comvenient for planning the next operation.'''

import pandas as pd
import datetime
import os

data_folder = os.environ['ROBOCHEM_DATA_PATH'].replace('\\', '/') + '/'
experiment_name = 'multicomp-reactions/2023-04-12-run01/'

# df = pd.read_csv(data_folder + experiment_name + 'pipetter_io/run_info_0322.csv', delimiter=', ',
#                  usecols=['plate_code', 'experiment_name', 'finish_time_unix', 'note'])

df = pd.read_csv(data_folder + experiment_name + 'pipetter_io/run_info.csv', delimiter=', ',
                 usecols=['plate_code', 'experiment_name', 'finish_time_unix', 'note'])

delay_in_hours = 16
df['new_start_unixtime'] = pd.to_datetime(df['finish_time_unix'] + delay_in_hours * 60 * 60, unit='s')
df.new_start_unixtime = df.new_start_unixtime.dt.tz_localize('UTC').dt.tz_convert('Asia/Seoul')
df = df.loc[df.new_start_unixtime.dt.date == datetime.datetime.now().date()]
df_out = df[['plate_code', 'new_start_unixtime', 'experiment_name']]

# df.new_start_unixtime = df.new_start_unixtime + pd.Timedelta('06:00:00')
print(df_out.to_string(index=False))

