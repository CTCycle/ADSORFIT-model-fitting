from __future__ import annotations

from typing import Any

import numpy as np

from ADSORFIT.src.packages.constants import FITTING_MODEL_NAMES


###############################################################################
class AdsorptionModels:
    def __init__(self) -> None:
        self.model_names = list(FITTING_MODEL_NAMES)

    # -------------------------------------------------------------------------
    @staticmethod
    def langmuir(pressure: np.ndarray, k: float, qsat: float) -> np.ndarray:
        k_p = pressure * k
        return qsat * (k_p / (1 + k_p))

    # -------------------------------------------------------------------------
    @staticmethod
    def sips(
        pressure: np.ndarray, k: float, qsat: float, exponent: float
    ) -> np.ndarray:
        k_p = k * (pressure**exponent)
        return qsat * (k_p / (1 + k_p))

    # -------------------------------------------------------------------------
    @staticmethod
    def freundlich(pressure: np.ndarray, k: float, exponent: float) -> np.ndarray:
        return (pressure * k) ** (1 / exponent)

    # -------------------------------------------------------------------------
    @staticmethod
    def temkin(pressure: np.ndarray, k: float, beta: float) -> np.ndarray:
        return beta * np.log(k * pressure)

    # -------------------------------------------------------------------------
    def get_model(self, model_name: str) -> Any:
        models = {
            "LANGMUIR": self.langmuir,
            "SIPS": self.sips,
            "FREUNDLICH": self.freundlich,
            "TEMKIN": self.temkin,
        }
        try:
            return models[model_name.upper()]
        except KeyError as exc:
            raise ValueError(f"Model {model_name} is not supported") from exc
