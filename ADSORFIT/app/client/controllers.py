from __future__ import annotations

import copy
import math
from collections.abc import Sequence
from typing import Any

import httpx
from ADSORFIT.app.constants import HTTP_TIMEOUT_SECONDS, MODEL_PARAMETER_DEFAULTS


type DatasetPayload = dict[str, Any]
type ParameterKey = tuple[str, str, str]


# -----------------------------------------------------------------------------
def get_parameter_defaults() -> dict[str, dict[str, tuple[float, float]]]:
    return copy.deepcopy(MODEL_PARAMETER_DEFAULTS)


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
async def load_dataset(url: str, file_bytes: bytes | None, filename: str | None) -> dict[str, Any]:
    if file_bytes is None:
        return {"dataset": None, "message": "No dataset loaded."}
    
    safe_name = filename or "dataset"
    files = {"file": (safe_name, file_bytes, "application/octet-stream")}

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.post(url, files=files)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        message = extract_error_message(exc.response)
        return {"dataset": None, "message": f"[ERROR] {message}"}
    except httpx.RequestError as exc:
        return {
            "dataset": None,
            "message": f"[ERROR] Failed to reach ADSORFIT backend: {exc}",
        }

    try:
        payload = response.json()
    except ValueError:
        detail = response.text.strip() or "Invalid response from ADSORFIT backend."
        return {"dataset": None, "message": f"[ERROR] {detail}"}

    if not isinstance(payload, dict):
        return {
            "dataset": None,
            "message": "[ERROR] Backend returned an invalid dataset payload.",
        }

    status = payload.get("status") if isinstance(payload, dict) else None
    if status != "success":
        detail = payload.get("detail") if isinstance(payload, dict) else None
        if not detail:
            detail = "Failed to load dataset."
        return {"dataset": None, "message": f"[ERROR] {detail}"}

    dataset = payload.get("dataset") if isinstance(payload, dict) else None
    summary = payload.get("summary") if isinstance(payload, dict) else None

    if not isinstance(dataset, dict):
        return {
            "dataset": None,
            "message": "[ERROR] Backend returned an invalid dataset payload.",
        }

    if not isinstance(summary, str):
        summary = "[INFO] Dataset loaded successfully."

    return {"dataset": dataset, "message": summary}


# -----------------------------------------------------------------------------
def build_parameter_bounds(
    metadata: list[ParameterKey],
    values: Sequence[Any],
) -> dict[str, dict[str, dict[str, float | None]]]:
    bounds: dict[str, dict[str, dict[str, float | None]]] = {}
    for (
        model,
        parameter,
        bound_type,
    ), raw_value in zip(metadata, values, strict=False):
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
async def start_fitting(
    url: str,
    metadata: list[ParameterKey],
    max_iterations: float,
    save_best: bool,
    dataset: DatasetPayload | None,
    selected_models: list[str],
    *values: Any,
) -> dict[str, Any]:
    if dataset is None:
        return {
            "message": (
                "[ERROR] Please load a dataset before starting the fitting process."
            ),
            "json": None,
        }

    if not metadata:
        return {
            "message": "[ERROR] No parameter configuration available.",
            "json": None,
        }

    if not selected_models:
        return {
            "message": (
                "[ERROR] Please select at least one model before starting the fitting process."
            ),
            "json": None,
        }

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
        return {
            "message": f"[ERROR] Invalid parameter ranges: {formatted}.",
            "json": None,
        }

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

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        message = extract_error_message(exc.response)
        return {"message": f"[ERROR] {message}", "json": None}
    except httpx.RequestError as exc:
        return {
            "message": f"[ERROR] Failed to reach ADSORFIT backend: {exc}",
            "json": None,
        }

    try:
        response_payload = response.json()
    except ValueError:
        detail = response.text.strip() or "Invalid response from ADSORFIT backend."
        return {"message": f"[ERROR] {detail}", "json": None}

    if not isinstance(response_payload, dict):
        return {
            "message": "[ERROR] Backend returned an invalid response payload.",
            "json": response_payload,
        }

    status = response_payload.get("status")
    if status != "success":
        detail = (
            response_payload.get("detail")
            or response_payload.get("message")
            or "Unknown error"
        )
        return {"message": f"[ERROR] {detail}", "json": response_payload}

    summary = response_payload.get("summary")
    if isinstance(summary, str):
        return {"message": summary, "json": response_payload}

    formatted_lines: list[str] = ["[INFO] Fitting completed successfully."]
    processed_rows = response_payload.get("processed_rows")
    if isinstance(processed_rows, int):
        formatted_lines.append(f"Processed experiments: {processed_rows}")
    saved_best = response_payload.get("best_model_saved")
    if isinstance(saved_best, bool):
        formatted_lines.append(f"Best model saved: {'Yes' if saved_best else 'No'}")
    models = response_payload.get("models")
    if isinstance(models, list) and models:
        formatted_lines.append("Configured models:")
        for model_name in models:
            formatted_lines.append(f"  - {model_name}")

    return {"message": "\n".join(formatted_lines), "json": response_payload}
