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
            # Create a list to store parameter fields for enabling/disabling
            param_fields = []

            with ui.grid().style('grid-template-columns: 1fr 2fr 3fr'):
                # Leftmost column: Toggle for selecting the model
                with ui.column():
                    model_state = ui.switch(text=f"Select {model_name}", value=False)

                    # Register the state and fields to enable updates later
                    self.model_states[model_name] = (model_state, param_fields)

                    # Attach the event handler, binding model_name
                    model_state.on(partial(self.update_selection, model_name=model_name))

                # Right column: Parameters organized into three sub-columns
                with ui.column():
                    with ui.grid().style('grid-template-columns: repeat(3, 1fr)'):
                        # Min values column
                        with ui.column():
                            ui.label("Min")
                            for param, value in params["min"].items():
                                field = ui.number(label=f"{param} (Min)", value=value, disabled=True)
                                param_fields.append(field)

                        # Max values column
                        with ui.column():
                            ui.label("Max")
                            for param, value in params["max"].items():
                                field = ui.number(label=f"{param} (Max)", value=value, disabled=True)
                                param_fields.append(field)

                        # Initial values column
                        with ui.column():
                            ui.label("Initial")
                            for param, value in params["initial"].items():
                                field = ui.number(label=f"{param} (Initial)", value=value, disabled=True)
                                param_fields.append(field)

    #--------------------------------------------------------------------------
    def update_selection(self, model_name, e):
        model_state, param_fields = self.model_states[model_name]
        disabled = not e.value
        for field in param_fields:
            field.disabled = disabled
            field.update()