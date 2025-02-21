import json
from os.path import join, abspath 

# [PATHS]
###############################################################################
ROOT_DIR = abspath(join(__file__, "../../.."))
PROJECT_DIR = abspath(join(__file__, "../.."))
DATA_PATH = join(PROJECT_DIR, 'resources')
BEST_FIT_PATH = join(DATA_PATH, 'best fit')
LOGS_PATH = join(PROJECT_DIR, 'resources', 'logs')

# [FILENAMES]
###############################################################################
DATASET_PATH = join(DATA_PATH, 'adsorption_data.csv') 
RESULTS_PATH = join(DATA_PATH, 'adsorption_model_fit.csv')


