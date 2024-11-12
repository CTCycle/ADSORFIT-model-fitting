from nicegui import ui

# [SETTING WARNINGS]
import warnings
warnings.simplefilter(action='ignore', category=Warning)

# [IMPORT CUSTOM MODULES]
from ADSORFIT.commons.utils.app.widgets import ModelsConfigurationWidgets
from ADSORFIT.commons.utils.datamaker.datasets import AdsorptionDataProcessing, DatasetAdapter
from ADSORFIT.commons.utils.solver.fitting import DatasetSolver
from ADSORFIT.commons.constants import CONFIG
from ADSORFIT.commons.logger import logger


 
###############################################################################
with ui.tabs() as tabs:
    # Define two tabs
    tab_main = ui.tab('ADSORFIT Solver')
    tab_parameters = ui.tab('Model configurations')

# Set the 'value' parameter to 'tab_main' to make it the default active tab
with ui.tab_panels(tabs, value=tab_main) as panels:
    with ui.tab_panel(tab_main):
        with ui.row():
            # Left column: Button for processing data
            with ui.column():
                ui.label('Options for data processing can be added here.')
                ui.button('Process Data', on_click=lambda: print("Processing data..."))                
            
            # Center column: Two stacked checkboxes
            with ui.column():
                ui.label('Column options and configuration go here.')
                ui.checkbox('Identify Columns', on_change=lambda checked: print(f"Identify Columns: {checked}"))
                ui.checkbox('Normalize Data', on_change=lambda checked: print(f"Normalize Data: {checked}"))
                

            # Right column: Text box for displaying text statistics
            with ui.column():
                ui.textarea('Statistics', value="Statistics will be displayed here.")
        
        # Second row
        with ui.row():
            ui.label('Further configurations can go in this row.')

    # Secondary tab    
    with ui.tab_panel(tab_parameters):
        models_widgets = ModelsConfigurationWidgets()
        ui.label('Model parameters will be set here.')
        models_widgets.model_configurations(CONFIG)

        

ui.run()