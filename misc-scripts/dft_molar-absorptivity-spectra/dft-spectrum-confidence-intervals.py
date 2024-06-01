import numpy as np
from matplotlib import pyplot as plt
import re
import importlib
st = importlib.import_module('uv-vis-absorption-spectroscopy.spectraltools')


def parse_tddft(text):
    # Excitation energies and oscillator strengths
    # Groups: id, spin symm, spat symm, dE, wavelength, osc. strength, S**2
    EXC_LINE = ''' Excited State\\s+(\\d+):\\s+([\\w\\.]+)-([\\?\\w'\\"]+)\\s+([0-9\\.-]+) eV\\s+([0-9\\.-]+) nm\\s+f=([0-9\\.-]+)\\s+<S\\*\\*2>=([0-9\\.]+)'''
    lines = text.split("\n")
    excited_states = list()
    for i, line in enumerate(lines):
        match = re.match(EXC_LINE, line)
        # if 'Excited State' in line:
        #     print(line)
        # groups are 'id', 'spin symm', 'spat symm', 'dE', 'wavelength', 'osc. strength', 'S**2'
        # add a dictionary to excited_states list, with keys matching group descriptions
        if match:
            excited_states.append({
                'id': int(match.group(1)),
                'spin symm': match.group(2),
                'spat symm': match.group(3),
                'dE': float(match.group(4)),
                'wavelength': float(match.group(5)),
                'osc. strength': float(match.group(6)),
                'S**2': float(match.group(7))
            })
            # print(excited_states[-1])

    return excited_states

def load_excited_states_from_gaussian_output_file(path_to_gaussian_file):
    with open(path_to_gaussian_file, 'r') as file:
        text = file.read()
    excited_states = parse_tddft(text)
    return excited_states

def ev_to_nm(energy):
    return 1240/energy

def gaussian_default_spectrum(vs, v_centers, fs, sigma):
    spectrum = np.zeros_like(vs)
    for v_center, f in zip(v_centers, fs):
        spectrum += 1.3062974e8 * f/sigma * np.exp(-1* (vs - v_center)**2 / sigma**2)
    return spectrum


def correct_lambdas(nms):
    return 1.234 * nms + 28.301


def gaussian_file_to_spectrum(gaussian_file, spectrum_npoints=1000, N_samples = 1000, ev_range=None):
    # From [Amjad Ali, Muhammad Imran Rafiq, Zhuohan Zhang, Jinru Cao, Renyong Geng,
    # Baojing Zhou* and Weihua Tang]
    # RMS in eV for CAM-B3LYP and all FREA types:
    RMSE_eV = 0.086  # eV

    # From [Mai Van Bay1,2, Nguyen Khoa Hien3
    # , Phan Thi Diem Tran3
    # , Nguyen Tran Kim Tuyen4
    # ,
    # Doan Thi Yen Oanh5
    # , Pham Cam Nam6*
    # , Duong Tuan Quang1*
    # Very roughly, it's like this. But I should digitize it and reanalyze in energy space
    # RMSE_eV = 1240/450 - 1240/(450 + 13)

    # best-fit delta and alpha from
    # Péter Pál Fehér*a
    # , Ádám Madarásza and András Stirling*a,b
    alpha = 1.14
    delta_FMS = 0.22
    excited_states = load_excited_states_from_gaussian_output_file(gaussian_file)
    v_centers = [state['dE'] for state in excited_states]
    v_centers = np.array(v_centers) / alpha
    fs = [state['osc. strength'] for state in excited_states]

    # # computing sigma based on fwhm
    # fwhm = 0.33 * 2
    # sigma = fwhm / (2*np.sqrt(2*np.log(2)))

    # Computing sigma based on delta_FMS
    # Since the Gaussian.inc definition of sigma and delta_FMS differ like so:
    # 2*delta_fms**2 == sigma**2 , we compute sigma from delta_FMS
    sigma = np.sqrt(2) * delta_FMS

    if ev_range is None:
        vs = np.linspace(np.min(v_centers) - sigma*3, np.max(v_centers) + sigma*3, spectrum_npoints)
    else:
        vs = np.linspace(ev_range[0], ev_range[1], spectrum_npoints)
    spectrum = gaussian_default_spectrum(vs, v_centers, fs, sigma)
    nms = ev_to_nm(vs)

    # sample the spectrum N_samples times
    spectra = np.zeros((N_samples, len(vs)))
    for i in range(N_samples):
        randomized_v_centers = np.random.normal(v_centers, RMSE_eV)
        spectra[i] = gaussian_default_spectrum(vs, randomized_v_centers, fs, sigma)

    # for each energy, find the one sigma percentile
    percentiles = np.percentile(spectra, [16, 84], axis=0)

    return nms, spectrum, percentiles


