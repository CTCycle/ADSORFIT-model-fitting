from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from ADSORFIT.app.constants import CONFIG_PATH, DATASET_PATH

DEFAULT_CONFIGURATION: dict[str, Any] = {
    "datasetPath": DATASET_PATH,
    "detectCols": True,
    "maxIterations": 50000,
    "selectLangmuir": False,
    "experimentColumn": "experiment",
    "temperatureColumn": "temperature [K]",
    "pressureColumn": "pressure [Pa]",
    "uptakeColumn": "uptake [mol/g]",
    "minLangK": 0.01,
    "maxLangK": 1.0,
    "minLangQSat": 0.01,
    "maxLangQSat": 10.0,
}


###############################################################################
class Configuration:
    def __init__(self) -> None:
        Path(CONFIG_PATH).mkdir(parents=True, exist_ok=True)
        self._configuration = deepcopy(DEFAULT_CONFIGURATION)

    # -------------------------------------------------------------------------
    def get_configuration(self) -> dict[str, Any]:
        return deepcopy(self._configuration)

    # -------------------------------------------------------------------------
    def update_value(self, key: str, value: Any) -> None:
        self._configuration[key] = value

    # -------------------------------------------------------------------------
    def update_values(self, values: dict[str, Any]) -> None:
        self._configuration.update(values)

    # -------------------------------------------------------------------------
    def save_configuration_to_json(self, name: str) -> Path:
        target = Path(CONFIG_PATH, f"{name}.json")
        with target.open("w", encoding="utf-8") as handle:
            json.dump(self._configuration, handle, indent=4)
        return target

    # -------------------------------------------------------------------------
    def load_configuration_from_json(self, name: str) -> dict[str, Any]:
        target = Path(CONFIG_PATH, name)
        with target.open(encoding="utf-8") as handle:
            data = json.load(handle)
        self._configuration = deepcopy(DEFAULT_CONFIGURATION)
        self._configuration.update(data)
        return self.get_configuration()

    # -------------------------------------------------------------------------
    def get_model_configuration(self) -> dict[str, Any]:
        models: dict[str, Any] = {}
        if self._configuration.get("selectLangmuir", False):
            min_k = self._configuration["minLangK"]
            max_k = self._configuration["maxLangK"]
            min_q = self._configuration["minLangQSat"]
            max_q = self._configuration["maxLangQSat"]
            models["LANGMUIR"] = {
                "initial": {
                    "K": (min_k + max_k) / 2,
                    "qsat": (min_q + max_q) / 2,
                },
                "min": {"K": min_k, "qsat": min_q},
                "max": {"K": max_k, "qsat": max_q},
            }
        return models
