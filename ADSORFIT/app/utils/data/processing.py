import os
import re
import numpy as np
import pandas as pd
from difflib import get_close_matches

from ADSORFIT.commons.utils.data.database import ADSORFITDatabase
from ADSORFIT.commons.constants import DATASET_PATH, RESULTS_PATH
from ADSORFIT.commons.logger import logger


# [DATASET OPERATIONS]
###############################################################################
class AdsorptionDataProcessing:

    def __init__(self): 
        database = ADSORFITDatabase()          
        self.dataset = pd.read_csv(DATASET_PATH, sep =';', encoding='utf-8')
        database.save_adsorption_data(self.dataset) 

        self.processed_data = pd.DataFrame() 
        self.stats = None   
        self.processing_done = False         
        self.experiment_col = 'experiment'
        self.temperature_col = 'temperature [K]'  
        self.pressure_col = 'pressure [Pa]' 
        self.uptake_col = 'uptake [mol/g]'
        
    #--------------------------------------------------------------------------
    def identify_target_columns(self):        
        target_patterns = {'experiment_col': 'experiment',
                           'temperature_col': 'temperature',
                           'pressure_col': 'pressure',
                           'uptake_col': 'uptake'}

        # Iterate over patterns to find matching columns in dataset
        for attr, pattern in target_patterns.items():  
            # Find columns that match the pattern (case-insensitive)
            matched_cols = [col for col in self.dataset.columns 
                            if re.search(pattern, col, re.IGNORECASE)]

            # If exact pattern match is not found, try to find a close match
            if not matched_cols:
                close_matches = get_close_matches(
                    pattern, self.dataset.columns, cutoff=0.6)
                if close_matches:                 
                    setattr(self, attr, close_matches[0])  
            else:                
                setattr(self, attr, matched_cols[0])   

    #--------------------------------------------------------------------------
    def drop_negative_values(self, dataset):
        # remove negative values from temperature, pressure and uptake measurements
        dataset = dataset[dataset[self.temperature_col].astype(np.int32) > 0]
        dataset = dataset[dataset[self.pressure_col].astype(np.int32) >= 0]
        dataset = dataset[dataset[self.uptake_col].astype(np.int32) >= 0]

        return dataset   

    #--------------------------------------------------------------------------
    def aggregate_by_experiment(self, dataset):
        # create aggregation dictionary by setting aggregation rules
        # then perform grouping based on aggregated dictionary    
        aggregate_dict = {self.temperature_col : 'first',                  
                          self.pressure_col : list,
                          self.uptake_col : list}
                 
        dataset_grouped = dataset.groupby(
            self.experiment_col, as_index=False).agg(aggregate_dict)        

        return dataset_grouped
    
    #--------------------------------------------------------------------------
    def calculate_min_max(self, dataset):
        dataset[f'min {self.pressure_col}'] = dataset[self.pressure_col].apply(
            lambda x : min(x))
        dataset[f'max {self.pressure_col}'] = dataset[self.pressure_col].apply(
            lambda x : max(x))
        dataset[f'min {self.uptake_col}'] = dataset[self.uptake_col].apply(
            lambda x : min(x))
        dataset[f'max {self.uptake_col}'] = dataset[self.uptake_col].apply(
            lambda x : max(x))

        return dataset 
    
    #--------------------------------------------------------------------------
    def preprocess_dataset(self, detect_columns=False):
        if detect_columns:                  
            self.identify_target_columns()

        no_nan_data = self.dataset.dropna().reset_index()
        processed_data = self.drop_negative_values(no_nan_data)
        processed_data = self.aggregate_by_experiment(processed_data)
        processed_data = self.calculate_min_max(processed_data)
        self.processed_data = processed_data
        self.processing_done = True        
        num_experiments = processed_data.shape[0]
        num_measurements = no_nan_data.shape[0]  
        removed_NaN = self.dataset.shape[0] - num_measurements        

        self.stats = f"""
        #### Dataset Statistics

        **Experiments column:**      {self.experiment_col}  
        **Temperature column:**      {self.temperature_col}  
        **Pressure column:**         {self.pressure_col}  
        **Uptake column:**           {self.uptake_col}  

        **Number of NaN values:**    {removed_NaN}  
        **Number of experiments:**   {num_experiments}  
        **Number of measurements:**  {num_measurements}  
        **Average measurements by experiment:** {num_measurements / num_experiments:.1f}
        """


# [DATASET OPERATIONS]
###############################################################################
class DatasetAdapter:

    def __init__(self):
        self.csv_kwargs = {'sep': ';', 'encoding': 'utf-8'}
        database = ADSORFITDatabase()    

    #--------------------------------------------------------------------------
    def adapt_results_to_dataset(self, fitting_results : dict, dataset):        
        for k, v in fitting_results.items():            
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
    def find_best_model(self, dataset):       
        LSS_columns = [x for x in dataset.columns if 'LSS' in x]
        dataset['best model'] = dataset[LSS_columns].apply(
            lambda x : x.idxmin(), axis=1)
        dataset['best model'] = dataset['best model'].apply(
            lambda x : x.replace(' LSS', ''))
        dataset['worst model'] = dataset[LSS_columns].apply(
            lambda x : x.idxmax(), axis=1)
        dataset['worst model'] = dataset['worst model'].apply(
            lambda x : x.replace(' LSS', ''))

        return dataset
    
    #--------------------------------------------------------------------------
    def save_to_database(self, dataset, configuration : dict, save_best_models):        
        # save dataframe as a table in sqlite database
        dataset.drop(columns=['pressure [Pa]', 'uptake [mol/g]'], inplace=True)
        database.save_fitting_results(dataset)
        if save_best_models:
            for model in configuration.keys():
                model_dataset = dataset[dataset['best model'] == model]
                model_cols = [x for x in model_dataset.columns if model in x]
                target_cols = [x for x in model_dataset.columns[:8]] + model_cols
                best_fit_data = model_dataset[target_cols]
                table_name = f'BEST_FIT_{model}'
                database.save_best_fit(best_fit_data, table_name)

  


   
        
    