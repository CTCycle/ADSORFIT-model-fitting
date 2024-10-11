import gradio as gr

# [SETTING WARNINGS]
import warnings
warnings.simplefilter(action='ignore', category=Warning)

# [IMPORT CUSTOM MODULES]
from ADSORFIT.commons.utils.solver.models import update_models_dictionary
from ADSORFIT.commons.utils.app.tabs import solver_tab, models_tab
from ADSORFIT.commons.constants import CONFIG
from ADSORFIT.commons.logger import logger


# Main window
###############################################################################
with gr.Blocks() as demo:
    
    selected_models = gr.State([])
    with gr.Tab('Solver'):
        run_button, get_models_button = solver_tab(selected_models)
    with gr.Tab('Models'):
        models = models_tab()        

    get_models_button.click(fn=update_models_dictionary,
                            inputs=[models],
                            outputs=selected_models)


# Launch the app
###############################################################################
if __name__ == '__main__':
    demo.launch(inbrowser=True)
