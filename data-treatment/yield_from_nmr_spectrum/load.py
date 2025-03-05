import pandas as pd
import matplotlib.pyplot as plt

# load df from csv
df = pd.read_csv("C:\\Users\\jiaya\\Desktop\\1D.csv", sep="\t")
print(df.head())
df.columns = ['ppm', 'intensity', 'none']
# plot the first column against the second column
plt.plot(df['ppm'], df['intensity'])
plt.xlabel('ppm')
plt.show()
