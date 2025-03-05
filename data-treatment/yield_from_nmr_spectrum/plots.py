from matplotlib import pyplot as plt


ys_ori = {
0:'92.03727024121508',
1:'44.85000344605123',
2:'21.30438829283912',
3:'9.689694961722125',
4:'4.404170234225603'}

ys = [float(value) for key, value in ys_ori.items()]
print(ys)

xs_init = 152.4
xs = [xs_init, xs_init/2, xs_init/4, xs_init/8, xs_init/16 ]

yb_ori =  {0:'58.26061628299067',
1:'29.7097988122041',
2:'14.252173271263246',
3:'6.550650316834435',
4:'2.1064971663290635'}

yb = [float(value) for key, value in yb_ori.items()]
xb_init = 252.1
xb = [xb_init,xb_init/2,xb_init/4,xb_init/8,xb_init/16 ]

# plt.plot(xs, ys,'o', ls = '-')
# plt.plot(xb, yb, 'o', ls = '-')

# plt.xscale('log')  # Set the x-axis to logarithmic scale
# plt.plot()
# plt.show()

import pandas as pd
# plot csv
path ="D:\\Dropbox\\brucelee\\data\\DPE_bromination\\_Refs\\ref_B_TEST\\205244-1D EXTENDED+-B1\\data.csv"

df = pd.read_csv(path)
print(df.head())
plt.plot(df['x'], df['y'], 'o', ls = '-')
plt.plot()
plt.show()