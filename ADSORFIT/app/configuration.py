import json
import os
from typing import Any

from AEGIS.app.constants import SETUP_DIR, CONFIGURATION_PATH

CONFIGURATION_CACHE: dict[str, Any] | None = None
CONFIGURATION_FILE = os.path.join(SETUP_DIR, "configurations.json")

###############################################################################
def load_configuration_file() -> dict[str, Any] | None:
    if os.path.exists(CONFIGURATION_FILE):
        try:
            with open(CONFIGURATION_FILE, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"Unable to load configuration from {CONFIGURATION_FILE}"
            ) from exc
             

# -----------------------------------------------------------------------------
def get_nested_value(data: dict[str, Any], *keys: str, default: Any | None = None) -> Any:
    current: Any = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

# -----------------------------------------------------------------------------
CONFIGURATION_DATA = load_configuration_file()

def get_configuration_value(*keys: str, default: Any | None = None) -> Any:
    configuration = CONFIGURATION_DATA if CONFIGURATION_DATA is not None else {}
    return get_nested_value(configuration, *keys, default=default)


###############################################################################
THRESHOLD_ITERATIONS = get_configuration_value("threshold_iterations", default="")

