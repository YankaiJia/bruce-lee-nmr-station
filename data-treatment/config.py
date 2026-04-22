import os

BRUCELEE_PROJECT_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))

# Root folder of the experimental dataset.
# Download from Zenodo (https://doi.org/10.5281/zenodo.XXXXXXX) and either:
#   - Set the environment variable BRUCELEE_DATA_ROOT to your local path, or
#   - Edit the fallback path below.
DATA_ROOT = os.environ.get(
    "BRUCELEE_DATA_ROOT",
    r"D:\Dropbox\brucelee\data"
)


dictionnary_H_count = {  # Normalisation dictionnary
    "Starting material-1": 0.5,  # H expected for this signal
    "Starting material-2": 0.5,  # H expected for this signal

    "Product_PX1-1": 0.5,  # H expected for this signal
    "Product_PX1-2": 0.5,  # H expected for this signal
    "Product_PX1-3": 0.5,  # H expected for this signal
    "Product_PX1-4": 0.5,  # H expected for this signal

    "Product_PX1_prime-1": 0.5,  # H expected for this signal
    "Product_PX1_prime-2": 0.5,  # H expected for this signal
    "Product_PX1_prime-3": 0.5,  # H expected for this signal
    "Product_PX1_prime-4": 0.5,  # H expected for this signal

    "Product_PX2-1": 0.5,  # H expected for this signal
    "Product_PX2-2": 0.5,  # H expected for this signal
    "Product_PX2-3": 0.5,  # H expected for this signal
    "Product_PX2-4": 0.5,  # H expected for this signal
    "Product_PX2-5": 0.5,  # H expected for this signal
    "Product_PX2-6": 1,  # H expected for this signal
    "Product_PX2-7": 1,  # H expected for this signal
    "Product_PX2-8": 0.5,  # H expected for this signal

    "Product_PX3-1": 1,  # H expected for this signal
    "Product_PX3-2": 0.5,  # H expected for this signal
    "Product_PX3-3": 0.5,  # H expected for this signal
    "Product_PX3-4": 0.5,  # H expected for this signal
    "Product_PX3-5": 0.5,  # H expected for this signal

    "Product_PX4-1": 1,  # H expected for this signal

    "Product_PX5-1": 1,  # H expected for this signal
    "Product_PX5-2": 2,  # H expected for this signal

    "Product_PX5_prime-1": 1,  # H expected for this signal
    "Product_PX5_prime-2": 2,  # H expected for this signal

    "Product_PX6-1": 1,  # H expected for this signal
    "Product_PX6-2": 1,  # H expected for this signal

    "Product_PX7-1": 0.5,  # H expected for this signal
    "Product_PX7-2": 0.5,  # H expected for this signal
    "Product_PX7-3": 2,  # H expected for this signal
    "Product_PX7-4": 0.5,  # H expected for this signal
    "Product_PX7-5": 0.5,  # H expected for this signal

    "Product_PX7_prime-1": 0.5,  # H expected for this signal
    "Product_PX7_prime-2": 0.5,  # H expected for this signal
    "Product_PX7_prime-3": 2,  # H expected for this signal
    "Product_PX7_prime-4": 0.5,  # H expected for this signal
    "Product_PX7_prime-5": 0.5,  # H expected for this signal

    "Product_PX8-1": 0.5,  # H expected for this signal
    "Product_PX8-2": 0.5,  # H expected for this signal
    "Product_PX8-3": 1,  # H expected for this signal
    "Product_PX8-4": 0.5,  # H expected for this signal
    "Product_PX8-5": 0.5,  # H expected for this signal

    "Product_PX8_prime-1": 0.5,  # H expected for this signal
    "Product_PX8_prime-2": 0.5,  # H expected for this signal
    "Product_PX8_prime-3": 1,  # H expected for this signal
    "Product_PX8_prime-4": 0.5,  # H expected for this signal
    "Product_PX8_prime-5": 0.5,  # H expected for this signal

    "Product_PU1-1": 1,  # H hypothtetical, structure unknow

}

