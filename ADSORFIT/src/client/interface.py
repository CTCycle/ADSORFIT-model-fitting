from __future__ import annotations

from collections.abc import Callable
from types import CoroutineType
from typing import Any

from nicegui import ui
from nicegui.elements.checkbox import Checkbox
from nicegui.elements.expansion import Expansion
from nicegui.elements.markdown import Markdown
from nicegui.elements.number import Number
from nicegui.elements.switch import Switch
from nicegui.elements.textarea import Textarea

from ADSORFIT.src.client.controllers import (
    DatasetEndpointController,
    DatasetPayload,
    FittingEndpointController,
    ParameterKey,
    SettingsController,
)
from ADSORFIT.src.client.layouts import (
    CARD_BASE_CLASSES,
    INTERFACE_THEME_CSS,
    PAGE_CONTAINER_CLASSES,
)
from ADSORFIT.src.packages.configurations import configurations

ui_settings = configurations.client.ui
dataset_settings = configurations.server.datasets
fitting_settings = configurations.server.fitting


# [INTERFACE CONTROLLER]
###############################################################################
class InterfaceController:
    def __init__(
        self,
        dataset_endpoint: DatasetEndpointController,
        fitting_endpoint: FittingEndpointController,
    ) -> None:
        self.dataset_endpoint = dataset_endpoint
        self.fitting_endpoint = fitting_endpoint
        self.dataset_state: dict[str, DatasetPayload | None] = {"dataset": None}
        self.parameter_collectors: list[tuple[ParameterKey, Callable[[], Any]]] = []
        self.model_toggles: dict[str, Switch] = {}

    # -------------------------------------------------------------------------
    def reset_collectors(self) -> None:
        self.parameter_collectors.clear()

    # -------------------------------------------------------------------------
    def reset_model_toggles(self) -> None:
        self.model_toggles.clear()

    # -------------------------------------------------------------------------
    def register_parameter_collector(
        self, key: ParameterKey, reader: Callable[[], Any]
    ) -> None:
        self.parameter_collectors.append((key, reader))

    # -------------------------------------------------------------------------
    def register_model_toggle(self, model_name: str, toggle: Switch) -> None:
        self.model_toggles[model_name] = toggle

    # -------------------------------------------------------------------------
    def collect_parameter_payload(
        self,
    ) -> tuple[list[ParameterKey], list[Any]]:
        metadata: list[ParameterKey] = []
        values: list[Any] = []
        for entry_metadata, reader in self.parameter_collectors:
            metadata.append(entry_metadata)
            values.append(reader())
        return metadata, values

    # -------------------------------------------------------------------------
    def build_stats_markdown(self, summary: str) -> str:
        lines = [line.strip() for line in summary.splitlines() if line.strip()]
        if not lines:
            return "#### Dataset statistics\n\n_No dataset information available._"

        formatted: list[str] = ["#### Dataset statistics"]
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

    # -------------------------------------------------------------------------
    def extract_upload_payload(
        self, event: Any | None
    ) -> tuple[bytes | None, str | None]:
        if not event:
            return None, None

        file = getattr(event, "file", None)
        if file is not None:
            content = getattr(file, "_data", None) or getattr(file, "content", None)
            if isinstance(content, bytearray):
                content = bytes(content)
            if isinstance(content, bytes):
                return content, file.name or None

        args = getattr(event, "args", {}) or {}
        content = args.get("content")
        name = args.get("name") or args.get("filename")

        if isinstance(content, bytearray):
            content = bytes(content)
        if isinstance(content, bytes):
            return content, name

        file_entry = args.get("file")
        if isinstance(file_entry, dict):
            content = file_entry.get("content")
            name = file_entry.get("name") or file_entry.get("filename") or name
            if isinstance(content, bytearray):
                content = bytes(content)
            if isinstance(content, bytes):
                return content, name

        return None, name

    # -------------------------------------------------------------------------
    def build_model_toggle_handler(self, expansion: Expansion) -> Callable[..., None]:
        def _handler(event: Any) -> None:
            toggle_active = bool(event.value)
            if not toggle_active:
                expansion.value = False
                expansion.disable()
            else:
                expansion.enable()

        return _handler

    # -------------------------------------------------------------------------
    def build_dataset_upload_handler(self, dataset_stats: Markdown) -> Callable[..., CoroutineType[Any, Any, None]]:
        async def _handler(event: Any) -> None:
            dataset_stats.set_content(
                self.build_stats_markdown("[INFO] Uploading dataset.")
            )
            file_bytes, filename = self.extract_upload_payload(event)
            if not file_bytes:
                dataset_stats.set_content(
                    self.build_stats_markdown("[ERROR] Could not read uploaded file.")
                )
                return
            url = f"{ui_settings.api_base_url}/datasets/load"
            result = await self.dataset_endpoint.load_dataset(url, file_bytes, filename)
            self.dataset_state["dataset"] = result.get("dataset")
            dataset_stats.set_content(
                self.build_stats_markdown(result.get("message", ""))
            )

        return _handler

    # -------------------------------------------------------------------------
    def build_start_fitting_handler(
        self,
        max_iterations_input: Number,
        save_best_checkbox: Checkbox,
        status_area: Textarea,
    ) -> Callable[[], CoroutineType[Any, Any, None]]:
        async def _handler() -> None:
            status_area.value = "[INFO] Starting fitting process..."
            metadata, values = self.collect_parameter_payload()

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
                name
                for name, toggle in self.model_toggles.items()
                if bool(toggle.value)
            ]

            url = f"{ui_settings.api_base_url}/fitting/run"
            result = await self.fitting_endpoint.start_fitting(
                url,
                metadata,
                max_iterations,
                save_best,
                self.dataset_state.get("dataset"),
                selected_models,
                *values,
            )
            status_area.value = result.get("message", "")

        return _handler


