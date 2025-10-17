##Modules importation##
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, peak_prominences, peak_widths
from scipy.optimize import curve_fit
from numpy.polynomial.polynomial import Polynomial
import os
import json
import math
import re, textwrap
import concurrent.futures
from scipy.optimize import least_squares
import matplotlib.patheffects as path_effects
import matplotlib

matplotlib.use('Agg')  # Use a non-interactive backend (no GUI)
plt.ioff() # Turn off interactive mode, so multithreading will work

# Disable multithreading for numpy and MKL to avoid conflicts with parallel processing in this script   #Uncomment this if your set--up have issue with multithreading
os.environ["OMP_NUM_THREADS"] = "1"                                 #Uncomment this if your set-up have issue with multithreading
os.environ['OPENBLAS_NUM_THREADS'] = '1'                            #Uncomment this if your set-up have issue with multithreading
os.environ['MKL_NUM_THREADS'] = '1'                                 #Uncomment this if your set-up have issue with multithreading

# get the system path of BRUCELEE_PROJECT_DATA_PATH
BRUCELEE_PROJECT_DATA_PATH = os.environ['BRUCELEE_PROJECT_DATA_PATH']

########################
########################

solvent_shift = None
peak_width_50 = None
threshold_amplitude = None
peaks_info, reference_shift = None, None

