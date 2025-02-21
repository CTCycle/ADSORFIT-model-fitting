import os
from dotenv import load_dotenv

from ADSORFIT.commons.constants import ROOT_DIR
from ADSORFIT.commons.logger import logger

# [IMPORT CUSTOM MODULES]
###############################################################################
class EnvironmentVariables:

    def __init__(self):        
        self.env_path = os.path.join(ROOT_DIR, 'setup', 'variables', '.env')        
        if os.path.exists(self.env_path):
            load_dotenv(dotenv_path=self.env_path, override=True)
        else:
            logger.error(f".env file not found at: {self.env_path}")   
    
    #--------------------------------------------------------------------------
    def get_environment_variables(self):                  
        return {"NICEGUI_PORT": os.getenv("NICEGUI_PORT", "8080"),
                "NICEGUI_HOST": os.getenv("NICEGUI_HOST", "0.0.0.0")}
       
