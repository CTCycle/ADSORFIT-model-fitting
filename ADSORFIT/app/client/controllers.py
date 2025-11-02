from __future__ import annotations

import asyncio
import copy
from dataclasses import dataclass
import inspect
import math
import os
from collections.abc import Sequence
from typing import Any

import httpx

DEFAULT_API_URL = "http://127.0.0.1:800/api"
HTTP_TIMEOUT_SECONDS = 120.0

MODEL_PARAMETER_DEFAULTS: dict[str, dict[str, tuple[float, float]]] = {
    "Langmuir": {
        "k": (1e-06, 10.0),
        "qsat": (0.0, 100.0),
    },
    "Sips": {
        "k": (1e-06, 10.0),
        "qsat": (0.0, 100.0),
        "exponent": (0.1, 10.0),
    },
    "Freundlich": {
        "k": (1e-06, 10.0),
        "exponent": (0.1, 10.0),
    },
    "Temkin": {
        "k": (1e-06, 10.0),
        "beta": (0.1, 10.0),
    },
}

type DatasetPayload = dict[str, Any]
type ParameterKey = tuple[str, str, str]


###############################################################################
@dataclass
class ApiConfig:
    base_url: str
    timeout: float = HTTP_TIMEOUT_SECONDS


###############################################################################
@dataclass
class DatasetLoadResult:
    dataset: DatasetPayload | None
    message: str


###############################################################################
def get_client_config(api_base_url: str | None = None) -> ApiConfig:
    base_url = api_base_url or os.environ.get("ADSORFIT_API_URL", DEFAULT_API_URL)
    return ApiConfig(base_url=base_url.rstrip("/"))


# -----------------------------------------------------------------------------
def get_parameter_defaults() -> dict[str, dict[str, tuple[float, float]]]:
    return copy.deepcopy(MODEL_PARAMETER_DEFAULTS)


# -----------------------------------------------------------------------------
def build_request_url(config: ApiConfig, route: str) -> str:
    return f"{config.base_url}/{route.lstrip('/')}"


# -----------------------------------------------------------------------------
def read_upload_source(upload: Any) -> bytes:
    reader = getattr(upload, "read", None)
    if callable(reader):
        result = reader()
        if inspect.isawaitable(result):
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                return asyncio.run(result)
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(result)
            finally:
                loop.close()
        if isinstance(result, (bytes, bytearray)):
            return bytes(result)

    data = getattr(upload, "_data", None)
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)

    path = getattr(upload, "_path", None)
    if isinstance(path, str) and os.path.exists(path):
        with open(path, "rb") as handle:
            return handle.read()
    if hasattr(path, "__fspath__"):
        file_path = os.fspath(path)
        if isinstance(file_path, str) and os.path.exists(file_path):
            with open(file_path, "rb") as handle:
                return handle.read()

    raise ValueError("Unable to access the uploaded dataset contents.")


# -----------------------------------------------------------------------------
def extract_file_payload(file: Any) -> tuple[bytes, str | None]:
    upload = getattr(file, "file", None)
    if upload is not None:
        data = read_upload_source(upload)
        name = getattr(upload, "name", None)
        if isinstance(name, str):
            name = os.path.basename(name)
        return data, name

    content = getattr(file, "content", None)
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
        if not isinstance(data, (bytes, bytearray)):
            data = bytes(data)
        name = getattr(file, "name", None)
        if isinstance(name, str):
            name = os.path.basename(name)
        return data, name

    if isinstance(file, (bytes, bytearray)):
        return bytes(file), None

    possible_paths: list[str] = []
    for attribute in ("name", "path"):
        candidate = getattr(file, attribute, None)
        if isinstance(candidate, str):
            possible_paths.append(candidate)
    if isinstance(file, dict):
        for key in ("name", "path"):
            candidate = file.get(key)
            if isinstance(candidate, str):
                possible_paths.append(candidate)
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "rb") as handle:
                return handle.read(), os.path.basename(path)

    data_holder = getattr(file, "data", None)
    if isinstance(data_holder, (bytes, bytearray)):
        name = getattr(file, "orig_name", None) if hasattr(file, "orig_name") else None
        if name is None and hasattr(file, "name"):
            name = getattr(file, "name")
        if isinstance(name, str):
            name = os.path.basename(name)
        return bytes(data_holder), name

    if isinstance(file, dict):
        data_holder = file.get("data")
        if isinstance(data_holder, (bytes, bytearray)):
            name = file.get("orig_name") or file.get("name") or file.get("path")
            if isinstance(name, str):
                name = os.path.basename(name)
            return bytes(data_holder), name

    raise ValueError("Unable to access the uploaded dataset.")


