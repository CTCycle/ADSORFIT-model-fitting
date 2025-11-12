from __future__ import annotations

from typing import Any

import pandas as pd

from ADSORFIT.src.packages.utils.repository.database import database


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
        encoded = self.convert_lists_to_strings(dataset)
        database.save_into_database(encoded, "ADSORPTION_FITTING_RESULTS")

    # -------------------------------------------------------------------------
    def load_fitting_results(self) -> pd.DataFrame:
        encoded = database.load_from_database("ADSORPTION_FITTING_RESULTS")
        if encoded.empty:
            return encoded
        return self.convert_strings_to_lists(encoded)

    # -------------------------------------------------------------------------
    def save_best_fit(self, dataset: pd.DataFrame) -> None:
        encoded = self.convert_lists_to_strings(dataset)
        database.save_into_database(encoded, "ADSORPTION_BEST_FIT")

    # -------------------------------------------------------------------------
    def load_best_fit(self) -> pd.DataFrame:
        encoded = database.load_from_database("ADSORPTION_BEST_FIT")
        if encoded.empty:
            return encoded
        return self.convert_strings_to_lists(encoded)

    # -------------------------------------------------------------------------
    def convert_list_to_string(self, value: Any) -> Any:
        if isinstance(value, (list, tuple)):
            parts: list[str] = []
            for element in value:
                if element is None:
                    continue
                text = str(element)
                if text:
                    parts.append(text)
            return ",".join(parts)
        return value

    # -------------------------------------------------------------------------
    def convert_string_to_list(self, value: Any) -> Any:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            parts = [segment.strip() for segment in stripped.split(",")]
            converted: list[float] = []
            for part in parts:
                if not part:
                    continue
                try:
                    converted.append(float(part))
                except ValueError:
                    return value
            return converted
        return value

    # -------------------------------------------------------------------------
    def convert_lists_to_strings(self, dataset: pd.DataFrame) -> pd.DataFrame:
        converted = dataset.copy()
        for column in converted.columns:
            converted[column] = converted[column].apply(self.convert_list_to_string)
        return converted

    # -------------------------------------------------------------------------
    def convert_strings_to_lists(self, dataset: pd.DataFrame) -> pd.DataFrame:
        converted = dataset.copy()
        for column in converted.columns:
            if converted[column].dtype == object:
                converted[column] = converted[column].apply(self.convert_string_to_list)
        return converted
