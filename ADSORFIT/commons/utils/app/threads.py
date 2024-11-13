from nicegui import ui

from tqdm import tqdm
tqdm.pandas()

from ADSORFIT.commons.utils.datamaker.datasets import AdsorptionDataProcessing, DatasetAdapter
from ADSORFIT.commons.utils.solver.fitting import ModelSolver
from ADSORFIT.commons.utils.solver.models import AdsorptionModels
from ADSORFIT.commons.constants import CONFIG
from ADSORFIT.commons.logger import logger



                
# [FITTING FUNCTION]
###############################################################################
class SolverThread:

    def __init__(self):
       self.solver = ModelSolver()
       self.adapter = DatasetAdapter()  

    #--------------------------------------------------------------------------
    def start_data_fitting_thread(self, processed_data, experiment_col, pressure_col,
                                  uptake_col, model_states, max_iterations):
        
        fitting_results = self.solver.bulk_data_fitting(processed_data, experiment_col, pressure_col,
                                                        uptake_col, model_states, max_iterations)                                                        
                                                                                                            
        fitting_dataset = self.adapter.adapt_results_to_dataset(fitting_results, processed_data)        
        fitting_dataset = self.adapter.find_best_model(fitting_dataset)
        self.adapter.save_data_to_csv(fitting_dataset, model_states)                                                              
    