compds_in_crude = [
                    'Starting material',
                    'Product_PX1',
                    'Product_PX1_prime',
                    'Product_PX2',
                    'Product_PX3',
                    'Product_PX4',
                    'Product_PX5',
                    'Product_PX5_prime',
                    'Product_PX6',
                    'Product_PX7',
                    'Product_PX7_prime',
                    'Product_PX8',
                    'Product_PX8_prime',
                    'Product_PU1'
                   ]

# Stockiometry dictionnary
dictionnary_stockiometry = {
                            "Starting material": {'Br': 0, 'BDA': 1},
                            "Product_PX1": {'Br': 1, 'BDA': 1},
                            "Product_PX1_prime": {'Br': 1, 'BDA': 1},
                            "Product_PX2": {'Br': 2, 'BDA': 1},
                            "Product_PX3": {'Br': 3, 'BDA': 1},
                            "Product_PX4": {'Br': 1, 'BDA': 1},
                            "Product_PX5": {'Br': 2, 'BDA': 1},
                            "Product_PX5_prime": {'Br': 2, 'BDA': 1},
                            "Product_PX6": {'Br': 3, 'BDA': 1},
                            "Product_PX7": {'Br': 1, 'BDA': 1},
                            "Product_PX7_prime": {'Br': 1, 'BDA': 1},
                            "Product_PX8": {'Br': 2, 'BDA': 1},
                            "Product_PX8_prime": {'Br': 2, 'BDA': 1},
                            "Product_PU1": {'Br': 1, 'BDA': 1},  # structure unknow, stockiometry placeholder
                        }


##px2 outliers
# in these three cases, use the two orange peaks as hcp.
# os.path.join(DATA_ROOT, r'DPE_bromination\_BDA_Benzylideneacetone\2025-12-12-run02_BDA_2nd\Results_2025-12-12-run02_400MHz\Results\BDA-2025-12-12-run02-7')
# os.path.join(DATA_ROOT, r'DPE_bromination\_BDA_Benzylideneacetone\2025-12-12-run02_BDA_2nd\Results_2025-12-12-run02_400MHz\Results\BDA-2025-12-12-run02-10')
# os.path.join(DATA_ROOT, r'DPE_bromination\_BDA_Benzylideneacetone\2025-12-12-run02_BDA_2nd\Results_2025-12-12-run02_400MHz\Results\BDA-2025-12-12-run02-22')


##px5 outliers
# px1p needs to be removed from the slice
# os.path.join(DATA_ROOT, r'DPE_bromination\_BDA_Benzylideneacetone\2025-12-12-run01_BDA_2nd\Results_2025-12-12-run01_long_400MHz\Results\BDA-2025-12-12-run01-long-17')
# os.path.join(DATA_ROOT, r'DPE_bromination\_BDA_Benzylideneacetone\2025-12-12-run02_BDA_2nd\Results_2025-12-12-run02_long_48h_400MHz\Results\BDA-2025-12-12-run02-long-9')


OLD_NAME_VS_NEW_NAME_DICT = {
    'px1': 'anti-Q1',
    'px1p': 'syn-Q1',
    'px2': 'Q4',
    'px3': 'Q5',
    'px4': 'Q6',
    'px5': 'Q7',
    'px5p': "Q7'",
    'px6': 'Q8',
    'px7': 'Q2',
    'px7p': "Q2'",
    'px8': 'Q3',
    'px8p': "Q3'"
}


