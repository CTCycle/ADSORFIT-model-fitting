from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from typing import Any
from collections.abc import Callable

from AEGIS.app.constants import OPENAI_CLOUD_MODELS
from nicegui import ui

from AEGIS.app.client.layouts import (
    CARD_BASE_CLASSES,
    INTERFACE_THEME_CSS,
    PAGE_CONTAINER_CLASSES,
)
from AEGIS.app.client.controllers import (
    ComponentUpdate,
    MISSING,
    set_coordinates_as_input,
    submit_location_search,
    get_runtime_settings,
    sync_cloud_model_options,
)
from AEGIS.app.constants import AGENT_MODEL_CHOICES, FILTER_CHOICES, CLOUD_MODEL_CHOICES

CLOUD_PROVIDERS: list[str] = [k for k in CLOUD_MODEL_CHOICES.keys()]


# [COMPONENTS DATACLASS]
###############################################################################
@dataclass
class ClientComponents:
    auth_button: Any
    country: Any
    city: Any
    address: Any
    use_coordinates: Any
    latitude: Any
    longitude: Any
    date: Any
    filter: Any
    search: Any
    agentic_toggle: Any
    llm_query: Any
    use_cloud: Any
    cloud_model: Any
    agent_model: Any
    temperature: Any
    agentic_search: Any
    status: Any
    map_display: Any


# HELPERS
###############################################################################



# UPDATES
###############################################################################
def apply_component_update(component: Any, update: ComponentUpdate) -> None:
    if update.value is not MISSING and hasattr(component, "value"):
        value_to_set = update.value
        if value_to_set == "" and hasattr(component, "set_options"):
            value_to_set = None
        component.value = value_to_set
        if hasattr(component, "update"):
            component.update()
    if update.options is not None and hasattr(component, "set_options"):
        component.set_options(update.options)
        if hasattr(component, "update"):
            component.update()
    if update.enabled is not None:
        if update.enabled and hasattr(component, "enable"):
            component.enable()
        elif not update.enabled and hasattr(component, "disable"):
            component.disable()
    if update.visible is not None and hasattr(component, "visible"):
        component.visible = update.visible

# -----------------------------------------------------------------------------
def update_status(components: ClientComponents, data: dict[str, Any] | None, message: str) -> None:
    """Format and display status output strictly in the status component."""
    if not data:
        content = message or ""
    else:
        payload = data.get("payload") if isinstance(data, dict) else None
        if isinstance(payload, dict):
            serialized = json.dumps(payload, indent=2, sort_keys=True)
            content = f"{message}\n\n```json\n{serialized}\n```"
        else:
            content = message or ""

    components.status.set_content(content)
    components.status.update()

# -----------------------------------------------------------------------------
def get_datetime_default_value() -> str:
    current = datetime.now().replace(second=0, microsecond=0)
    return current.isoformat(timespec="minutes")

# -----------------------------------------------------------------------------
async def handle_use_coordinates_change(
    components: ClientComponents, event: Any
) -> None:
    use_coordinates = bool(event.value)
    updates = set_coordinates_as_input(use_coordinates)
    apply_component_update(components.country, updates["country"])
    apply_component_update(components.city, updates["city"])
    apply_component_update(components.address, updates["address"])
    apply_component_update(components.latitude, updates["latitude"])
    apply_component_update(components.longitude, updates["longitude"])


# ACTIONS
###############################################################################
async def handle_search_click(components: ClientComponents, event: Any) -> None:
    data, message = await submit_location_search(
        components.filter.value,
        components.country.value,
        components.city.value,
        components.address.value,
        components.use_coordinates.value,
        components.latitude.value,
        components.longitude.value,
        components.date.value,
    )
    message = message if message else "Location search payload submitted."
    update_status(components, data, message)
    


