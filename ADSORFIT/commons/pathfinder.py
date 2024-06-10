from os.path import join, dirname, abspath 

PROJECT_DIR = dirname(dirname(abspath(__file__)))
DATA_PATH = join(PROJECT_DIR, 'resources')
BEST_FIT_PATH = join(DATA_PATH, 'best fit')