########Functions#########
def specify_para(sol_name, outlier_type=None):

    """Specify global NMR-processing parameters from the solvent name and, optionally,
    an outlier type.

    This routine sets a number of module-level globals used downstream in peak
    finding, integration, and assignment. Values depend on the `sol_name`
    (currently "DCE") and may be further adjusted for adressing outliers 
    requiring different windows or thresholds via `outlier_type` (eg."Type1" or "Type2")."""


    global solvent_shift, peak_width_50, threshold_amplitude, peaks_info, reference_shift

    if sol_name == 'DCE':
        solvent_shift = 3.73  #ppm DCE
        peak_width_50 = 0.008  #ppm at 50% #Default 0.01
        threshold_amplitude = 1E-7  # Minimum threshold to be integrated
        peaks_info = [  # Begining of region of itnerest, End of region of interest, expected peak number
            [5.20, 5.70],  # Substrate SM, 2H
            [4.1, 5.00],  # DCE
            [2.5, 3.05], #DCE 
            [6.5, 7.0],  # Product B, 1H
            [4.45, 4.70],  # Product A, 2H
            [2.2, 2.7],  # HBr adduct
            [7.80, 8.5],  #Ketone
            [8.5, 12], #Acid
        ]
        reference_shift = {
            "Starting material": [5.467],  # ppm #Confirmed
            "Product A": [4.527],  # ppm #Confirmed
            "Product B": [6.807],  # ppm #Confirmed
            "SolventDown": [4.775, 4.693, 4.605],  # ppm #Confirmed
            "SolventUp": [2.850, 2.764, 2.682],  # ppm #Confirmedz
            "Unknown impurity SM peak 1": [6.453],  # ppm
            "Unknown impurity SM peak 2": [4.474],  # ppm
            "Unknown impurity 1": [6.523],
            "Unknown impurity 2": [5.509],  # ppm
            "Unknown impurity 3": [4.340],  # ppm
            "Unknown impurity 4": [2.549],  # ppm
            "Alcohol": [6.727],  # ppm #Confirmed
            "HBr_adduct": [2.463],  # ppm #Confirmed
            "Acid": [8.5], #Acid
            #"Bromo ketone": [8.18],  # ppm
            #"Bromo ketone impurity 1": [7.99],  # ppm
            #"Bromo ketone impurity 2": [7.96],  # ppm 
        }

        if outlier_type == 'Type1':  # Type 1 outlier: Asymetric pick upshift of Product B
            print("Type1 error paras are set in if conditon!")
            # global solvent_shift, peak_width_50, threshold_amplitude, peaks_info, reference_shift


            solvent_shift = 3.73  #ppm DCE
            peak_width_50 = 0.008  #ppm at 50% #Default 0.01
            threshold_amplitude = 1E-7  # Minimum threshold to be integrated
            peaks_info = [  # Begining of region of itnerest, End of region of interest, expected peak number
                [5.20, 5.70],  # Substrate SM, 2H
                [4.1, 5.00],  # DCE
                [2.5, 3.05],  # DCE
                [6.5, 6.9],  # Product B, 1H   ############Truncate the asymetric peak for baseline fitting to take care
                [4.45, 4.70],  # Product A, 2H
                [2.2, 2.7],  # HBr adduct
                [7.80, 8.5],  #Ketone
                [8.5, 12], #Acid
            ]
            reference_shift = {
                "Starting material": [5.467],  # ppm  
                "Product A": [4.527],  # ppm
                "Product B": [6.807],  # ppm
                "SolventDown": [4.775, 4.693, 4.605],  # ppm
                "SolventUp": [2.850, 2.764, 2.682],  # ppm
                "Unknown impurity SM peak 1": [6.453],  # ppm
                "Unknown impurity SM peak 2": [4.474],  # ppm
                "Unknown impurity 1": [6.523],
                "Unknown impurity 2": [5.509],  # ppm
                "Unknown impurity 3": [4.340],  # ppm
                "Unknown impurity 4": [2.549],  # ppm
                "Alcohol": [6.727],  # ppm
                "HBr_adduct": [2.463],  # ppm
                "Acid": [8.5], #Acid
                #"Bromo ketone": [8.18],  # ppm
                #"Bromo ketone impurity 1": [7.99],  # ppm
                #"Bromo ketone impurity 2": [7.96],  # ppm 
            }
            #pass # change corresponding parameters
        elif outlier_type == 'Type2':  # Type 2 outlier: Asymetric pick downshift of Product B
            print("Type2 error paras are set in if conditon!")
            # global solvent_shift, peak_width_50, threshold_amplitude, peaks_info, reference_shift

            solvent_shift = 3.73  #ppm DCE
            peak_width_50 = 0.008  #ppm at 50% #Default 0.01
            threshold_amplitude = 1E-7  # Minimum threshold to be integrated
            peaks_info = [  # Begining of region of itnerest, End of region of interest, expected peak number
                [5.20, 5.70],  # Substrate SM, 2H
                [4.1, 5.00],  # DCE
                [2.5, 3.05],  # DCE
                [6.6, 7.0],  # Product B, 1H   ####Truncate the asymetric peak for baseline fitting to take care
                [4.45, 4.70],  # Product A, 2H
                [2.2, 2.7],  # HBr adduct
                [7.70, 8.5],  #Ketone
                [8.5, 9], #Acid
            ]
            reference_shift = {
                "Starting material": [5.467],  # ppm
                "Product A": [4.527],  # ppm
                "Product B": [6.807],  # ppm
                "SolventDown": [4.775, 4.693, 4.605],  # ppm
                "SolventUp": [2.850, 2.764, 2.682],  # ppm
                "Unknown impurity SM peak 1": [6.453],  # ppm
                "Unknown impurity SM peak 2": [4.474],  # ppm
                "Unknown impurity 1": [6.523],
                "Unknown impurity 2": [5.509],  # ppm
                "Unknown impurity 3": [4.340],  # ppm
                "Unknown impurity 4": [2.549],  # ppm
                "Alcohol": [6.727],  # ppm
                "HBr_adduct": [2.463],  # ppm
                "Acid": [8.5], #Acid
                #"Bromo ketone": [8.18],  # ppm
                #"Bromo ketone impurity 1": [7.99],  # ppm
                #"Bromo ketone impurity 2": [7.96],  # ppm 
            } 
        elif outlier_type == 'Type3':  # Type 2 outlier: Asymetric pick downshift of Product B
            print("Type2 error paras are set in if conditon!")
            # global solvent_shift, peak_width_50, threshold_amplitude, peaks_info, reference_shift

            solvent_shift = 3.73  #ppm DCE
            peak_width_50 = 0.008  #ppm at 50% #Default 0.01
            threshold_amplitude = 1E-7  # Minimum threshold to be integrated
            peaks_info = [  # Begining of region of itnerest, End of region of interest, expected peak number
                [5.20, 5.70],  # Substrate SM, 2H
                [4.1, 5.00],  # DCE
                [2.5, 3.05],  # DCE
                [6.6, 7.0],  # Product B, 1H   ####Truncate the asymetric peak for baseline fitting to take care
                [4.45, 4.70],  # Product A, 2H
                [2.2, 2.7],  # HBr adduct
                [7.80, 8.5],  #Ketone
                [8.5, 12], #Acid
            ]
            reference_shift = {
                "Starting material": [5.467],  # ppm
                "Product A": [4.527],  # ppm
                "Product B": [6.807],  # ppm
                "SolventDown": [4.775, 4.693, 4.605],  # ppm
                "SolventUp": [2.850, 2.764, 2.682],  # ppm
                "Unknown impurity SM peak 1": [6.453],  # ppm
                "Unknown impurity SM peak 2": [4.474],  # ppm
                "Unknown impurity 1": [6.523],
                "Unknown impurity 2": [5.509],  # ppm
                "Unknown impurity 3": [4.340],  # ppm
                "Unknown impurity 4": [2.549],  # ppm
                "Alcohol": [6.727],  # ppm
                "HBr_adduct": [2.463],  # ppm
                "Acid": [8.5], #Acid
                #"Bromo ketone": [8.18],  # ppm
                #"Bromo ketone impurity 1": [7.99],  # ppm
                #"Bromo ketone impurity 2": [7.96],  # ppm 
            } 
            #pass

    elif sol_name == 'MeCN':
        solvent_shift = 1.94  # ppm ACN
        peak_width_50 = 0.008  # ppm at 50% #Default 0.01
        threshold_amplitude = 1E-7  # Minimum threshold to be integrated
        peaks_info = [  # Begining of region of itnerest, End of region of interest, expected peak number
            #Old
            # [7.80, 14],
            # [6.5, 7.15],  
            # [4.4, 4.80],  
            # [3.8, 4.4],  
            # [2.8, 3.3],
            # [2.65,2.75]
            #New
            #[0.8, 1.6],
            #[2.0, 3.3],  #Not good, salt in the middle
            [2.0, 2.9],     #Instead of [2.0, 3.3],
            [3.65, 4.40],
            [4.41, 6.0],
            [6.5, 7.15],
            #[7.80, 14],  #Acid? #Irrelevant, skipped
        ]
        reference_shift = {
            "Starting material": [5.454],  # ppm #Confirmed
            "Water": [2.131],  #ppm #Confirmedp
            "Product A": [3.946],  # ppm 
            "Product B": [6.907],  # ppm #Confirmed
            "SolventDown": [2.788],  # ppm #Confirmed
            "SolventUp": [1.086],  # ppm #Confirmed
            "Unknown 1": [4.610],  # ppm (Observed in  3-1D EXTENDED+-20250325-182317) 3-1D EXTENDED+-20250325-182317:300Br2, 150DPE,0TBAB
            #"Unknown 2": [3.940],  # ppm (Observed in  3-1D EXTENDED+-20250325-182317) Probably Product A
            "Unknown 3": [7.024],  # ppm (Observed in  3-1D EXTENDED+-20250325-182317)
            "Unknown 4": [2.425],  # ppm (Observed in  1-1D EXTENDED+-20250325-142708)  1-1D EXTENDED+-20250325-142708: 300Br2, 75DPE,300TBAB #Potentially water
            "Unknown 5": [2.544],  # ppm (Observed in   7-1D EXTENDED+-20250325-185257)   7-1D EXTENDED+-20250325-185257: 112Br2, 262DPE,0TBAB
            #"Unknown 6": [2.463],  # ppm (Observed in   7-1D EXTENDED+-20250325-185257)
            "HBr_adduct": [2.463],  # ppm (Observed in   7-1D EXTENDED+-20250325-185257)
            "Unknown 7": [2.364],  # ppm (Observed in   7-1D EXTENDED+-20250325-185257)
            "Unknown 8": [2.937],  # ppm (Observed in  21-1D EXTENDED+-20250325-170904)  21-1D EXTENDED+-20250325-170904: 300Br2, 187DPE,0TBAB   #Detection hindered by salt
            "Unknown 9": [4.201],  # ppm (Observed in  21-1D EXTENDED+-20250325-170904)
            "Unknown 10": [4.645],  # ppm (Observed in  21-1D EXTENDED+-20250325-170904)
            "Acid": [8.0], #Acid? #Irrelevant, skipped
            "Water": [2.13]
        }

    elif sol_name == 'DCE-BF4':
        solvent_shift = 3.73  #ppm DCE
        peak_width_50 = 0.008  #ppm at 50% #Default 0.01
        threshold_amplitude = 1E-7  # Minimum threshold to be integrated
        peaks_info = [  # Begining of region of itnerest, End of region of interest, expected peak number
            [5.20, 5.70],  # Substrate SM, 2H
            [4.1, 5.00],  # DCE
            [2.5, 3.0],  # DCE #[2.5, 3.05], default 
            [6.5, 7.0],  # Product B, 1H
            [4.45, 4.70],  # Product A, 2H
            [2.2, 2.7],  # HBr adduct
            [7.80, 8.5],  #Ketone
            [8.5, 14], #Acid
        ]
        reference_shift = {
            "Starting material": [5.467],  # ppm #Confirmed
            "Product A": [4.527],  # ppm #Confirmed
            "Product B": [6.807],  # ppm #Confirmed
            "SolventDown": [4.775, 4.693, 4.605],  # ppm #Confirmed
            "SolventUp": [2.850, 2.764, 2.682],  # ppm #Confirmedz
            "Unknown impurity SM peak 1": [6.453],  # ppm
            "Unknown impurity SM peak 2": [4.474],  # ppm
            "Unknown impurity 1": [6.523],
            "Unknown impurity 2": [5.509],  # ppm
            "Unknown impurity 3": [4.340],  # ppm
            "Unknown impurity 4": [2.549],  # ppm
            "Alcohol": [6.727],  # ppm #Confirmed
            "HBr_adduct": [2.463],  # ppm #Confirmed
            "Acid": [8.5], #Acid
            "Bromo ketone": [8.18],  # ppm
            "Bromo ketone impurity 1": [7.99],  # ppm
            "Bromo ketone impurity 2": [7.96],  # ppm 
        }


        if outlier_type == 'Type1':  # Type 1 outlier
            pass # change corresponding parameters
        elif outlier_type == 'Type2':  # Type 2 outlier
            pass
    
    elif sol_name == 'MeCN-Nik':
        solvent_shift = 1.94  # ppm ACN
        peak_width_50 = 0.008  # ppm at 50% #Default 0.01
        threshold_amplitude = 1E-7  # Minimum threshold to be integrated
        peaks_info = [  # Begining of region of itnerest, End of region of interest, expected peak number
            [5.1, 6.2],  #[5.2, 6.2],
            #[3.6,4.0],   #Methoxy tend to shift, not fitted anymore
            [9.5,10.5],    
             
        ]
        reference_shift = {
            "Benzoin_monomethoxy-CH1": [5.87],  # ppm
            "Benzoin_monomethoxy-CH2": [5.95],  # ppm
            "Benzoin_dimethoxy-CH1": [5.73],  # ppm
            "Benzoin_dimethoxy-CH2": [5.731],  # ppm  
            # "Benzoin_dimethoxy-Methoxy1": [3.71],  #ppm
            # "Benzoin_dimethoxy-Methoxy2": [ 3.79],  #ppm  
            # "Carbene_precursor-Methoxy": [3.82],  #ppm 
            "p-Methoxybenzaldehyde-Methoxy": [3.86],  #ppm
            "p-Methoxybenzaldehyde-Carbonyl": [9.84], #ppm
            "Benzaldehyde-Carbonyl": [9.98], #ppm
            "Benzaldehyde-Carbonyl_satellite":[10.12], #ppm
            "Unknown_peak_2":[11.07], #ppm
            "unkown-double_doublet_1":[5.28], #ppm
            "unkown-double_doublet_2":[5.36], #ppm
            "unkown-double_doublet_3":[5.44], #ppm
            "unkown-double_doublet_4":[5.47], #ppm
            "unkown-doublet_1":[6.09], #ppm
            "unkown-doublet_2":[6.16], #ppm
            }

    elif sol_name == 'MeCN-Nik-4_pyr':
        solvent_shift = 1.94  # ppm ACN
        peak_width_50 = 0.008  # ppm at 50% #Default 0.01
        threshold_amplitude = 1E-7  # Minimum threshold to be integrated
        peaks_info = [  # Begining of region of itnerest, End of region of interest, expected peak number
            [5.1, 6.78],  #[5.2, 6.2],
            #[3.6,4.0],   #Methoxy tend to shift, not fitted anymore
            [9.5,10.5],    
             
        ]
        reference_shift = {
            "Benzoin_monomethoxy-CH1": [5.87],  # ppm
            "Benzoin_monomethoxy-CH2": [5.95],  # ppm
            "Benzoin_dimethoxy-CH1": [5.73],  # ppm
            "Benzoin_dimethoxy-CH2": [5.731],  # ppm  
            # "Benzoin_dimethoxy-Methoxy1": [3.71],  #ppm
            # "Benzoin_dimethoxy-Methoxy2": [ 3.79],  #ppm  
            # "Carbene_precursor-Methoxy": [3.82],  #ppm 
            "p-Methoxybenzaldehyde-Methoxy": [3.86],  #ppm
            "p-Methoxybenzaldehyde-Carbonyl": [9.84], #ppm
            "Benzaldehyde-Carbonyl": [9.98], #ppm
            "Benzaldehyde-Carbonyl_satellite":[10.12], #ppm
            "Unknown_peak_2":[11.07], #ppm
            "unkown-double_doublet_1":[5.28], #ppm
            "unkown-double_doublet_2":[5.36], #ppm
            "unkown-double_doublet_3":[5.44], #ppm
            "unkown-double_doublet_4":[5.47], #ppm
            "unkown-doublet_1":[6.09], #ppm
            "unkown-doublet_2":[6.16], #ppm
            }
        
    elif sol_name == 'MeCN-Nik-morph':
        solvent_shift = 1.94  # ppm ACN
        peak_width_50 = 0.008  # ppm at 50% #Default 0.01
        threshold_amplitude = 1E-7  # Minimum threshold to be integrated
        peaks_info = [  # Begining of region of itnerest, End of region of interest, expected peak number
            [4.0, 6.2],  #[5.2, 6.2],
            #[3.6, 4.0],   #Methoxy tend to shift, not fitted anymore
            [9.5,10.5],    
             
        ]
        reference_shift = {
            "Benzoin_monomethoxy-CH1": [5.87],  # ppm
            "Benzoin_monomethoxy-CH2": [5.95],  # ppm
            "Benzoin_dimethoxy-CH1": [5.73],  # ppm
            "Benzoin_dimethoxy-CH2": [5.731],  # ppm  
            # "Benzoin_dimethoxy-Methoxy1": [3.71],  #ppm
            # "Benzoin_dimethoxy-Methoxy2": [ 3.79],  #ppm  
            # "Carbene_precursor-Methoxy": [3.82],  #ppm 
            "p-Methoxybenzaldehyde-Methoxy": [3.86],  #ppm
            "p-Methoxybenzaldehyde-Carbonyl": [9.84], #ppm
            "Benzaldehyde-Carbonyl": [9.98], #ppm
            "Benzaldehyde-Carbonyl_satellite":[10.12], #ppm
            "Unknown_peak_2":[11.07], #ppm
            "unkown-double_doublet_1":[5.28], #ppm
            "unkown-double_doublet_2":[5.36], #ppm
            "unkown-double_doublet_3":[5.44], #ppm
            "unkown-double_doublet_4":[5.47], #ppm
            "unkown-doublet_1":[6.09], #ppm
            "unkown-doublet_2":[6.16], #ppm
            }
        
    elif sol_name == 'MeCN-Nik-DBU':
        solvent_shift = 1.94  # ppm ACN
        peak_width_50 = 0.008  # ppm at 50% #Default 0.01
        threshold_amplitude = 1E-7  # Minimum threshold to be integrated
        peaks_info = [  # Begining of region of itnerest, End of region of interest, expected peak number
            [4.9, 6.2],  #[5.2, 6.2],
            #[3.6,4.0],   #Methoxy tend to shift, not fitted anymore
            [9.5,10.5],    
             
        ]
        reference_shift = {
            "Benzoin_monomethoxy-CH1": [5.87],  # ppm
            "Benzoin_monomethoxy-CH2": [5.95],  # ppm
            "Benzoin_dimethoxy-CH1": [5.73],  # ppm
            "Benzoin_dimethoxy-CH2": [5.731],  # ppm  
            # "Benzoin_dimethoxy-Methoxy1": [3.71],  #ppm
            # "Benzoin_dimethoxy-Methoxy2": [ 3.79],  #ppm  
            # "Carbene_precursor-Methoxy": [3.82],  #ppm 
            "p-Methoxybenzaldehyde-Methoxy": [3.86],  #ppm
            "p-Methoxybenzaldehyde-Carbonyl": [9.84], #ppm
            "Benzaldehyde-Carbonyl": [9.98], #ppm
            "Benzaldehyde-Carbonyl_satellite":[10.12], #ppm
            "Unknown_peak_2":[11.07], #ppm
            "unkown-double_doublet_1":[5.28], #ppm
            "unkown-double_doublet_2":[5.36], #ppm
            "unkown-double_doublet_3":[5.44], #ppm
            "unkown-double_doublet_4":[5.47], #ppm
            "unkown-doublet_1":[6.09], #ppm
            "unkown-doublet_2":[6.16], #ppm
            }
    
    elif sol_name == 'DMSO-Nik':
        solvent_shift = 2.5  # ppm ACN
        peak_width_50 = 0.008  # ppm at 50% #Default 0.01
        threshold_amplitude = 1E-7  # Minimum threshold to be integrated
        peaks_info = [  # Begining of region of itnerest, End of region of interest, expected peak number
            [5.1, 6.2],
            #[3.6,4.0],   #Methoxy tend to shift, not fitted anymore
            [9.5,10.5],

        ]
        reference_shift = {
            "SM-NH2": [5.71],  # ppm
            "Benzoin_monomethoxy-CH1": [5.98],  # ppm
            "unkown-double_doublet_1":[5.46], #ppm
            "unkown-double_doublet_2":[5.49], #ppm
            "unkown-double_doublet_3":[5.53], #ppm
            "unkown-double_doublet_4":[5.57], #ppm
            "p-Methoxybenzaldehyde-Methoxy": [3.86],  #ppm To verify
            "p-Methoxybenzaldehyde-Carbonyl": [9.82], #ppm
            "Benzaldehyde-Carbonyl": [9.98], #ppmf
            "Benzaldehyde-Carbonyl_satellite":[10.12], #ppm
            "Unknown_peak_2":[11.07], #ppm
            }
        
    elif sol_name == 'DMSO-Nik-DBU':
        solvent_shift = 2.5  # ppm ACN
        peak_width_50 = 0.008  # ppm at 50% #Default 0.01
        threshold_amplitude = 1E-7  # Minimum threshold to be integrated
        peaks_info = [  # Begining of region of itnerest, End of region of interest, expected peak number
            [4.9, 6.2],
            #[3.6,4.0],   #Methoxy tend to shift, not fitted anymore
            [9.5,10.5],

        ]
        reference_shift = {
            "SM-NH2": [5.71],  # ppm
            "Benzoin_monomethoxy-CH1": [5.98],  # ppm
            "unkown-double_doublet_1":[5.46], #ppm
            "unkown-double_doublet_2":[5.49], #ppm
            "unkown-double_doublet_3":[5.53], #ppm
            "unkown-double_doublet_4":[5.57], #ppm
            "p-Methoxybenzaldehyde-Methoxy": [3.86],  #ppm To verify
            "p-Methoxybenzaldehyde-Carbonyl": [9.82], #ppm
            "Benzaldehyde-Carbonyl": [9.98], #ppmf
            "Benzaldehyde-Carbonyl_satellite":[10.12], #ppm
            "Unknown_peak_2":[11.07], #ppm
            }

    elif sol_name == 'DMSO-Nik-DBN':
        solvent_shift = 2.5  # ppm ACN
        peak_width_50 = 0.008  # ppm at 50% #Default 0.01
        threshold_amplitude = 1E-7  # Minimum threshold to be integrated
        peaks_info = [  # Begining of region of itnerest, End of region of interest, expected peak number
            [4.2, 6.4],
            #[3.6,4.0],   #Methoxy tend to shift, not fitted anymore
            [9.5,10.5],

        ]
        reference_shift = {
            "SM-NH2": [5.71],  # ppm
            "Benzoin_monomethoxy-CH1": [5.98],  # ppm
            "unkown-double_doublet_1":[5.46], #ppm
            "unkown-double_doublet_2":[5.49], #ppm
            "unkown-double_doublet_3":[5.53], #ppm
            "unkown-double_doublet_4":[5.57], #ppm
            "p-Methoxybenzaldehyde-Methoxy": [3.86],  #ppm To verify
            "p-Methoxybenzaldehyde-Carbonyl": [9.82], #ppm
            "Benzaldehyde-Carbonyl": [9.98], #ppmf
            "Benzaldehyde-Carbonyl_satellite":[10.12], #ppm
            "Unknown_peak_2":[11.07], #ppm
            }

