from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx

from AEGIS.app.utils.services.payload import sanitize_search_payload

from AEGIS.app.configurations import ClientRuntimeConfig
from AEGIS.app.constants import (
    API_BASE_URL,
    CLOUD_MODEL_CHOICES,
    GEO_SEARCH_URL,
    HTTP_TIMEOUT_SECONDS,
)

MISSING = object()


###############################################################################
@dataclass
class ComponentUpdate:
    value: Any = MISSING
    options: list[Any] | None = None
    enabled: bool | None = None
    visible: bool | None = None
    download_path: str | None = None

# -----------------------------------------------------------------------------
@dataclass
class RuntimeSettings:
    use_cloud_services: bool
    provider: str
    cloud_model: str
    agent_model: str
    temperature: float | None
    reasoning: bool


# [HELPERS]
###############################################################################
def extract_text(result: Any) -> str:
    if isinstance(result, dict):
        for key in ("output", "result", "text", "message", "response"):
            val = result.get(key)
            if isinstance(val, str) and val.strip():
                return val
        try:
            formatted = json.dumps(result, ensure_ascii=False, indent=2)
        except Exception:  # noqa: BLE001
            return str(result)
        return f"```json\n{formatted}\n```"
    if isinstance(result, str):
        return result
    if isinstance(result, (list, tuple)):
        try:
            formatted = json.dumps(result, ensure_ascii=False, indent=2)
        except Exception:  # noqa: BLE001
            return str(result)
        return f"```json\n{formatted}\n```"
    try:
        formatted = json.dumps(result, ensure_ascii=False, indent=2)
    except Exception:  # noqa: BLE001
        return str(result)
    return f"```json\n{formatted}\n```"


# -----------------------------------------------------------------------------
def build_json_output(payload: dict[str, Any] | list[Any] | None) -> ComponentUpdate:
    if payload is None:
        return ComponentUpdate(value=None, visible=False)
    return ComponentUpdate(value=payload, visible=True)


# [LLM CLIENT CONTROLLERS]
###############################################################################
def resolve_cloud_selection(
    provider: str | None, cloud_model: str | None
) -> tuple[str, list[str], str | None]:
    normalized_provider = (provider or "").strip().lower()
    if normalized_provider not in CLOUD_MODEL_CHOICES:
        normalized_provider = next(iter(CLOUD_MODEL_CHOICES), "")
    models = CLOUD_MODEL_CHOICES.get(normalized_provider, [])
    normalized_model = (cloud_model or "").strip()
    if normalized_model not in models:
        normalized_model = models[0] if models else ""
    return normalized_provider, models, normalized_model or None

# -----------------------------------------------------------------------------
def get_runtime_settings() -> RuntimeSettings:
    return RuntimeSettings(
        use_cloud_services=ClientRuntimeConfig.is_cloud_enabled(),
        provider=ClientRuntimeConfig.get_llm_provider(),
        cloud_model=ClientRuntimeConfig.get_cloud_model(),
        agent_model=ClientRuntimeConfig.get_agent_model(),
        temperature=ClientRuntimeConfig.get_ollama_temperature(),
        reasoning=ClientRuntimeConfig.is_ollama_reasoning_enabled(),
    )

# -----------------------------------------------------------------------------
def reset_runtime_settings() -> RuntimeSettings:
    ClientRuntimeConfig.reset_defaults()
    return get_runtime_settings()

# -----------------------------------------------------------------------------
def apply_runtime_settings(settings: RuntimeSettings) -> RuntimeSettings:
    ClientRuntimeConfig.set_use_cloud_services(settings.use_cloud_services)
    provider = ClientRuntimeConfig.set_llm_provider(settings.provider)
    ClientRuntimeConfig.set_cloud_model(settings.cloud_model)
    agent_model = ClientRuntimeConfig.set_agent_model(settings.agent_model)

    temperature = ClientRuntimeConfig.set_ollama_temperature(settings.temperature)
    reasoning = ClientRuntimeConfig.set_ollama_reasoning(settings.reasoning)
    return RuntimeSettings(
        use_cloud_services=ClientRuntimeConfig.is_cloud_enabled(),
        provider=provider,
        cloud_model=ClientRuntimeConfig.get_cloud_model(),
        agent_model=agent_model,
        temperature=temperature,
        reasoning=reasoning,
    )

