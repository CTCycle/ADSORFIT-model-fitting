from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from ADSORFIT.src.packages.constants import CONFIGURATION_FILE
from ADSORFIT.src.packages.types import (
    coerce_bool,
    coerce_float,
    coerce_int,
    coerce_str,
    coerce_str_or_none,
    coerce_str_sequence,
)


###############################################################################
@dataclass(frozen=True)
class UIRuntimeSettings:
    host: str
    port: int
    title: str
    mount_path: str
    redirect_path: str
    show_welcome_message: bool
    reconnect_timeout: int


###############################################################################
@dataclass(frozen=True)
class APISettings:
    base_url: str


###############################################################################
@dataclass(frozen=True)
class HTTPSettings:
    timeout: float


###############################################################################
@dataclass(frozen=True)
class DatabaseSettings:
    selected_database: str
    database_address: str | None
    database_name: str | None
    username: str | None
    password: str | None
    insert_batch_size: int


###############################################################################
@dataclass(frozen=True)
class DatasetSettings:
    allowed_extensions: tuple[str, ...]


###############################################################################
@dataclass(frozen=True)
class FittingSettings:
    default_max_iterations: int
    max_iterations_upper_bound: int
    save_best_default: bool


###############################################################################
@dataclass(frozen=True)
class AppConfigurations:
    ui: UIRuntimeSettings
    api: APISettings
    http: HTTPSettings
    database: DatabaseSettings
    datasets: DatasetSettings
    fitting: FittingSettings


###############################################################################
def load_configuration_data(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        raise RuntimeError(f"Configuration file not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to load configuration from {path}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Configuration root must be a JSON object.")
    return data


# -----------------------------------------------------------------------------
def build_ui_settings(payload: dict[str, Any] | Any | Any) -> UIRuntimeSettings:
    return UIRuntimeSettings(
        host=coerce_str(payload.get("host"), "0.0.0.0"),
        port=coerce_int(payload.get("port"), 7861, minimum=1, maximum=65535),
        title=coerce_str(payload.get("title"), "ADSORFIT Model Fitting"),
        mount_path=coerce_str(payload.get("mount_path"), "/ui"),
        redirect_path=coerce_str(payload.get("redirect_path"), "/ui"),
        show_welcome_message=coerce_bool(payload.get("show_welcome_message"), False),
        reconnect_timeout=coerce_int(
            payload.get("reconnect_timeout"), 180, minimum=1
        ),
    )


# -----------------------------------------------------------------------------
def build_api_settings(payload: dict[str, Any] | Any) -> APISettings:
    return APISettings(base_url=coerce_str(payload.get("base_url"), "http://127.0.0.1:8000"))


# -----------------------------------------------------------------------------
def build_http_settings(payload: dict[str, Any] | Any) -> HTTPSettings:
    return HTTPSettings(
        timeout=coerce_float(payload.get("timeout"), 120.0, minimum=1.0)
    )


# -----------------------------------------------------------------------------
def build_database_settings(payload: dict[str, Any] | Any) -> DatabaseSettings:
    return DatabaseSettings(
        selected_database=coerce_str(payload.get("selected_database"), "sqlite").lower(),
        database_address=coerce_str_or_none(payload.get("database_address")),
        database_name=coerce_str_or_none(payload.get("database_name")),
        username=coerce_str_or_none(payload.get("username")),
        password=coerce_str_or_none(payload.get("password")),
        insert_batch_size=coerce_int(payload.get("insert_batch_size"), 1000, minimum=1)
    )


# -----------------------------------------------------------------------------
def build_dataset_settings(payload: dict[str, Any] | Any) -> DatasetSettings:
    return DatasetSettings(
        allowed_extensions=coerce_str_sequence(
            payload.get("allowed_extensions"), [".csv", ".xls", ".xlsx"]
        )
    )


# -----------------------------------------------------------------------------
def build_fitting_settings(payload: dict[str, Any] | Any) -> FittingSettings:
    default_iterations = coerce_int(payload.get("default_max_iterations"), 1000, minimum=1)
    upper_bound = coerce_int(
        payload.get("max_iterations_upper_bound"), 1_000_000, minimum=default_iterations
    )
    return FittingSettings(
        default_max_iterations=default_iterations,
        max_iterations_upper_bound=upper_bound,
        save_best_default=coerce_bool(payload.get("save_best_default"), True),
    )


# -----------------------------------------------------------------------------
def load_configurations(config_path: str | None = None) -> AppConfigurations:
    path = config_path or CONFIGURATION_FILE
    data = load_configuration_data(path)
    ui_payload = data.get("ui") if isinstance(data.get("ui"), dict) else {}
    api_payload = data.get("api") if isinstance(data.get("api"), dict) else {}
    http_payload = data.get("http") if isinstance(data.get("http"), dict) else {}
    db_payload = data.get("database") if isinstance(data.get("database"), dict) else {}
    dataset_payload = (
        data.get("datasets") if isinstance(data.get("datasets"), dict) else {}
    )
    fitting_payload = (
        data.get("fitting") if isinstance(data.get("fitting"), dict) else {}
    )
    return AppConfigurations(
        ui=build_ui_settings(ui_payload),
        api=build_api_settings(api_payload),
        http=build_http_settings(http_payload),
        database=build_database_settings(db_payload),
        datasets=build_dataset_settings(dataset_payload),
        fitting=build_fitting_settings(fitting_payload),
    )


###############################################################################
configurations = load_configurations()


# -----------------------------------------------------------------------------
def get_configurations() -> AppConfigurations:
    return configurations