def CSV_Loader(name_file, Yankai_temporary_fix=True):  #Yankai_temporary_fix: quick fix for the inverted ppm scale
    
    """Load the CSV for a given path `name_file`."""

    name_file = r"{}".format(name_file)
    data = pd.read_csv(name_file, delimiter=',', names=['Shift', 'Intensity'], skiprows=1).values
    if Yankai_temporary_fix == True:
        data[::-1, 1] = data[::, 1]
    if False:
        plt.figure(figsize=(12, 6))
        plt.plot(data[:, 0], data[:, 1], alpha=0.9, linewidth=2.5)
        plt.xlabel('Shift (ppm)')
        plt.ylabel('Intensity')
        plt.title('Loading check')
        plt.show()

    return (data)

def merge_overlapping_intervals(peaks_info):

    """Return the minimum set of intervals required to cover the sections of interest.
    Merge intervals when they are overlaping."""

    # Sort intervals based on the start of the range
    peaks_info.sort(key=lambda x: x[0])

    merged_intervals = []

    for interval in peaks_info:
        start, end = interval[:2]  # Extract the first two values (range start and end)

        if not merged_intervals or merged_intervals[-1][1] < start:
            # No overlap, add as a new separate interval
            merged_intervals.append([start, end])
        else:
            # Overlapping, merge with the last interval by extending the end point
            merged_intervals[-1][1] = max(merged_intervals[-1][1], end)

    return merged_intervals

def extract_slices(nmr_data, merged_intervals):
    """
    Extracts slices from the 2D numpy array based on merged intervals.

    Parameters:
    - nmr_data: 2D numpy array where first column is NMR SHIFT and second column is Intensity
    - merged_intervals: List of merged intervals [[start1, end1], [start2, end2], ...]

    Returns:
    - List of numpy arrays, each representing a slice
    """
    slices = []

    for start, end in merged_intervals:
        # Extract rows where NMR SHIFT falls within the interval
        mask = (nmr_data[:, 0] >= start) & (nmr_data[:, 0] <= end)
        slice_data = nmr_data[mask]
        slices.append(slice_data)

    return slices

def lorentzian(x, amp, cen, wid):
    # Define a Lorentzian function
    return (amp  / np.pi) * (wid/ ((x - cen) ** 2 + wid ** 2))

def sum_of_lorentzian(x, *params):
    # Define a sum of Lorentzians
    num_peaks = len(params) // 3
    y = np.zeros_like(x)

    for i in range(num_peaks):
        amp = params[i * 3]
        cen = params[i * 3 + 1]
        wid = params[i * 3 + 2]
        y += lorentzian(x, amp, cen, wid)

    return y

def gaussian(x, amp, cen, wid):
    # Define a Gaussian function
    return (amp/ (wid*(2*np.pi)**0.5) ) * np.exp(-0.5*( (x - cen) ** 2 / ( wid ** 2)))

def sum_of_gaussian(x, *params):
    # Define a sum of Gaussians
    num_peaks = len(params) // 3
    y = np.zeros_like(x)

    for i in range(num_peaks):
        amp = params[i * 3]
        cen = params[i * 3 + 1]
        wid = params[i * 3 + 2]
        y += gaussian(x, amp, cen, wid)

    return y

def pseudovoigt1(x, amp, cen, wid, prop):
    # Define a Voigt Sum function
    return prop*gaussian(x, amp, cen, wid)+ (1-prop)*lorentzian(x, amp, cen, wid)

def sum_of_voigt1(x, *params):
    # Define a sum of Voigt Sum function
    num_peaks = len(params) // 4
    y = np.zeros_like(x)

    for i in range(num_peaks):
        amp = params[i * 4]
        cen = params[i * 4 + 1]
        wid = params[i * 4 + 2]
        prop = params[i * 4 + 3]
        y += pseudovoigt1(x, amp, cen, wid, prop)

    return y

def pseudovoigt2(x, amp, cen, wid1, wid2, prop):
    # Define a Voigt Sum with 2 different half-width function
    return (1-prop)*gaussian(x, amp, cen, wid2) + (prop)*lorentzian(x, amp, cen, wid1)

def sum_of_voigt2(x, *params):
    # Define a sum of Voigt Sum with 2 different half-width function
    num_peaks = len(params) // 5
    y = np.zeros_like(x)

    for i in range(num_peaks):
        amp = params[i * 5]
        cen = params[i * 5 + 1]
        wid1 = params[i * 5 + 2]
        wid2 = params[i * 5 + 3]
        prop = params[i * 5 + 4]
        y += pseudovoigt2(x, amp, cen, wid1, wid2, prop)

    return y

def generalised_lorentzian(x, amp, cen, wid, prop):
    # Define a Genereralised Lorentzian function
    return (1-prop) *  amp * ((1 + ((x-cen)**2)) / (1 + (x - cen) ** 2 + (x - cen) ** 4 )) + (prop)*lorentzian(x, amp, cen, wid)

def sum_of_generalised_lorentzian(x, *params):
    # Define a sum of Generalised Lorentzian
    num_peaks = len(params) // 4
    y = np.zeros_like(x)

    for i in range(num_peaks):
        amp = params[i * 4]
        cen = params[i * 4 + 1]
        wid = params[i * 4 + 2]
        prop = params[i * 4 + 3]
        y += generalised_lorentzian(x, amp, cen, wid, prop)

    return y

def insert_every(lst, interval, value):
    
    """
    Inserts `value` into `lst` every `interval` elements.

    Parameters:
        lst      : List of elements (unchanged, original list).
        interval : Insert `value` after every `interval` items.
        value    : The value to insert.

    Returns:
        A new list with the value inserted at every `interval` position.
    """

    if interval <= 0:
        raise ValueError("Interval must be a positive integer.")

    result = []
    for i in range(0, len(lst), interval):
        result.extend(lst[i:i + interval])
        result.append(value)
    return result

def replace_in_groups(lst, group_size, indice_to_replace, value):
    
    """
    Replaces specific indices within each group of size `group_size`.

    Parameters:
        lst                : Input list (unchanged).
        group_size         : Number of items per group.
        indice_to_replace : Indice to replace within each group.
        value              : The value to insert at those indices.

    Returns:
        A new list with replacements applied group-wise.
    """

    if group_size <= 0:
        raise ValueError("Group size must be a positive integer.")
    
    result = lst[:]
    for i in range(0, len(lst)):
        if i - indice_to_replace // group_size == 0:
            result[i] = float(value)
    return result
        
