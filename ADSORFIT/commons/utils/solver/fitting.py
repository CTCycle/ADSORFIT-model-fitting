import inspect
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from tqdm import tqdm
tqdm.pandas()

from ADSORFIT.commons.utils.solver.models import AdsorptionModels
from ADSORFIT.commons.constants import CONFIG
from ADSORFIT.commons.logger import logger




###############################################################################
def run_solver(data, P_col, Q_col, selected_models, max_iterations, seed):     

    fitter = AdsorptionDataFitting(selected_models)
    fitting_results = fitter.fit_all_data(P_col, Q_col, max_iterations, data)
    logger.info(f'Fitting completed with {max_iterations} iterations and seed = {seed}.')

    return fitting_results


# # Function to return model settings for Tab 2
# ###############################################################################
# def show_model_settings(models_dict):
#     result = {}
#     for model, params in models_dict.items():
#         result[model] = {
#             'description': f'{model} model fitting parameters',
#             'initial': params['initial'],
#             'min': params['min'],
#             'max': params['max']}
        
#     return result


    


# [FITTING FUNCTION]
###############################################################################
class AdsorptionDataFitting:


    def __init__(self):  
        self.adsorption_models = AdsorptionModels()            
          

    #--------------------------------------------------------------------------
    def single_experiment_fit(self, X, Y, selected_models, max_iterations):

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
        
        model_parameters = {k : v for k, v in self.selected_models.items()}
        
        results = {}        
        for name, conf in model_parameters.items():
            # get the model based on name indexing            
            model = self.adsorption_models.get_model(name) 
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
                lss = np.sum((Y - predicted_Y) ** 2)

                # Calculate errors from covariance                 
                errors = np.sqrt(np.diag(covariance))
                results[name] = {'optimal_params': optimal_params, 
                                 'covariance': covariance, 
                                 'errors': errors,
                                 'LSS' : lss,
                                 'arguments' : fn_parameters}
                                
            except Exception as e: 
                logger.error(f'Could not fit data using {name} - Error: {e}')               
                nan_list = [np.nan for x in range(num_params)]
                results[name] = {'optimal_params': nan_list, 
                                 'covariance': nan_list, 
                                 'errors': nan_list,
                                 'LSS' : np.nan,
                                 'arguments' : fn_parameters,
                                 'exception' : e}                

        return results 
    
    #--------------------------------------------------------------------------
    def fit_all_data(self, P_col, Q_col, selected_models, max_iterations, dataset : pd.DataFrame):

        pressures = [np.array(x) for x in dataset[P_col].to_list()]
        uptakes = [np.array(x) for x in dataset[Q_col].to_list()]  
        # fitting adsorption isotherm data with theoretical models  
        results_dictionary = {k : [] for k in selected_models}
        logger.debug(f'About to perform data fitting with following models: {selected_models}')
        for x, y in zip(tqdm(pressures), uptakes):
            results = self.single_experiment_fit(x, y, max_iterations)
            for model in selected_models:
                results_dictionary[model].append(results[model])
        
        return results_dictionary

            
