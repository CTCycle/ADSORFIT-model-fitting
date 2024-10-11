import gradio as gr
import pandas as pd
from tqdm import tqdm
tqdm.pandas()

from ADSORFIT.commons.constants import CONFIG, DATA_PATH, BEST_FIT_PATH
from ADSORFIT.commons.logger import logger


###############################################################################
def drop_negative_values(P_col, Q_col, T_col, dataset : pd.DataFrame): 
     
    dataset = dataset[dataset[T_col].astype(int) > 0]
    dataset = dataset[dataset[P_col].astype(int) >= 0]
    dataset = dataset[dataset[Q_col].astype(int) >= 0]

    return dataset  

###############################################################################
def aggregate_by_experiment(P_col, Q_col, T_col, exp_col, dataset : pd.DataFrame):
 
    aggregate_dict = {T_col : 'first', P_col : list, Q_col : list}            
    dataset_grouped = dataset.groupby(exp_col, as_index=False).agg(aggregate_dict)        

    return dataset_grouped

###############################################################################
def calculate_boundary_values(P_col, Q_col, dataset : pd.DataFrame):

        dataset[f'min {P_col}'] = dataset[P_col].apply(lambda x : min(x))
        dataset[f'max {P_col}'] = dataset[P_col].apply(lambda x : max(x))
        dataset[f'min {Q_col}'] = dataset[Q_col].apply(lambda x : min(x))
        dataset[f'max {Q_col}'] = dataset[Q_col].apply(lambda x : max(x))

        return dataset 


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

        processed_data = drop_negative_values(P_col, Q_col, T_col, dataset) 
        raw_measurements_count = dataset.shape[0]
        processed_measurements_count = processed_data.shape[0]

        processed_data = aggregate_by_experiment(P_col, Q_col, T_col, exp_col, processed_data)
        processed_data = calculate_boundary_values(P_col, Q_col, processed_data)
        experiments_count = processed_data.shape[0]        

        statistics = ('Source data summary:\n'
                      f'- Raw measurements count: {raw_measurements_count}\n'
                      f'- Processed measurements count: {processed_measurements_count}\n'
                      f'- Number of unique experiments: {experiments_count}')
        
        return processed_data, statistics
        






