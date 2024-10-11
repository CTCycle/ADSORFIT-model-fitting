import pandas as pd
import gradio as gr
from tqdm import tqdm
tqdm.pandas()

from ADSORFIT.commons.constants import CONFIG, DATA_PATH
from ADSORFIT.commons.logger import logger


###############################################################################
class SourceFileWidgets:

    def __init__(self):
        pass

    #--------------------------------------------------------------------------
    def update_process_data_button_state(self, X_value, Y_value, T_value, exp_value):
        
        if X_value and Y_value and T_value and exp_value:
            return gr.update(interactive=True) 
        else:
            return gr.update(interactive=False)

    #--------------------------------------------------------------------------
    def columns_selection_dropdown(self):
        
        P_col_select = gr.Dropdown(label='Pressure data', choices=[], interactive=True)
        Q_col_select = gr.Dropdown(label='Uptake data', choices=[], interactive=True)
        temp_col_dd = gr.Dropdown(label='Temperature', choices=[], interactive=True)
        exp_col_select = gr.Dropdown(label='Experiments', choices=[], interactive=True)
        process_button = gr.Button('Process data', interactive=False)

        return P_col_select, Q_col_select, temp_col_dd, exp_col_select, process_button

    #--------------------------------------------------------------------------
    def file_browser(self):

        file_browser = gr.File(label='Select source CSV File', type='filepath', file_types=['.csv'])  

        return file_browser  

    #--------------------------------------------------------------------------
    def text_display(self):            
        
        text_display = gr.Textbox(label='File Content', placeholder='File statistics will appear here', 
                                  lines=8, interactive=False)         
        
        return text_display


###############################################################################
class ModelSelectionWidgets:

    def __init__(self):
        self.default_selected_models = CONFIG['MODELS']      

    #--------------------------------------------------------------------------
    def models_selector(self):        
        model_inputs = []
        for model_name, params in self.default_selected_models.items():
            with gr.Row():
                with gr.Column(scale=1, min_width=40):                    
                    is_selected = gr.Checkbox(label=f'Use {model_name}', value=True, interactive=True)
                with gr.Column(scale=1, min_width=50):                    
                    initial_values = gr.JSON(label=f'Initial values for {model_name}', value=params['initial'], interactive=True)
                with gr.Column(scale=1, min_width=50):
                    min_values = gr.JSON(label=f'Min values for {model_name}', value=params['min'], interactive=True)
                with gr.Column(scale=1, min_width=50):
                    max_values = gr.JSON(label=f'Max values for {model_name}', value=params['max'], interactive=True)
                    
            # Add the individual components to model_inputs
            model_inputs.extend([model_name, initial_values, min_values, max_values, is_selected])
        
        return model_inputs


    
###############################################################################
class SolverParametersWidgets:

    def __init__(self, seed, max_iterations):

        self.seed = seed
        self.max_iterations = max_iterations

    #--------------------------------------------------------------------------
    def update_fitting_button_state(self, processed_data):
        
        if processed_data is not None:
            return gr.update(interactive=True) 
        else:
            return gr.update(interactive=False)

    #--------------------------------------------------------------------------
    def solver_parametrizer(self):

        with gr.Row():
            with gr.Column():
                iterations = gr.Number(label='Number of Iterations', value=self.max_iterations, 
                                       interactive=True)
                seed = gr.Number(label='Random Seed', value=self.seed, interactive=True)
            with gr.Column():
                get_model_button = gr.Button('Update model references', interactive=True)
                run_button = gr.Button('Run Fitting', interactive=False)

        return iterations, seed, get_model_button, run_button 