def plot_dft_vs_pink(gaussian_file, molar_concentration, legend=True, ymax=0.35, showmolar=False, ev_range=(1.3, 5)):
    print(f'Molar concentration: {molar_concentration} mol/L')
    nms, spectrum, percentiles = gaussian_file_to_spectrum(gaussian_file, ev_range=ev_range)

    data = np.load('D:/Docs/Dropbox/robochem/data/Yaroslav/mystery_prod/extracted_pink_spectrum.npy')
    cut_from = 170
    fig, ax = plt.subplots(figsize=(6,4))
    plt.plot(data[cut_from:, 0], data[cut_from:, 1], label='Measured in reaction crude', color='C1')

    cary_file = 'D:/Docs/Dropbox/robochem/data/Yaroslav/SN1_mystery_product_pi nk/deuterated_TLC_pink_from_rafal_rep1.csv'
    wav, spec = st.read_cary_agilent_csv_spectrum(cary_file, column_name='deuterated_TLC_pink_from_rafal_rep1')
    tlc_factor = 2.1
    plt.plot(wav, (spec - spec[0])*tlc_factor, label=f'Measured after prep. TLC, deuterated solvent, $\\times${tlc_factor:.1f}', zorder=10, color='C2')

    if showmolar:
        molarstring = f' for {molar_concentration*1e9:.1f} nmol/L'
    else:
        molarstring = ''
    plt.plot(nms, spectrum * molar_concentration, label=f'Theoretical (nominal spectrum){molarstring}', linestyle='--', color='black', zorder=-10)
    plt.fill_between(nms, percentiles[0] * molar_concentration, percentiles[1] * molar_concentration, alpha=0.4, label=f'Theoretical 1$\sigma$-confidence interval{molarstring}', color='grey', zorder=-10)

    plt.xlim(385, 800)
    plt.ylim(-0.01, ymax)
    plt.xlabel('Wavelength, nm')
    plt.ylabel('Absorbance per 1 cm path length, absorbance units')
    if legend:
        plt.legend()
    st.simpleaxis(ax)
    # plt.tight_layout()
    fig.savefig(f'misc-scripts/figures_for_articles/dft-uv-vis/{gaussian_file.split("/")[-1].replace(".out", ".png")}')


if __name__ == '__main__':
    base_folder = 'D:/Docs/Dropbox/Lab/pink-mystery/candidates/dimer_OHplus/'
    # plot_dft_vs_pink(gaussian_file = base_folder + 'dimer_OHplus_conf2_1054kjm_uv.out',
    #                  molar_concentration=1/(1e9*0.6/1.20*1.63),
    #                  legend=False)
    # plt.show()

    base_folder = 'D:/Docs/Dropbox/Lab/pink-mystery/candidates/other_candidates_uv/'
    # plot_dft_vs_pink(gaussian_file = base_folder + 'dimer_cage_anti_uv.out',
    #                  molar_concentration=2.5e-9, legend=False)
    # plt.show()
    #
    # plot_dft_vs_pink(gaussian_file = base_folder + 'dimer-double-bond-connected-optav-1-wb-pvdz-optfreq.out',
    #                  molar_concentration=3.5e-9, legend=False)
    # plt.show()
    #
    # plot_dft_vs_pink(gaussian_file = base_folder + 'g1_uv.out',
    #                  molar_concentration=100e-9, legend=False)
    # plt.show()
    #
    # plot_dft_vs_pink(gaussian_file = base_folder + 'mono_pin_rear1.out',
    #                  molar_concentration=2.5e-9, legend=True)
    # plt.show()
    #
    # plot_dft_vs_pink(gaussian_file = base_folder + 'mono_pin_rear2.out',
    #                  molar_concentration=2.5e-9, legend=False)
    # plt.show()
    #
    # plot_dft_vs_pink(gaussian_file = base_folder + 'monomer_radical.out',
    #                  molar_concentration=4e-9, legend=False)
    # plt.show()
    #
    # plot_dft_vs_pink(gaussian_file = base_folder + 'MONOMER_RADICAL-CATION-OPT1.out',
    #                  molar_concentration=1.6e-9, legend=False)
    # plt.show()
    plot_dft_vs_pink(gaussian_file = base_folder + 'g2_uv.out',
                     molar_concentration=1.6e-9, legend=False)
    plt.show()