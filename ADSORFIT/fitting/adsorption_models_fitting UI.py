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
processed_dataset = None
processor = AdsorptionDataProcessing()



###############################################################################
with ui.tabs() as tabs:
    # Define two tabs
    tab_main = ui.tab('ADSORFIT Solver')
    tab_parameters = ui.tab('Model configurations')

# Set the 'value' parameter to 'tab_main' to make it the default active tab
with ui.tab_panels(tabs, value=tab_main) as panels:

    with ui.tab_panel(tab_main).style('width: 100%; padding: 10px;'):             


        with ui.row().style('width: 100%; justify-content: space-between;'):
            # Left column: Button for processing data
            with ui.column().style('width: 30%; padding: 10px;'):
                ui.label('This will process the adsorption_dataset.csv file.')
                ui.button('Process Data', on_click=processor.preprocess_dataset())

            # Center column: Two stacked checkboxes
            with ui.column().style('width: 30%; padding: 10px;'):
                ui.checkbox('Identify Columns', on_change=lambda checked: print(f"Identify Columns: {checked}")).bind_value()
                ui.checkbox('Normalize Data', on_change=lambda checked: print(f"Normalize Data: {checked}"))

            # Right column: Text area for displaying text statistics
            with ui.column().style('width: 30%; padding: 10px;'):
                ui.textarea('Statistics', value="Statistics will be displayed here.")

        ui.separator()

        # Second row
        with ui.row().style('width: 100%; justify-content: space-between;'):            
            with ui.column().style('width: 30%; padding: 10px;'):
                ui.button('Data fitting', on_click=lambda: print("Processing data..."))

    # Secondary tab
    with ui.tab_panel(tab_parameters):
        models_widgets = ModelsConfigurationWidgets()
        ui.label('Model parameters will be set here.')
        models_widgets.model_configurations(CONFIG)

ui.run()