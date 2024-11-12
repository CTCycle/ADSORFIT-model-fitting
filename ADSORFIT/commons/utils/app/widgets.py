import os
from nicegui import ui
from functools import partial

from ADSORFIT.commons.constants import RESULTS_PATH, DATASET_PATH, BEST_FIT_PATH
from ADSORFIT.commons.logger import logger


###############################################################################
class ModelsConfigurationWidgets:

    def __init__(self):        
        self.model_states = {}

    #--------------------------------------------------------------------------
    def model_configurations(self, configurations):
        
        for model_name, params in configurations['MODELS'].items():
            # Create a list to store parameter fields
            param_fields = []

            with ui.grid().style('grid-template-columns: 1fr 2fr 3fr'):
                # Leftmost column: Toggle for selecting the model
                with ui.column():
                    model_state = ui.switch(text=f"Select {model_name}", value=False)

                    # Register the state and fields for future use if needed
                    self.model_states[model_name] = (model_state, param_fields)

                    # No need to attach the event handler since we won't enable/disable fields

                # Right column: Parameters organized into three sub-columns
                with ui.column():
                    with ui.grid().style('grid-template-columns: repeat(3, 1fr)'):
                        # Min values column
                        with ui.column():
                            ui.label("Min")
                            for param, value in params["min"].items():
                                field = ui.number(f"{param}", value=value)
                                param_fields.append(field)

                        # Max values column
                        with ui.column():
                            ui.label("Max")
                            for param, value in params["max"].items():
                                field = ui.number(f"{param}", value=value)
                                param_fields.append(field)

                        # Initial values column
                        with ui.column():
                            ui.label("Initial")
                            for param, value in params["initial"].items():
                                field = ui.number(f"{param}", value=value)
                                param_fields.append(field)

    #--------------------------------------------------------------------------
    # The update_selection method is no longer needed and has been removed


    #--------------------------------------------------------------------------
    def update_selection(self, model_name, event):
        model_state, param_fields = self.model_states[model_name]

        # Determine the enabled/disabled state based on the switch value
        disabled = not model_state.value
        for field in param_fields:
            if disabled:
                field.props('disable')
            else:
                field.props(remove='disable')
            field.update()