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

        with gr.Row():
            with gr.Column(scale=1, min_width=50):  
                process_button = gr.Button('Process data', interactive=False)
            with gr.Column(scale=1, min_width=100):  
                P_col_select = gr.Dropdown(label='Pressure data', choices=[], interactive=True)
            with gr.Column(scale=1, min_width=100):  
                Q_col_select = gr.Dropdown(label='Uptake data', choices=[], interactive=True)
            with gr.Column(scale=1, min_width=100):  
                temp_col_dd = gr.Dropdown(label='Temperature', choices=[], interactive=True)
            with gr.Column(scale=1, min_width=100):  
                exp_col_select = gr.Dropdown(label='Experiments', choices=[], interactive=True)

        return process_button, P_col_select, Q_col_select, temp_col_dd, exp_col_select

    #--------------------------------------------------------------------------
    def file_browser(self):

        with gr.Row():
            with gr.Column():
                file_browser = gr.File(label='Select source CSV File', type='filepath', file_types=['.csv'])                
            with gr.Column():
                text_display = gr.Textbox(label='File Content', placeholder='File statistics will appear here', 
                                          lines=8, interactive=False)         
        
        return file_browser, text_display


###############################################################################
class ModelSelectionWidgets:

    def __init__(self, models_json: dict):
        self.models_json = models_json

    #--------------------------------------------------------------------------    
    def update_selected_models(self, selected_models, model_name, selected, 
                           initial_inputs_values, min_inputs_values, max_inputs_values):

        if selected:
            # Update the selected models with the current values of the inputs
            selected_models[model_name] = {
                'initial': initial_inputs_values,
                'min': min_inputs_values,
                'max': max_inputs_values
            }
        else:
            # If the model is deselected, remove it from the selected models
            if model_name in selected_models:
                del selected_models[model_name]

        return gr.update(value=selected_models)    

    #--------------------------------------------------------------------------
    def models_selector(self, selected_models):
        
        
        for model, params in self.models_json.items():
            # Store parameter values for later updates
            initial_inputs_values = {k: v for k, v in params['initial'].items()}
            min_inputs_values = {k: v for k, v in params['min'].items()}
            max_inputs_values = {k: v for k, v in params['max'].items()}
            
            with gr.Row():
                with gr.Column(scale=1, min_width=40):
                    # Checkbox for selecting/deselecting the model
                    is_selected = gr.Checkbox(label=f'Use {model}', value=True)
                with gr.Column(scale=1, min_width=50):
                    # Inputs for initial, min, and max parameter values
                    initial_inputs = {k: gr.Number(label=f'Initial {k}', value=v) for k, v in params['initial'].items()}
                with gr.Column(scale=1, min_width=50):
                    min_inputs = {k: gr.Number(label=f'Min {k}', value=v) for k, v in params['min'].items()}
                with gr.Column(scale=1, min_width=50):
                    max_inputs = {k: gr.Number(label=f'Max {k}', value=v) for k, v in params['max'].items()}
                
                # Add line break between models
                gr.HTML('<hr>')

                # Set up change events for individual inputs and the selection checkbox
                is_selected.change(
                    fn=self.update_selected_models,
                    inputs=[selected_models, gr.State(model), is_selected, 
                            gr.State(initial_inputs_values), gr.State(min_inputs_values),
                            gr.State(max_inputs_values)],
                    outputs=selected_models)

        return selected_models


    
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