# MAIN UI PAGE
###############################################################################
def main_page() -> None:
    current_settings = get_runtime_settings()
    provider, model_update = sync_cloud_model_options(
        current_settings.provider, current_settings.cloud_model
    )
    cloud_models = model_update.options or []
    selected_cloud_model = model_update.value
    cloud_enabled = current_settings.use_cloud_services

    ui.page_title("AEGIS Geographics")
    ui.add_head_html(f"<style>{INTERFACE_THEME_CSS}</style>")

    with ui.column().classes(PAGE_CONTAINER_CLASSES):
        ui.markdown(
            "## AEGIS Geographics\nVisualize geographic data overlays in real time"
        ).classes("text-3xl font-semibold text-slate-800 dark:text-slate-100")
        with ui.row().classes("w-full flex-wrap justify-start"):
            with ui.card().classes(f"{CARD_BASE_CLASSES} w-full"):
                with ui.column().classes("gap-4"):
                    ui.markdown("**Authentication**")
                    auth_button = ui.button("Authenticate", on_click=None)
                    auth_button.props("color=secondary")
                    auth_button.props("size=sm")

        with ui.row().classes("w-full gap-6 items-stretch flex-wrap md:flex-nowrap"):
            # LOCATION SEARCH (left)
            with ui.card().classes(f"{CARD_BASE_CLASSES} flex-1 w-full md:w-1/2"):
                with ui.column().classes("gap-4 h-full"):
                    ui.markdown("### Location search")

                    with ui.column().classes("gap-3"):
                        use_coordinates_switch = ui.switch(
                            "Provide latitude and longitude"
                        ).props("color=primary")

                        country_input = ui.input(
                            label="Country or Region",
                            placeholder="Enter a country or region",
                        ).classes("w-full")

                        city_input = ui.input(
                            label="City Name",
                            placeholder="Enter a city or locale",
                        ).classes("w-full")

                        address_input = (
                            ui.input(
                                label="Street Address",
                                placeholder="Enter the specific address",
                            )
                            .classes("w-full")
                            .props("required")
                        )

                        with ui.row().classes("w-full gap-3 flex-wrap"):
                            latitude_input = ui.number(
                                label="Latitude (°)",
                                format="%.6f",
                                step=0.000001,
                            ).classes("flex-1 min-w-[160px]")
                            longitude_input = ui.number(
                                label="Longitude (°)",
                                format="%.6f",
                                step=0.000001,
                            ).classes("flex-1 min-w-[160px]")

                        date_input = ui.input(label="Reference Moment")
                        date_input.props["type"] = "datetime-local"
                        date_input.set_value(get_datetime_default_value())

                        filter_select = ui.select(
                            FILTER_CHOICES,
                            label="Imagery Style",
                        ).classes("w-full")

                    ui.space()  # push button to bottom
                    search_button = ui.button("Start search", on_click=None).props(
                        "color=primary"
                    )

            # AGENTIC SEARCH (right)
            with ui.card().classes(f"{CARD_BASE_CLASSES} flex-1 w-full md:w-1/2"):
                with ui.column().classes("gap-3 h-full"):
                    ui.markdown("### Agentic Search")
                    agentic_checkbox = ui.checkbox("Activate agentic assistant")
                    llm_query_input = ui.textarea(
                        label="Agent Prompt",
                        placeholder="Describe the geographic insights you need",
                    ).classes("w-full")

                    with ui.expansion("Model configuration", icon="settings"):
                        use_cloud_checkbox = ui.checkbox(
                            "Leverage OpenAI cloud models", value=cloud_enabled
                        )
                        cloud_model_dropdown = ui.select(
                            OPENAI_CLOUD_MODELS,
                            label="OpenAI model choice",
                            value=selected_cloud_model,
                        ).classes("w-full")

                        agent_model_dropdown = ui.select(
                            AGENT_MODEL_CHOICES,
                            value=current_settings.agent_model,
                            label="Ollama agent model",
                        ).classes("w-full")

                        temperature_input = ui.number(
                            label="Temperature",
                            value=current_settings.temperature,
                            min=0.0,
                            max=2.0,
                            step=0.1,
                        ).classes("w-full")

                        reasoning_checkbox = ui.checkbox(
                            "Enable reasoning (think)",
                            value=current_settings.reasoning,
                        )

                    ui.space()
                    agentic_button = ui.button(
                        "Run agentic search", on_click=None
                    ).props("color=secondary")

        with ui.row().classes("w-full gap-4 items-stretch flex-wrap md:flex-nowrap"):
            with ui.card().classes(f"{CARD_BASE_CLASSES} flex-1 min-w-0 w-full md:w-1/2"):
                with ui.column().classes("gap-3 h-full"):
                    ui.markdown("### Map Preview")
                    map_canvas = ui.image()
                    map_canvas.classes(
                        "w-full h-full min-h-[560px] max-h-[800px] object-contain bg-slate-100"
                    )

            with ui.card().classes(f"{CARD_BASE_CLASSES} flex-1 min-w-0 w-full md:w-1/2"):
                with ui.column().classes("gap-3 h-full"):
                    ui.markdown("### Endpoint Output")
                    with ui.scroll_area().classes("w-full h-full max-h-[640px] min-w-0"):
                        status_display = ui.markdown("Waiting for response...")
                        status_display.classes("status-output w-full text-sm font-mono")

    components = ClientComponents(
        auth_button=auth_button,
        country=country_input,
        city=city_input,
        address=address_input,
        use_coordinates=use_coordinates_switch,
        latitude=latitude_input,
        longitude=longitude_input,
        date=date_input,
        filter=filter_select,
        search=search_button,
        agentic_toggle=agentic_checkbox,
        llm_query=llm_query_input,
        use_cloud=use_cloud_checkbox,
        cloud_model=cloud_model_dropdown,
        agent_model=agent_model_dropdown,
        temperature=temperature_input,
        agentic_search=agentic_button,
        status=status_display,
        map_display=map_canvas,
    )

    # Wire events (targeted updates)
    use_coordinates_switch.on_value_change(
        partial(handle_use_coordinates_change, components)
    )
    search_button.on_click(partial(handle_search_click, components))


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
        title="AEGIS Geographics",
        show_welcome_message=False,
    )


# -----------------------------------------------------------------------------
if __name__ in {"__main__", "__mp_main__"}:
    launch_interface()
