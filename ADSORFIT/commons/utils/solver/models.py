import gradio as gr
from tqdm import tqdm
tqdm.pandas()

from ADSORFIT.commons.constants import CONFIG, DATA_PATH
from ADSORFIT.commons.logger import logger


###############################################################################
def update_models_dictionary(*inputs):
    models = []
    num_models = len(inputs)//4  

    for i in range(num_models):
        is_selected = inputs[i * 4 + 3]  
        if is_selected:
            model_data = {
                'name': inputs[i * 4], 
                'initial': inputs[i * 4 + 1],  
                'min': inputs[i * 4 + 2], 
                'max': inputs[i * 4 + 3],  
                'is_selected': is_selected
            }
            models.append(model_data)
    
    return models


# [ADSORPTION MODELS]
###############################################################################
class AdsorptionModels:

    def __init__(self):

        pass        
            
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
    
            
