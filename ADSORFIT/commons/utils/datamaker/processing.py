import os
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