def fit_without_bounds(model_func,shift_array, intensity_array, initial_guesses, std_deviation):
    
    """General method to fit in absence of boundaries for the parameters."""

    popt, covariance_matrix = curve_fit(
        model_func, shift_array, intensity_array, p0=initial_guesses,
        sigma=std_deviation * np.ones_like(shift_array),
        absolute_sigma=True,
        maxfev=20000,  # Increase max function evaluations
        ftol=1e-14,  # Function tolerance (adjust for better precision)
        xtol=1e-14,  # Parameter change tolerance
        gtol=1e-14,  # Gradient tolerance
    )
    return popt, covariance_matrix

def fit_with_bounds(model_func,shift_array, intensity_array, initial_guesses, std_deviation, lower_bounds, upper_bounds):
    
    """General method to fit using provided boundaries for the parameters."""

    popt, covariance_matrix = curve_fit(
        model_func, shift_array, intensity_array, p0=initial_guesses, bounds=[lower_bounds, upper_bounds],
        sigma=std_deviation * np.ones_like(shift_array),
        absolute_sigma=True,
        maxfev=20000,  # Increase max function evaluations
        ftol=1e-14,  # Function tolerance (adjust for better precision)
        xtol=1e-14,  # Parameter change tolerance
        gtol=1e-14,  # Gradient tolerance
    )
    return popt, covariance_matrix

def fit_with_bounds_do_your_best(model_func,shift_array, intensity_array, initial_guesses, std_deviation, lower_bounds, upper_bounds):
    
    """Method to fit using provided boundaries for the parameters.
    Used for cases where `fit_with_bounds` does not converge to be
    able to exctract the best acheived parameters regardless of the 
    convergence. This is use mainly as a last option in hard fitting
    cases such as multiple merging peaks or low S/N."""
    
    def residuals(params, x, y, sigma):
        return (y - model_func(x, *params)) / sigma

    try:
        result = least_squares(
            residuals,
            x0=initial_guesses,
            bounds=(lower_bounds, upper_bounds),
            args=(shift_array, intensity_array, std_deviation * np.ones_like(shift_array)),
            max_nfev=20000,
            ftol=1e-14,
            xtol=1e-14,
            gtol=1e-14
        )

        popt = result.x

        # Approximate covariance matrix like curve_fit (J^T J)^(-1)
        if result.jac.shape[0] >= result.jac.shape[1]:
            try:
                residual_variance = np.sum(result.fun**2) / (len(shift_array) - len(popt))
                jacobian = result.jac
                cov = np.linalg.inv(jacobian.T @ jacobian) * residual_variance
            except np.linalg.LinAlgError:
                cov = np.full((len(popt), len(popt)), np.nan)
        else:
            cov = np.full((len(popt), len(popt)), np.nan)

        return popt, cov

    except Exception as e:
        print(f"Total failure during least_squares: {e}")
        return np.full_like(initial_guesses, np.nan), np.full((len(initial_guesses), len(initial_guesses)), np.nan)

def exponential_decay(x, a, b, c):   # Gaussian type baseline
    return np.exp(np.clip(a * (x + b), -700, 700)) + c  # add clip to avoid overflow

def linear_baseline (x,a,b): #Linear type baseline
    return a*x+b

def exponential_decay_linear_corrected(x, a, b, c, d):   #EXPERIMENTAL (NOT TESTED YET)
    return np.exp(np.clip(a * (x + b), -700, 700)) + c + d * x  # add clip to avoid overflow

def baseline_fit(shift_array, intensity_array, ppm_per_index,baseline_linear_correction=False, force_line=False, ppm_window=0.1): #ppm_window=0.1 Default
    
    """Fit a baseline to spectral data using exponential or linear models. Data
    points near the center of the spectrum (within `ppm_window`) are down-
    weighted to avoid fitting the region of interest. The fitted baseline
    is returned as an array of the same length as the input.
    
        Parameters
    ----------
    shift_array : array_like
        1D array of chemical shift values (ppm).
    intensity_array : array_like
        1D array of intensity values corresponding to `shift_array`.
    ppm_per_index : float
        Conversion factor from array index to ppm, used to calculate
        how many indices correspond to `ppm_window`.
    baseline_linear_correction : bool, optional
        If False (default), fit a simple exponential decay.
        If True, fit an exponential decay with an additional linear term.
    force_line : bool, optional
        If True, override other options and fit a simple linear baseline.
        Default is False.
    ppm_window : float, optional
        Width (in ppm) of the central region to down-weight during fitting.
        Default is 0.1 ppm.

    Returns
    -------
    baseline : ndarray
        1D array of fitted baseline values, same shape as `shift_array`.

    Notes
    -----
    - Uses `scipy.optimize.curve_fit` with strict tolerances and increased
      iteration limits.
    - If `baseline_linear_correction=False` and `force_line=False`,
      the model is `exponential_decay`.
    - If `baseline_linear_correction=True` and `force_line=False`,
      the model is `exponential_decay_linear_corrected`.
    - If `force_line=True`, the model is `linear_baseline`.
    
    """

    
    indices_to_keep = int(ppm_window / ppm_per_index)
    shift_offset = shift_array[0]

    if False:
        # Plot data and fitted curve
        plt.plot(shift_array, intensity_array, label='Data', color='Black')
        plt.axvline(shift_array[indices_to_keep], color='blue', linestyle='--', label='Ignored Region Start')
        plt.axvline(shift_array[-indices_to_keep], color='blue', linestyle='--', label='Ignored Region End')
        plt.legend()
        plt.xlabel('Shift (ppm)')
        plt.ylabel('Intensity')
        plt.title('Baseline fitting')
        plt.show()

    # Define weights 
    weights = np.ones_like(intensity_array)  # Default all weights = 1

    # Mask data
    weights[indices_to_keep:-indices_to_keep] = 100

    # Select baseline function

    log_start=math.log(abs(intensity_array[0]))  
    log_end=math.log(abs(intensity_array[-1]))
    log_slope=(log_start-log_end)/(shift_array[0]-shift_array[-1])
    
    if baseline_linear_correction==False:
        baseline_function = exponential_decay
        initial_guess = [
            log_slope,   # A_guess (Amplitude)
            log_start/log_slope,  # B_guess (Decay/Growth)
            np.min(intensity_array),  # C_guess (Offset)
        ]
    else:
        baseline_function = exponential_decay_linear_corrected
        initial_guess = [
            log_slope,   # A_guess (Amplitude)
            log_start/log_slope,  # B_guess (Decay/Growth)
            np.min(intensity_array),  # C_guess (Offset)
            0 # D_guess (Linear correction)
        ]

    if force_line == True:
        baseline_function = linear_baseline
        initial_guess = [
            (intensity_array[0]-intensity_array[-1])/(shift_array[0]-shift_array[-1]),   # A_guess (Slope)
            np.min(intensity_array)  # B_guess (Intercept)
        ]
    
    params, covariance = curve_fit(baseline_function,
                                   shift_array - shift_offset,
                                   intensity_array,
                                   p0=initial_guess,
                                   sigma=weights,
                                   maxfev=10000,  # Increase max function evaluations
                                   ftol=1e-14,  # Function tolerance
                                   xtol=1e-14,  # Parameter change tolerance
                                   gtol=1e-14,  # Gradient tolerance
                                   )

    baseline = baseline_function(shift_array - shift_offset, *params)

    return baseline

