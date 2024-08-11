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
class DataFit:


    def __init__(self):
        self.collection = AdsorptionModels()

    #--------------------------------------------------------------------------
    def single_experiment_fit(self, X, Y):

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
        self.collection = AdsorptionModels()
        all_parameters = CONFIG["MODELS"]
        selected_models = CONFIG["SELECTED_MODELS"]
        model_parameters = {k : v for k, v in all_parameters.items() if k in selected_models}
        max_iterations = CONFIG["MAX_ITERATIONS"] 

        results = {}        
        for name, conf in model_parameters.items():            
            model = self.collection.get_model(name) 

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
                                'LSS' : lss}
                                
            except Exception as e: 
                logger.error(f'Could not fit data using {name} - Error: {e}')               
                nan_list = [np.nan for x in range(num_params)]
                results[name] = {'optimal_params': nan_list, 
                                'covariance': nan_list, 
                                'errors': nan_list,
                                'LSS' : np.nan,
                                'exception' : e}                

        return results 
    
    #--------------------------------------------------------------------------
    def fit_all_data(self, dataset : pd.DataFrame):

        pressures = [np.array(x) for x in dataset['pressure [Pa]'].to_list()]
        uptakes = [np.array(x) for x in dataset['uptake [mol/g]'].to_list()]       

        # fitting adsorption isotherm data with theoretical models    
        fitting_results = []
        for x, y in zip(tqdm(pressures), uptakes):
            results = self.single_experiment_fit(x, y)
            fitting_results.append(results)

        return fitting_results

            
