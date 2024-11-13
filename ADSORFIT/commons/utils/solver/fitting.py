from nicegui import ui
import inspect
import pandas as pd
import numpy as np

from scipy.optimize import curve_fit
from tqdm import tqdm
tqdm.pandas()

from ADSORFIT.commons.utils.solver.models import AdsorptionModels
from ADSORFIT.commons.constants import CONFIG
from ADSORFIT.commons.logger import logger



                
# [FITTING FUNCTION]
###############################################################################
class ModelSolver:


    def __init__(self):
        self.collection = AdsorptionModels()  
        
    #--------------------------------------------------------------------------
    def single_experiment_fit(self, X, Y, exp_name, configuration, max_iterations):

        '''
        Fits adsorption model functions to provided data using non-linear least squares optimization.
        Iterates over a dictionary of adsorption models, attempting to fit each model to the 
        provided data (X, Y) using curve fitting with specified initial guesses, parameter boundaries, and 
        a maximum number of iterations. It calculates the sum of squared residuals (LSS) for model evaluation 
        and extracts parameter estimation errors from the covariance matrix.

        Keywords arguments:
            X (array-like): Independent variable data (e.g., concentration or pressure) for fitting the models.
            Y (array-like): Dependent variable data (e.g., adsorption capacity) corresponding to X.
            max_iter (int): Maximum number of iterations for the curve fitting process.

        Returns:
            results (dict): A dictionary containing the fitting results for each model. For each model, the dictionary
                            includes optimal parameters ('optimal_params'), covariance matrix ('covariance'),
                            parameter estimation errors ('errors'), and the sum of squared residuals ('LSS'). 
        
        '''  
        results = {}        
        for name, conf in configuration.items():
            # get the model based on name indexing            
            model = self.collection.get_model(name) 
            # get the model function signature to retrieve its arguments
            signature = inspect.signature(model)            
            fn_parameters = [name for name in signature.parameters.keys()][1:]

            p0_values = [v for v in conf['initial'].values()]
            num_params = len(p0_values)

            boundaries = ([v for v in conf['min'].values()], 
                          [v for v in conf['max'].values()])
            
            try:
                optimal_params, covariance = curve_fit(model, X, Y, p0=p0_values, bounds=boundaries,
                                                       full_output=False, maxfev=max_iterations, 
                                                       check_finite=True, absolute_sigma=False)
                
                # Calculate LSS comparing predicted vs true value 
                predicted_Y = model(X, *optimal_params)                
                lss = np.sum((Y - predicted_Y) ** 2, dtype=np.float32)

                # Calculate errors from covariance                 
                errors = np.sqrt(np.diag(covariance))
                results[name] = {'optimal_params': optimal_params, 
                                 'covariance': covariance, 
                                 'errors': errors,
                                 'LSS' : lss,
                                 'arguments' : fn_parameters}
                                
            except Exception as e: 
                tqdm.write(f'Could not fit {exp_name} data using {name} - Error: {e}')               
                nan_list = [np.nan for x in range(num_params)]
                results[name] = {'optimal_params': nan_list, 
                                 'covariance': nan_list, 
                                 'errors': nan_list,
                                 'LSS' : np.nan,
                                 'arguments' : fn_parameters,
                                 'exception' : e}                

        return results 
    
    #--------------------------------------------------------------------------    
    def bulk_data_fitting(self, dataset: pd.DataFrame, experiment_col,
                          pressure_col, uptake_col, configuration: dict,
                          max_iterations, progress_callback=None):

        experiments = dataset[experiment_col].to_list()
        pressures = [np.array(x, dtype=np.float32) for x in dataset[pressure_col].to_list()]
        uptakes = [np.array(x, dtype=np.float32) for x in dataset[uptake_col].to_list()]
        total_experiments = len(experiments)

        # fitting adsorption isotherm data with theoretical models
        results_dictionary = {k: [] for k in configuration.keys()}
        for idx, (x, y, name) in enumerate(zip(pressures, uptakes, experiments)):
            results = self.single_experiment_fit(x, y, name, configuration, max_iterations)
            for model in configuration.keys():
                results_dictionary[model].append(results[model])

            # Update progress
            if progress_callback:
                progress_callback(idx + 1, total_experiments)

        return results_dictionary

   
