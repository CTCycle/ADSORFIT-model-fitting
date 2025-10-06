from __future__ import annotations

import copy
import io
import json
import math
import os
from typing import Any
from urllib import error, request

import pandas as pd


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

API_BASE_URL = os.environ.get("ADSORFIT_API_URL", "http://127.0.0.1:8000/api")


#-------------------------------------------------------------------------------
def get_parameter_defaults() -> dict[str, dict[str, tuple[float, float]]]:
    return copy.deepcopy(MODEL_PARAMETER_DEFAULTS)


#-------------------------------------------------------------------------------
def _resolve_file_path(file: Any) -> str | None:
    if file is None:
        return None

    if isinstance(file, str) and os.path.exists(file):
        return file

    if hasattr(file, "name"):
        path = getattr(file, "name")
        if isinstance(path, str) and os.path.exists(path):
            return path

    if hasattr(file, "path"):
        path = getattr(file, "path")
        if isinstance(path, str) and os.path.exists(path):
            return path

    if isinstance(file, dict):
        for key in ("name", "path"):
            candidate = file.get(key)
            if isinstance(candidate, str) and os.path.exists(candidate):
                return candidate

    return None


#-------------------------------------------------------------------------------
def _read_dataframe(file: Any) -> pd.DataFrame:
    path = _resolve_file_path(file)
    if path:
        extension = os.path.splitext(path)[1].lower()
        if extension == ".csv":
            return pd.read_csv(path)
        if extension in {".xls", ".xlsx"}:
            return pd.read_excel(path, sheet_name=0)
        raise ValueError(f"Unsupported file type: {extension}")

    binary_data: bytes | None = None
    if hasattr(file, "data"):
        data = getattr(file, "data")
        if isinstance(data, (bytes, bytearray)):
            binary_data = bytes(data)
    if binary_data is None and isinstance(file, dict):
        data = file.get("data")
        if isinstance(data, (bytes, bytearray)):
            binary_data = bytes(data)

    if binary_data is None:
        raise ValueError("Unable to access the uploaded dataset.")

    buffer = io.BytesIO(binary_data)
    if hasattr(file, "orig_name"):
        name = getattr(file, "orig_name")
    elif isinstance(file, dict):
        name = file.get("orig_name")
    else:
        name = None

    if isinstance(name, str):
        extension = os.path.splitext(name)[1].lower()
    else:
        extension = ""

    if extension == ".csv" or not extension:
        buffer.seek(0)
        return pd.read_csv(buffer)
    if extension in {".xls", ".xlsx"}:
        buffer.seek(0)
        return pd.read_excel(buffer, sheet_name=0)

    raise ValueError(f"Unsupported file type: {extension or 'unknown'}")


#-------------------------------------------------------------------------------
def _format_dataset_summary(df: pd.DataFrame) -> str:
    rows, columns = df.shape
    total_nans = int(df.isna().sum().sum())
    column_summaries: list[str] = []
    for column in df.columns:
        dtype = df[column].dtype
        missing = int(df[column].isna().sum())
        column_summaries.append(
            f"- {column}: dtype={dtype}, missing={missing}"
        )

    summary_lines = [
        f"Rows: {rows}",
        f"Columns: {columns}",
        f"NaN cells: {total_nans}",
        "Column details:",
        *column_summaries,
    ]
    return "\n".join(summary_lines)


#-------------------------------------------------------------------------------
def load_dataset(file: Any) -> tuple[DatasetPayload | None, str]:
    if file is None:
        return None, "No dataset loaded."

    try:
        dataframe = _read_dataframe(file)
    except ValueError as exc:
        return None, f"[ERROR] {exc}"
    except Exception as exc:  # noqa: BLE001
        return None, f"[ERROR] Failed to read dataset: {exc}"

    serializable = dataframe.where(pd.notna(dataframe), None)
    dataset_payload: DatasetPayload = {
        "columns": list(serializable.columns),
        "records": serializable.to_dict(orient="records"),
        "row_count": int(serializable.shape[0]),
    }
    stats = _format_dataset_summary(dataframe)
    return dataset_payload, stats


#-------------------------------------------------------------------------------
def _build_parameter_bounds(
    metadata: list[ParameterKey],
    values: tuple[Any, ...],
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


#-------------------------------------------------------------------------------
def _build_solver_configuration(
    bounds: dict[str, dict[str, dict[str, float | None]]],
) -> dict[str, dict[str, dict[str, float]]]:
    configuration: dict[str, dict[str, dict[str, float]]] = {}
    for model_name, parameters in MODEL_PARAMETER_DEFAULTS.items():
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


#-------------------------------------------------------------------------------
def _post_json(route: str, payload: dict[str, Any]) -> tuple[bool, dict[str, Any] | None, str]:
    url = f"{API_BASE_URL.rstrip('/')}/{route.lstrip('/')}"
    encoded = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    request_obj = request.Request(url, data=encoded, headers=headers, method="POST")
    try:
        with request.urlopen(request_obj, timeout=120) as response:
            raw_body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        try:
            raw_body = exc.read().decode("utf-8")
        except Exception:  # noqa: BLE001
            raw_body = ""
        message = raw_body or f"HTTP error {exc.code}"
        return False, None, message
    except error.URLError as exc:
        return False, None, f"Failed to reach ADSORFIT backend: {exc.reason}"
    except Exception as exc:  # noqa: BLE001
        return False, None, f"Unexpected error contacting backend: {exc}"

    if not raw_body:
        return False, None, "Backend returned an empty response."

    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        return False, None, f"Invalid JSON response: {exc}"
    return True, data, ""


#-------------------------------------------------------------------------------
def start_fitting(
    metadata: list[ParameterKey],
    max_iterations: float,
    save_best: bool,
    dataset: DatasetPayload | None,
    *values: Any,
) -> str:
    if dataset is None:
        return "[ERROR] Please load a dataset before starting the fitting process."

    if not metadata:
        return "[ERROR] No parameter configuration available."

    bounds = _build_parameter_bounds(metadata, values)

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

    configuration = _build_solver_configuration(bounds)

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

    ok, response, message = _post_json("fitting/run", payload)
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
