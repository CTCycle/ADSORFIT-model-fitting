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
        self.progress, self.total = 0, 0        
        logger.debug(f"Solver thread initialized with progress as {self.progress} and total as {self.total}")

   #---------------------------------------------------------------------------
   def start_data_fitting_thread(self, processed_data, experiment_col, pressure_col,
                                 uptake_col, model_states, max_iterations, find_best_models):
      
      # Start the data fitting process in a separate thread to keep the GUI responsive
      # give the data fitting function as target for the Thread instance 
      threading.Thread(
         target=self.run_data_fitting, args=(
            processed_data, experiment_col, pressure_col, uptake_col, 
            model_states, max_iterations, find_best_models), daemon=True).start()

   #---------------------------------------------------------------------------
   def run_data_fitting(self, processed_data, experiment_col, pressure_col,
                        uptake_col, model_states, max_iterations, find_best_models):
      
      # Callback function to update progress bar values
      def progress_callback(current, total):
         self.progress = current
         self.total = total

      # Call the solver bulk data fitting and add the progress bar callback 
      fitting_results = self.solver.bulk_data_fitting(
         processed_data, experiment_col, pressure_col, uptake_col, 
         model_states, max_iterations, progress_callback=progress_callback)

      # downstream data manipulation and process to adapt the results to the dataset
      fitting_dataset = self.adapter.adapt_results_to_dataset(fitting_results, processed_data)
      fitting_dataset = self.adapter.find_best_model(fitting_dataset) if find_best_models else fitting_dataset
      self.adapter.save_data_to_csv(fitting_dataset, model_states, find_best_models)