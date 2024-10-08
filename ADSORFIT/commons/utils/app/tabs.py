import gradio as gr
from tqdm import tqdm
tqdm.pandas()

from ADSORFIT.commons.utils.app.widgets import SourceFileWidgets, ModelSelectionWidgets
from ADSORFIT.commons.utils.app.backend import execute_fitting
from ADSORFIT.commons.constants import CONFIG, DATA_PATH
from ADSORFIT.commons.logger import logger


# [UI Design - Solver tab]
###############################################################################
def solver_tab():

    widgets = SourceFileWidgets()    
    file_browser, text_display = widgets.file_browser()
    dropdowns = widgets.columns_selection()       

    return file_browser, text_display, dropdowns


# [UI Design - Models tab]
###############################################################################
def models_tab(model_json):
    model_selectors = []
    selector = ModelSelectionWidgets(model_json)
    model_selectors = selector.models_selector(model_selectors)
    





