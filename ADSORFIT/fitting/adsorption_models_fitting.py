# [SETTING WARNINGS]
import warnings
warnings.simplefilter(action='ignore', category=Warning)

# [IMPORT CUSTOM MODULES]
from ADSORFIT.commons.utils.datamaker.datasets import AdsorptionDataProcessing, DatasetAdapter
from ADSORFIT.commons.utils.solver.fitting import ModelSolver
from ADSORFIT.commons.constants import CONFIG
from ADSORFIT.commons.logger import logger


# [RUN MAIN]
###############################################################################
if __name__ == '__main__':

    # 1. # [LOAD AND CLEAN DATA]
    #--------------------------------------------------------------------------
    processor = AdsorptionDataProcessing(CONFIG)
    dataset = processor.preprocess_dataset()       
   
    # 2. [PERFORM CURVE FITTING]
    #-------------------------------------------------------------------------- 
    # fitting adsorption isotherm data with theoretical models, using the column
    # references updated from the processor instance (either the hardcoded ones
    # or those automatically detected)       
    fitter = ModelSolver(CONFIG)   
    fitting_results = fitter.bulk_data_fitting(dataset, processor.experiment_col, 
                                               processor.pressure_col, processor.uptake_col)    

    # extract data programmatically from the dictionaries and populate grouped dataframe     
    adapter = DatasetAdapter(CONFIG, fitting_results)
    logger.info('Generating dataset with fitting results')
    fitting_dataset = adapter.adapt_results_to_dataset(dataset)

    # check best fitting model and split datasets on best fitting  
    fitting_dataset = adapter.find_best_model(fitting_dataset)
    adapter.save_data_to_csv(fitting_dataset)
   
        
            

 