def fit_peaks(NMR_spectrum, std_deviation,
              estimated_peak_width_for_indexes,
              peak_function,
              shift_tolerance=0.02,
              constrained_fit=True,
              baseline_correction=True,
              is_show_plot=False,
              ):
    
    """Detect and fit peaks in a 1D NMR spectrum, with optional baseline correction
    and bounded/unbounded nonlinear least-squares fitting.

    Workflow
    --------
    1) Detect candidate peaks with `scipy.signal.find_peaks` using a width estimate.
    2) Build initial guesses and bounds (center within ±`shift_tolerance`, widths/amplitudes ≥ 0).
    3) Optionally subtract a fitted baseline (`baseline_fit`) from the intensities.
    4) Fit the composite model `peak_function(shift, *params)` either with or
       without bounds.
    5) Return per-peak parameters, their 1σ uncertainties (from covariance),
       warnings, and a figure summarizing the fit.

    Parameters
    ----------
    NMR_spectrum : (N, 2) array_like
        Two-column array: first column is chemical shift (ppm), second column
        is intensity. Assumed uniformly spaced in shift.
    std_deviation : float
        Estimated noise standard deviation used to build the `sigma` weights for
        the fit (uniform across points). Interpreted as absolute sigma.
    estimated_peak_width_for_indexes : float
        Peak width estimate **in index units** for `find_peaks(width=...)`.
        This is also used to seed the initial width guesses (converted to ppm).
    peak_function : callable
        Composite model of the form `f(x, *params)` that sums all peaks. The
        function must accept (x, p1, p2, ...) where parameters are grouped per
        peak. Supported groupings in this function:
        - 3 parameters/peak: (amplitude, center, width)
        - 4 parameters/peak: (amplitude, center, width, shape) for
          `sum_of_generalised_lorentzian` or `sum_of_voigt1`
        - 5 parameters/peak: (amplitude, center, width_L, eta, width_G) for
          `sum_of_voigt2` (as used here)
    shift_tolerance : float, default 0.02
        Allowed deviation (± ppm) around each detected center for bounded fits.
    constrained_fit : bool, default True
        If True, fit with bounds using `fit_with_bounds` (fall back to
        `fit_with_bounds_do_your_best` on failure). If False, fit with
        `fit_without_bounds`.
    baseline_correction : bool, default True
        If True, estimate and subtract a baseline via `baseline_fit`. Several
        fallback window sizes are attempted; if all fail, a zero baseline is used.
    is_show_plot : bool, default False
        If True, displays a matplotlib figure with data, baseline, model fit,
        residuals, and the covariance heatmap. If False, closes the figure but
        still returns it.

    Returns
    -------
    opti_parameter : (P, K) ndarray
        Fitted parameters grouped per peak. `P` = number of peaks, `K` =
        parameters per peak (3, 4, or 5 depending on `peak_function`).
        Ordering within each group is as described under `peak_function`.
    opti_parameter_error : (P, K) ndarray
        standard deviations of the fitted parameters, computed as
        `sqrt(diag(covariance_matrix))` reshaped per peak.
    warning_string : str or None
        A message describing non-fatal issues (e.g., strong residuals, fallback
        baseline, or non-converged bounded fit). `None` if no warnings.
    fig : matplotlib.figure.Figure
        Summary figure containing:
        - Covariance matrix heatmap
        - Original spectrum, fitted model (including added-back baseline),
          baseline, residuals, and detected peaks
        The figure stores custom metadata in `fig._custom_metadata` with keys:
        `'intensity'`, `'shift'`, `'width'`,
        `'intensity_error'`, `'shift_error'`, `'width_error'`,
        `'peak_intensity_lorentzian'`.
"""
    
    
    shift_array = NMR_spectrum[:, 0]
    intensity_array = NMR_spectrum[:, 1]
    intensity_array_original = intensity_array.copy()
    ppm_step = shift_array[1] - shift_array[0]
    warning_string = None
    
      
    peaks, peaks_properties = find_peaks(intensity_array, width=estimated_peak_width_for_indexes)
    # If no peaks are found, stop
    if len(peaks) == 0:
        print(f"Slices skipped, no peak found.")
        return [], [], None, []

    # Get initial guesses for peak parameters (amplitude, center, width)
    initial_guesses = []
    lower_bounds = []
    upper_bounds = []
    parameter_number=3

    for peak, peak_width in zip(peaks[:], peaks_properties["widths"]):
        if intensity_array[peak] > 0:
            amp_guess = intensity_array[peak]  # Peak height
        else:
            amp_guess = std_deviation
        cen_guess = shift_array[peak]  # Peak center
        wid_guess = peak_width*  0.5 * ppm_step # Initial width guess (adjust as needed), default: peak_width_50
        initial_guesses.extend([amp_guess, cen_guess, wid_guess])
        lower_bounds.extend([0, cen_guess - shift_tolerance, 0])
        upper_bounds.extend([amp_guess * 2, cen_guess + shift_tolerance, wid_guess * 4])
    
    if peak_function == sum_of_generalised_lorentzian:
        initial_guesses = insert_every(initial_guesses, 3, 1)
        lower_bounds = insert_every(lower_bounds, 3, 0.0)
        upper_bounds = insert_every(upper_bounds, 3, 1.0)
        parameter_number=4

    if peak_function == sum_of_voigt1:
        initial_guesses = insert_every(initial_guesses, 3, 0.5)
        lower_bounds = insert_every(lower_bounds, 3, 0.0)
        upper_bounds = insert_every(upper_bounds, 3, 1.0)
        parameter_number=4

    if peak_function == sum_of_voigt2:
        initial_guesses = insert_every(initial_guesses, 3, wid_guess)
        lower_bounds = insert_every(lower_bounds, 3, 0.0)
        upper_bounds = insert_every(upper_bounds, 3,  wid_guess * 4)
        initial_guesses = insert_every(initial_guesses, 4, 1)
        lower_bounds = insert_every(lower_bounds, 4, 0.0)
        upper_bounds = insert_every(upper_bounds, 4, 1.0)
        parameter_number=5


    if baseline_correction == True:

        try:
            baseline = baseline_fit(shift_array, intensity_array, ppm_step)
        except Exception as e:
            print(f"Baseline could not be corrected:{e} \nAttempt with reduced window...")
            try:
                baseline = baseline_fit(shift_array, intensity_array, ppm_step, ppm_window=0.05)
            except:
                warning_string = "Baseline difficult to fit"
                try:
                    baseline = baseline_fit(shift_array, intensity_array, ppm_step, ppm_window=0.025)
                except:
                    print("Exponential baseline could not be fitted")
                    warning_string = "Exponential baseline could not be fitted"
                    try:
                        baseline = baseline_fit(shift_array, intensity_array, ppm_step,force_line=True, ppm_window=0.025)
                    except:
                        baseline = np.zeros_like(intensity_array)
                        warning_string = "No baseline could be fitted"

        finally:
            intensity_array -= baseline


    #Fitting
    try:
        if constrained_fit == False:
            popt, covariance_matrix = fit_without_bounds(peak_function,shift_array, intensity_array, initial_guesses,
                                                         std_deviation)
        else:
            try:
                popt, covariance_matrix = fit_with_bounds(peak_function,shift_array, intensity_array,
                                                        initial_guesses, std_deviation,
                                                        lower_bounds, upper_bounds)
                

            except:
                popt, covariance_matrix = fit_with_bounds_do_your_best(peak_function,shift_array, intensity_array,
                                                        initial_guesses, std_deviation,
                                                        lower_bounds, upper_bounds)
                warning_string = "Fit did not converge. "
        
        errors_of_parameters = np.sqrt(np.diag(covariance_matrix))
        opti_parameter = popt.reshape(-1, parameter_number)
        opti_parameter_error = errors_of_parameters.reshape(-1, parameter_number)

        # Generate fitted curve
        fitted_y = peak_function(shift_array, *popt)

        max_residuals = np.max(intensity_array - peak_function(shift_array, *popt))
        if max_residuals > 0.1 and warning_string == None:
            if warning_string !=None:
                warning_string = warning_string + "Strong residual: a peak might have been not fitted"
            else:
                warning_string = "Strong residual: a peak might have been not fitted"
                
        # Plot original data and fit results
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))  # Two subplots (1 row, 2 columns)
        # ---- Subplot 1: Covariance Matrix ----
        ax1 = axes[0]
        cax = ax1.imshow(covariance_matrix, cmap='seismic',
                         vmin=-1 * np.max(np.abs(covariance_matrix)),
                         vmax=np.max(np.abs(covariance_matrix)))
        fig.colorbar(cax, ax=ax1)
        ax1.set_title("Covariance Matrix")
        # ---- Subplot 2: Spectral Data and Fitting Results ----
        ax2 = axes[1]
        ax2.plot(shift_array, intensity_array_original, color='black', label="Original")
        ax2.plot(shift_array, fitted_y + baseline, 'r--',alpha=0.5, label="Lorentzian Fit")
        ax2.plot(shift_array, baseline, 'b--',alpha=0.5, label="Baseline Fit")
        ax2.plot(shift_array, intensity_array_original - fitted_y, color='silver',alpha=0.5, label="Residuals")
        ax2.scatter(shift_array[peaks], intensity_array_original[peaks], color='green',alpha=0.5, marker='o',
                    label="Detected Peaks")
        ax2.set_xlabel("Shift (ppm)")
        ax2.set_ylabel("Intensity")
        ax2.legend()
        ax2.set_title("Peak Fitting")

        peaks_shift = opti_parameter[:,1]

        peak_intensity_lorentzian = [peak_function(shift, *popt) + baseline[np.abs(shift_array - shift).argmin()] \
                                     for shift in peaks_shift]
        fig._custom_metadata = {'intensity': opti_parameter[:,0],
                               'shift': peaks_shift,
                               'width': opti_parameter[:,2],
                               'intensity_error': opti_parameter[:,0],
                               'shift_error': opti_parameter[:,1],
                               'width_error': opti_parameter[:,2],
                               'peak_intensity_lorentzian': peak_intensity_lorentzian,}
        if is_show_plot:
            plt.tight_layout()  # Adjust spacing between plots
            plt.show()
        else:
            plt.close(fig)

        return opti_parameter, opti_parameter_error, warning_string, fig

    except Exception as e:
        print(f"Curve fitting failed for this slice:{e}")
        return [], [], ["Fit failed"], 0

def integration_peak(peak_function, *arg):
    """Return integration of the peaks depending on the model used for fitting.
    This function is mostly a platform for further development. At the 
    moment, the main models used (Lorentzians, Gaussian and Voigt1) are based
    on normalised peak functions, resulting in amp = area."""

    if  peak_function == sum_of_lorentzian:
        amp, cen, wid = arg
        return amp 

    elif  peak_function == sum_of_gaussian:
        amp, cen, wid = arg
        return amp
    
    elif  peak_function == sum_of_generalised_lorentzian:
        amp, cen, wid, prop = arg
        return amp #TO BE DETERMINED PLACEHOLDER
    
    elif  peak_function == sum_of_voigt1:
        amp, cen, wid, prop = arg
        return amp
    
    elif  peak_function == sum_of_voigt2:
        amp, cen, wid1, wid2, prop = arg
        return amp  #TO BE DETERMINED PLACEHOLDER
    
    else:
        print("Model peak unkown. Integration impossible")

def find_closest_reference(fitted_center, reference_dict):
    """
    Find the closest reference shift in the dictionary for a given fitted peak center.
    
    - fitted_center: The peak center from the fitted parameters.
    - reference_dict: Dictionary of reference shifts.

    Returns:
    - The name of the closest product/material.
    - The corresponding reference shift.
    """
    closest_product = None
    closest_shift = None
    min_difference = float('inf')  # Initialize with a very large value  

    for product, shifts in reference_dict.items():
        for shift in shifts:  # Handle multiple reference shifts per product
            difference = abs(fitted_center - shift)
            if difference < min_difference:
                min_difference = difference
                closest_product = product
                closest_shift = shift
                

    return closest_product, closest_shift

def replot_fittings(figures, is_show_plot=False, dir=None):

    """Collect figures from the different fitting them as a single figure."""

    num_figs = len(figures)

    if num_figs == 0:
        print("No figures to plot.")
        return None

    num_cols = 2
    num_rows = math.ceil(num_figs / num_cols)

    # Create the figure with the correct number of rows and columns
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(4 * num_cols, 4 * num_rows))
    dir = dir.split('data')[1]
    dir = textwrap.fill(dir, width=70)

    fig.suptitle(dir, fontsize=12, fontweight="bold")

    # Flatten axes array for easy indexing
    axes = axes.flatten()

    # Iterate over stored figures and plot on the new shared figure
    for i, fig_old in enumerate(figures):
        for ax_old in fig_old.axes:  # Extract each axis from the stored figure
            x_min, x_max = ax_old.get_xlim()  # Get the x-axis limits
            for line in ax_old.get_lines():  # Extract line plots
                axes[i].plot(line.get_xdata(), line.get_ydata(), label=line.get_label(), alpha=0.8)

                # set title for each subplot
                title_text = f"ppm: {round(x_min,2)} - {round(x_max,2)}"
                axes[i].set_title(title_text, fontsize=15, fontweight="bold")

                # set y-axis limits and make it 120% of the original
                y_min, y_max = ax_old.get_ylim()
                y_range = y_max - y_min
                axes[i].set_ylim(y_min, y_max + 0.05 * y_range)
                # set x-axis limits and make it 110% of the original
                x_range = x_max - x_min
                axes[i].set_xlim(x_min - 0.03 * x_range, x_max + 0.03 * x_range)

            # axes[i].set_title(ax_old.get_title())
            axes[i].set_xlabel(ax_old.get_xlabel())
            axes[i].set_ylabel(ax_old.get_ylabel())
            if axes[i].has_data():  # Only add legend if data exists
                axes[i].legend()

            # print(f'#### Figure_metadata: {fig_old._custom_metadata} ###')
            for j in range(len(fig_old._custom_metadata['intensity'])):
                intensity_here = fig_old._custom_metadata['peak_intensity_lorentzian'][j]
                shift_here = fig_old._custom_metadata['shift'][j]

                # plot a red dot for each peak and make it bigger
                if x_min <= shift_here <= x_max:
                    axes[i].scatter(shift_here, intensity_here, color='blue', marker='o', s=100)
                    # plot the shift as text beside the dot
                    text = axes[i].text(shift_here, intensity_here, f"{round(shift_here, 2)}", fontsize=12,
                                 va='bottom', ha='right', clip_on=True, zorder=20,)
                    text.set_path_effects([
                        path_effects.Stroke(linewidth=3, foreground='white'),  # white edge
                        path_effects.Normal()  # normal text on top
                    ])

    plt.tight_layout()

    if is_show_plot:
        plt.show(block=True)  # Show only the combined figure and block execution
    else:
        plt.close(fig)  # Close the figure without showing it

    return fig

