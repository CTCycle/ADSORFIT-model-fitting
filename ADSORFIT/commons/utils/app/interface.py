import os
from nicegui import ui

from ADSORFIT.commons.constants import RESULTS_PATH, DATASET_PATH, BEST_FIT_PATH
from ADSORFIT.commons.logger import logger



def process_data():
    ui.notify('Processing data...')


###############################################################################
def main_tab_interface():
    
    with ui.tabs() as tabs:
        # Define two tabs
        tab_main = ui.tab('Core Functionalities')
        tab_parameters = ui.tab('Model Parameters')

    with ui.tab_panels(tabs) as panels:
        # Main tab
        with ui.tab_panel(tab_main):
            with ui.row():
                with ui.column():
                    # Processing data button on the left
                    ui.button('Process Data', on_click=process_data)
                with ui.column():
                    # Placeholder for parameters on the right
                    ui.input('Parameter 1', placeholder='Enter value...')
                    ui.input('Parameter 2', placeholder='Enter value...')

        # Secondary tab
        with ui.tab_panel(tab_parameters):
            ui.label('Model parameters will be set here.')

    # Run the application
    ui.run()
