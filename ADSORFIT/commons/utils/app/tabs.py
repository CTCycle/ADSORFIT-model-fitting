import gradio as gr
from tqdm import tqdm
tqdm.pandas()

from ADSORFIT.commons.utils.app.widgets import SourceFileWidgets, ModelSelectionWidgets, SolverParametersWidgets
from ADSORFIT.commons.utils.datamaker.processing import SourceFileHandling
from ADSORFIT.commons.utils.solver.fitting import run_solver
from ADSORFIT.commons.constants import CONFIG, DATA_PATH
from ADSORFIT.commons.logger import logger


# [UI Design - Solver tab]
###############################################################################
def solver_tab(selected_models_snapshot):

    # [INITIALIZATION]
    #--------------------------------------------------------------------------
    file_widgets = SourceFileWidgets() 
    file_handler = SourceFileHandling() 
    solver_widgets = SolverParametersWidgets(CONFIG['SEED'], CONFIG['MAX_ITERATIONS']) 

    # initialize session stateful variables
    source_data = gr.State()
    processed_data = gr.State() 
    solver_results = gr.State()

    # [WIDGETS]
    #--------------------------------------------------------------------------
    # define the widget elements    
    with gr.Blocks() as solver_ui:
        # 1. File browser to look for the source .csv file
        file_browser, text_display = file_widgets.file_browser()
        gr.HTML('<div style="border-top: 1px solid black; margin-top: 20px; margin-bottom: 20px;"></div>')
        # 2. Dropdown menus to select different columns
        process_button, P_col, Q_col, T_col, exp_col = file_widgets.columns_selection_dropdown()        
        gr.HTML('<div style="border-top: 1px solid black; margin-top: 20px; margin-bottom: 20px;"></div>')
        # 3. Parameters for the solver
        iterations, seed, get_models_button, run_button = solver_widgets.solver_parametrizer()


    # [INTERACTIONS]
    #--------------------------------------------------------------------------
    # When file is selected, get the file content and store it in the state
    file_browser.change(fn=file_handler.get_file, inputs=file_browser, outputs=source_data)

    # Once the file is selected, update the dropdowns based on file content
    source_data.change(fn=file_handler.update_columns_dropdown, 
                       inputs=source_data, outputs=[P_col, Q_col, T_col, exp_col])      
    
    # update the interactive state of the button based on interactions with the dropdowns
    # when all dropdowns have a value, the process data button becomes interactive
    P_col.change(fn=file_widgets.update_process_data_button_state,
                    inputs=[P_col, Q_col, T_col, exp_col],
                    outputs=process_button)

    Q_col.change(fn=file_widgets.update_process_data_button_state,
                    inputs=[P_col, Q_col, T_col, exp_col],
                    outputs=process_button)
    
    T_col.change(fn=file_widgets.update_process_data_button_state,
                    inputs=[P_col, Q_col, T_col, exp_col],
                    outputs=process_button)

    exp_col.change(fn=file_widgets.update_process_data_button_state,
                      inputs=[P_col, Q_col, T_col, exp_col],
                      outputs=process_button)

    # process file when the process data button is clicked
    process_button.click(fn=file_handler.process_source_file, 
                         inputs=[P_col, Q_col, T_col, exp_col, source_data],
                         outputs=[processed_data, text_display])
    
    # the fitting button becomes interactive when processed data is available
    processed_data.change(fn=solver_widgets.update_fitting_button_state, 
                          inputs=processed_data, 
                          outputs=run_button)    
    
    # the fitting button becomes interactive when processed data is available
    run_button.click(fn=run_solver, 
                     inputs=[processed_data, P_col, Q_col, selected_models_snapshot, iterations, seed], 
                     outputs=solver_results)

    return solver_ui

    


# [UI Design - Models tab]
###############################################################################
def models_tab(model_json, selected_models):

    with gr.Blocks() as models_ui:                
        selector = ModelSelectionWidgets(model_json)
        model_selectors = selector.models_selector(selected_models)           
        
        

    return models_ui
    