def integrate_spectrum(file_name, is_save_plot=True, is_show_plot=False):
    
    """
    NMR integration pipeline for a single spectrum file.

    This function loads a 1D NMR spectrum, estimates noise and peak width,
    slices the spectrum into regions of interest, fits peaks within each slice,
    integrates them, assigns them to references, and returns a results dictionary
    along with an experiment name inferred from the file path.

    The behavior relies on module-level configuration set elsewhere (e.g., by
    `set_global_params`), including `peak_width_50`, `peaks_info`,
    `threshold_amplitude`, and `reference_shift`.

    Parameters
    ----------
    file_name : str 
        Path to the spectrum file (CSV expected by `CSV_Loader`).
    is_save_plot : bool, default True
        If True, downstream plotting inside `process_nmr_peaks` is saved to disk
        in `file_dir`. Exact filenames are determined by that helper.
    is_show_plot : bool, default False
        If True, figures produced during fitting are displayed interactively.
        If False, figures are closed after creation.

    Returns
    -------
    results_dictionary : dict
        Aggregated outputs from `process_nmr_peaks`. The exact structure is
        defined by that function, typically including per-peak fitted parameters,
        uncertainties, integrated areas, assignments, and any warnings/notes.
    experiment_name : str
        Name inferred from the parent directory of `file_name`, useful for
        labeling outputs.

    Notes
    -----
    - Noise level is estimated as the standard deviation of the last 2000
      intensity points of the loaded spectrum:
      ``std_deviation = std(NMR_spectrum[-2000:, 1])``.
    - The estimated peak width in **index units** is computed from the global
      `peak_width_50` (ppm at 50%) divided by the spectral resolution (ppm/idx).
    - Regions of interest are derived by merging `peaks_info` via
      `merge_overlapping_intervals`, then slicing with `extract_slices`.
    - The default composite peak model is `sum_of_voigt1` (can be replaced if
      needed).
    - Core helpers used downstream:
        `CSV_Loader`, `merge_overlapping_intervals`, `extract_slices`,
        `process_nmr_peaks`, `fit_peaks`, `integration_peak`,
        `find_closest_reference`.
    - This function depends on globals: `peak_width_50`, `peaks_info`,
      `threshold_amplitude`, `reference_shift`. Ensure they are set before call.
    """
    
    # get the dir path of the file
    file_dir = os.path.dirname(file_name)
    # Remove the extension
    experiment_name = os.path.basename(os.path.dirname(file_name))  #= os.path.splitext(filename_with_ext)[0]

    NMR_spectrum = CSV_Loader(file_name)
    std_deviation = float(np.std(NMR_spectrum[-2000:, 1]))
    spectral_resolution = abs(NMR_spectrum[1, 0] - NMR_spectrum[0, 0])
    estimated_peak_width_for_indexes = peak_width_50 / spectral_resolution

    interval_to_slice_spectrum = merge_overlapping_intervals(peaks_info)

    if False:  # for debugging
        print(f"\nUseful interval in NMR: {interval_to_slice_spectrum}")

    NMR_slices = extract_slices(NMR_spectrum, interval_to_slice_spectrum)

    peak_function = sum_of_voigt1 # Default: sum_of_lorentzian
    
    results_dictionary = process_nmr_peaks(
        NMR_slices,
        std_deviation,
        estimated_peak_width_for_indexes,
        threshold_amplitude,
        reference_shift,
        fit_peaks,
        peak_function,
        integration_peak,
        find_closest_reference,
        file_dir,
        is_save_plot,
        is_show_plot,
    )

    return results_dictionary, experiment_name

def process_nmr_peaks(
        NMR_slices,
        std_deviation,
        estimated_peak_width_for_indexes,
        threshold_amplitude,
        reference_shift,
        fit_peaks_func,
        peak_function,
        integration_peak_func,
        find_closest_reference_func,
        file_dir,
        is_save_plot=True,
        is_show_plot=False,
        tolerance=0.05
                    ):
    """
    Fit, integrate, and assign peaks across sliced NMR regions, aggregating results.

    For each spectrum slice, this function:
      (1) fits peaks via `fit_peaks_func`,
      (2) computes per-peak areas and uncertainties,
      (3) assigns each fitted peak to the closest reference species,
      (4) selects at most one (closest/best) peak per species,
      (5) collects warnings and renders a combined summary figure.

    Parameters
    ----------
    NMR_slices : list[array_like]
        Iterable of sliced spectra. Each slice is an (N, 2) array-like object
        with columns [shift_ppm, intensity].
    std_deviation : float
        Estimated noise standard deviation for weighting in downstream fitting.
    estimated_peak_width_for_indexes : float
        Peak width estimate in index units used by `fit_peaks_func` for detection
        and initial guesses.
    threshold_amplitude : float
        Minimum amplitude required to keep a fitted peak (peaks below are ignored).
    reference_shift : dict[str, list[float]]
        Mapping {label -> list of expected shifts in ppm}. This routine uses the
        *first* shift per label as the primary reference.
    fit_peaks_func : callable
        Function with signature
        ``fit_peaks_func(slice, std_dev, est_width_idx, peak_function) -> (params, param_errs, warning, fig)``
        returning per-slice fitted parameters, their errors, an optional
        warning string, and a matplotlib Figure.
    peak_function : callable
        Composite model `f(x, *params)` used both for fitting and integration.
        Parameter grouping per peak must match what `fit_peaks_func` produces.
    integration_peak_func : callable
        Function computing the *area per peak* from `(peak_function, *peak_params)`.
        Must return area in the same units as the model amplitude; this code scales
        areas by 1000 afterwards.
    find_closest_reference_func : callable
        Function mapping `(fitted_center_ppm, reference_shift_dict) -> (label, ref_shift)`.
        Used to assign each peak to a product/species label.
    file_dir : str or os.PathLike
        Directory where the combined summary figure will be saved if `is_save_plot` is True.
    is_save_plot : bool, default True
        If True, saves the combined fitting figure as ``fitting_results.png`` in `file_dir`.
    is_show_plot : bool, default False
        If True, per-slice fit figures may be shown by downstream routines; the combined
        figure is also created.
    tolerance : float, default 0.05
        Extra selection heuristic (ppm): if two candidate peaks for the same product
        are within `tolerance` of the reference shift, prefer the one with larger area.

    Returns
    -------
    results_dictionary : dict
        Aggregated outputs with keys:
          - `'Raw peaks data'`: list of dicts per accepted fitted peak:
            `{product, center, area, area_uncertainty, parameter, amplitude, warning}`.
          - Per-product keys mapping to the selected peak area (scaled by 1000).
          - `'Warning'`: dict of warnings per product; may also contain
            `'UnmatchedPeaks'` with human-readable strings for above-threshold peaks
            not selected in the final assignment.

    Notes
    -----
    - Area and area uncertainty: this implementation assumes the model is normalized
      such that the area scales with amplitude; thus uncertainty is taken from
      the amplitude's error.
    - Peak assignment uses the closest reference shift.
    """

    all_peaks = []
    figures = []

    for slice in NMR_slices:
        parameters, parameter_errors, warning_string, fig = fit_peaks_func(slice, std_deviation, estimated_peak_width_for_indexes, peak_function)

        if fig:
            figures.append(fig)
            # print(f"################ Figure {len(figures)} created for slice.")

        for parameter, error in zip(parameters,parameter_errors):
            if parameter[0] < threshold_amplitude:
                continue

            fitted_center = parameter[1]
            peak_area = integration_peak_func(peak_function,*parameter) * 1000
            peak_area_uncertainty = error[0] * 1000  #Works if using Lorentzian, Gaussian or Voigt Model as their area is normalised by definition and scaled by amplitude parameter 
            closest_product, closest_shift = find_closest_reference_func(fitted_center, reference_shift)

            if 'SolventDown' in closest_product or 'SolventUp' in closest_product:
                continue

            all_peaks.append({
                'product': closest_product,
                'center': fitted_center,
                'area': peak_area,
                'area_uncertainty': peak_area_uncertainty,
                'parameter': parameter.tolist(),
                'amplitude': parameter[0],
                'warning': warning_string
            })

    # Assign closest peak to each product
    closest_peaks = {}
    for peak in all_peaks:
        prod = peak['product']
        center = peak['center']
        ref_center = reference_shift[prod]
        distance = abs(center - ref_center[0])

        if prod not in closest_peaks or distance < abs(closest_peaks[prod]['center'] - ref_center):
            closest_peaks[prod] = peak
            closest_peaks[prod]['area'] = peak['area']

    #####In test to avoid situation when a noise is detected and take place of the actual peak shifted
        if prod in closest_peaks and distance < tolerance and closest_peaks[prod]['area'] < peak['area']:
            closest_peaks[prod] = peak
            closest_peaks[prod]['area'] = peak['area']
    #####

    results_dictionary = {'Warning': {}}
    results_dictionary['Raw peaks data'] = all_peaks

    for prod, peak in closest_peaks.items():
        results_dictionary[prod] = peak['area']
        if peak['warning'] is not None:
            results_dictionary['Warning'][prod] = peak['warning']

    # Extract unmatched peaks (above-threshold, not assigned)
    assigned_peak_ids = {id(peak) for peak in closest_peaks.values()}

    unmatched_peaks = [
        f"center={round(peak['center'], 3)} ppm    area={peak['area']}     param={peak['parameter']}"
        for peak in all_peaks
        if id(peak) not in assigned_peak_ids and peak['amplitude'] >= threshold_amplitude
    ]

    if unmatched_peaks:
        results_dictionary['Warning']['UnmatchedPeaks'] = unmatched_peaks

    fig_combined = replot_fittings(figures, is_show_plot=is_show_plot, dir=file_dir)

    if is_save_plot and fig_combined:
        fig_combined.savefig(file_dir + "\\fitting_results.png")

    return results_dictionary

