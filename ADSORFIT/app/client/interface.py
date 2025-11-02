from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from functools import partial
from typing import Any

from nicegui import ui
from nicegui.elements.checkbox import Checkbox
from nicegui.elements.expansion import Expansion
from nicegui.elements.number import Number
from nicegui.elements.switch import Switch
from nicegui.elements.textarea import Textarea
from nicegui.events import EventArguments, UploadEventArguments
from nicegui.events import ValueChangeEventArguments

from ADSORFIT.app.client.layouts import (
    CARD_BASE_CLASSES,
    INTERFACE_THEME_CSS,
    PAGE_CONTAINER_CLASSES,
)
from ADSORFIT.app.client.controllers import (
    ApiConfig,
    DatasetPayload,
    ParameterKey,
    get_client_config,
    get_parameter_defaults,
    load_dataset,
    start_fitting,
)


###############################################################################
@dataclass
class ClientComponents:
    max_iterations: Number | None = None
    save_best: Checkbox | None = None
    dataset_stats: Textarea | None = None
    fitting_status: Textarea | None = None
    start_button: Any | None = None
    model_toggles: dict[str, Switch] = field(default_factory=dict)
    model_expansions: dict[str, Expansion] = field(default_factory=dict)


###############################################################################
@dataclass
class InterfaceState:
    config: ApiConfig
    dataset: DatasetPayload | None = None
    parameter_inputs: list[tuple[ParameterKey, Number]] = field(default_factory=list)

    # -------------------------------------------------------------------------
    def reset_parameters(self) -> None:
        self.parameter_inputs.clear()

    # -------------------------------------------------------------------------
    def collect_parameter_payload(self) -> tuple[list[ParameterKey], list[Any]]:
        metadata: list[ParameterKey] = []
        values: list[Any] = []
        for entry_metadata, element in self.parameter_inputs:
            metadata.append(entry_metadata)
            values.append(element.value)
        return metadata, values


# -----------------------------------------------------------------------------
def handle_model_toggle(
    components: ClientComponents, model_name: str, event: ValueChangeEventArguments
) -> None:
    toggle_active = bool(event.value)
    expansion = components.model_expansions.get(model_name)
    if expansion is None:
        return
    if not toggle_active:
        expansion.value = False
        expansion.disable()
    else:
        expansion.enable()


# -----------------------------------------------------------------------------
async def handle_dataset_upload(
    state: InterfaceState, components: ClientComponents, event: UploadEventArguments
) -> None:
    if components.dataset_stats is not None:
        components.dataset_stats.value = "[INFO] Uploading dataset..."
    result = await asyncio.to_thread(load_dataset, event, config=state.config)
    state.dataset = result.dataset
    if components.dataset_stats is not None:
        components.dataset_stats.value = result.message


# -----------------------------------------------------------------------------
async def handle_start_fitting(
    state: InterfaceState, components: ClientComponents, event: EventArguments
) -> None:
    del event
    if components.fitting_status is not None:
        components.fitting_status.value = "[INFO] Starting fitting process..."

    max_iterations = 1.0
    if components.max_iterations is not None and components.max_iterations.value is not None:
        try:
            max_iterations = float(components.max_iterations.value)
        except (TypeError, ValueError):
            max_iterations = 1.0

    save_best = bool(components.save_best.value) if components.save_best is not None else False

    metadata, values = state.collect_parameter_payload()

    selected_models = [
        name for name, toggle in components.model_toggles.items() if toggle.value
    ]
    if not selected_models:
        if components.fitting_status is not None:
            components.fitting_status.value = (
                "[ERROR] Please select at least one model before starting the fitting process."
            )
        return

    message = await asyncio.to_thread(
        start_fitting,
        metadata,
        max_iterations,
        save_best,
        state.dataset,
        selected_models,
        *values,
        config=state.config,
    )

    if components.fitting_status is not None:
        components.fitting_status.value = message


