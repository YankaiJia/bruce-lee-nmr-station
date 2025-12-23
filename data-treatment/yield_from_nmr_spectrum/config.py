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

