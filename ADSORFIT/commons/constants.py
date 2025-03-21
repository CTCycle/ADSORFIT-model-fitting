from os.path import join, abspath 

# [PATHS]
###############################################################################
ROOT_DIR = abspath(join(__file__, "../../.."))
PROJECT_DIR = join(ROOT_DIR, 'ADSORFIT')
DATA_PATH = join(PROJECT_DIR, 'resources', 'database')
LOGS_PATH = join(PROJECT_DIR, 'resources', 'logs')

# [FILENAMES]
###############################################################################
DATASET_PATH = join(DATA_PATH, 'adsorption_data.csv') 
RESULTS_PATH = join(DATA_PATH, 'adsorption_model_fit.csv')