import gradio as gr
from tqdm import tqdm
tqdm.pandas()

from ADSORFIT.commons.utils.app.widgets import SourceFileWidgets, ModelSelectionWidgets
from ADSORFIT.commons.utils.datamaker.handlers import SourceFileHandling
from ADSORFIT.commons.constants import CONFIG, DATA_PATH
from ADSORFIT.commons.logger import logger


# [UI Design - Solver tab]
###############################################################################
def solver_tab():

    file_widgets = SourceFileWidgets() 
    file_handler = SourceFileHandling()  

    source_data = gr.State()
    processed_data = gr.State() 

    # define the widget elements
    # 1. file browser to look for source .csv file
    # 2. dropdown menus to select different columns
    file_browser, text_display = file_widgets.file_browser()
    process_button, P_col_select, Q_col_select, T_col_select, exp_col_select = file_widgets.columns_selection_dropdown()

    # When file is selected, get the file content and store it in the state
    file_browser.change(fn=file_handler.get_file, inputs=file_browser, outputs=source_data)

    # Once the file is selected, update the dropdowns based on file content
    source_data.change(fn=file_handler.update_columns_dropdown, 
                       inputs=source_data, 
                       outputs=[P_col_select, Q_col_select, T_col_select, exp_col_select])    
    
    # update the interactive state of the button based on interactions with the dropdowns
    P_col_select.change(fn=file_widgets.update_process_data_button_state,
                    inputs=[P_col_select, Q_col_select, T_col_select, exp_col_select],
                    outputs=process_button)

    Q_col_select.change(fn=file_widgets.update_process_data_button_state,
                    inputs=[P_col_select, Q_col_select, T_col_select, exp_col_select],
                    outputs=process_button)
    
    T_col_select.change(fn=file_widgets.update_process_data_button_state,
                    inputs=[P_col_select, Q_col_select, T_col_select, exp_col_select],
                    outputs=process_button)

    exp_col_select.change(fn=file_widgets.update_process_data_button_state,
                      inputs=[P_col_select, Q_col_select, T_col_select, exp_col_select],
                      outputs=process_button)

    process_button.click(fn=file_handler.process_source_file, 
                         inputs=[P_col_select, Q_col_select, T_col_select, exp_col_select, source_data],
                         outputs=[processed_data, text_display])    

    return processed_data

    


# [UI Design - Models tab]
###############################################################################
def models_tab(model_json):
    model_selectors = []
    selector = ModelSelectionWidgets(model_json)
    model_selectors = selector.models_selector(model_selectors)
    





