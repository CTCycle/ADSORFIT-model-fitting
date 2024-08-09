import os
import pandas as pd
import numpy as np
from tqdm import tqdm

# [SETTING WARNINGS]
import warnings
warnings.simplefilter(action='ignore', category = Warning)

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
    logger.info(f'Average measurements by experiment: {processor.num_measurements/processor.num_experiments}')

    
   
    # 2. [PERFORM CURVE FITTING]
    #-------------------------------------------------------------------------- 
    # fitting adsorption isotherm data with theoretical models       
    fitter = DataFit()   
    fitting_results = fitter.fit_all_data(dataset)
    

    # extract data programmatically from the dictionaries and populate grouped dataframe     
    adapter = DataSetAdapter(fitting_results)
    print('\nGenerating dataset with fitting results\n')
    fitting_dataset = adapter.expand_fitting_data(dataset_grouped)

    # check best fitting model and split datasets on best fitting  
    fitting_dataset = adapter.find_best_model(fitting_dataset)
    adapter.save_best_fitting(fitter.model_names, fitting_dataset, BEST_FIT_PATH)

    # save fitting results as .csv file    
    file_loc = os.path.join(DATA_PATH, 'fitting_results.csv') 
    fitting_dataset.to_csv(file_loc, index=False, sep=';', encoding='utf-8')
        
            

 
