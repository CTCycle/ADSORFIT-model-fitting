from __future__ import annotations

import json
import os
import tarfile
from typing import Any

import httpx
from gradio import update as gr_update

from Pharmagent.app.configurations import ClientRuntimeConfig
from Pharmagent.app.constants import (
    AGENT_API_URL,
    API_BASE_URL,
    BATCH_AGENT_API_URL,
    CLOUD_MODEL_CHOICES,
    LIVERTOX_ARCHIVE,
    PHARMACOLOGY_LIVERTOX_FETCH_ENDPOINT,
    SOURCES_PATH,
)
from Pharmagent.app.api.models.providers import (
    OllamaClient,
    OllamaError,
    OllamaTimeout,
)
from Pharmagent.app.utils.jobs import (
    _await_livertox_job,
    _format_progress_log,
)


# [HELPERS]
###############################################################################
def _extract_text(result: Any) -> str:
    if isinstance(result, dict):
        for key in ("output", "result", "text", "message", "response"):
            val = result.get(key)
            if isinstance(val, str) and val.strip():
                return val
    try:
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception:
        return str(result)


# -----------------------------------------------------------------------------
def _sanitize_field(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


# -----------------------------------------------------------------------------
def toggle_cloud_services(
    enabled: bool,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    ClientRuntimeConfig.set_use_cloud_services(enabled)
    provider = ClientRuntimeConfig.get_llm_provider()
    provider_update = gr_update(value=provider, interactive=enabled)
    models = CLOUD_MODEL_CHOICES.get(provider, [])
    selected_model = ClientRuntimeConfig.get_cloud_model()
    if selected_model not in models:
        selected_model = ClientRuntimeConfig.set_cloud_model(models[0] if models else "")
    model_update = gr_update(
        value=selected_model,
        choices=models,
        interactive=enabled,
    )
    button_update = gr_update(interactive=not enabled)
    return provider_update, model_update, button_update, button_update


# -----------------------------------------------------------------------------
def set_llm_provider(provider: str) -> tuple[str, dict[str, Any]]:
    selected = ClientRuntimeConfig.set_llm_provider(provider)
    models = CLOUD_MODEL_CHOICES.get(selected, [])
    current_model = ClientRuntimeConfig.get_cloud_model()
    if current_model not in models:
        current_model = ClientRuntimeConfig.set_cloud_model(models[0] if models else "")
    model_update = gr_update(
        value=current_model,
        choices=models,
        interactive=ClientRuntimeConfig.is_cloud_enabled(),
    )
    return selected, model_update


# -----------------------------------------------------------------------------
def set_cloud_model(model: str) -> str:
    return ClientRuntimeConfig.set_cloud_model(model)


# -----------------------------------------------------------------------------
def set_parsing_model(model: str) -> str:
    return ClientRuntimeConfig.set_parsing_model(model)


# -----------------------------------------------------------------------------
def set_agent_model(model: str) -> str:
    return ClientRuntimeConfig.set_agent_model(model)


# -----------------------------------------------------------------------------
async def pull_selected_models(parsing_model: str, agent_model: str) -> str:
    models: list[str] = []
    for name in (parsing_model, agent_model):
        if not name:
            continue
        normalized = name.strip()
        if normalized and normalized not in models:
            models.append(normalized)

    if not models:
        return "[ERROR] No models selected to pull."

    try:
        async with OllamaClient() as client:
            for model in models:
                await client.pull(model, stream=False)
    except OllamaTimeout as exc:
        return f"[ERROR] Timed out pulling models: {exc}"
    except OllamaError as exc:
        return f"[ERROR] Failed to pull models: {exc}"
    except Exception as exc:  # noqa: BLE001
        return f"[ERROR] Unexpected error while pulling models: {exc}"

    pulled = ", ".join(models)
    return f"[INFO] Models available locally: {pulled}."


# -----------------------------------------------------------------------------
async def start_ollama_client() -> str:
    if ClientRuntimeConfig.is_cloud_enabled():
        return "[INFO] Cloud provider enabled; Ollama client is disabled."

    try:
        async with OllamaClient() as client:
            status = await client.start_server()
    except OllamaTimeout as exc:
        return f"[ERROR] Timed out starting Ollama server: {exc}"
    except OllamaError as exc:
        return f"[ERROR] Failed to start Ollama server: {exc}"
    except Exception as exc:  # noqa: BLE001
        return f"[ERROR] Unexpected error while starting Ollama server: {exc}"

    if status == "already_running":
        return "[INFO] Ollama server is already running."

    return "[INFO] Ollama server started successfully."


# -----------------------------------------------------------------------------
async def preload_selected_models(parsing_model: str, agent_model: str) -> str:
    if ClientRuntimeConfig.is_cloud_enabled():
        return "[INFO] Cloud provider enabled; skipping Ollama preload."

    parser = parsing_model.strip() if parsing_model else ""
    agent = agent_model.strip() if agent_model else ""
    requested = [name for name in (parser, agent) if name]

    if not requested:
        return "[ERROR] No models selected to preload."

    try:
        async with OllamaClient() as client:
            if not await client.is_server_online():
                return "[ERROR] Ollama server is not reachable. Start the Ollama client first."
            loaded, skipped = await client.preload_models(parser, agent)
    except OllamaTimeout as exc:
        return f"[ERROR] Timed out while preloading models: {exc}"
    except OllamaError as exc:
        return f"[ERROR] Failed to preload models: {exc}"
    except Exception as exc:  # noqa: BLE001
        return f"[ERROR] Unexpected error while preloading models: {exc}"

    if not loaded:
        return "[ERROR] No models were preloaded."

    message = f"[INFO] Preloaded models: {', '.join(loaded)}."
    if skipped:
        message += f" [WARN] Skipped due to limited memory: {', '.join(skipped)}."
    return message


# -----------------------------------------------------------------------------
async def fetch_clinical_data(skip_download: bool) -> str:
    url = f"{API_BASE_URL}{PHARMACOLOGY_LIVERTOX_FETCH_ENDPOINT}"
    params = {"skip_download": "true"} if skip_download else None

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            try:
                initial_status = response.json()
            except ValueError:
                return "[ERROR] Backend response was not valid JSON."

            if not isinstance(initial_status, dict):
                return "[ERROR] Unexpected response format from backend."

            job_result = await _await_livertox_job(client, initial_status)
    except httpx.ConnectError as exc:
        return f"[ERROR] Could not connect to backend at {url}.\nDetails: {exc}"
    except httpx.HTTPStatusError as exc:
        body = exc.response.text if exc.response is not None else ""
        code = exc.response.status_code if exc.response else "unknown"
        return (
            f"[ERROR] Backend returned status {code}."
            f"\nURL: {url}\nResponse body:\n{body}"
        )
    except httpx.TimeoutException:
        return f"[ERROR] Request timed out after {120} seconds."
    except Exception as exc:  # noqa: BLE001
        return f"[ERROR] Unexpected error: {exc}"

    if isinstance(job_result, str):
        return job_result

    payload, progress_log = job_result
    progress_suffix = _format_progress_log(progress_log)

    file_path = payload.get("file_path")
    reported_size = payload.get("size")
    last_modified = payload.get("last_modified")
    processed_entries = payload.get("processed_entries")
    stored_records = payload.get("records")

    if not isinstance(file_path, str) or not file_path:
        return "[ERROR] Backend response did not include a valid file path." + progress_suffix

    absolute_file_path = os.path.abspath(file_path)
    sources_dir = os.path.abspath(SOURCES_PATH)

    if not absolute_file_path.startswith(sources_dir):
        return (
            "[ERROR] Downloaded file is located outside the expected sources directory."
            + progress_suffix
        )

    if os.path.basename(absolute_file_path) != LIVERTOX_ARCHIVE:
        return "[ERROR] Unexpected file downloaded from backend." + progress_suffix

    if not os.path.isfile(absolute_file_path):
        return "[ERROR] Download failed: file not found after fetch." + progress_suffix

    actual_size = os.path.getsize(absolute_file_path)
    if actual_size <= 0:
        return "[ERROR] Downloaded file is empty." + progress_suffix

    if isinstance(reported_size, int) and reported_size > 0 and actual_size < reported_size:
        return (
            "[ERROR] Downloaded file size is smaller than expected; download may be incomplete."
            + progress_suffix
        )

    try:
        with tarfile.open(absolute_file_path, "r:gz") as archive:
            member = archive.next()
            if member is None:
                return "[ERROR] Downloaded archive contains no data." + progress_suffix
    except (tarfile.TarError, OSError) as exc:
        return f"[ERROR] Downloaded file appears corrupted: {exc}" + progress_suffix

    if not isinstance(stored_records, int) or stored_records <= 0:
        return "[ERROR] Backend did not report stored LiverTox records." + progress_suffix

    message = (
        "[INFO] Clinical data downloaded successfully."
        f"\nSize: {actual_size} bytes"
    )

    if isinstance(last_modified, str) and last_modified:
        message += f"\nLast-Modified: {last_modified}"

    if isinstance(processed_entries, int) and processed_entries >= 0:
        message += f"\nProcessed monographs: {processed_entries}"

    if isinstance(stored_records, int) and stored_records >= 0:
        message += f"\nStored monographs: {stored_records}"

    if progress_suffix:
        message += progress_suffix

    return message


# -----------------------------------------------------------------------------
def clear_agent_fields() -> tuple[
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    list[str],
    bool,
    bool,
    bool,
    bool,
    str,
    str,
]:
    return (
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        [],
        False,
        False,
        False,
        False,
        "",
        "",
    )


# trigger function to start the agent on button click. Payload is optional depending
# on the requested endpoint URL (defined through run_agent function)
# -----------------------------------------------------------------------------
async def _trigger_agent(url: str, payload: dict[str, Any] | None = None) -> str:
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                url,
                json=payload
            )
            resp.raise_for_status()
            try:
                return _extract_text(resp.json())
            except ValueError:
                return resp.text

    except httpx.ConnectError as exc:
        return f"[ERROR] Could not connect to backend at {url}.\nDetails: {exc}"
    except httpx.HTTPStatusError as exc:
        body = exc.response.text if exc.response is not None else ""
        code = exc.response.status_code if exc.response else "unknown"
        return (
            f"[ERROR] Backend returned status {code}."
            f"\nURL: {url}\nResponse body:\n{body}"
        )
    except httpx.TimeoutException:
        return f"[ERROR] Request timed out after {120} seconds."
    except Exception as exc:  # noqa: BLE001
        return f"[ERROR] Unexpected error: {exc}"


# [AGENT RUNNING LOGIC]
###############################################################################
async def run_agent(
    patient_name: str | None,
    anamnesis: str,
    drugs: str,
    exams: str,
    alt: str,
    alt_max: str,
    alp: str,
    alp_max: str,
    symptoms: list[str],
    process_from_files: bool,
    translate_to_eng: bool,
) -> str:
    if process_from_files:
        url = f"{API_BASE_URL}{BATCH_AGENT_API_URL}"
        return await _trigger_agent(url)

    cleaned_payload = {
        "name": _sanitize_field(patient_name),
        "anamnesis": _sanitize_field(anamnesis),
        "drugs": _sanitize_field(drugs),
        "exams": _sanitize_field(exams),
        "alt": _sanitize_field(alt),
        "alt_max": _sanitize_field(alt_max),
        "alp": _sanitize_field(alp),
        "alp_max": _sanitize_field(alp_max),
        "symptoms": symptoms or [],
        "translate_to_eng": translate_to_eng,
    }

    if not any(cleaned_payload[key] for key in ("anamnesis", "drugs", "exams")):
        return "[ERROR] Please provide at least one clinical section."

    url = f"{API_BASE_URL}{AGENT_API_URL}"
    return await _trigger_agent(url, cleaned_payload)
