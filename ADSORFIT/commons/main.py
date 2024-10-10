import gradio as gr

# [SETTING WARNINGS]
import warnings
warnings.simplefilter(action='ignore', category=Warning)

# [IMPORT CUSTOM MODULES]
from ADSORFIT.commons.utils.app.tabs import solver_tab, models_tab
from ADSORFIT.commons.constants import CONFIG
from ADSORFIT.commons.logger import logger


# Main window
###############################################################################
with gr.Blocks() as demo:
    
    selected_models = gr.State([])
    with gr.Tab('Solver'):
        solver_UI = solver_tab(selected_models)
    with gr.Tab('Models'):
        models_selection = models_tab(CONFIG['MODELS'], selected_models)

# Launch the app
###############################################################################
if __name__ == '__main__':
    demo.launch(inbrowser=True)