def analyze_one_spectrum(file_name, sol_name,  outliers):
    
    """
    Configure globals for a given solvent/outlier case, analyze a single spectrum,
    and return the experiment name with its results.

    If `outliers` is falsy, the routine calls `specify_para(sol_name)` to set
    module-level parameters. Otherwise it tries to infer a vial identifier from
    `file_name` using the regex ``r'(\\d+)-1D'``; if that vial ID exists in the
    `outliers` mapping, it calls `specify_para(sol_name, outliers[vial_id])`
    to apply the appropriate outlier type, else falls back to `specify_para(sol_name)`.
    The spectrum is then processed via `integrate_spectrum`.

    Parameters
    ----------
    file_name : str or os.PathLike
        Path to the spectrum file to analyze. The vial ID is extracted from this
        string using the pattern ``'<digits>-1D'`` (e.g., ``'.../023-1D/...'``).
    sol_name : str
        Solvent key passed to `specify_para`, e.g., "DCE" or "MeCN".
    outliers : dict or mapping
        Mapping from integer vial IDs to outlier type strings understood by
        `specify_para`. If empty/falsy, outlier handling is skipped.

    Returns
    -------
    experiment_name : str
        Name inferred by `integrate_spectrum` from the file path (typically the
        parent directory name of `file_name`).
    experiment_dictionary : dict
        Results produced by `integrate_spectrum`, typically including fitted
        parameters, uncertainties, integrated areas, assignments, and warnings.
    """
    
    # Specify global parameters based on the solvent name and outlier_type
    if not outliers:
        specify_para(sol_name)
    else:
        print(file_name)
        # Extract vial number by regex
        vial_name_here = re.search(r'(\d+)-1D', file_name).group(1)
        vial_name_here = int(vial_name_here)
        if vial_name_here in outliers.keys():
            specify_para(sol_name, outliers[vial_name_here])
            print('##########Outlier type specified for vial##########:', file_name)

        else:
            specify_para(sol_name)


    # Analyze spectrum and return results
    experiment_dictionary, experiment_name = integrate_spectrum(file_name, is_save_plot=True, is_show_plot=False)
    print(f"\n{experiment_name}: {experiment_dictionary}")

    return experiment_name, experiment_dictionary


def analyze_one_run_folder(master_path,
                           sol_name='DCE',
                           outliers=None,  # Example: {33:'Type1', 43:'Type2'}
                           is_show_plot=False):

    """
    Batch-analyze all 1D spectra in a run folder and save aggregated results.

    The function scans ``<master_path>/Results`` for subfolders whose path names
    contain the substring ``"1D EXTENDED"``. For each such folder, it expects a
    ``data.csv`` file, submits it to `analyze_one_spectrum` in parallel, and
    aggregates the per-experiment outputs into:
      * ``fitting_results.json`` — a dict mapping experiment names to their
        results dictionaries, and
      * ``fitting_list.txt`` — a newline-separated list of experiment names.

    Parameters
    ----------
    master_path : str or os.PathLike
        Path to the run folder that contains a ``Results`` subdirectory.
    sol_name : str, default 'DCE'
        Solvent identifier forwarded to the parameter-setting routine used by
        `analyze_one_spectrum` (e.g., "DCE", "MeCN").
    outliers : dict[int, str] or None, optional
        Mapping from vial IDs (integers parsed from file paths) to outlier type
        strings (e.g., ``{33: "Type1", 43: "Type2"}``). Passed through to
        `analyze_one_spectrum`.
    is_show_plot : bool, default False
        Reserved flag to control plotting behavior; currently **not forwarded**
        to `analyze_one_spectrum` (plots there are saved, not shown).

    Returns
    -------
    None
        Results are written to disk:
          - ``<master_path>/Results/fitting_results.json``
          - ``<master_path>/Results/fitting_list.txt``

    Notes
    -----
    Parallelism: We encountered issues depending on the configuration
    of the computer running using multhreading. Two modes are available:
    multithreading or multiprocessing. To change the mode:
    - comment:
        -`with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:`
    - uncomment:
        - `with concurrent.futures.ProcessPoolExecutor(max_workers=12) as executor:`
        - os.environ["OMP_NUM_THREADS"] = "1"
        - os.environ['OPENBLAS_NUM_THREADS'] = '1'
        - os.environ['MKL_NUM_THREADS'] = '1'

    By default, parallelism uses 12 workers.
    """

    data_dir_ls = []
    data_file_ls = []

    results_path = os.path.join(master_path, "Results")
    if not os.path.isdir(results_path):  # Ensure "Results" is a directory
        raise FileNotFoundError(f"Error! Results folder not found in: {master_path}")

    # Iterate through subfolders inside "Results", and get all csv data files
    for folder in os.listdir(results_path):
        folder_path = os.path.join(results_path, folder)
        if "1D EXTENDED" in folder_path:
            try:
                data_dir_ls.append(folder_path)
                data_file = folder_path + "\\data.csv"
                if not os.path.isfile(data_file):
                    raise FileNotFoundError(f"Error! Data file not found in: {folder_path}")
                data_file_ls.append(data_file)
            except Exception as e:
                print(f"An error occured in:{folder_path}")
                print(f"Error: {e}")

    total_result_dictionary = {}
    list_experiment_loaded = []

    # Use ThreadPoolExecutor for multithreaded analysis
    #with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:  ###Comment this if your set-up have issue with multithreading
    with concurrent.futures.ProcessPoolExecutor(max_workers=14) as executor:  ###Uncomment this if your set-up have issue with multithreading, 12 worker by default

        # Submit all file jobs to the thread pool
        futures = [executor.submit(analyze_one_spectrum, file_name, sol_name, outliers)
                   for file_name in data_file_ls]

        # Collect results as they finish
        for future in concurrent.futures.as_completed(futures):
            try:
                experiment_name, experiment_dictionary = future.result()
                list_experiment_loaded.append(experiment_name)
                total_result_dictionary[experiment_name] = experiment_dictionary
            except Exception as e:
                print(f"Error processing file: {e}")

    # Save dictionary as JSON
    json_filename = os.path.join(results_path, f"fitting_results.json")
    with open(json_filename, "w") as json_file:
        json.dump(total_result_dictionary, json_file, indent=4)

    # Save list to text file (each entry on a new line)
    text_filename = os.path.join(results_path, f"fitting_list.txt")
    with open(text_filename, "w") as text_file:
        text_file.write("\n".join(list_experiment_loaded))  # Write each list item on a new line


