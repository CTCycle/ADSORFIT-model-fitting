from nicegui import ui

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

    processor = AdsorptionDataProcessing()
    fitter = ModelSolver()
    
    # [SOLVER TAB]
    #--------------------------------------------------------------------------
    with ui.tab_panel(tab_main).classes('w-full justify-between'):   

        with ui.row().classes('w-full no-wrap justify-between'):             
           
            with ui.column().classes('w-full p-4'):
                identify_cols = ui.checkbox('Identify Columns')
                best_fit = ui.checkbox('Save best fitting')

            with ui.column().classes('w-full p-4'):
                max_iterations = ui.number("Max iterations", value=1000)           

        ui.separator()

        # [BUTTONS ROW]
        #----------------------------------------------------------------------
        with ui.row().classes('w-full no-wrap justify-between'):           

            with ui.column().classes('w-full p-4'):                
                ui.button('Process data', on_click=lambda : [processor.preprocess_dataset(identify_cols.value),
                                                             stats.set_value(processor.stats),
                                                             print(models_widgets.model_states)]) 
                ui.button('Data fitting', on_click=lambda : [fitter.run_bulk_fitting_thread(processor.processed_data,
                                                                                            processor.experiment_col,
                                                                                            processor.pressure_col,
                                                                                            processor.uptake_col,
                                                                                            models_widgets.model_states,
                                                                                            max_iterations.value)]) 


            with ui.column().classes('w-full p-4'):
                stats = ui.textarea('Statistics', value="Statistics will be displayed here.").style(
                    'padding: 10px; width: 400px; text-align: left;') 
                
        # [PROGRESS BAR]
        #----------------------------------------------------------------------
        with ui.row().classes('w-full no-wrap justify-between'):              
            progress_bar = ui.linear_progress(value=0)
            

    # [MODEL CONFIGURATIONS TAB]
    #--------------------------------------------------------------------------
    with ui.tab_panel(tab_parameters):
        models_widgets = ModelsConfigurationWidgets()       
        models_widgets.model_configurations()
                
        

ui.run()