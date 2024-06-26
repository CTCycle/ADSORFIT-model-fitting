import os
import sys
import pandas as pd
import numpy as np
from tqdm import tqdm

# [SETTING WARNINGS]
import warnings
warnings.simplefilter(action='ignore', category = Warning)

# [IMPORT CUSTOM MODULES]
from commons.utils.datasets import AdaptDataSet
from commons.utils.models import AdsorptionModels
from commons.pathfinder import DATA_PATH, BEST_FIT_PATH
import commons.configurations as cnf

# [RUN MAIN]
if __name__ == '__main__':

    # 1. # [LOAD AND CLEAN DATA]
    #--------------------------------------------------------------------------
    # load data from csv    
    file_loc = os.path.join(DATA_PATH, 'adsorption_data.csv') 
    df_adsorption = pd.read_csv(file_loc, sep =';', encoding='utf-8')
    df_adsorption = df_adsorption.dropna().reset_index()

    # filter the dataset to remove experiments with negative values of temperature, 
    # pressure and uptake      
    dataset = df_adsorption[df_adsorption['temperature'].astype(int) >= 0]
    dataset = dataset[dataset['pressure [Pa]'].astype(int) >= 0]
    dataset = dataset[dataset['uptake [mol/g]'].astype(int) >= 0]

    # create aggregation dictionary to set aggregation rules
    aggregate_dict = {'temperature' : 'first',                  
                      'pressure [Pa]' : list,
                      'uptake [mol/g]' : list}

    # perform grouping based on aggregated dictionary             
    dataset_grouped = dataset.groupby('experiment', as_index=False).agg(aggregate_dict)
    num_experiments = dataset_grouped.shape[0]
    print(f'\nNumber of total experiments:  {num_experiments}')
    print(f'Number of total measurements:   {dataset.shape[0]}')
    print(f'Average of measurements:        {dataset.shape[0]//num_experiments}\n')

    # create columns holding information about min-max of pressure and uptake measurements    
    dataset_grouped['min pressure [Pa]'] = dataset_grouped['pressure [Pa]'].apply(lambda x : min(x))
    dataset_grouped['max pressure [Pa]'] = dataset_grouped['pressure [Pa]'].apply(lambda x : max(x))
    dataset_grouped['min uptake [mol/g]'] = dataset_grouped['uptake [mol/g]'].apply(lambda x : min(x))
    dataset_grouped['max uptake [mol/g]'] = dataset_grouped['uptake [mol/g]'].apply(lambda x : max(x))
   
    # 2. [PERFORM CURVE FITTING]
    #--------------------------------------------------------------------------
    # convert pressure and uptake series to arrays   
    pressures = [np.array(x) for x in dataset_grouped['pressure [Pa]'].to_list()]
    uptakes = [np.array(x) for x in dataset_grouped['uptake [mol/g]'].to_list()]

    # initialize fitter and extract base model parameters  
    fitter = AdsorptionModels(cnf.PARAMETERS)
    model_params = fitter.ads_models

    # fitting adsorption isotherm data with theoretical models    
    fitting_results = []
    for x, y in zip(tqdm(pressures), uptakes):
        results = fitter.adsorption_fitter(x, y, cnf.MAX_ITERATIONS)
        fitting_results.append(results)

    # extract data programmatically from the dictionaries and populate grouped dataframe     
    adapter = AdaptDataSet(fitting_results)
    print('\nGenerating dataset with fitting results\n')
    fitting_dataset = adapter.expand_fitting_data(dataset_grouped)

    # check best fitting model and split datasets on best fitting  
    fitting_dataset = adapter.find_best_model(fitting_dataset)
    adapter.save_best_fitting(fitter.model_names, fitting_dataset, BEST_FIT_PATH)

    # save fitting results as .csv file    
    file_loc = os.path.join(DATA_PATH, 'fitting_results.csv') 
    fitting_dataset.to_csv(file_loc, index=False, sep=';', encoding='utf-8')
        
            

 
