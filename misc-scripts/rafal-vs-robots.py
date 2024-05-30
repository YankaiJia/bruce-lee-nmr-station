
import matplotlib.pyplot as plt

ys_1 = [1.35E-02,
1.47E-02,
1.95E-02]

ys_2 = [4.33E-03,
1.35E-02,
1.04E-02]

xs = [6.46E-03,
2.35E-02,
2.18E-02]

for i in range(3):
    plt.plot([xs[i]]*2, [ys_1[i], ys_2[i]], 'o-', color='C0')

plt.plot([0, 0.03], [0, 0.03], color='black')
plt.xlabel('Robots: product concentration (mol/L)')
plt.ylabel('Rafal: product concentration (mol/L)')
plt.show()


xs = [1.88E-02,
2.32E-02,
9.43E-03,
6.64E-02,
]

ys = [1.97E-02,
2.24E-02,
8.85E-03,
2.03E-02,
]

plt.scatter(xs, ys)
plt.plot([0, 0.03], [0, 0.03], color='black')
plt.xlabel('By HPLC: product concentration (mol/L)')
plt.ylabel('By absorbance: product concentration (mol/L)')
plt.show()