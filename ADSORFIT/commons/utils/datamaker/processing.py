import os
import pandas as pd
from tqdm import tqdm
tqdm.pandas()

from ADSORFIT.commons.constants import CONFIG, DATA_PATH, BEST_FIT_PATH
from ADSORFIT.commons.logger import logger



    


# [DATASET OPERATIONS]
###############################################################################
class ProcessAdsorptionData:

    def __init__(self, dataset : pd.DataFrame):        
        
        self.dataset = dataset 
        self.raw_num_measurements = dataset.shape[0]              

    #--------------------------------------------------------------------------
    def drop_negative_values(self, dataset : pd.DataFrame):  
        dataset = dataset[dataset['temperature [K]'].astype(int) > 0]
        dataset = dataset[dataset['pressure [Pa]'].astype(int) >= 0]
        dataset = dataset[dataset['uptake [mol/g]'].astype(int) >= 0]

        return dataset   

    #--------------------------------------------------------------------------
    def aggregate_by_experiment(self, dataset : pd.DataFrame):

        # create aggregation dictionary to set aggregation rules
        aggregate_dict = {'temperature [K]' : 'first',                  
                          'pressure [Pa]' : list,
                          'uptake [mol/g]' : list}

        # perform grouping based on aggregated dictionary             
        dataset_grouped = dataset.groupby('experiment', as_index=False).agg(aggregate_dict)        

        return dataset_grouped
    
    #--------------------------------------------------------------------------
    def calculate_min_max(self, dataset : pd.DataFrame):

        dataset['min pressure [Pa]'] = dataset['pressure [Pa]'].apply(lambda x : min(x))
        dataset['max pressure [Pa]'] = dataset['pressure [Pa]'].apply(lambda x : max(x))
        dataset['min uptake [mol/g]'] = dataset['uptake [mol/g]'].apply(lambda x : min(x))
        dataset['max uptake [mol/g]'] = dataset['uptake [mol/g]'].apply(lambda x : max(x))

        return dataset 
    
    #--------------------------------------------------------------------------
    def preprocess_dataset(self):

        
        self.dataset = self.dataset.dropna().reset_index()
        processed_data = self.drop_negative_values(self.dataset)
        processed_data = self.aggregate_by_experiment(processed_data)
        processed_data = self.calculate_min_max(processed_data)
        self.num_experiments = processed_data.shape[0]
        self.num_measurements = self.dataset.shape[0] 


        stats_summary = (
            f'CSV file statistics (before processing):\n'
            f'Number of measurements: {num_measurements}') 

        return processed_data, processed_data_info



