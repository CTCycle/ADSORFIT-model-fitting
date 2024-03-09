import os
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import curve_fit
from tqdm import tqdm
tqdm.pandas()


# [ADSORPTION MODELS]
#==============================================================================
#==============================================================================
class AdsorptionModels:

    def __init__(self, parameters):
        self.model_names = ['langmuir', 'sips']
        Langmuir_param = parameters['langmuir']
        Sips_param = parameters['sips']        
        self.ads_models = {'langmuir' : {'initial_guess' : [Langmuir_param[0][0], Langmuir_param[0][1]], 
                                         'low_boundary' : [0, 0], 
                                         'high_boundary' : [Langmuir_param[1][0], Langmuir_param[1][1]],
                                         'model_func': self.Langmuir_model},
                           'sips' :     {'initial_guess' : [Sips_param[0][0], Sips_param[0][1], Sips_param[0][2]], 
                                         'low_boundary' : [0, 0, 0], 
                                         'high_boundary' : [Sips_param[1][0], Sips_param[1][1], Sips_param[1][2]],
                                         'model_func': self.Sips_model}} 
            
    #--------------------------------------------------------------------------
    def Langmuir_model(self, P, k, qsat):        
        kP = P * k
        qe = qsat * (kP/(1 + kP))        
        return qe    
   
    #--------------------------------------------------------------------------
    def Sips_model(self, P, k, qsat, N):        
        kP = k * (P**N)
        qe = qsat * (kP/(1 + kP))        
        return qe    

    #--------------------------------------------------------------------------
    def adsorption_fitter(self, X, Y, max_iter):         
        results = {}
        
        for name, values in self.ads_models.items():
            model = values['model_func']  
            p0_values = values['initial_guess']
            bounds = (values['low_boundary'], values['high_boundary'])
            num_params = len(p0_values)
            try:
                optimal_params, covariance = curve_fit(model, X, Y, p0=p0_values, bounds=bounds,
                                                       full_output=False, maxfev=max_iter, check_finite=True,
                                                       absolute_sigma=False)               

                # Calculate LSS comparing predicted vs true value 
                predicted_Y = model(X, *optimal_params)                
                lss = np.sum((Y - predicted_Y) ** 2) 
                # Calculate errors from covariance                 
                errors = np.sqrt(np.diag(covariance))
                results[name] = {'optimal_params': optimal_params, 
                                 'covariance': covariance, 
                                 'errors': errors,
                                 'LSS' : lss}                
            except:
                nan_list = [np.nan for x in range(num_params)]
                results[name] = {'optimal_params': nan_list, 
                                 'covariance': nan_list, 
                                 'errors': nan_list,
                                 'LSS' : np.nan}                

        return results 
            
# [DATASET OPERATIONS]
#==============================================================================
#==============================================================================
class AdaptDataSet:

    def __init__(self, fitting_data):
        self.results = fitting_data        

    def expand_fitting_data(self, dataset):

        langmuir_data = [d['langmuir'] for d in self.results]
        sips_data = [d['sips'] for d in self.results]

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

        return dataset
    
    def find_best_model(self, dataset):
        LSS_columns = [x for x in dataset.columns if 'LSS' in x]
        dataset['best model'] = dataset[LSS_columns].apply(lambda x : x.idxmin(), axis=1)
        dataset['best model'] = dataset['best model'].apply(lambda x : x.replace(' LSS', ''))
        dataset['worst model'] = dataset[LSS_columns].apply(lambda x : x.idxmax(), axis=1)
        dataset['worst model'] = dataset['worst model'].apply(lambda x : x.replace(' LSS', ''))

        return dataset
    
    def save_best_fitting(self, models, dataset, path):
        for mod in models:
            df = dataset[dataset['best model'] == mod]
            model_cols = [x for x in df.columns if mod in x]
            target_cols = [x for x in df.columns[:8]] + model_cols
            df_model = df[target_cols]
            file_loc = os.path.join(path, f'{mod}_best_fit.csv') 
            df_model.to_csv(file_loc, index=False, sep=';', encoding='utf-8')
                    


   
        
    