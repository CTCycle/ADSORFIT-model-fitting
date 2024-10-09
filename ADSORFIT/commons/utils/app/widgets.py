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
                process_button = gr.Button("Process data", interactive=False)
            with gr.Column(scale=1, min_width=100):  
                P_col_select = gr.Dropdown(label="Pressure data", choices=[], interactive=True)
            with gr.Column(scale=1, min_width=100):  
                Q_col_select = gr.Dropdown(label="Uptake data", choices=[], interactive=True)
            with gr.Column(scale=1, min_width=100):  
                temp_col_dd = gr.Dropdown(label="Temperature", choices=[], interactive=True)
            with gr.Column(scale=1, min_width=100):  
                exp_col_select = gr.Dropdown(label="Experiments", choices=[], interactive=True)

        return process_button, P_col_select, Q_col_select, temp_col_dd, exp_col_select

    #--------------------------------------------------------------------------
    def file_browser(self):

        with gr.Row():
            with gr.Column():
                file_browser = gr.File(label="Select source CSV File", type="filepath", file_types=[".csv"])                
            with gr.Column():
                text_display = gr.Textbox(label="File Content", placeholder="File statistics will appear here", 
                                          lines=10, interactive=False)           
        
        
        return file_browser, text_display


###############################################################################
class ModelSelectionWidgets:

    def __init__(self, models_json : dict):

        self.models_json = models_json

    #--------------------------------------------------------------------------
    def models_selector(self, model_selectors : list):

        with gr.Column():
            for model, params in self.models_json.items(): 

                if model_selectors:
                    gr.HTML("<hr>")  

                with gr.Row():
                    selected = gr.Checkbox(label=f"Use {model}", value=True)                    

                    with gr.Column():                    
                        initial_inputs = {k: gr.Number(label=f"Initial {k}", value=v) for k, v in params["initial"].items()}                
                    with gr.Column():                    
                        min_inputs = {k: gr.Number(label=f"Min {k}", value=v) for k, v in params["min"].items()}
                    with gr.Column(): 
                        max_inputs = {k: gr.Number(label=f"Max {k}", value=v) for k, v in params["max"].items()}
                    
                    model_selectors.append((selected, initial_inputs, min_inputs, max_inputs))

        return model_selectors

  
###############################################################################
def solver_parameters_widget():

    with gr.Row():
        with gr.Column():
            iterations = gr.Number(label="Number of Iterations", value=100)
            seed = gr.Number(label="Random Seed", value=42)
        with gr.Column():
            run_button = gr.Button("Run Fitting")

    return iterations, seed, run_button