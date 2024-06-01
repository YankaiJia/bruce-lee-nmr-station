import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')

def plot_concs(a_list, b_list, c_list, ab_list, bc_list, ac_list, abc_list):
    ## make 7 subplots for each species
    fig, axs = plt.subplots(1, 7, figsize=(20, 5))
    axs[0].plot(a_list)
    axs[0].set_title('a')
    axs[1].plot(b_list)
    axs[1].set_title('b')
    axs[2].plot(c_list)
    axs[2].set_title('c')
    axs[3].plot(ab_list)
    axs[3].set_title('ab')
    axs[4].plot(ac_list)
    axs[4].set_title('ac')
    axs[5].plot(bc_list)
    axs[5].set_title('bc')
    axs[6].plot(abc_list)
    axs[6].set_title('abc')

    return fig

def kinetic_equations(a, b, c, ab, bc, ac, kab, kac, kbc, kabc, kacb, kbca):

    d_a = -kab * a * b - kac * a * c - kbca * bc * a
    d_b = -kab * a * b - kbc * b * c - kacb * ac * b
    d_c = -kac * a * c - kbc * b * c - kabc * ab * c
    d_ab = kab * a * b - kabc * ab * c
    d_bc = kbc * b * c - kbca * bc * a
    d_ac = kac * a * c - kacb * ac * b
    d_abc = kabc * ab * c + kbca * bc * a + kacb * ac * b

    return d_a, d_b, d_c, d_ab, d_bc, d_ac, d_abc

def concentration_iterate(a:float=1, b:float=1, c:float=1,
                          kab:float=1, kac:float=1, kbc:float=1, kabc:float=1, kacb:float=1, kbca:float=1,
                          t_step_size:float=0.01, t_end:int=1000):

    a_list, b_list, c_list, ab_list, bc_list, ac_list, abc_list = [], [], [], [], [], [], []
    ab, bc, ac, abc = 0, 0, 0, 0

    for t in [t_step_size]*t_end:
        d_a, d_b, d_c, d_ab, d_bc, d_ac, d_abc = (
            kinetic_equations(a, b, c, ab, bc, ac, kab, kac, kbc, kabc, kacb, kbca))
        a += d_a*t
        b += d_b*t
        c += d_c*t
        ab += d_ab*t
        bc += d_bc*t
        ac += d_ac*t
        abc += d_abc*t

        a_list.append(a)
        b_list.append(b)
        c_list.append(c)
        ab_list.append(ab)
        bc_list.append(bc)
        ac_list.append(ac)
        abc_list.append(abc)

    # fig = plot_concs(a_list, b_list, c_list, ab_list, bc_list, ac_list, abc_list)

    return abc_list[-1]

def sweep_diff_concs():

    abc_list = []
    for a0 in range(1, 20):
        for b0 in range(1, 20):
            for c0 in range(1, 20):
                abc = concentration_iterate(a=a0, b=b0, c=c0)
                abc_list.append(abc / min(a0, b0, c0))
                print(f'abc: {abc_list[-1]}, a0: {a0}, b0: {b0}, c0: {c0}')

    return abc_list

if __name__ == "__main__":

    print(1)