# -----------------------------------------------------------------------------
def toggle_cloud_services(
    enabled: bool, *, provider: str | None, cloud_model: str | None
) -> dict[str, ComponentUpdate]:
    normalized_provider, models, normalized_model = resolve_cloud_selection(
        provider, cloud_model
    )
    provider_update = ComponentUpdate(value=normalized_provider, enabled=enabled)
    model_update = ComponentUpdate(
        value=normalized_model,
        options=models,
        enabled=enabled,
    )
    button_update = ComponentUpdate(enabled=not enabled)
    temperature_update = ComponentUpdate(enabled=not enabled)
    reasoning_update = ComponentUpdate(enabled=not enabled)
    clinical_update = ComponentUpdate(enabled=not enabled)

    return {
        "provider": provider_update,
        "model": model_update,
        "button": button_update,
        "temperature": temperature_update,
        "reasoning": reasoning_update,
        "clinical": clinical_update,
    }

# -----------------------------------------------------------------------------
def sync_cloud_model_options(
    provider: str | None, current_model: str | None
) -> tuple[str, ComponentUpdate]:
    normalized_provider, models, normalized_model = resolve_cloud_selection(
        provider, current_model
    )
    model_update = ComponentUpdate(value=normalized_model, options=models)
    return normalized_provider, model_update


# [SEARCH PANELS]
###############################################################################
def set_coordinates_as_input(use_coordinates: bool) -> dict[str, ComponentUpdate]:
    if use_coordinates:
        return {
            "country": ComponentUpdate(value=None, enabled=False),
            "city": ComponentUpdate(value="", enabled=False),
            "address": ComponentUpdate(value="", enabled=False),
            "latitude": ComponentUpdate(value=None, enabled=True),
            "longitude": ComponentUpdate(value=None, enabled=True),
        }

    return {
        "country": ComponentUpdate(enabled=True),
        "city": ComponentUpdate(enabled=True),
        "address": ComponentUpdate(enabled=True),
        "latitude": ComponentUpdate(value=None, enabled=False),
        "longitude": ComponentUpdate(value=None, enabled=False),
    }


###############################################################################
# trigger function to start the location based search on button click
###############################################################################
async def trigger_search_maps(
    url: str, payload: dict[str, Any] | None = None
) -> tuple[dict[str, Any] | None, str]:
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload)
        response.raise_for_status()
    except httpx.RequestError as exc:
        return None, f"[ERROR] Unable to reach map service: {exc}"
    except httpx.HTTPStatusError as exc:
        detail = extract_error_detail(exc.response)
        return None, f"[ERROR] Map service error {exc.response.status_code}: {detail}"

    try:
        data = response.json()
    except json.JSONDecodeError as exc:
        return None, f"[ERROR] Invalid response received from map service: {exc}"

    if not isinstance(data, dict):
        return None, "[ERROR] Map service returned an unexpected payload."

    status_message = extract_status_message(data)
    formatted_status = f"Endpoint: {GEO_SEARCH_URL}\nStatus: {status_message.strip()}"
    return data, formatted_status

# -----------------------------------------------------------------------------
def extract_error_detail(response: httpx.Response) -> str:
    try:
        data = response.json()
    except json.JSONDecodeError:
        return response.text.strip() or "Unexpected error"

    if isinstance(data, dict):
        detail = data.get("detail") or data.get("message")
        if isinstance(detail, str) and detail.strip():
            return detail.strip()
    return "Unexpected error"

# -----------------------------------------------------------------------------
def extract_status_message(data: dict[str, Any]) -> str:
    for key in ("status_message", "message", "detail", "status"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "Map search request submitted."

# -----------------------------------------------------------------------------
async def submit_location_search(
    filter_val: Any,
    country: str | None,
    city: str | None,
    address: str | None,
    use_coordinates: bool,
    latitude: Any,
    longitude: Any,
    date: str | None,
) -> tuple[dict[str, Any] | None, str]:
    cleaned_payload = sanitize_search_payload(
        filter_val=filter_val,
        country=country,
        city=city,
        address=address,
        use_coordinates=use_coordinates,
        latitude=latitude,
        longitude=longitude,
        date=date,
    )

    url = f"{API_BASE_URL}{GEO_SEARCH_URL}"
    data, message = await trigger_search_maps(url, cleaned_payload)
    normalized_message = (message or "").strip()
    return data, normalized_message
