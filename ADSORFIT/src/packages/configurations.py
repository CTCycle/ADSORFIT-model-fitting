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

# [SERVER SETTINGS]
###############################################################################
@dataclass(frozen=True)
class FastAPISettings:
    title: str
    description: str
    version: str
    api_base_url: str

# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class DatabaseSettings:
    embedded_database: bool
    engine: str | None          
    host: str | None            
    port: int | None            
    database_name: str | None
    username: str | None
    password: str | None
    ssl: bool                   
    ssl_ca: str | None         
    connect_timeout: int
    insert_batch_size: int

# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class DatasetSettings:
    allowed_extensions: tuple[str, ...]
    column_detection_cutoff: float

# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class FittingSettings:
    default_max_iterations: int
    max_iterations_upper_bound: int
    save_best_default: bool
    parameter_initial_default: float
    parameter_min_default: float
    parameter_max_default: float
    preview_row_limit: int

# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class ServerSettings:
    fastapi: FastAPISettings
    database: DatabaseSettings
    datasets: DatasetSettings
    fitting: FittingSettings


# [CLIENT SETTINGS]
###############################################################################
@dataclass(frozen=True)
class UIRuntimeSettings:
    host: str
    port: int
    title: str
    show_welcome_message: bool
    reconnect_timeout: int    
    http_timeout: float

# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class ClientSettings:
    ui: UIRuntimeSettings


# [APPLICATION SETTINGS]
###############################################################################
@dataclass(frozen=True)
class AppConfigurations:
    server: ServerSettings
    client: ClientSettings


# [UTILITY FUNCTIONS]
###############################################################################
def ensure_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}

# -----------------------------------------------------------------------------
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


# [BUILDER FUNCTIONS]
###############################################################################
def build_fastapi_settings(payload: dict[str, Any] | Any) -> FastAPISettings:
    return FastAPISettings(
        title=coerce_str(payload.get("title"), "ADSORFIT Backend"),
        description=coerce_str(payload.get("description"), "FastAPI backend"),
        version=coerce_str(payload.get("version"), "0.1.0"),
        api_base_url=coerce_str(payload.get("base_url"), "http://127.0.0.1:8000"),
    )

# -----------------------------------------------------------------------------
def build_database_settings(payload: dict[str, Any] | Any) -> DatabaseSettings:
    embedded = bool(payload.get("embedded_database", True))
    if embedded:
        # External fields are ignored entirely when embedded DB is active
        return DatabaseSettings(
            embedded_database=True,
            engine=None,
            host=None,
            port=None,
            database_name=None,
            username=None,
            password=None,
            ssl=False,
            ssl_ca=None,
            connect_timeout=10,
            insert_batch_size=coerce_int(payload.get("insert_batch_size"), 1000, minimum=1),
        )

    # External DB mode
    engine_value = coerce_str_or_none(payload.get("engine")) or "postgres"
    normalized_engine = engine_value.lower() if engine_value else None
    return DatabaseSettings(
        embedded_database=False,
        engine=normalized_engine,
        host=coerce_str_or_none(payload.get("host")),
        port=coerce_int(payload.get("port"), 5432, minimum=1, maximum=65535),
        database_name=coerce_str_or_none(payload.get("database_name")),
        username=coerce_str_or_none(payload.get("username")),
        password=coerce_str_or_none(payload.get("password")),
        ssl=bool(payload.get("ssl", False)),
        ssl_ca=coerce_str_or_none(payload.get("ssl_ca")),
        connect_timeout=coerce_int(payload.get("connect_timeout"), 10, minimum=1),
        insert_batch_size=coerce_int(payload.get("insert_batch_size"), 1000, minimum=1),
    )

# -----------------------------------------------------------------------------
def build_dataset_settings(payload: dict[str, Any] | Any) -> DatasetSettings:
    return DatasetSettings(
        allowed_extensions=coerce_str_sequence(
            payload.get("allowed_extensions"), [".csv", ".xls", ".xlsx"]
        ),
        column_detection_cutoff=coerce_float(
            payload.get("column_detection_cutoff"), 0.6, minimum=0.0, maximum=1.0
        ),
    )

# -----------------------------------------------------------------------------
def build_fitting_settings(payload: dict[str, Any] | Any) -> FittingSettings:
    default_iterations = coerce_int(
        payload.get("default_max_iterations"), 1000, minimum=1
    )
    upper_bound = coerce_int(
        payload.get("max_iterations_upper_bound"), 1_000_000, minimum=default_iterations
    )
    parameter_initial_default = coerce_float(
        payload.get("default_parameter_initial"), 1.0, minimum=0.0
    )
    parameter_min_default = coerce_float(
        payload.get("default_parameter_min"), 0.0, minimum=0.0
    )
    parameter_max_default = coerce_float(
        payload.get("default_parameter_max"), 100.0, minimum=parameter_min_default
    )
    return FittingSettings(
        default_max_iterations=default_iterations,
        max_iterations_upper_bound=upper_bound,
        save_best_default=coerce_bool(payload.get("save_best_default"), True),
        parameter_initial_default=parameter_initial_default,
        parameter_min_default=parameter_min_default,
        parameter_max_default=parameter_max_default,
        preview_row_limit=coerce_int(payload.get("preview_row_limit"), 5, minimum=1),
    )

# -----------------------------------------------------------------------------
def build_server_settings(data: dict[str, Any] | Any) -> ServerSettings:
    payload = ensure_mapping(data)

    fastapi_payload = ensure_mapping(payload.get("fastapi"))
    database_payload = ensure_mapping(payload.get("database"))
    dataset_payload = ensure_mapping(payload.get("datasets"))
    fitting_payload = ensure_mapping(payload.get("fitting"))

    return ServerSettings(
        fastapi=build_fastapi_settings(fastapi_payload),
        database=build_database_settings(database_payload),
        datasets=build_dataset_settings(dataset_payload),
        fitting=build_fitting_settings(fitting_payload),
    )

# -----------------------------------------------------------------------------
def build_ui_settings(payload: dict[str, Any] | Any | Any) -> UIRuntimeSettings:
    return UIRuntimeSettings(
        host=coerce_str(payload.get("host"), "0.0.0.0"),
        port=coerce_int(payload.get("port"), 7861, minimum=1, maximum=65535),
        title=coerce_str(payload.get("title"), "ADSORFIT Model Fitting"),        
        show_welcome_message=coerce_bool(payload.get("show_welcome_message"), False),
        reconnect_timeout=coerce_int(payload.get("reconnect_timeout"), 180, minimum=1),        
        http_timeout=coerce_float(payload.get("timeout"), 120.0, minimum=1.0)
    )

# -----------------------------------------------------------------------------
def build_client_settings(payload: dict[str, Any] | Any) -> ClientSettings:
    ui_payload = payload.get("ui") if isinstance(payload.get("ui"), dict) else {}
    return ClientSettings(
        ui=build_ui_settings(ui_payload)        
    )


# [APPLICATION CONFIGURATION LOADER]
###############################################################################
def get_configurations(config_path: str | None = None) -> AppConfigurations:
    path = config_path or CONFIGURATION_FILE
    data = load_configuration_data(path)
    server_payload = data.get("server") if isinstance(data.get("server"), dict) else {}
    client_payload = data.get("client") if isinstance(data.get("client"), dict) else {}
    return AppConfigurations(
        server=build_server_settings(server_payload),
        client=build_client_settings(client_payload),
    )

configurations = get_configurations()
