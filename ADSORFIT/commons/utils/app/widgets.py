import pandas as pd
import gradio as gr
from tqdm import tqdm
tqdm.pandas()

from ADSORFIT.commons.utils.app.backend import process_source_file
from ADSORFIT.commons.constants import CONFIG, DATA_PATH
from ADSORFIT.commons.logger import logger


###############################################################################
class SourceFileWidgets:

    def __init__(self):
        pass

    #--------------------------------------------------------------------------
    def columns_selection(self):

        with gr.Row():
            with gr.Column():
                X_col_dropdown = gr.Dropdown(label="Select X Column", choices=[], interactive=True)
            with gr.Column():
                Y_col_dropdown = gr.Dropdown(label="Select Y Column", choices=[], interactive=True)
            with gr.Column():
                exp_col_dropdown = gr.Dropdown(label="Select Experiment Column", choices=[], interactive=True)

        return X_col_dropdown, Y_col_dropdown, exp_col_dropdown

    #--------------------------------------------------------------------------
    def file_browser(self):

        with gr.Row():
            with gr.Column():
                file_browser = gr.File(label="Select source CSV File", type="filepath", file_types=[".csv"])
                print(file_browser)
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