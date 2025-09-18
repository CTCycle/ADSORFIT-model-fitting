from __future__ import annotations

import json
from typing import Any

import pandas as pd

from ADSORFIT.app.utils.data.database import database

RAW_DATA_TABLE = "ADSORPTION_DATA"
PROCESSED_DATA_TABLE = "ADSORPTION_PROCESSED_DATA"
FITTING_RESULTS_TABLE = "ADSORPTION_FITTING_RESULTS"
BEST_FIT_TABLE = "ADSORPTION_BEST_FIT"


###############################################################################
class DataSerializer:
    # -------------------------------------------------------------------------
    def save_raw_dataset(self, dataset: pd.DataFrame) -> None:
        database.write_dataframe(dataset, RAW_DATA_TABLE)

    # -------------------------------------------------------------------------
    def load_raw_dataset(self) -> pd.DataFrame:
        return database.read_dataframe(RAW_DATA_TABLE)

    # -------------------------------------------------------------------------
    def save_processed_dataset(self, dataset: pd.DataFrame) -> None:
        encoded = dataset.applymap(self._encode_lists)
        database.write_dataframe(encoded, PROCESSED_DATA_TABLE)

    # -------------------------------------------------------------------------
    def load_processed_dataset(self) -> pd.DataFrame:
        df = database.read_dataframe(PROCESSED_DATA_TABLE)
        return df.applymap(self._decode_lists)

    # -------------------------------------------------------------------------
    def save_fitting_results(self, dataset: pd.DataFrame) -> None:
        database.write_dataframe(dataset, FITTING_RESULTS_TABLE)

    # -------------------------------------------------------------------------
    def load_fitting_results(self) -> pd.DataFrame:
        return database.read_dataframe(FITTING_RESULTS_TABLE)

    # -------------------------------------------------------------------------
    def save_best_fit(self, dataset: pd.DataFrame) -> None:
        database.write_dataframe(dataset, BEST_FIT_TABLE)

    # -------------------------------------------------------------------------
    def load_best_fit(self) -> pd.DataFrame:
        return database.read_dataframe(BEST_FIT_TABLE)

    # -------------------------------------------------------------------------
    @staticmethod
    def _encode_lists(value: Any) -> Any:
        if isinstance(value, list):
            return json.dumps(value)
        return value

    # -------------------------------------------------------------------------
    @staticmethod
    def _decode_lists(value: Any) -> Any:
        if isinstance(value, str) and value.startswith("["):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value
