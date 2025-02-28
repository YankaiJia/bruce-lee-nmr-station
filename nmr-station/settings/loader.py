from dotenv import load_dotenv
import os 

env_path = os.path.join(os.path.dirname(__file__), '.env')
# override flag set True to allow .env content updates
load_dotenv(env_path, override=True)

# config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
# self.config = configparser.ConfigParser().read(config_path)

"""
TUBE_COUNT: no. of nmr tubes serving in tube rack for sample transfer
    - affects tube_count in TubeManager in SharedState
    - affects NUM_OF_TUBES_IN_RACK in Planner.generate_events in pipetter.py
"""

TUBE_COUNT = 2

"""
Time constant for each cleaning step
    - Changing these affect the waiting time in scheduler.py
"""
div = 1

## for real run
T_WASTE_COLLECTOR = 15 / div
T_WASHER1 = 30 / div
T_WASHER2 = 30 / div
T_DRYER = 120 / div

## for testing or taking video
# T_WASTE_COLLECTOR = 2
# T_WASHER1 = 2
# T_WASHER2 = 2
# T_DRYER = 5


"""
Pipetter settings
"""
PIPETTER_LOG_PATH = os.getenv('PIPETTER_LOG_PATH')
PIPETTER_TIP_RACK_FILE_PATH = os.getenv('PIPETTER_TIP_RACK_FILE_PATH')
PIPETTER_COORDINATES_FILE_PATH = os.getenv('PIPETTER_COORDINATES_FILE_PATH')
PIPETTER_GRBL_SETTINGS_FILE_PATH = os.getenv('PIPETTER_GRBL_SETTINGS_FILE_PATH')

"""
Robot Arm settings
"""
ROBOT_ARM_HOST = os.getenv('ROBOT_ARM_HOST')
ROBOT_ARM_LOG_PATH = os.getenv('ROBOT_ARM_LOG_PATH')
TUBE_LENGTH = 275
SAFE_POS = [0, -23.27248, -44.76893, 0, 68.04142, 0]
HIGH_Z = 340  # this is the Z position for arm when moving between spots.
CAROUSEL_RADIUS = 25


"""
Spectrometer settings
    - modify the host and port in .env
"""
REMOTE_CONTROL_HOST = os.getenv('SPECTROMETER_REMOTE_CONTROL_HOST')
REMOTE_CONTROL_PORT = os.getenv('SPECTROMETER_REMOTE_CONTROL_PORT')
# SPECTROMETER_LOG_PATH = os.getenv('SPECTROMETER_LOG_PATH')
MEASUREMENT_DATA_GUI_PATH = os.getenv('MEASUREMENT_DATA_GUI_PATH')
REMOTE_CONTROL_TIMEOUT = 10

# MAX_SAMPLE_COUNT_AFTER_SHIMMING = 20
MAX_SAMPLE_COUNT_AFTER_SHIMMING = 10
REGULAR_SHIM_XML = """<?xml version="1.0" encoding="utf-8"?>
<Message>
        <Start protocol="SHIM">
                <Option name="Shim" value="QuickShim" />
        </Start>
</Message>
"""

# shiming methods
# 1. CheckShim: 1min
# 2. QuickShim: 4min
# 3. QuickShim1st2nd: 6min
# 4. PowerShim: 40min