# -----------------------------------------------------------------------------
def build_model_cards(
    state: InterfaceState,
    components: ClientComponents,
    parameter_defaults: dict[str, dict[str, tuple[float, float]]],
) -> None:
    state.reset_parameters()
    components.model_toggles.clear()
    components.model_expansions.clear()

    for model_name, parameters in parameter_defaults.items():
        with ui.card().classes(f"{CARD_BASE_CLASSES} flex-1 min-w-[320px]"):
            with ui.column().classes("gap-3"):
                with ui.row().classes("w-full items-center justify-between gap-3"):
                    ui.markdown(f"**{model_name}**")
                    toggle = ui.switch(
                        value=True,
                        on_change=partial(handle_model_toggle, components, model_name),
                    ).props("color=primary")
                    components.model_toggles[model_name] = toggle
                expansion = ui.expansion("Configure parameters", value=False).classes(
                    "w-full"
                )
                components.model_expansions[model_name] = expansion
                with expansion:
                    with ui.column().classes("gap-3 w-full"):
                        for parameter_name, (min_default, max_default) in parameters.items():
                            with ui.row().classes("w-full gap-3 flex-wrap"):
                                min_input = ui.number(
                                    f"{parameter_name} min",
                                    value=float(min_default),
                                    min=0.0,
                                    precision=4,
                                    step=0.0001,
                                ).classes("flex-1 min-w-[140px]")
                                max_input = ui.number(
                                    f"{parameter_name} max",
                                    value=float(max_default),
                                    min=0.0,
                                    precision=4,
                                    step=0.0001,
                                ).classes("flex-1 min-w-[140px]")
                            state.parameter_inputs.append(
                                ((model_name, parameter_name, "min"), min_input)
                            )
                            state.parameter_inputs.append(
                                ((model_name, parameter_name, "max"), max_input)
                            )


# -----------------------------------------------------------------------------
def main_page() -> None:
    state = InterfaceState(config=get_client_config())
    components = ClientComponents()
    parameter_defaults = get_parameter_defaults()

    ui.page_title("ADSORFIT Model Fitting")
    ui.add_head_html(f"<style>{INTERFACE_THEME_CSS}</style>")

    with ui.column().classes(PAGE_CONTAINER_CLASSES):
        ui.markdown("## ADSORFIT Model Fitting").classes(
            "adsorfit-heading text-3xl font-semibold"
        )
        with ui.row().classes("w-full gap-6 items-start flex-wrap md:flex-nowrap"):
            with ui.card().classes(f"{CARD_BASE_CLASSES} flex-1 min-w-[320px]"):
                with ui.column().classes("gap-4"):
                    components.max_iterations = ui.number(
                        "Max iteration",
                        value=1000,
                        min=1,
                        max=1_000_000,
                        precision=0,
                        step=1,
                    ).classes("w-full")
                    components.save_best = ui.checkbox(
                        "Save best fitting data", value=True
                    )
                    ui.upload(
                        label="Load dataset",
                        on_upload=partial(handle_dataset_upload, state, components),
                        auto_upload=True,
                    ).props("accept=.csv,.xlsx").classes("w-full")
                    components.dataset_stats = (
                        ui.textarea(
                            "Dataset statistics",
                            value="No dataset loaded.",
                        )
                        .props("readonly rows=8")
                        .classes("w-full adsorfit-status")
                    )
                    components.start_button = ui.button(
                        "Start fitting",
                        on_click=partial(handle_start_fitting, state, components),
                    ).props("color=primary")
                    components.fitting_status = (
                        ui.textarea(
                            "Fitting status",
                            value="",
                        )
                        .props("readonly rows=8")
                        .classes("w-full adsorfit-status")
                    )

            with ui.column().classes("flex-1 min-w-[320px] gap-4"):
                build_model_cards(state, components, parameter_defaults)


# -----------------------------------------------------------------------------
def render_page() -> None:
    main_page()


# -----------------------------------------------------------------------------
def create_interface() -> None:
    ui.page("/")(render_page)
    ui.page("/ui")(render_page)