OUTLIERS = [
        # Acid overlap, too much impurity, 2025-09-11-run01_DCE_TBABr3_add\\Results\\10-1D EXTENDED+-20250912-130752
        "hGUPYwyiiGe94UBSB6HtyM",
        # Yield of prod_B too high, too much impurity, 2025-09-11-run02_DCE_TBABr3_add\\Results\\6-1D EXTENDED+-20250912-174433
        "3zcaskEYsSmCUcAeXZDAvK",
        # Yield of prod_B too high, too much impurity, 2025-09-11-run02_DCE_TBABr3_add\\Results\\2-1D EXTENDED+-20250912-171350
        "8fVQtffNmqZwXFVJHi3FVZ",
        # Yield of prod_B too high, too much impurity, 2025-09-11-run01_DCE_TBABr3_add\\Results\\34-1D EXTENDED+-20250912-160154
        "nHyFFbBecdkRwuszweUWna",
        # Yield of prod_A too high, too much impurity, 2025-09-11-run02_DCE_TBABr3_add\\Results\\9-1D EXTENDED+-20250912-180612
        "GXxTsVrSj4GVNnbYsP4d6L",
        # Yield of prod_A too high, too much impurity, 2025-09-11-run02_DCE_TBABr3_add\\Results\\16-1D EXTENDED+-20250912-185543
        "JoHTpg2Wqo2inSjrMtRq3C",
        # HBr_adduct is wrong, too much impurity, 2025-09-11-run01_DCE_TBABr3_add\\Results\\32-1D EXTENDED+-20250912-154632
        "dV3yitsANpi6KteH3HCMFG",
        # HBr_adduct is wrong, too much impurity, 2025-09-11-run02_DCE_TBABr3_add\\Results\\19-1D EXTENDED+-20250912-191828
        "cSbuh6sy7qZcH9fLjJPnH8",
        # Yield of prod_B too high, too much impurity, 2025-04-28-run02_DCE_TBABF4_normal\\Results\\ 26-1D EXTENDED+-20250429-210103
        "7i5CGhGNEJ4ooKe9qjkVRZ",
        # Yield of prod_B too high, too much impurity, 2025-04-28-run02_DCE_TBABF4_normal\\Results\\ 16-1D EXTENDED+-20250429-194857
        "VDxrRimQGie5q5uGM7DW5x",
        # Yield of Alcohol too high, too much impurity, 04-28-run01 2
        "cxPvN6tDvXNvgRabvGNYDV",
        # Yield of Alcohol too high, too much impurity, 04-28-run01 8
        "d6NmTysXaCR4sTETqLgXfx",
        # Yield of Alcohol too high, too much impurity, 04-28-run01 22
        "ErPe4gwEhybkJF62smrXxd",
        # Yield of Alcohol too high, too much impurity, 04-28-run01 24
        "Hxe4Bf4AciGqDfGh23cEAG",
        # Yield of Alcohol too high, too much impurity, 04-28-run02 10
        "bF8i3JmTjnsiUmj8JMH2aK",
        # Yield of Alcohol too high, too much impurity, 04-28-run03 11
        "88AFpG5cHcwSmHLH9sQaHP",
        # Yield of Alcohol too high, too much impurity, 09-09-run01 37
        "mnp4HQVLHijMxEkA4M4SYg",
        # Yield of Alcohol too high, too much impurity, 09-09-run02 6
        "YAvqJbnJCsGCN53hTijMMN",
        # Yield of HBr_adduct too high, too much impurity, 09-09-run01 2
        "5Nm6CfviHLhgiDd7ftDHhS",
        # Yield of Alcohol too high, too much impurity, 05-30-run01 22
        "U5zEU8jk76Cg6dPebEHqXX",
        # Yield of Alcohol too high, too much impurity, 05-30-run02 10
        "jLHqLvaq6AL7M4EbzYMmzy",
        # Yield of Alcohol too high, too much impurity, 05-30-run02 14
        "dbVLdLWJEa6MJJkyLxo4r7",
        # Yield of Alcohol too high, too much impurity, 05-30-run04 12
        "PzUND3jN3KUGRdFYnSUmpf",
        # Yield of Alcohol too high, too much impurity, 09-10-run02 26
        "LfQefrKHYR2GoT6J8BZgxc",
    ]