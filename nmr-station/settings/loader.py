from dotenv import load_dotenv

import os 


env_path = os.path.join(os.path.dirname(__file__), '.env')
# override flag set True to allow .env content updates
load_dotenv(env_path, override=True)

ROBOT_ARM_LOG_PATH = os.getenv('ROBOT_ARM_LOG_PATH')
PIPETTER_LOG_PATH = os.getenv('PIPETTER_LOG_PATH')
# SPECTROMETER_LOG_PATH = os.getenv('SPECTROMETER_LOG_PATH')


# config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
# self.config = configparser.ConfigParser().read(config_path)



"""
TUBE_COUNT: no of nmr tubes serving in tube rack for sample transfer
    - affects tube_count in TubeManager in SharedState
    - affects NUM_OF_TUBES_IN_RACK in Planner.generate_events in pipetter.py
"""
TUBE_COUNT = 2