# [INTERFACE STRUCTURE]
###############################################################################
class InterfaceStructure:
    def __init__(
        self,
        controller: InterfaceController,
        settings_controller: SettingsController,
    ) -> None:
        self.controller = controller
        self.settings_controller = settings_controller

    # -------------------------------------------------------------------------
    def build_model_cards(
        self,
        parameter_defaults: dict[str, dict[str, tuple[float, float]]],
    ) -> None:
        self.controller.reset_collectors()
        self.controller.reset_model_toggles()

        for model_name, parameters in parameter_defaults.items():
            with ui.card().classes(f"{CARD_BASE_CLASSES} flex-1 min-w-[320px]"):
                with ui.column().classes("gap-3"):
                    with ui.row().classes("w-full items-center justify-between gap-3"):
                        with ui.row().classes("items-center gap-2"):
                            ui.markdown(f"**{model_name}**")
                            toggle = ui.switch(value=True).props("color=primary")
                            self.controller.register_model_toggle(model_name, toggle)

                    expansion = ui.expansion(
                        "Configure parameters", value=False
                    ).classes("w-full")
                    toggle.on_value_change(
                        self.controller.build_model_toggle_handler(expansion)
                    )

                    with expansion:
                        with ui.column().classes("gap-3 w-full"):
                            for parameter_name, (
                                min_default,
                                max_default,
                            ) in parameters.items():
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
                                self.controller.register_parameter_collector(
                                    (model_name, parameter_name, "min"),
                                    lambda mi=min_input: mi.value,
                                )
                                self.controller.register_parameter_collector(
                                    (model_name, parameter_name, "max"),
                                    lambda ma=max_input: ma.value,
                                )

    # -------------------------------------------------------------------------
    def build_controls_panel(self) -> dict[str, Any]:
        with ui.card().classes(f"{CARD_BASE_CLASSES} flex-1 min-w-[320px]"):
            with ui.column().classes("gap-4 w-full items-stretch"):
                max_iterations_input = ui.number(
                    "Max iterations",
                    value=fitting_settings.default_max_iterations,
                    min=1,
                    max=fitting_settings.max_iterations_upper_bound,
                    precision=0,
                    step=1,
                ).classes("w-full")

                save_best_checkbox = ui.checkbox(
                    "Save best fitting data",
                    value=fitting_settings.save_best_default,
                )

                dataset_stats = ui.markdown(
                    self.controller.build_stats_markdown("No dataset loaded.")
                ).classes("w-full adsorfit-status min-h-[260px]")

                status_area = (
                    ui.textarea("Fitting status", value="")
                    .props("readonly rows=10 autogrow")
                    .classes("w-full adsorfit-status min-h-[260px]")
                )

                dataset_upload = (
                    ui.upload(
                        label="Load dataset",
                        auto_upload=True,
                    )
                    .props(f"accept={','.join(dataset_settings.allowed_extensions)}")
                    .classes("w-full")
                )

                fit_button = ui.button("Start fitting").props("color=primary")
        return {
            "max_iterations_input": max_iterations_input,
            "save_best_checkbox": save_best_checkbox,
            "dataset_stats": dataset_stats,
            "status_area": status_area,
            "dataset_upload": dataset_upload,
            "fit_button": fit_button,
        }

    # -------------------------------------------------------------------------
    def compose_main_page(self) -> None:
        parameter_defaults = self.settings_controller.parameter_defaults()

        ui.page_title(ui_settings.title)
        ui.add_head_html(f"<style>{INTERFACE_THEME_CSS}</style>")

        with ui.column().classes(PAGE_CONTAINER_CLASSES):
            ui.markdown(f"## {ui_settings.title}").classes(
                "adsorfit-heading text-3xl font-semibold"
            )
            with ui.row().classes("w-full gap-6 items-start flex-wrap md:flex-nowrap"):
                controls = self.build_controls_panel()
                with ui.column().classes("flex-1 min-w-[320px] gap-4"):
                    self.build_model_cards(parameter_defaults)

        controls["dataset_upload"].on_upload(
            self.controller.build_dataset_upload_handler(controls["dataset_stats"])
        )
        controls["fit_button"].on_click(
            self.controller.build_start_fitting_handler(
                controls["max_iterations_input"],
                controls["save_best_checkbox"],
                controls["status_area"],
            )
        )

    # -------------------------------------------------------------------------
    def mount_routes(self) -> None:
        ui.page("/")(self.compose_main_page)


# [INTERFACE CREATION AND LAUNCHING]
###############################################################################
def create_interface() -> InterfaceStructure:
    settings_controller = SettingsController()
    dataset_endpoint = DatasetEndpointController()
    fitting_endpoint = FittingEndpointController()
    controller = InterfaceController(dataset_endpoint, fitting_endpoint)
    structure = InterfaceStructure(controller, settings_controller)
    structure.mount_routes()
    return structure

# -----------------------------------------------------------------------------
def launch_interface() -> None:
    create_interface()
    ui.run(
        host=ui_settings.host,
        port=ui_settings.port,
        title=ui_settings.title,
        show_welcome_message=ui_settings.show_welcome_message,
        reconnect_timeout=ui_settings.reconnect_timeout,
    )

# -----------------------------------------------------------------------------
if __name__ in {"__main__", "__mp_main__"}:
    launch_interface()
