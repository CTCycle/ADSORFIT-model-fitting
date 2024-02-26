import os
import sys
import art
import pandas as pd
import numpy as np
import pickle 
from tqdm import tqdm

# set warnings
#------------------------------------------------------------------------------
import warnings
warnings.simplefilter(action='ignore', category = Warning)

# import modules and classes
#------------------------------------------------------------------------------
from components.data_assets import AdsorptionModels
import components.global_paths as globpt
import configurations as cnf

# welcome message
#------------------------------------------------------------------------------
ascii_art = art.text2art('ADSCON')
print(ascii_art)

# [LOAD AND TRANSFORM DATA]
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
dataset_grouped.drop(columns='experiment', axis=1, inplace=True)
num_experiments = dataset_grouped.shape[0]

# [ANALYZE DATA]
#==============================================================================
#==============================================================================

print(f'''
-------------------------------------------------------------------------------
DATA REPORT
-------------------------------------------------------------------------------    
Num of experiments: {num_experiments}
  
''')

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
fitter = AdsorptionModels()
model_params = fitter.ads_models

# fitting adsorption isotherm data with theoretical models
#------------------------------------------------------------------------------ 
fitting_results = []
for x, y in zip(tqdm(pressures), uptakes):
    results = fitter.adsorption_fitter(x, y)
    fitting_results.append(results)

# extract data programmatically from the dictionaries and populate grouped dataframe
#------------------------------------------------------------------------------  
langmuir_data = [d['Langmuir'] for d in fitting_results]
sips_data = [d['Sips'] for d in fitting_results]

# Langmuir adsorption model
dataset_grouped['langmuir K'] = [x['optimal_params'][0] for x in langmuir_data]
dataset_grouped['langmuir qsat'] = [x['optimal_params'][1] for x in langmuir_data]
dataset_grouped['langmuir K error'] =[x['errors'][0] for x in langmuir_data]
dataset_grouped['langmuir qsat error'] = [x['errors'][1] for x in langmuir_data]
dataset_grouped['langmuir LSS'] = [x['LSS'] for x in langmuir_data]

# Sips adsorption model
dataset_grouped['sips K'] = [x['optimal_params'][0] for x in sips_data]
dataset_grouped['sips qsat'] = [x['optimal_params'][1] for x in sips_data]
dataset_grouped['sips N'] = [x['optimal_params'][2] for x in sips_data]
dataset_grouped['sips K error'] =[x['errors'][0] for x in sips_data]
dataset_grouped['sips qsat error'] = [x['errors'][1] for x in sips_data]
dataset_grouped['sips N error'] = [x['errors'][2] for x in sips_data]
dataset_grouped['sips LSS'] = [x['LSS'] for x in sips_data]

# save fitting results as .csv file
#------------------------------------------------------------------------------ 
file_loc = os.path.join(globpt.data_path, 'fitting_results.csv') 
dataset_grouped.to_csv(file_loc, index=False, sep=';', encoding='utf-8')
      
        

 
