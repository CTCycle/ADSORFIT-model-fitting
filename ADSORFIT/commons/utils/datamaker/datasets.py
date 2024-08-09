import os
import pandas as pd
from tqdm import tqdm
tqdm.pandas()

from ADSORFIT.commons.constants import CONFIG, DATA_PATH
from ADSORFIT.commons.logger import logger



# [DATASET OPERATIONS]
###############################################################################
class DataPreProcess:

    def __init__(self):
        
        file_loc = os.path.join(DATA_PATH, 'adsorption_data.csv') 
        self.dataset = pd.read_csv(file_loc, sep =';', encoding='utf-8')
        self.dataset = self.dataset.dropna().reset_index()     
         

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

        processed_data = self.drop_negative_values(self.dataset)
        processed_data = self.aggregate_by_experiment(processed_data)
        processed_data = self.calculate_min_max(processed_data)
        self.num_experiments = processed_data.shape[0]
        self.num_measurements = self.dataset.shape[0]  

        return processed_data



# [DATASET OPERATIONS]
###############################################################################
class DataSetAdapter:

    def __init__(self, dataset : pd.DataFrame):
        
        self.dataset = dataset      

    

    #--------------------------------------------------------------------------
    def expand_fitting_data(self):

        langmuir_data = [d['langmuir'] for d in self.results]
        sips_data = [d['sips'] for d in self.results]
        freundlich_data = [d['freundlich'] for d in self.results]

        # Langmuir adsorption model
        dataset['langmuir K'] = [x['optimal_params'][0] for x in langmuir_data]
        dataset['langmuir qsat'] = [x['optimal_params'][1] for x in langmuir_data]
        dataset['langmuir K error'] =[x['errors'][0] for x in langmuir_data]
        dataset['langmuir qsat error'] = [x['errors'][1] for x in langmuir_data]
        dataset['langmuir LSS'] = [x['LSS'] for x in langmuir_data]

        # Sips adsorption model
        dataset['sips K'] = [x['optimal_params'][0] for x in sips_data]
        dataset['sips qsat'] = [x['optimal_params'][1] for x in sips_data]
        dataset['sips N'] = [x['optimal_params'][2] for x in sips_data]
        dataset['sips K error'] =[x['errors'][0] for x in sips_data]
        dataset['sips qsat error'] = [x['errors'][1] for x in sips_data]
        dataset['sips N error'] = [x['errors'][2] for x in sips_data]
        dataset['sips LSS'] = [x['LSS'] for x in sips_data]

        # Freundlich adsorption model
        dataset['freundlich K'] = [x['optimal_params'][0] for x in freundlich_data]        
        dataset['freundlich N'] = [x['optimal_params'][1] for x in freundlich_data]
        dataset['freundlich K error'] =[x['errors'][0] for x in freundlich_data]        
        dataset['freundlich N error'] = [x['errors'][1] for x in freundlich_data]   
        dataset['freundlich LSS'] = [x['LSS'] for x in freundlich_data]     

        return dataset
    
    #--------------------------------------------------------------------------
    def find_best_model(self, dataset):
        LSS_columns = [x for x in dataset.columns if 'LSS' in x]
        dataset['best model'] = dataset[LSS_columns].apply(lambda x : x.idxmin(), axis=1)
        dataset['best model'] = dataset['best model'].apply(lambda x : x.replace(' LSS', ''))
        dataset['worst model'] = dataset[LSS_columns].apply(lambda x : x.idxmax(), axis=1)
        dataset['worst model'] = dataset['worst model'].apply(lambda x : x.replace(' LSS', ''))

        return dataset
    
    #--------------------------------------------------------------------------
    def save_best_fitting(self, models, dataset, path):
        for mod in models:
            df = dataset[dataset['best model'] == mod]
            model_cols = [x for x in df.columns if mod in x]
            target_cols = [x for x in df.columns[:8]] + model_cols
            df_model = df[target_cols]
            file_loc = os.path.join(path, f'{mod}_best_fit.csv') 
            df_model.to_csv(file_loc, index=False, sep=';', encoding='utf-8')
                    


   
        
    