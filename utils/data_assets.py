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
        Langmuir_param = parameters['Langmuir']
        Sips_param = parameters['Sips']

        Langmuir_param[0]
        self.ads_models = {'Langmuir' : {'initial_guess' : [Langmuir_param[0][0], Langmuir_param[0][1]], 
                                         'low_boundary' : [0, 0], 
                                         'high_boundary' : [Langmuir_param[1][0], Langmuir_param[1][1]],
                                         'model_func': self.Langmuir_model},
                           'Sips' :     {'initial_guess' : [Sips_param[0][0], Sips_param[0][1], Sips_param[0][2]], 
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

        langmuir_data = [d['Langmuir'] for d in self.results]
        sips_data = [d['Sips'] for d in self.results]

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
              


   
        
    