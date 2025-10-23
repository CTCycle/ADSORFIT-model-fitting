import json
import os
from typing import Any

from ADSORFIT.app.constants import CONFIG_PATH


###############################################################################
class Configuration:
    def __init__(self) -> None:
        self.configuration = {
            "detect_cols": True,
            "max_iterations": 50000,
            "select_langmuir": False,
            "select_sips": False,
            "select_freundlich": False,
            "select_temkin": False,
            "min_lang_k": 0.01,
            "max_lang_k": 1.0,
            "min_lang_qsat": 0.01,
            "max_lang_qsat": 10.0,
            "min_sips_k": 0.01,
            "max_sips_k": 1.0,
            "min_sips_qsat": 0.01,
            "max_sips_qsat": 10.0,
            "min_sips_n": 0.5,
            "max_sips_n": 5.0,
            "min_freundlich_k": 0.01,
            "max_freundlich_k": 1.0,
            "min_freundlich_qsat": 0.01,
            "max_freundlich_qsat": 10.0,
            "min_temkin_k": 0.01,
            "max_temkin_k": 1.0,
            "min_temkin_b": 0.01,
            "max_temkin_b": 10.0,
            "experiment_column": "experiment",
            "temperature_column": "temperature [K]",
            "pressure_column": "pressure [Pa]",
            "uptake_column": "uptake [mol/g]",
        }

    # -------------------------------------------------------------------------
    def get_configuration(self) -> dict[str, Any]:
        return self.configuration

    # -------------------------------------------------------------------------
    def update_value(self, key: str, value: Any) -> None:
        self.configuration[key] = value

    # -------------------------------------------------------------------------
    def save_configuration_to_json(self, name: str) -> None:
        full_path = os.path.join(CONFIG_PATH, f"{name}.json")
        with open(full_path, "w", encoding="utf-8") as handle:
            json.dump(self.configuration, handle, indent=4)

    # -------------------------------------------------------------------------
    def load_configuration_from_json(self, name: str) -> None:
        full_path = os.path.join(CONFIG_PATH, name)
        with open(full_path, encoding="utf-8") as handle:
            self.configuration = json.load(handle)
