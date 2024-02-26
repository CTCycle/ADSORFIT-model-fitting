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

    def __init__(self):
        self.ads_models = {'Langmuir' : {'initial_guess' : [0.000001, 10], 
                                         'low_boundary' : [0, 0], 
                                         'high_boundary' : [10, 100],
                                         'model_func': self.Langmuir_model},
                           'Sips' :     {'initial_guess' : [0.000001, 1, 10], 
                                         'low_boundary' : [0, 0, 0], 
                                         'high_boundary' : [10, 10, 100],
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
    def adsorption_fitter(self, X, Y):         
        results = {}
        
        for name, values in self.ads_models.items():
            model = values['model_func']  
            p0_values = values['initial_guess']
            bounds = (values['low_boundary'], values['high_boundary'])
            num_params = len(p0_values)
            try:
                optimal_params, covariance = curve_fit(model, X, Y, p0=p0_values, bounds=bounds,
                                                       full_output=False, maxfev=20000, check_finite=True,
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
            

              


   
        
    