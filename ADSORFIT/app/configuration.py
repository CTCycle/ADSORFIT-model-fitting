import json
import os
from typing import Any

from AEGIS.app.constants import SETUP_DIR, CONFIGURATION_PATH

CONFIGURATION_CACHE: dict[str, Any] | None = None
CONFIGURATION_FILE = os.path.join(SETUP_DIR, "configurations.json")

DEFAULT_CONFIGURATION: dict[str, Any] = {
    "threshold_iterations": 1000
}

###############################################################################
def load_configuration_file() -> dict[str, Any]:
    if os.path.exists(CONFIGURATION_FILE):
        try:
            with open(CONFIGURATION_FILE, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"Unable to load configuration from {CONFIGURATION_FILE}"
            ) from exc
    return json.loads(json.dumps(DEFAULT_CONFIGURATION))

# -----------------------------------------------------------------------------
def get_nested_value(data: dict[str, Any], *keys: str, default: Any | None = None) -> Any:
    current: Any = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

###############################################################################
CONFIGURATION_DATA = load_configuration_file()

# -----------------------------------------------------------------------------
def get_configuration() -> dict[str, Any]:
    return CONFIGURATION_DATA

# -----------------------------------------------------------------------------
def get_configuration_value(*keys: str, default: Any | None = None) -> Any:
    return get_nested_value(CONFIGURATION_DATA, *keys, default=default)

###############################################################################
THRESHOLD_ITERATIONS = list(get_configuration_value("threshold_iterations", default=[]))

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