# -----------------------------------------------------------------------------
def extract_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        text = response.text.strip()
        return text or f"HTTP error {response.status_code}"

    detail = payload.get("detail") if isinstance(payload, dict) else None
    if isinstance(detail, str) and detail:
        return detail

    message = payload.get("message") if isinstance(payload, dict) else None
    if isinstance(message, str) and message:
        return message

    return f"HTTP error {response.status_code}"


# -----------------------------------------------------------------------------
def post_json(
    route: str,
    payload: dict[str, Any],
    *,
    config: ApiConfig | None = None,
) -> tuple[bool, dict[str, Any] | None, str]:
    active_config = config or get_client_config()
    url = build_request_url(active_config, route)
    try:
        response = httpx.post(url, json=payload, timeout=active_config.timeout)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        message = extract_error_message(exc.response)
        return False, None, message
    except httpx.RequestError as exc:
        return False, None, f"Failed to reach ADSORFIT backend: {exc}"

    try:
        data = response.json()
    except ValueError as exc:
        return False, None, f"Invalid JSON response: {exc}"

    return True, data, ""


# -----------------------------------------------------------------------------
def post_file(
    route: str,
    file_bytes: bytes,
    filename: str | None,
    *,
    config: ApiConfig | None = None,
) -> tuple[bool, dict[str, Any] | None, str]:
    active_config = config or get_client_config()
    url = build_request_url(active_config, route)
    safe_name = filename or "dataset"
    files = {"file": (safe_name, file_bytes, "application/octet-stream")}

    try:
        response = httpx.post(url, files=files, timeout=active_config.timeout)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        message = extract_error_message(exc.response)
        return False, None, message
    except httpx.RequestError as exc:
        return False, None, f"Failed to reach ADSORFIT backend: {exc}"

    try:
        data = response.json()
    except ValueError as exc:
        return False, None, f"Invalid JSON response: {exc}"

    return True, data, ""


# -----------------------------------------------------------------------------
def load_dataset(file: Any, *, config: ApiConfig | None = None) -> DatasetLoadResult:
    if file is None:
        return DatasetLoadResult(dataset=None, message="No dataset loaded.")

    try:
        file_bytes, filename = extract_file_payload(file)
    except ValueError as exc:
        return DatasetLoadResult(dataset=None, message=f"[ERROR] {exc}")

    ok, response, message = post_file("datasets/load", file_bytes, filename, config=config)
    if not ok or response is None:
        return DatasetLoadResult(dataset=None, message=f"[ERROR] {message}")

    status = response.get("status") if isinstance(response, dict) else None
    if status != "success":
        detail = response.get("detail") if isinstance(response, dict) else None
        if not detail:
            detail = "Failed to load dataset."
        return DatasetLoadResult(dataset=None, message=f"[ERROR] {detail}")

    dataset = response.get("dataset") if isinstance(response, dict) else None
    summary = response.get("summary") if isinstance(response, dict) else None

    if not isinstance(dataset, dict):
        return DatasetLoadResult(
            dataset=None, message="[ERROR] Backend returned an invalid dataset payload."
        )

    if not isinstance(summary, str):
        summary = "[INFO] Dataset loaded successfully."

    return DatasetLoadResult(dataset=dataset, message=summary)


