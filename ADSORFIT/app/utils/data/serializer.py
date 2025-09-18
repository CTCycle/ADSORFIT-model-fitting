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
        database.save_into_database(dataset, "ADSORPTION_DATA")

    # -------------------------------------------------------------------------
    def load_raw_dataset(self) -> pd.DataFrame:
        return database.load_from_database("ADSORPTION_DATA")

    # -------------------------------------------------------------------------
    def save_processed_dataset(self, dataset: pd.DataFrame) -> None:
        database.save_into_database(dataset, "ADSORPTION_PROCESSED_DATA")

    # -------------------------------------------------------------------------
    def load_processed_dataset(self) -> pd.DataFrame:
        encoded = database.load_from_database("ADSORPTION_PROCESSED_DATA")
        return encoded

    # -------------------------------------------------------------------------
    def save_fitting_results(self, dataset: pd.DataFrame) -> None:
        database.save_into_database(dataset, "ADSORPTION_FITTING_RESULTS")

    # -------------------------------------------------------------------------
    def load_fitting_results(self) -> pd.DataFrame:
        return database.load_from_database("ADSORPTION_FITTING_RESULTS")

    # -------------------------------------------------------------------------
    def save_best_fit(self, dataset: pd.DataFrame) -> None:
        database.save_into_database(dataset, "ADSORPTION_BEST_FIT")

    # -------------------------------------------------------------------------
    def load_best_fit(self) -> pd.DataFrame:
        return database.load_from_database("ADSORPTION_BEST_FIT")

    