from nicegui import ui

# [SETTING WARNINGS]
import warnings
warnings.simplefilter(action='ignore', category=Warning)

# [IMPORT CUSTOM MODULES]
from ADSORFIT.commons.utils.app.widgets import ModelsConfigurationWidgets, ProgressBarWidgets
from ADSORFIT.commons.utils.datamaker.datasets import AdsorptionDataProcessing
from ADSORFIT.commons.utils.app.threads import SolverThread
from ADSORFIT.commons.logger import logger


###############################################################################
with ui.tabs() as tabs:
    
    tab_main = ui.tab('ADSORFIT Solver')
    tab_parameters = ui.tab('Model configurations')

with ui.tab_panels(tabs, value=tab_main) as panels:
    
    pb = ProgressBarWidgets()
    processor = AdsorptionDataProcessing()
    solver = SolverThread()     
    
    # [SOLVER TAB]
    #--------------------------------------------------------------------------
    with ui.tab_panel(tab_main).classes('w-full justify-between'):   

        with ui.row().classes('w-full no-wrap justify-between'):             
           
            with ui.column().classes('w-full p-4'):
                identify_cols = ui.checkbox('Automatically detect columns')
                best_models = ui.checkbox('Identify best models')
                
            with ui.column().classes('w-full p-4'):
                max_iterations = ui.number("Max iterations", value=1000) 

            with ui.column().classes('w-full p-4'):
                stats = ui.markdown(content="Statistics will be displayed here.").style(
                    'padding: 10px; width: 400px; text-align: left;')                           

        ui.separator()

        # [BUTTONS ROW]
        #----------------------------------------------------------------------
        with ui.row().classes('w-full no-wrap justify-between'):                         

            with ui.column().classes('w-full p-4'):                
                ui.button('Process data', on_click=lambda : [processor.preprocess_dataset(identify_cols.value),
                                                             stats.set_content(processor.stats)]) 
            with ui.column().classes('w-full p-4'):     
                data_fitting_button = ui.button('Data fitting', on_click=lambda : [solver.start_data_fitting_thread(
                                                                                   processor.processed_data,
                                                                                   processor.experiment_col,
                                                                                   processor.pressure_col,
                                                                                   processor.uptake_col,
                                                                                   models_widgets.model_states,
                                                                                   max_iterations.value,
                                                                                   best_models.value)])                

        # [PROGRESS BAR]
        #----------------------------------------------------------------------
        with ui.row().classes('w-full no-wrap justify-between'):              
            progress_bar = pb.build_progress_bar()

        # [TIMER TO UPDATE PROGRESS BAR]
        ui.timer(0.5, lambda: pb.update_progress_bar(progress_bar, solver))

    # [MODEL CONFIGURATIONS TAB]
    #--------------------------------------------------------------------------
    with ui.tab_panel(tab_parameters):
        models_widgets = ModelsConfigurationWidgets()       
        models_widgets.model_configurations()  
        

ui.run()