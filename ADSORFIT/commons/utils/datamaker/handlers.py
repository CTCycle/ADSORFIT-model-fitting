import gradio as gr
import pandas as pd
from tqdm import tqdm
tqdm.pandas()

from ADSORFIT.commons.utils.datamaker.processing import (drop_negative_values,
                                                         aggregate_by_experiment,
                                                         calculate_boundary_values)
from ADSORFIT.commons.utils.solver.fitting import DataFit
from ADSORFIT.commons.constants import CONFIG, DATA_PATH
from ADSORFIT.commons.logger import logger


    

###############################################################################    
class SourceFileHandling:


    def __init__(self):
        pass

    #--------------------------------------------------------------------------
    def get_file(self, path):

        try:
            dataset = pd.read_csv(path, sep=';', encoding='utf-8')
            logger.info(f'Successfully loaded dataset from {path}')        
        except Exception as e:
            dataset = None
            logger.error(f'Error reading file: {e}')
        
        return dataset
            

    #--------------------------------------------------------------------------
    def update_columns_dropdown(self, dataset):   

        if dataset is not None:
            columns = dataset.columns.to_list()
            updates = gr.update(choices=columns)
            logger.debug(f'Columns selection dropdown has been updated: {columns}')
        
            return updates, updates, updates, updates          
        
    
    #--------------------------------------------------------------------------
    def process_source_file(self, P_col, Q_col, T_col, exp_col, dataset):
        
        dataset = drop_negative_values(P_col, Q_col, T_col, dataset)
        dataset = aggregate_by_experiment(P_col, Q_col, T_col, exp_col, dataset)
        dataset = calculate_boundary_values(P_col, Q_col, dataset)

        statistics = 'Ciao'

        return dataset, statistics
        





# # Function to preprocess dataset and run the fitting
# ###############################################################################
# def execute_fitting(source_file, iterations, seed):

#     processor = ProcessAdsorptionData()
#     dataset = processor.preprocess_dataset(source_file)    
#     logger.info(f'Number of experiments:   {processor.num_experiments}')
#     logger.info(f'Number of measurements:  {processor.num_measurements}')
    
#     fitter = DataFit(iterations=iterations, seed=seed)
#     fitting_results = fitter.fit_all_data(dataset)    
#     return f'Fitting completed with {iterations} iterations and seed {seed}. Check logs for details.'


# # Function to return model settings for Tab 2
# ###############################################################################
# def show_model_settings(models_dict):
#     result = {}
#     for model, params in models_dict.items():
#         result[model] = {
#             "description": f"{model} model fitting parameters",
#             "initial": params["initial"],
#             "min": params["min"],
#             "max": params["max"]}
        
#     return result


    
