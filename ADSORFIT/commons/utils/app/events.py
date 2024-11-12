import os
from nicegui import ui

from ADSORFIT.commons.constants import RESULTS_PATH, DATASET_PATH, BEST_FIT_PATH
from ADSORFIT.commons.logger import logger



def process_data():
    ui.notify('Processing data...')