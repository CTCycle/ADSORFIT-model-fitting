import numpy as np

from ADSORFIT.commons.constants import DATA_PATH
from ADSORFIT.commons.logger import logger


# [ADSORPTION MODELS]
###############################################################################
class AdsorptionModels:

    def __init__(self):
        self.model_names = ['LANGMUIR', 'SIPS', 'FREUNDLICH', 'TEMKIN']              
            
    #--------------------------------------------------------------------------
    def Langmuir_model(self, P, k, qsat):

        '''
        Langmuir adsorption model assumes monolayer adsorption onto a surface
        with a finite number of identical sites. 
        
        Parameters:
        P - Pressure
        k - Langmuir constant (related to affinity)
        qsat - Maximum adsorption capacity (monolayer)
        
        Returns:
        qe - Adsorption capacity at pressure P

        '''
        kP = P * k
        qe = qsat * (kP / (1 + kP))
        return qe    
    
    #--------------------------------------------------------------------------
    def Sips_model(self, P, k, qsat, N):

        '''
        Sips adsorption model is a hybrid of Langmuir and Freundlich models, used 
        to describe heterogeneous surfaces.
        
        Parameters:
        P - Pressure
        k - Sips constant (related to adsorption affinity)
        qsat - Maximum adsorption capacity
        N - Sips exponent (degree of surface heterogeneity)
        
        Returns:
        qe - Adsorption capacity at pressure P

        '''
        kP = k * (P ** N)
        qe = qsat * (kP / (1 + kP))
        return qe    
    
    #--------------------------------------------------------------------------
    def Freundlich_model(self, P, k, N):

        '''
        Freundlich adsorption model describes multilayer adsorption on heterogeneous 
        surfaces.
        
        Parameters:
        P - Pressure
        k - Freundlich constant (related to adsorption strength)
        N - Freundlich exponent (related to adsorption intensity)
        
        Returns:
        qe - Adsorption capacity at pressure P

        '''
        kP = P * k
        qe = kP ** (1 / N)
        return qe

    #--------------------------------------------------------------------------
    def Temkin_model(self, P, k, B):

        '''
        Temkin adsorption model accounts for adsorbate-adsorbent interactions and assumes 
        that the heat of adsorption decreases linearly with surface coverage.
        
        Parameters:
        P - Pressure
        K - Temkin constant (related to binding energy)
        B - Constant related to heat of adsorption
        
        Returns:
        qe - Adsorption capacity at pressure P

        '''        
        qe = B * np.log(k * P)
        return qe
    
    #--------------------------------------------------------------------------
    def get_model(self, model_name): 

        models = {'LANGMUIR' : self.Langmuir_model,
                  'SIPS' : self.Sips_model,
                  'FREUNDLICH': self.Freundlich_model,
                  'TEMKIN': self.Temkin_model} 
        
        return models[model_name]
    
            
