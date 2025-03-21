from nicegui import ui
import copy

from ADSORFIT.commons.utils.app.threads import SolverThread
from ADSORFIT.commons.logger import logger


# Progress bar widget for tracking the progress of operations in the GUI
###############################################################################
class ProgressBarWidgets:

    def __init__(self):
        # Set feedback property to enable instant UI updates
        self.feedback = 'instant-feedback'

    #--------------------------------------------------------------------------
    def build_progress_bar(self):
        # Create a linear progress bar widget with an initial value of 0
        # and the selected type of feedback, set it as non visible
        progress_bar = ui.linear_progress(value=0).props(self.feedback)
        progress_bar.visible = False 

        return progress_bar

    #--------------------------------------------------------------------------
    def update_progress_bar(self, progress_bar, solver : SolverThread):
            # Check if the solver instance has started and is running
            if solver.total > 0:
                progress_bar.visible = True
                progress_bar.value = solver.progress/solver.total
                # If progress reaches or exceeds total, hide the progress bar and notify
                # the user with a prompt
                if solver.progress >= solver.total:
                    progress_bar.visible = False
                    ui.notify('Data fitting is completed')
                    # reset progress bar values to 0 after completion
                    solver.progress = 0
                    solver.total = 0
            else:
                progress_bar.visible = False
                

###############################################################################
class ModelsConfigurationWidgets:

    def __init__(self):        
        self.model_states = {"LANGMUIR": {"initial": {"K": 0.000001, "qsat": 1.0},
                                          "min": {"K": 0.0, "qsat": 0.0},
                                          "max": {"K": 100.0, "qsat": 100.0}},
                             "SIPS": {"initial": {"K": 0.000001, "qsat": 1.0, "N": 1.0},
                                      "min": {"K": 0.0, "qsat": 0.0, "N": 0.0},
                                      "max": {"K": 100.0, "qsat": 100.0, "N": 50.0}},                                    
                             "FREUNDLICH": {"initial": {"K": 0.000001, "qsat": 1.0},
                                            "min": {"K": 0.0, "qsat": 0.0},
                                            "max": {"K": 100.0, "qsat": 100.0}},
                             "TEMKIN": {"initial": {"K": 0.000001, "B": 1.0},
                                        "min": {"K": 0.0, "B": 0.0},
                                        "max": {"K": 100.0, "B": 100.0}}}  
        
        self.default_values = copy.deepcopy(self.model_states)
              
    #--------------------------------------------------------------------------
    def model_configurations(self):
        for model_name, params in self.model_states.items():
            ui.separator()
            with ui.grid().style('grid-template-columns: 1fr 2fr 3fr'):
                with ui.column().classes('w-full p-4').style('display: flex; justify-content: center;'):
                    model_state = ui.switch(
                        text=f"{model_name}", value=True, on_change=lambda e, 
                        m_name=model_name: self.on_model_selection(m_name, e.value))
                with ui.column().classes('w-full p-4').bind_visibility_from(model_state, 'value'):
                    with ui.grid().style('grid-template-columns: repeat(3, 1fr)'):
                        # Set column with min parameters values
                        with ui.column():
                            ui.label("Min")
                            for param, value in params["min"].items():
                                ui.number(
                                    f"{param}", value=value, on_change=lambda e, 
                                    m_name=model_name, cat='min', 
                                    p=param: self.update_model_state(m_name, cat, p, e.value))
                        # Set column with max parameters values
                        with ui.column():
                            ui.label("Max")
                            for param, value in params["max"].items():
                                ui.number(
                                    f"{param}", value=value, on_change=lambda e, 
                                    m_name=model_name, cat='max', 
                                    p=param: self.update_model_state(m_name, cat, p, e.value))

                        # Initial values column
                        with ui.column():
                            ui.label("Initial")
                            for param, value in params["initial"].items():
                                ui.number(
                                    f"{param}", value=value, on_change=lambda e, 
                                    m_name=model_name, cat='initial',
                                    p=param: self.update_model_state(m_name, cat, p, e.value))

    #--------------------------------------------------------------------------
    def update_model_state(self, model_name, category, param, value):
        self.model_states[model_name][category][param] = value

    #--------------------------------------------------------------------------
    def on_model_selection(self, model_name, value):
        if value:            
            if model_name not in self.model_states:
                self.model_states[model_name] = self.default_model_values(model_name)
        else:            
            if model_name in self.model_states:
                del self.model_states[model_name]       

    #--------------------------------------------------------------------------
    def default_model_values(self, model_name):        
        return self.default_values.get(model_name, {})




