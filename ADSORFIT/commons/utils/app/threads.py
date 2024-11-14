import threading

from ADSORFIT.commons.utils.datamaker.datasets import DatasetAdapter
from ADSORFIT.commons.utils.solver.fitting import ModelSolver
from ADSORFIT.commons.logger import logger



                
# [FITTING FUNCTION]
###############################################################################
class SolverThread:

   def __init__(self):
        self.solver = ModelSolver()
        self.adapter = DatasetAdapter()
        self.progress = 0
        self.total = 0

   #---------------------------------------------------------------------------
   def start_data_fitting_thread(self, processed_data, experiment_col, pressure_col,
                                  uptake_col, model_states, max_iterations, find_best_models):
      
      threading.Thread(target=self.run_data_fitting,
                       args=(processed_data, experiment_col, pressure_col, uptake_col, 
                             model_states, max_iterations, find_best_models),
                       daemon=True).start()

   #---------------------------------------------------------------------------
   def run_data_fitting(self, processed_data, experiment_col, pressure_col,
                         uptake_col, model_states, max_iterations, find_best_models):
      
      def progress_callback(current, total):
         self.progress = current
         self.total = total

      fitting_results = self.solver.bulk_data_fitting(processed_data, experiment_col, pressure_col,
                                                      uptake_col, model_states, max_iterations,
                                                      progress_callback=progress_callback)

      fitting_dataset = self.adapter.adapt_results_to_dataset(fitting_results, processed_data)
      if find_best_models:
         fitting_dataset = self.adapter.find_best_model(fitting_dataset)
      self.adapter.save_data_to_csv(fitting_dataset, model_states, find_best_models)