import json
from os.path import join, dirname, abspath 

# [PATHS]
###############################################################################
PROJECT_DIR = dirname(dirname(abspath(__file__)))
DATA_PATH = join(PROJECT_DIR, 'resources')
BEST_FIT_PATH = join(DATA_PATH, 'best fit')
LOGS_PATH = join(PROJECT_DIR, 'resources', 'logs')

# [FILENAMES]
###############################################################################
# add filenames here

# [CONFIGURATIONS]
###############################################################################
CONFIG_PATH = join(PROJECT_DIR, 'settings', 'app_configurations.json')
with open(CONFIG_PATH, 'r') as file:
    CONFIG = json.load(file)
