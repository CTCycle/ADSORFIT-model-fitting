import os
import pandas as pd
import numpy as np
from tqdm import tqdm

# [SETTING WARNINGS]
import warnings
warnings.simplefilter(action='ignore', category=Warning)

# [IMPORT CUSTOM MODULES]
from ADSORFIT.commons.utils.datamaker.datasets import DataPreProcess, DataSetAdapter
from ADSORFIT.commons.utils.solver.fitting import DataFit
from ADSORFIT.commons.constants import CONFIG, DATA_PATH, BEST_FIT_PATH
from ADSORFIT.commons.logger import logger


# [RUN MAIN]
###############################################################################
if __name__ == '__main__':

    # 1. # [LOAD AND CLEAN DATA]
    #--------------------------------------------------------------------------
    processor = DataPreProcess()
    dataset = processor.preprocess_dataset()    
    logger.info(f'Number of experiments:   {processor.num_experiments}')
    logger.info(f'Number of measurements:  {processor.num_measurements}')
    logger.info(f'Average measurements by experiment: {processor.num_measurements/processor.num_experiments:.1f}')   
   
    # 2. [PERFORM CURVE FITTING]
    #-------------------------------------------------------------------------- 
    # fitting adsorption isotherm data with theoretical models       
    fitter = DataFit()   
    fitting_results = fitter.fit_all_data(dataset)    

    # extract data programmatically from the dictionaries and populate grouped dataframe     
    adapter = DataSetAdapter(fitting_results)
    logger.info('Generating dataset with fitting results')
    fitting_dataset = adapter.adapt_results_to_dataset(dataset)

    # check best fitting model and split datasets on best fitting  
    fitting_dataset = adapter.find_best_model(fitting_dataset)
    adapter.save_data_to_csv(fitting_dataset)
   
        
            

 
