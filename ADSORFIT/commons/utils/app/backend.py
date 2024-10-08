import pandas as pd
from tqdm import tqdm
tqdm.pandas()

from ADSORFIT.commons.utils.datamaker.processing import ProcessAdsorptionData
from ADSORFIT.commons.utils.solver.fitting import DataFit
from ADSORFIT.commons.constants import CONFIG, DATA_PATH
from ADSORFIT.commons.logger import logger



###############################################################################
def process_source_file(path):

    dataset = pd.read_csv(path, sep=';', encoding='utf-8')
    processor = ProcessAdsorptionData(dataset)
    processed_dataset, info = processor.preprocess_dataset()


    if dataset is not None:       
        num_measurements = dataset.shape[0]        
        stats_summary = (
            f'CSV file statistics (before processing):\n'
            f'Number of measurements: {num_measurements}')
        
        return stats_summary
    


# Function to preprocess dataset and run the fitting
###############################################################################
def execute_fitting(source_file, iterations, seed):

    processor = ProcessAdsorptionData()
    dataset = processor.preprocess_dataset(source_file)    
    logger.info(f'Number of experiments:   {processor.num_experiments}')
    logger.info(f'Number of measurements:  {processor.num_measurements}')
    
    fitter = DataFit(iterations=iterations, seed=seed)
    fitting_results = fitter.fit_all_data(dataset)    
    return f'Fitting completed with {iterations} iterations and seed {seed}. Check logs for details.'


# Function to return model settings for Tab 2
###############################################################################
def show_model_settings(models_dict):
    result = {}
    for model, params in models_dict.items():
        result[model] = {
            "description": f"{model} model fitting parameters",
            "initial": params["initial"],
            "min": params["min"],
            "max": params["max"]}
        
    return result


###############################################################################
class ShowFileStatistics:

    def __init__(self):
        pass

    
