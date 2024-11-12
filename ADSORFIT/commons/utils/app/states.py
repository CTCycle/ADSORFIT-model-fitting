import os
from nicegui import ui

from ADSORFIT.commons.constants import RESULTS_PATH, DATASET_PATH, BEST_FIT_PATH
from ADSORFIT.commons.logger import logger


###############################################################################
class DataProcessor:
    def __init__(self):
        self.processed_df = None  # Instance variable to store the DataFrame

    def handle_processing(self):
        # Call the first function and store the DataFrame in an instance variable
        self.processed_df = processor.preprocess_dataset(identify_cols.value)
        print("DataFrame processed.")
        # Optionally trigger the second function immediately
        self.handle_second_function()

    def handle_second_function(self):
        if self.processed_df is not None:
            result = processor.second_function(self.processed_df)
            print("Second function completed with result:", result)
        else:
            print("No processed DataFrame available for the second function.")