# -----------------------------------------------------------------------------
def build_parameter_bounds(
    metadata: list[ParameterKey],
    values: Sequence[Any],
) -> dict[str, dict[str, dict[str, float | None]]]:
    bounds: dict[str, dict[str, dict[str, float | None]]] = {}
    for (model, parameter, bound_type), raw_value in zip(metadata, values, strict=False):
        if model not in bounds:
            bounds[model] = {}
        if parameter not in bounds[model]:
            bounds[model][parameter] = {"min": 0.0, "max": 0.0}

        numeric_value: float | None
        try:
            numeric_value = float(raw_value)
        except (TypeError, ValueError):
            numeric_value = None
        if numeric_value is not None and not math.isfinite(numeric_value):
            numeric_value = None

        bounds[model][parameter][bound_type] = numeric_value

    return bounds


# -----------------------------------------------------------------------------
def build_solver_configuration(
    bounds: dict[str, dict[str, dict[str, float | None]]],
    selected_models: list[str],
) -> dict[str, dict[str, dict[str, float]]]:
    configuration: dict[str, dict[str, dict[str, float]]] = {}
    for model_name in selected_models:
        parameters = MODEL_PARAMETER_DEFAULTS.get(model_name)
        if parameters is None:
            continue
        selected = bounds.get(model_name, {})
        config_entry = {"min": {}, "max": {}, "initial": {}}
        for parameter, (default_min, default_max) in parameters.items():
            candidate = selected.get(parameter, {})
            lower = candidate.get("min")
            upper = candidate.get("max")
            if lower is None:
                lower = float(default_min)
            if upper is None:
                upper = float(default_max)
            if upper < lower:
                lower, upper = upper, lower
            midpoint = lower + ((upper - lower) / 2.0)
            config_entry["min"][parameter] = float(lower)
            config_entry["max"][parameter] = float(upper)
            config_entry["initial"][parameter] = float(midpoint)
        configuration[model_name] = config_entry
    return configuration


# -----------------------------------------------------------------------------
def start_fitting(
    metadata: list[ParameterKey],
    max_iterations: float,
    save_best: bool,
    dataset: DatasetPayload | None,
    selected_models: list[str],
    *values: Any,
    config: ApiConfig | None = None,
) -> str:
    if dataset is None:
        return "[ERROR] Please load a dataset before starting the fitting process."

    if not metadata:
        return "[ERROR] No parameter configuration available."

    if not selected_models:
        return "[ERROR] Please select at least one model before starting the fitting process."

    bounds = build_parameter_bounds(metadata, values)

    invalid_ranges: list[str] = []
    for model, parameters in bounds.items():
        for name, bound in parameters.items():
            lower = bound.get("min")
            upper = bound.get("max")
            if lower is None or upper is None:
                continue
            if lower > upper:
                invalid_ranges.append(f"{model}::{name} (min > max)")

    if invalid_ranges:
        formatted = ", ".join(invalid_ranges)
        return f"[ERROR] Invalid parameter ranges: {formatted}."

    iterations = max(1, int(round(max_iterations)))

    configuration = build_solver_configuration(bounds, selected_models)

    dataset_payload = {
        "columns": list(dataset.get("columns", [])),
        "records": list(dataset.get("records", [])),
    }

    payload = {
        "max_iterations": iterations,
        "save_best": bool(save_best),
        "parameter_bounds": configuration,
        "dataset": dataset_payload,
    }

    ok, response, message = post_json("fitting/run", payload, config=config)
    if not ok or response is None:
        return f"[ERROR] {message}"

    status = response.get("status")
    if status != "success":
        detail = response.get("detail") or response.get("message") or "Unknown error"
        return f"[ERROR] {detail}"

    summary = response.get("summary")
    if isinstance(summary, str):
        return summary

    formatted_lines: list[str] = ["[INFO] Fitting completed successfully."]
    processed_rows = response.get("processed_rows")
    if isinstance(processed_rows, int):
        formatted_lines.append(f"Processed experiments: {processed_rows}")
    saved_best = response.get("best_model_saved")
    if isinstance(saved_best, bool):
        formatted_lines.append(f"Best model saved: {'Yes' if saved_best else 'No'}")
    models = response.get("models")
    if isinstance(models, list) and models:
        formatted_lines.append("Configured models:")
        for model_name in models:
            formatted_lines.append(f"  - {model_name}")
    return "\n".join(formatted_lines)
