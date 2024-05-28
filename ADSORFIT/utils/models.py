import numpy as np
from scipy.optimize import curve_fit
from tqdm import tqdm
tqdm.pandas()


# [ADSORPTION MODELS]
#==============================================================================
class AdsorptionModels:

    def __init__(self, parameters):
        self.model_names = ['langmuir', 'sips', 'freundlich']
        langmuir_param = parameters['langmuir']
        sips_param = parameters['sips'] 
        freund_param = parameters['freundlich']       
        self.ads_models = {'langmuir' : {'initial_guess' : [langmuir_param[0][0], langmuir_param[0][1]], 
                                         'low_boundary' : [0, 0], 
                                         'high_boundary' : [langmuir_param[1][0], langmuir_param[1][1]],
                                         'model_func': self.Langmuir_model},
                           'sips' :     {'initial_guess' : [sips_param[0][0], sips_param[0][1], sips_param[0][2]], 
                                         'low_boundary' : [0, 0, 0], 
                                         'high_boundary' : [sips_param[1][0], sips_param[1][1], sips_param[1][2]],
                                         'model_func': self.Sips_model},
                           'freundlich' :{'initial_guess' : [freund_param[0][0], freund_param[0][1]], 
                                         'low_boundary' : [0, 0], 
                                         'high_boundary' : [freund_param[1][0], freund_param[1][1]],
                                         'model_func': self.Freundlich_model}} 
            
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
    def Freundlich_model(self, P, k, N):        
        kP = P * k
        qe = kP ** 1/N 
        return qe    

    #--------------------------------------------------------------------------
    def adsorption_fitter(self, X, Y, max_iter):

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
            except Exception as e:                
                nan_list = [np.nan for x in range(num_params)]
                results[name] = {'optimal_params': nan_list, 
                                 'covariance': nan_list, 
                                 'errors': nan_list,
                                 'LSS' : np.nan,
                                 'exception' : e}                

        return results 
    
            
