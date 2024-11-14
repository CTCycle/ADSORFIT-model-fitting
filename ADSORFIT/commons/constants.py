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
DATASET_PATH = join(DATA_PATH, 'adsorption_data.csv') 
RESULTS_PATH = join(DATA_PATH, 'adsorption_model_fit.csv')


