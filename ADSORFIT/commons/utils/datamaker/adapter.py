import os
import pandas as pd
from tqdm import tqdm
tqdm.pandas()

from ADSORFIT.commons.constants import CONFIG, DATA_PATH, BEST_FIT_PATH
from ADSORFIT.commons.logger import logger


# [DATASET OPERATIONS]
###############################################################################
class DatasetAdapter:

    def __init__(self, fitting_results : dict):

        self.selected_models = CONFIG["SELECTED_MODELS"]        
        self.fitting_results = fitting_results

    #--------------------------------------------------------------------------
    def adapt_results_to_dataset(self, dataset):  

        for k, v in self.fitting_results.items():
            
            arguments = v[0]['arguments'] 
            optimals = [item['optimal_params'] for item in v]
            errors =  [item['errors'] for item in v]
            LSS = [item['LSS'] for item in v]
            for i, arg in enumerate(arguments):
                dataset[f'{k} {arg}'] = [x[i] for x in optimals]
                dataset[f'{k} {arg} error'] = [x[i] for x in errors]
            dataset[f'{k} LSS'] = LSS
          
        return dataset   
    
    #--------------------------------------------------------------------------
    def find_best_model(self, dataset : pd.DataFrame):
        LSS_columns = [x for x in dataset.columns if 'LSS' in x]
        dataset['best model'] = dataset[LSS_columns].apply(lambda x : x.idxmin(), axis=1)
        dataset['best model'] = dataset['best model'].apply(lambda x : x.replace(' LSS', ''))
        dataset['worst model'] = dataset[LSS_columns].apply(lambda x : x.idxmax(), axis=1)
        dataset['worst model'] = dataset['worst model'].apply(lambda x : x.replace(' LSS', ''))

        return dataset
    
    #--------------------------------------------------------------------------
    def save_data_to_csv(self, dataset : pd.DataFrame):

        file_loc = os.path.join(DATA_PATH, 'adsorption_model_fit.csv') 
        dataset.to_csv(file_loc, index=False, sep=';', encoding='utf-8')

        for model in self.selected_models:
            model_dataset = dataset[dataset['best model']==model]
            model_cols = [x for x in model_dataset.columns if model in x]
            target_cols = [x for x in model_dataset.columns[:8]] + model_cols
            df_model = model_dataset[target_cols]
            file_loc = os.path.join(BEST_FIT_PATH, f'{model}_best_fit.csv') 
            df_model.to_csv(file_loc, index=False, sep=';', encoding='utf-8')
                    


   
        
    