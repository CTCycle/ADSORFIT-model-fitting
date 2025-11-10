from __future__ import annotations
from collections.abc import Callable
from functools import partial
from typing import Any
from nicegui import ui
from nicegui.elements.checkbox import Checkbox
from nicegui.elements.expansion import Expansion
from nicegui.elements.markdown import Markdown
from nicegui.elements.number import Number
from nicegui.elements.switch import Switch
from nicegui.elements.textarea import Textarea

from ADSORFIT.app.constants import API_BASE_URL
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

###############################################################################
# HELPERS
###############################################################################
def collect_parameter_payload(
    collectors: list[tuple[ParameterKey, Callable[[], Any]]],
) -> tuple[list[ParameterKey], list[Any]]:
    metadata: list[ParameterKey] = []
    values: list[Any] = []
    for entry_metadata, reader in collectors:
        metadata.append(entry_metadata)
        values.append(reader())
    return metadata, values

# -----------------------------------------------------------------------------
def build_stats_markdown(summary: str) -> str:
    lines = [line.strip() for line in summary.splitlines() if line.strip()]
    if not lines:
        return "### Dataset statistics\n\n_No dataset information available._"

    formatted: list[str] = ["### Dataset statistics"]
    for line in lines:
        lowered = line.lower()
        if lowered.startswith("column details"):
            formatted.append("")
            formatted.append("**Column details**")
            continue
        if line.startswith("- "):
            formatted.append(line)
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            formatted.append(f"- **{key.strip()}**: {value.strip()}")
            continue
        formatted.append(line)

    return "\n".join(formatted)

# -----------------------------------------------------------------------------
def extract_upload_payload(event: Any | None) -> tuple[bytes | None, str | None]:
    if not event:
        return None, None
    
    file = getattr(event, "file", None)
    if file is not None:
        content = getattr(file, "_data", None) or getattr(file, "content", None)
        if isinstance(content, bytearray):
            content = bytes(content)
        if isinstance(content, bytes):
            return content, file.name or None

    # Fallback for dict-like args (legacy style)
    args = getattr(event, "args", {}) or {}
    content = args.get("content")
    name = args.get("name") or args.get("filename")

    if isinstance(content, bytearray):
        content = bytes(content)
    if isinstance(content, bytes):
        return content, name

    # Fallback: nested {"file": {"content": ..., "name": ...}}
    file_entry = args.get("file")
    if isinstance(file_entry, dict):
        content = file_entry.get("content")
        name = file_entry.get("name") or file_entry.get("filename") or name
        if isinstance(content, bytearray):
            content = bytes(content)
        if isinstance(content, bytes):
            return content, name

    return None, name

# -----------------------------------------------------------------------------
def handle_model_toggle(expansion: Expansion, event: Any) -> None:
    toggle_active = bool(event.value)
    if not toggle_active:
        expansion.value = False
        expansion.disable()
    else:
        expansion.enable()

# -----------------------------------------------------------------------------
async def handle_dataset_upload(
    dataset_state, dataset_stats: Markdown, event: Any
) -> None:
    dataset_stats.set_content(build_stats_markdown("[INFO] Uploading dataset."))
    file_bytes, filename = extract_upload_payload(event)
    if not file_bytes:
        dataset_stats.set_content(
            build_stats_markdown("[ERROR] Could not read uploaded file.")
        )
        return
    url = f"{API_BASE_URL}/datasets/load"
    result = await load_dataset(url, file_bytes, filename)
    dataset_state["dataset"] = result.get("dataset")
    dataset_stats.set_content(build_stats_markdown(result.get("message", "")))

# -----------------------------------------------------------------------------
async def on_start_fitting_click(
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

    save_best = save_best_checkbox.value
    selected_models = [
        name for name, toggle in model_toggles.items() if bool(toggle.value)
    ]
    
    url = f"{API_BASE_URL}/fitting/run"
    result = await start_fitting(
        url,
        metadata,
        max_iterations,
        save_best,
        dataset_state.get("dataset"),
        selected_models,
        *values,
    )

    status_area.value = result.get("message", "")


###############################################################################
# MAIN UI PAGE
###############################################################################
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
                # Header row: model name and toggle side-by-side
                with ui.row().classes("w-full items-center justify-between gap-3"):
                    with ui.row().classes("items-center gap-2"):
                        ui.markdown(f"**{model_name}**")
                        toggle = ui.switch(value=True).props("color=primary")
                        model_toggles[model_name] = toggle
                
                expansion = ui.expansion("Configure parameters", value=False).classes("w-full")                
                toggle.on_value_change(partial(handle_model_toggle, expansion))

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
                                    lambda mi=min_input: mi.value,
                                )
                            )
                            parameter_collectors.append(
                                (
                                    (model_name, parameter_name, "max"),
                                    lambda ma=max_input: ma.value,
                                )
                            )

# -----------------------------------------------------------------------------
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

                    dataset_stats = ui.markdown(
                        build_stats_markdown("No dataset loaded.")
                    ).classes("w-full adsorfit-status min-h-[260px]")

                    status_area = (
                        ui.textarea(
                            "Fitting status",
                            value="",
                        )
                        .props("readonly rows=10 autogrow")
                        .classes("w-full adsorfit-status min-h-[260px]")
                    )

                    dataset_upload = (
                        ui.upload(
                            label="Load dataset",
                            auto_upload=True,
                        )
                        .props("accept=.csv,.xlsx,.xls")
                        .classes("w-full")
                    )

                    fit_button = ui.button(
                        "Start fitting",
                    ).props("color=primary")

            with ui.column().classes("flex-1 min-w-[320px] gap-4"):
                build_model_cards(parameter_defaults, parameter_collectors, model_toggles)

    dataset_upload.on_upload(
        partial(
            handle_dataset_upload, 
            dataset_state, 
            dataset_stats
        )
    )

    fit_button.on_click(
        partial(
            on_start_fitting_click,
            dataset_state,
            parameter_collectors,
            model_toggles,
            max_iterations_input,
            save_best_checkbox,
            status_area,
        )
    )


###############################################################################
# MOUNT AND LAUNCH
###############################################################################
def create_interface() -> None:
    ui.page("/")(main_page)

# -----------------------------------------------------------------------------
def launch_interface() -> None:
    create_interface()
    ui.run(
        host="0.0.0.0",
        port=7861,
        title="ADSORFIT Model Fitting Geographics",
        show_welcome_message=False,
    )

# -----------------------------------------------------------------------------
if __name__ in {"__main__", "__mp_main__"}:
    launch_interface()
