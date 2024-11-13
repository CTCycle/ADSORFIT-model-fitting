from nicegui import ui
from concurrent.futures import ProcessPoolExecutor

# [SETTING WARNINGS]
import warnings
warnings.simplefilter(action='ignore', category=Warning)

# [IMPORT CUSTOM MODULES]
from ADSORFIT.commons.utils.app.widgets import ModelsConfigurationWidgets
from ADSORFIT.commons.utils.datamaker.datasets import AdsorptionDataProcessing
from ADSORFIT.commons.utils.app.threads import SolverThread
from ADSORFIT.commons.constants import CONFIG
from ADSORFIT.commons.logger import logger


###############################################################################
with ui.tabs() as tabs:
    
    tab_main = ui.tab('ADSORFIT Solver')
    tab_parameters = ui.tab('Model configurations')

with ui.tab_panels(tabs, value=tab_main) as panels:
    
    processor = AdsorptionDataProcessing()
    solver = SolverThread()     
    
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
                                                                                    max_iterations.value)])

        # [PROGRESS BAR]
        #----------------------------------------------------------------------
        with ui.row().classes('w-full no-wrap justify-between'):              
            progressbar = ui.linear_progress(value=0).props('instant-feedback')
            progressbar.visible = False 

        # [TIMER TO UPDATE PROGRESS BAR]
        ui.timer(0.5, lambda: update_progress())


        def update_progress():
            if solver.total > 0:
                progressbar.visible = True
                progressbar.value = solver.progress / solver.total
                if solver.progress >= solver.total:
                    progressbar.visible = False
                    ui.notify('Data fitting is completed')
                    # Reset progress
                    solver.progress = 0
                    solver.total = 0
            else:
                progressbar.visible = False
        

    # [MODEL CONFIGURATIONS TAB]
    #--------------------------------------------------------------------------
    with ui.tab_panel(tab_parameters):
        models_widgets = ModelsConfigurationWidgets()       
        models_widgets.model_configurations()   
        

ui.run()