from tqdm import tqdm
tqdm.pandas()

from ADSORFIT.commons.constants import CONFIG, DATA_PATH
from ADSORFIT.commons.logger import logger


# [ADSORPTION MODELS]
###############################################################################
class AdsorptionModels:

    def __init__(self):
        self.model_names = ['LANGMUIR', 'SIPS', 'FREUNDLICH']              
        
            
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
    def get_model(self, model_name): 

        models = {'LANGMUIR' : self.Langmuir_model,
                  'SIPS' : self.Sips_model,
                  'FREUNDLICH': self.Freundlich_model} 
        
        return models[model_name]
    
            
