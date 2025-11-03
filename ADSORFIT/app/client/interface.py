from __future__ import annotations

import asyncio
from collections.abc import Callable
from functools import partial
from typing import Any
from nicegui import ui
from nicegui.elements.checkbox import Checkbox
from nicegui.elements.expansion import Expansion
from nicegui.elements.number import Number
from nicegui.elements.switch import Switch
from nicegui.elements.textarea import Textarea
from nicegui.events import UploadEventArguments, ValueChangeEventArguments

from ADSORFIT.app.client.layouts import (
    CARD_BASE_CLASSES,
    INTERFACE_THEME_CSS,
    PAGE_CONTAINER_CLASSES,
)
from ADSORFIT.app.client.controllers import (
    DatasetPayload,
    ParameterKey,
    get_parameter_defaults,
    load_dataset,
    start_fitting,
)


def read_widget_value(widget: Any) -> Any:
    return widget.value


def collect_parameter_payload(
    collectors: list[tuple[ParameterKey, Callable[[], Any]]],
) -> tuple[list[ParameterKey], list[Any]]:
    metadata: list[ParameterKey] = []
    values: list[Any] = []
    for entry_metadata, reader in collectors:
        metadata.append(entry_metadata)
        values.append(reader())
    return metadata, values


def extract_upload_payload(
    event: UploadEventArguments | None,
) -> tuple[bytes | None, str | None]:
    if event is None:
        return None, None
    content = getattr(event, "content", None)
    data: Any = None
    if content is not None:
        if hasattr(content, "seek"):
            try:
                content.seek(0)
            except (OSError, ValueError):
                pass
        if hasattr(content, "read"):
            data = content.read()
        else:
            data = content
    if data is None and hasattr(event, "args"):
        if isinstance(event.args, dict):
            data = event.args.get("content")
    if isinstance(data, bytearray):
        data = bytes(data)
    if data is not None and not isinstance(data, bytes):
        data = None
    name = event.name if isinstance(event.name, str) else None
    return data, name


def handle_model_toggle(expansion: Expansion, event: ValueChangeEventArguments) -> None:
    toggle_active = bool(event.value)
    if not toggle_active:
        expansion.value = False
        expansion.disable()
    else:
        expansion.enable()


async def handle_dataset_upload(
    dataset_state: dict[str, DatasetPayload | None],
    dataset_stats: Textarea,
    event: UploadEventArguments,
) -> None:
    dataset_stats.value = "[INFO] Uploading dataset..."
    file_bytes, filename = extract_upload_payload(event)
    result = await asyncio.to_thread(load_dataset, file_bytes, filename)
    dataset_state["dataset"] = result.get("dataset")
    dataset_stats.value = result.get("message", "")


async def handle_start_fitting(
    dataset_state: dict[str, DatasetPayload | None],
    parameter_collectors: list[tuple[ParameterKey, Callable[[], Any]]],
    model_toggles: dict[str, Switch],
    max_iterations_input: Number,
    save_best_checkbox: Checkbox,
    status_area: Textarea,
) -> None:
    status_area.value = "[INFO] Starting fitting process..."

    metadata, values = collect_parameter_payload(parameter_collectors)

    max_iterations_value = max_iterations_input.value
    if max_iterations_value is None:
        max_iterations = 1.0
    else:
        try:
            max_iterations = float(max_iterations_value)
        except (TypeError, ValueError):
            max_iterations = 1.0

    save_best = bool(save_best_checkbox.value)
    selected_models = [
        name for name, toggle in model_toggles.items() if bool(toggle.value)
    ]

    result = await asyncio.to_thread(
        start_fitting,
        metadata,
        max_iterations,
        save_best,
        dataset_state.get("dataset"),
        selected_models,
        *values,
    )

    status_area.value = result.get("message", "")


def build_model_cards(
    parameter_defaults: dict[str, dict[str, tuple[float, float]]],
    parameter_collectors: list[tuple[ParameterKey, Callable[[], Any]]],
    model_toggles: dict[str, Switch],
) -> None:
    parameter_collectors.clear()
    model_toggles.clear()

    for model_name, parameters in parameter_defaults.items():
        with ui.card().classes(f"{CARD_BASE_CLASSES} flex-1 min-w-[320px]"):
            with ui.column().classes("gap-3"):
                with ui.row().classes("w-full items-center justify-between gap-3"):
                    ui.markdown(f"**{model_name}**")
                    expansion = ui.expansion("Configure parameters", value=False).classes(
                        "w-full"
                    )
                    toggle = ui.switch(
                        value=True,
                        on_change=partial(handle_model_toggle, expansion),
                    ).props("color=primary")
                    model_toggles[model_name] = toggle
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
                            parameter_collectors.append(
                                (
                                    (model_name, parameter_name, "min"),
                                    partial(read_widget_value, min_input),
                                )
                            )
                            parameter_collectors.append(
                                (
                                    (model_name, parameter_name, "max"),
                                    partial(read_widget_value, max_input),
                                )
                            )


def main_page() -> None:
    dataset_state: dict[str, DatasetPayload | None] = {"dataset": None}
    parameter_collectors: list[tuple[ParameterKey, Callable[[], Any]]] = []
    model_toggles: dict[str, Switch] = {}
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
                    max_iterations_input = ui.number(
                        "Max iteration",
                        value=1000,
                        min=1,
                        max=1_000_000,
                        precision=0,
                        step=1,
                    ).classes("w-full")
                    save_best_checkbox = ui.checkbox(
                        "Save best fitting data",
                        value=True,
                    )
                    dataset_stats = (
                        ui.textarea(
                            "Dataset statistics",
                            value="No dataset loaded.",
                        )
                        .props("readonly rows=8")
                        .classes("w-full adsorfit-status")
                    )
                    status_area = (
                        ui.textarea(
                            "Fitting status",
                            value="",
                        )
                        .props("readonly rows=8")
                        .classes("w-full adsorfit-status")
                    )
                    ui.upload(
                        label="Load dataset",
                        on_upload=partial(handle_dataset_upload, dataset_state, dataset_stats),
                        auto_upload=True,
                    ).props("accept=.csv,.xlsx").classes("w-full")
                    ui.button(
                        "Start fitting",
                        on_click=partial(
                            handle_start_fitting,
                            dataset_state,
                            parameter_collectors,
                            model_toggles,
                            max_iterations_input,
                            save_best_checkbox,
                            status_area,
                        ),
                    ).props("color=primary")

            with ui.column().classes("flex-1 min-w-[320px] gap-4"):
                build_model_cards(parameter_defaults, parameter_collectors, model_toggles)


def render_page() -> None:
    main_page()


def create_interface() -> None:
    ui.page("/")(render_page)
    ui.page("/ui")(render_page)
