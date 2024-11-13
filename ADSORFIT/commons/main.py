from nicegui import ui
from concurrent.futures import ProcessPoolExecutor

# [SETTING WARNINGS]
import warnings
warnings.simplefilter(action='ignore', category=Warning)

# [IMPORT CUSTOM MODULES]
from ADSORFIT.commons.utils.app.widgets import ModelsConfigurationWidgets
from ADSORFIT.commons.utils.datamaker.datasets import AdsorptionDataProcessing, DatasetAdapter
from ADSORFIT.commons.utils.solver.fitting import ModelSolver
from ADSORFIT.commons.constants import CONFIG
from ADSORFIT.commons.logger import logger


###############################################################################
with ui.tabs() as tabs:
    
    tab_main = ui.tab('ADSORFIT Solver')
    tab_parameters = ui.tab('Model configurations')

with ui.tab_panels(tabs, value=tab_main) as panels:

    executor = ProcessPoolExecutor()
    processor = AdsorptionDataProcessing()    
    solver = ModelSolver() 
    adapter = DatasetAdapter()  
    
    # [SOLVER TAB]
    #--------------------------------------------------------------------------
    with ui.tab_panel(tab_main).classes('w-full justify-between'):   

        with ui.row().classes('w-full no-wrap justify-between'):             
           
            with ui.column().classes('w-full p-4'):
                identify_cols = ui.checkbox('Automatically identify columns')
                best_models = ui.checkbox('Identify best models')
                save_best_fit = ui.checkbox('Save best fitting')

            with ui.column().classes('w-full p-4'):
                max_iterations = ui.number("Max iterations", value=1000) 

            with ui.column().classes('w-full p-4'):
                stats = ui.markdown(content="Statistics will be displayed here.").style(
                    'padding: 10px; width: 400px; text-align: left;')                           

        ui.separator()

        # [BUTTONS ROW]
        #----------------------------------------------------------------------
        with ui.row().classes('w-full no-wrap justify-between'):

            def start_fitting_task():
                fitting_task = executor.submit(solver.bulk_data_fitting, processor.processed_data,
                                processor.experiment_col, processor.pressure_col,
                                processor.uptake_col, models_widgets.model_states,
                                max_iterations.value) 
                # Schedule the downstream adaptation to run after the fitting task completes
                fitting_task.add_done_callback(on_fitting_task_complete) 

            def on_fitting_task_complete(future):
                # This will be called once the fitting task is done
                # Execute the downstream_dataset_adaptation function
                adapter.downstream_dataset_adaptation(
                    processor.processed_data,
                    solver.results_dictionary,
                    models_widgets.model_states)
                          

            with ui.column().classes('w-full p-4'):                
                ui.button('Process data', on_click=lambda : [processor.preprocess_dataset(identify_cols.value),
                                                             stats.set_content(processor.stats)]) 
            with ui.column().classes('w-full p-4'):     
                ui.button('Data fitting', on_click=start_fitting_task)        

        # [PROGRESS BAR]
        #----------------------------------------------------------------------
        with ui.row().classes('w-full no-wrap justify-between'):              
            progressbar = ui.linear_progress(value=0).props('instant-feedback')
            progressbar.visible = False 
            

    # [MODEL CONFIGURATIONS TAB]
    #--------------------------------------------------------------------------
    with ui.tab_panel(tab_parameters):
        models_widgets = ModelsConfigurationWidgets()       
        models_widgets.model_configurations()   
        

ui.run()