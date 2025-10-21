from __future__ import annotations

import asyncio
from typing import Any

from nicegui import ui
from nicegui.elements.checkbox import Checkbox
from nicegui.elements.number import Number
from nicegui.elements.textarea import Textarea
from nicegui.events import EventArguments, UploadEventArguments

from ADSORFIT.app.client.controllers import (
    DatasetPayload,
    ParameterKey,
    client_controller,
)


###############################################################################
class InterfaceSession:
    def __init__(self) -> None:
        self.controller = client_controller
        self.parameter_defaults = self.controller.get_parameter_defaults()
        self.dataset: DatasetPayload | None = None
        self.parameter_metadata: list[ParameterKey] = []
        self.parameter_inputs: list[Number] = []
        self.max_iterations_input: Number | None = None
        self.save_best_checkbox: Checkbox | None = None
        self.model_checkboxes: dict[str, Checkbox] = {}
        self.dataset_stats_area: Textarea | None = None
        self.fitting_status_area: Textarea | None = None

    ###########################################################################
    def build(self) -> None:
        self.parameter_metadata = []
        self.parameter_inputs = []
        self.model_checkboxes = {}

        container = ui.column().classes("w-full max-w-6xl mx-auto gap-6 p-4")
        with container:
            ui.label("ADSORFIT Model Fitting").classes("text-2xl font-semibold")

            with ui.row().classes("w-full items-start gap-6 flex-wrap"):
                with ui.column().classes("flex-1 min-w-[320px] gap-4"):
                    self.max_iterations_input = ui.number(
                        "Max iteration",
                        value=1000,
                        min=1,
                        max=1_000_000,
                        precision=0,
                        step=1,
                    ).classes("w-full")
                    self.save_best_checkbox = ui.checkbox(
                        "Save best fitting data",
                        value=True,
                    )
                    ui.upload(
                        label="Load dataset",
                        on_upload=self.handle_dataset_upload,
                        auto_upload=True,
                    ).props("accept=.csv,.xlsx").classes("w-full")
                    self.dataset_stats_area = ui.textarea(
                        "Dataset statistics",
                        value="No dataset loaded.",
                    ).props("readonly rows=8").classes("w-full")
                    ui.button(
                        "Start fitting",
                        on_click=self.handle_start_fitting,
                    ).props("color=primary")
                    self.fitting_status_area = ui.textarea(
                        "Fitting status",
                        value="",
                    ).props("readonly rows=8").classes("w-full")

                with ui.column().classes("flex-1 min-w-[320px] gap-4"):
                    for model_name, parameters in self.parameter_defaults.items():
                        with ui.expansion(model_name, value=False).classes("w-full"):
                            with ui.column().classes("w-full gap-3"):
                                checkbox = ui.checkbox(
                                    "Enable model", value=True
                                ).props("dense")
                                self.model_checkboxes[model_name] = checkbox
                                for parameter_name, (min_default, max_default) in parameters.items():
                                    with ui.row().classes("w-full gap-3"):
                                        min_input = ui.number(
                                            f"{parameter_name} min",
                                            value=float(min_default),
                                            min=0.0,
                                            precision=4,
                                            step=0.0001,
                                        ).classes("w-full")
                                        max_input = ui.number(
                                            f"{parameter_name} max",
                                            value=float(max_default),
                                            min=0.0,
                                            precision=4,
                                            step=0.0001,
                                        ).classes("w-full")
                                    self.parameter_metadata.append((model_name, parameter_name, "min"))
                                    self.parameter_inputs.append(min_input)
                                    self.parameter_metadata.append((model_name, parameter_name, "max"))
                                    self.parameter_inputs.append(max_input)

    ###########################################################################
    async def handle_dataset_upload(self, event: UploadEventArguments) -> None:
        if self.dataset_stats_area is not None:
            self.dataset_stats_area.value = "[INFO] Uploading dataset..."
        dataset, message = await asyncio.to_thread(self.controller.load_dataset, event)
        self.dataset = dataset
        if self.dataset_stats_area is not None:
            self.dataset_stats_area.value = message

    ###########################################################################
    async def handle_start_fitting(self, event: EventArguments) -> None:
        del event
        if self.fitting_status_area is not None:
            self.fitting_status_area.value = "[INFO] Starting fitting process..."

        max_iterations = 1.0
        if self.max_iterations_input is not None and self.max_iterations_input.value is not None:
            max_iterations = float(self.max_iterations_input.value)

        save_best = False
        if self.save_best_checkbox is not None:
            save_best = bool(self.save_best_checkbox.value)

        values: list[Any] = []
        for element in self.parameter_inputs:
            values.append(element.value)

        selected_models = [
            name
            for name, checkbox in self.model_checkboxes.items()
            if checkbox.value
        ]
        if not selected_models:
            if self.fitting_status_area is not None:
                self.fitting_status_area.value = (
                    "[ERROR] Please select at least one model before starting the fitting process."
                )
            return

        message = await asyncio.to_thread(
            self.controller.start_fitting,
            list(self.parameter_metadata),
            max_iterations,
            save_best,
            self.dataset,
            selected_models,
            *values,
        )

        if self.fitting_status_area is not None:
            self.fitting_status_area.value = message


###########################################################################
def render_page() -> None:
    session = InterfaceSession()
    session.build()


###########################################################################
def create_interface() -> None:
    ui.page("/")(render_page)
    ui.page("/ui")(render_page)
