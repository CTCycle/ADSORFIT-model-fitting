import os
import pandas as pd
import numpy as np
from tqdm import tqdm

# set warnings
#------------------------------------------------------------------------------
import warnings
warnings.simplefilter(action='ignore', category = Warning)

# import modules and classes
#------------------------------------------------------------------------------
from utils.models import AdsorptionModels
from utils.datasets import AdaptDataSet
import utils.global_paths as globpt
import configurations as cnf

# specify relative paths from global paths and create subfolders
#------------------------------------------------------------------------------
best_path = os.path.join(globpt.data_path, 'best fit')
os.mkdir(best_path) if not os.path.exists(best_path) else None

# [LOAD AND CLEAN DATA]
#==============================================================================
#==============================================================================

# load data from csv
#------------------------------------------------------------------------------
file_loc = os.path.join(globpt.data_path, 'adsorption_data.csv') 
df_adsorption = pd.read_csv(file_loc, sep =';', encoding='utf-8')
df_adsorption = df_adsorption.dropna().reset_index()

# filter the dataset to remove experiments with negative values of temperature, 
# pressure and uptake 
#------------------------------------------------------------------------------ 
dataset = df_adsorption[df_adsorption['temperature'].astype(int) >= 0]
dataset = dataset[dataset['pressure [Pa]'].astype(int) >= 0]
dataset = dataset[dataset['uptake [mol/g]'].astype(int) >= 0]

# create aggregation dictionary to set aggregation rules
#------------------------------------------------------------------------------ 
aggregate_dict = {'temperature' : 'first',                  
                  'pressure [Pa]' : list,
                  'uptake [mol/g]' : list}

# perform grouping based on aggregated dictionary
#------------------------------------------------------------------------------          
dataset_grouped = dataset.groupby('experiment', as_index=False).agg(aggregate_dict)
num_experiments = dataset_grouped.shape[0]
print(f'\nNumber of total experiments:  {num_experiments}')
print(f'Number of total measurements:   {dataset.shape[0]}')
print(f'Average of measurements:        {dataset.shape[0]//num_experiments}\n')

# create columns holding information about min-max of pressure and uptake measurements
#------------------------------------------------------------------------------ 
dataset_grouped['min pressure [Pa]'] = dataset_grouped['pressure [Pa]'].apply(lambda x : min(x))
dataset_grouped['max pressure [Pa]'] = dataset_grouped['pressure [Pa]'].apply(lambda x : max(x))
dataset_grouped['min uptake [mol/g]'] = dataset_grouped['uptake [mol/g]'].apply(lambda x : min(x))
dataset_grouped['max uptake [mol/g]'] = dataset_grouped['uptake [mol/g]'].apply(lambda x : max(x))

# [PERFORM CURVE FITTING]
#==============================================================================
#==============================================================================

# convert pressure and uptake series to arrays
#------------------------------------------------------------------------------ 
pressures = [np.array(x) for x in dataset_grouped['pressure [Pa]'].to_list()]
uptakes = [np.array(x) for x in dataset_grouped['uptake [mol/g]'].to_list()]

# initialize fitter and extract base model parameters
#------------------------------------------------------------------------------ 
fitter = AdsorptionModels(cnf.parameters)
model_params = fitter.ads_models

# fitting adsorption isotherm data with theoretical models
#------------------------------------------------------------------------------ 
fitting_results = []
for x, y in zip(tqdm(pressures), uptakes):
    results = fitter.adsorption_fitter(x, y, cnf.max_iterations)
    fitting_results.append(results)

# extract data programmatically from the dictionaries and populate grouped dataframe
#------------------------------------------------------------------------------  
adapter = AdaptDataSet(fitting_results)
print('\nGenerating dataset with fitting results\n')
fitting_dataset = adapter.expand_fitting_data(dataset_grouped)

# check best fitting model and split datasets on best fitting
#------------------------------------------------------------------------------
fitting_dataset = adapter.find_best_model(fitting_dataset)
adapter.save_best_fitting(fitter.model_names, fitting_dataset, best_path)

# save fitting results as .csv file
#------------------------------------------------------------------------------ 
file_loc = os.path.join(globpt.data_path, 'fitting_results.csv') 
fitting_dataset.to_csv(file_loc, index=False, sep=';', encoding='utf-8')
      
        

 