if __name__ == "__main__":

    data_dir = BRUCELEE_PROJECT_DATA_PATH
    print(f"Path: {BRUCELEE_PROJECT_DATA_PATH}")
    # run folder structure: [run_folder, run_sol, run_outliers]
    run_folders = [
                #Bruce Lee
                # ["\\DPE_bromination\\2025-02-19-run02_normal_run\\", 'DCE', None],
                # ["\\DPE_bromination\\2025-03-01-run01_normal_run\\", 'DCE', None],
                # ["\\DPE_bromination\\2025-03-03-run01_normal_run\\", 'DCE', {46: 'Type1', 47: 'Type2'}],
                # [r"\\LGA\\test-tempo\\2025-03-03-run01_normal_run\\", 'DCE', {46: 'Type1', 47: 'Type2', 34: 'Type3'}],
                # ["\\DPE_bromination\\2025-03-03-run02_normal_run\\", 'DCE', None],
                # ["\\DPE_bromination\\2025-03-05-run01_normal_run\\", 'DCE', None],
                # ["\\DPE_bromination\\2025-03-12-run01_better_shimming\\", 'DCE', None]
                # ["\\DPE_bromination\\2025-03-24-run01_MeCN_normal\\", 'MeCN', None],
                # ["\\DPE_bromination\\2025-03-24-run02_MeCN_normal\\", 'MeCN', None],
                # ["\\DPE_bromination\\2025-04-01-run01_MeCN_normal\\", 'MeCN', None],
                # ["\\DPE_bromination\\2025-04-02-run01_MeCN_normal\\", 'MeCN', None],
                # ["\\DPE_bromination\\2025-04-02-run02_MeCN_normal\\", 'MeCN', None],
                # ["\\DPE_bromination\\2025-04-02-run03_MeCN_normal\\", 'MeCN', None],
                # ["\\DPE_bromination\\2025-04-03-run01_MeCN_normal\\", 'MeCN', None],
                # ["\\DPE_bromination\\2025-04-03-run02_MeCN_normal\\", 'MeCN', None],
                # ["\\DPE_bromination\\2025-04-08-run01_MeCN_normal\\", 'MeCN', None],
                # [r"\\DPE_bromination\\_Refs_MeCN\\Ref_B", 'MeCN', None],
                # [r"\\DPE_bromination\\_Refs_MeCN\\Ref_S", 'MeCN', None],
                # [r"\\DPE_bromination\\2025-02-19-run02_normal_run", 'DCE', None],
                # [r"\\DPE_bromination\\2025-03-01-run01_normal_run", 'DCE', None],
                # [r"\\DPE_bromination\\2025-03-03-run01_normal_run", 'DCE', {46: 'Type1', 47: 'Type2',34: 'Type3'}],
                # [r"\\DPE_bromination\\2025-03-03-run02_normal_run", 'DCE', None],
                # [r"\\DPE_bromination\\2025-03-05-run01_normal_run", 'DCE', None],
                # [r"\\DPE_bromination\\2025-03-12-run01_better_shimming", 'DCE', None],
                # [r"\\DPE_bromination\\2025-07-01-run01_DCE_TBABr_rerun", 'DCE', None],
                # [r"\\DPE_bromination\\_Refs\\ref_S_all_TBABr",'DCE',None],
                [r"\\DPE_bromination\\_Refs\\ref_S_all_TBPBr", 'DCE', None],
                # [r"\\DPE_bromination\\_Refs\\ref_S_all_TBABF4", 'DCE', None],

                # [r"\\DPE_bromination\\2025-04-28-run01_DCE_TBABF4_normal", 'DCE', None],
                # [r"\\DPE_bromination\\2025-04-28-run02_DCE_TBABF4_normal", 'DCE', None],
                # [r"\\DPE_bromination\\2025-04-28-run03_DCE_TBABF4_normal", 'DCE', None],
                # [r"\\DPE_bromination\\2025-04-28-run04_DCE_TBABF4_normal", 'DCE', None],
                # [r"\\DPE_bromination\\2025-09-09-run01_DCE_TBABF4_add", 'DCE', None],              [r"\\DPE_bromination\\2025-09-09-run01_DCE_TBABF4_add", 'DCE', None],
                # [r"\\DPE_bromination\\2025-09-09-run02_DCE_TBABF4_add", 'DCE', None],
                #
                # [r"\\DPE_bromination\\2025-05-30-run01_DCE_TBPBr_normal", 'DCE', None],
                # [r"\\DPE_bromination\\2025-05-30-run02_DCE_TBPBr_normal", 'DCE', None],
                # [r"\\DPE_bromination\\2025-05-30-run03_DCE_TBPBr_normal", 'DCE', None],
                # [r"\\DPE_bromination\\2025-05-30-run04_DCE_TBPBr_normal", 'DCE', None],
                # [r"\\DPE_bromination\\2025-09-10-run01_DCE_TBPBr_add", 'DCE', None],
                # [r"\\DPE_bromination\\2025-09-10-run02_DCE_TBPBr_add", 'DCE', None],

                # [r"\\DPE_bromination\\2025-09-11-run01_DCE_TBABr3_add", 'DCE', None],
                # [r"\\DPE_bromination\\2025-09-11-run02_DCE_TBABr3_add", 'DCE', None],

                # #NIK Calibration
                # ["\\NV\\Final Data\\Calibrations\\MeCN\\Methoxy benzoin_4\\",'MeCN-Nik', None],

                # #NIK ACN Pyridine serie
                # ["\\NV\\Final Data\\MeCN\\Pyridine-based nucleophiles\\Pyridine_cmpd\\2025-05-15-run01_MeCN_Pyr\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Pyridine-based nucleophiles\\DMAP\\2025-06-16-run01_MeCN_DMAP\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Pyridine-based nucleophiles\\DMAP\\2025-06-16-run02_MeCN_DMAP\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Pyridine-based nucleophiles\\4-Pyrrolidinopyridine\\2025-06-25-run01_MeCN_4_Pyrrol_Pyr\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Pyridine-based nucleophiles\\4-Pyrrolidinopyridine\\2025-06-25-run02_MeCN_4_Pyrrol_Pyr\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Pyridine-based nucleophiles\\4-Morpholino pyridine\\2025-06-20-run01_MeCN_4_Morph_Pyr\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Pyridine-based nucleophiles\\4-Morpholino pyridine\\2025-06-20-run02_MeCN_4_Morph_Pyr\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Pyridine-based nucleophiles\\4-Methyl pyridine\\2025-06-18-run01_MeCN_4_Me_Pyr\\", 'MeCN-Nik-longer_range', None],
                # ["\\NV\\Final Data\\MeCN\\Pyridine-based nucleophiles\\4-Methyl pyridine\\2025-06-18-run02_MeCN_4_Me_Pyr\\", 'MeCN-Nik-longer_range', None],
                # ["\\NV\\Final Data\\MeCN\\Pyridine-based nucleophiles\\4-Methoxy pyridine\\2025-06-22-run01_MeCN_4_Methoxy_Pyr\\", 'MeCN-Nik-4_pyr', None],
                # ["\\NV\\Final Data\\MeCN\\Pyridine-based nucleophiles\\4-Methoxy pyridine\\2025-06-22-run02_MeCN_4_Methoxy_Pyr\\", 'MeCN-Nik-4_pyr', None],
               
                #OLD
                # ["\\NV\\Final Data\\MeCN\\Pyridine-based nucleophiles\\4-Pyrrolidinopyridine\\2025-05-19-run01_MeCN_4_pyrrolidinopyridine\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Pyridine-based nucleophiles\\4-Pyrrolidinopyridine\\2025-05-19-run02_MeCN_4_pyrrolidinopyridine\\", 'MeCN-Nik', None],

                # #NIK ACN Other base serie
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\DABCO\\2025-06-02-run01_MeCN_DABCO\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\DABCO\\2025-06-02-run02_MeCN_DABCO\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\DBN\\2025-06-03-run01_MeCN_DBN\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\DBN\\2025-06-03-run02_MeCN_DBN\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\DBU\\2025-05-21-run01_MeCN_DBU\\", 'MeCN-Nik-DBU', None],
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\DBU\\2025-05-21-run02_MeCN_DBU\\", 'MeCN-Nik-DBU', None],
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\Morpholine\\2025-06-23-run01_MeCN_Morph\\", 'MeCN-Nik-morph', None],
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\Morpholine\\2025-06-23-run02_MeCN_Morph\\", 'MeCN-Nik-morph', None],
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\N-Methyl morpholine\\2025-06-24-run01_MeCN_N_Me_Morph\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\N-Methyl morpholine\\2025-06-24-run02_MeCN_N_Me_Morph\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\N-Methyl piperidine\\2025-05-26-run01_MeCN_1MePiper\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\N-Methyl piperidine\\2025-05-26-run02_MeCN_1MePiper\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\N-Methyl pyrrolidine\\2025-06-27-run01_MeCN_N_Me_Pyrrol\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\N-Methyl pyrrolidine\\2025-06-27-run02_MeCN_N_Me_Pyrrol\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\Piperidine\\2025-06-01-run01_MeCN_Piper\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\Piperidine\\2025-06-01-run02_MeCN_Piper\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\Pyrrolidine\\2025-06-25-run01_MeCN_Pyrrol\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\Pyrrolidine\\2025-06-25-run02_MeCN_Pyrrol\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\Quinuclidine\\2025-06-14-run01_MeCN_Quinuclidine\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\MeCN\\Other nucleophiles\\Quinuclidine\\2025-06-14-run01_MeCN_Quinuclidine\\", 'MeCN-Nik', None],

                # #NIK DMSO Pyridine serie
                # ["\\NV\\Final Data\\DMSO\\Pyridine-based nucleophiles\\DMAP\\2025-06-17-run01_DMSO_DMAP\\", 'DMSO-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Pyridine-based nucleophiles\\DMAP\\2025-06-17-run02_DMSO_DMAP\\", 'DMSO-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Pyridine-based nucleophiles\\Pyridine\\2025-06-04-run01_DMSO_Pyr\\", 'DMSO-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Pyridine-based nucleophiles\\Pyridine\\2025-06-04-run02_DMSO_Pyr\\", 'DMSO-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Pyridine-based nucleophiles\\4-Pyrrolidino pyridine\\2025-06-07-run01_DMSO_4_Pyrr_Pyr\\", 'DMSO-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Pyridine-based nucleophiles\\4-Pyrrolidino pyridine\\2025-06-07-run02_DMSO_4_Pyrr_Pyr\\", 'DMSO-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Pyridine-based nucleophiles\\4-Pyrrolidino pyridine\\2025-06-26-run01_DMSO_4_Pyrrol_Pyr\\", 'DMSO-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Pyridine-based nucleophiles\\4-Pyrrolidino pyridine\\2025-06-26-run02_DMSO_4_Pyrrol_Pyr\\", 'DMSO-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Pyridine-based nucleophiles\\4-Morpholino pyridine\\2025-06-21-run01_DMSO_4_Morph_Pyr\\", 'DMSO-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Pyridine-based nucleophiles\\4-Morpholino pyridine\\2025-06-21-run02_DMSO_4_Morph_Pyr\\", 'DMSO-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Pyridine-based nucleophiles\\4-Methyl pyridine\\2025-06-19-run01_DMSO_4_Me_Pyr\\", 'DMSO-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Pyridine-based nucleophiles\\4-Methyl pyridine\\2025-06-19-run01_DMSO_4_Me_Pyr\\", 'DMSO-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Pyridine-based nucleophiles\\4-Methoxy pyridine\\2025-06-22-run01_DMSO_4_Methoxy_Pyr\\", 'DMSO-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Pyridine-based nucleophiles\\4-Methoxy pyridine\\2025-06-22-run02_DMSO_4_Methoxy_Pyr\\", 'DMSO-Nik', None],
                
                # #NIK DMSO Other base serie
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\DABCO\\2025-06-12-run01_DMSO_DABCO\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\DABCO\\2025-06-12-run02_DMSO_DABCO\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\DBN\\2025-06-09-run01_DMSO_DBN\\", 'MeCN-Nik-DBN', None],
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\DBN\\2025-06-09-run02_DMSO_DBN\\", 'MeCN-Nik-DBN', None],
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\DBU\\2025-06-08-run01_DMSO_DBU\\", 'MeCN-Nik-DBU', None],
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\DBU\\2025-06-08-run02_DMSO_DBU\\", 'MeCN-Nik-DBU', None],
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\Morpholine\\2025-06-26-run01_DMSO_Morpholine\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\Morpholine\\2025-06-26-run02_DMSO_Morpholine\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\N-Methyl morpholine\\2025-06-24-run01_DMSO_Morpholine\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\N-Methyl morpholine\\2025-06-24-run02_DMSO_Morpholine\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\N-Methyl piperidine\\2025-06-11-run01_DMSO_1_Me_Piper\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\N-Methyl piperidine\\2025-06-11-run02_DMSO_1_Me_Piper\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\N-Methyl pyrrolidine\\2025-06-28-run01_DMSO_N_Me_Pyrrolidine\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\N-Methyl pyrrolidine\\2025-06-28-run02_DMSO_N_Me_Pyrrolidine\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\Piperidine\\2025-06-10-run01_DMSO_Piper\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\Piperidine\\2025-06-10-run02_DMSO_Piper\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\Pyrrolidine\\2025-06-25-run01_DMSO_Pyrrolidine\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\Pyrrolidine\\2025-06-25-run02_DMSO_Pyrrolidine\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\Quinuclidine\\2025-06-15-run01_DMSO_Quinuclidine\\", 'MeCN-Nik', None],
                # ["\\NV\\Final Data\\DMSO\\Other nucleophiles\\Quinuclidine\\2025-06-15-run02_DMSO_Quinuclidine\\", 'MeCN-Nik', None],
            ]

    for run_folder in run_folders:
        print(f"Run: {run_folder}")
        run_dir = data_dir + run_folder[0]
        run_sol = run_folder[1]
        run_outliers = run_folder[2]
        analyze_one_run_folder(run_dir, run_sol, run_outliers,is_show_plot=False)

    print("All runs processed successfully.")