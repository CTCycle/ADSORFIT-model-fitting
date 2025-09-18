from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import get_close_matches
from typing import Any

import numpy as np
import pandas as pd

from ADSORFIT.app.logger import logger

DEFAULT_COLUMN_MAPPING = {
    "experiment": "experiment",
    "temperature": "temperature [K]",
    "pressure": "pressure [Pa]",
    "uptake": "uptake [mol/g]",
}


###############################################################################
@dataclass
class DatasetColumns:
    experiment: str = DEFAULT_COLUMN_MAPPING["experiment"]
    temperature: str = DEFAULT_COLUMN_MAPPING["temperature"]
    pressure: str = DEFAULT_COLUMN_MAPPING["pressure"]
    uptake: str = DEFAULT_COLUMN_MAPPING["uptake"]

    # -------------------------------------------------------------------------
    def as_dict(self) -> dict[str, str]:
        return {
            "experiment": self.experiment,
            "temperature": self.temperature,
            "pressure": self.pressure,
            "uptake": self.uptake,
        }


###############################################################################
class AdsorptionDataProcessor:
    def __init__(self, dataset: pd.DataFrame) -> None:
        self.dataset = dataset.copy()
        self.columns = DatasetColumns()

    # -------------------------------------------------------------------------
    def preprocess(
        self, detect_columns: bool = True
    ) -> tuple[pd.DataFrame, DatasetColumns, str]:
        if self.dataset.empty:
            raise ValueError("Provided dataset is empty")

        if detect_columns:
            self._identify_columns()

        cleaned = self._drop_invalid_values(self.dataset)
        grouped = self._aggregate_by_experiment(cleaned)
        stats = self._build_statistics(cleaned, grouped)

        return grouped, self.columns, stats

    # -------------------------------------------------------------------------
    def _identify_columns(self) -> None:
        for attr, pattern in DEFAULT_COLUMN_MAPPING.items():
            matched_cols = [
                column
                for column in self.dataset.columns
                if re.search(pattern.split()[0], column, re.IGNORECASE)
            ]
            if matched_cols:
                setattr(self.columns, attr, matched_cols[0])
                continue
            close_matches = get_close_matches(
                pattern, list(self.dataset.columns), cutoff=0.6
            )
            if close_matches:
                setattr(self.columns, attr, close_matches[0])

    # -------------------------------------------------------------------------
    def _drop_invalid_values(self, dataset: pd.DataFrame) -> pd.DataFrame:
        cols = self.columns.as_dict()
        valid = dataset.dropna(subset=list(cols.values()))
        valid = valid[valid[cols["temperature"]].astype(float) > 0]
        valid = valid[valid[cols["pressure"]].astype(float) >= 0]
        valid = valid[valid[cols["uptake"]].astype(float) >= 0]
        return valid.reset_index(drop=True)

    # -------------------------------------------------------------------------
    def _aggregate_by_experiment(self, dataset: pd.DataFrame) -> pd.DataFrame:
        cols = self.columns.as_dict()
        aggregate = {
            cols["temperature"]: "first",
            cols["pressure"]: list,
            cols["uptake"]: list,
        }
        grouped = (
            dataset.groupby(cols["experiment"], as_index=False)
            .agg(aggregate)
            .rename(columns={cols["experiment"]: "experiment"})
        )
        grouped["measurement_count"] = grouped[cols["pressure"]].apply(len)
        grouped["min_pressure"] = grouped[cols["pressure"]].apply(min)
        grouped["max_pressure"] = grouped[cols["pressure"]].apply(max)
        grouped["min_uptake"] = grouped[cols["uptake"]].apply(min)
        grouped["max_uptake"] = grouped[cols["uptake"]].apply(max)
        return grouped

    # -------------------------------------------------------------------------
    def _build_statistics(
        self, cleaned: pd.DataFrame, grouped: pd.DataFrame
    ) -> str:
        total_measurements = cleaned.shape[0]
        total_experiments = grouped.shape[0]
        removed_nan = self.dataset.shape[0] - total_measurements
        avg_measurements = (
            total_measurements / total_experiments if total_experiments else 0
        )

        stats = (
            "#### Dataset Statistics\n\n"
            f"**Experiments column:** {self.columns.experiment}\n"
            f"**Temperature column:** {self.columns.temperature}\n"
            f"**Pressure column:** {self.columns.pressure}\n"
            f"**Uptake column:** {self.columns.uptake}\n\n"
            f"**Number of NaN values removed:** {removed_nan}\n"
            f"**Number of experiments:** {total_experiments}\n"
            f"**Number of measurements:** {total_measurements}\n"
            f"**Average measurements per experiment:** {avg_measurements:.1f}"
        )
        return stats


###############################################################################
class DatasetAdapter:
    
    @staticmethod
    def combine_results(
        fitting_results: dict[str, list[dict[str, Any]]],
        dataset: pd.DataFrame,
    ) -> pd.DataFrame:
        if not fitting_results:
            logger.warning("No fitting results were provided")
            return dataset

        result_df = dataset.copy()
        for model_name, entries in fitting_results.items():
            if not entries:
                logger.info("Model %s produced no entries", model_name)
                continue
            params = entries[0].get("arguments", [])
            result_df[f"{model_name} LSS"] = [entry.get("LSS", np.nan) for entry in entries]
            for index, param in enumerate(params):
                result_df[f"{model_name} {param}"] = [
                    entry.get("optimal_params", [np.nan] * len(params))[index]
                    for entry in entries
                ]
                result_df[f"{model_name} {param} error"] = [
                    entry.get("errors", [np.nan] * len(params))[index]
                    for entry in entries
                ]
        return result_df

    # -------------------------------------------------------------------------
    @staticmethod
    def compute_best_models(dataset: pd.DataFrame) -> pd.DataFrame:
        lss_columns = [column for column in dataset.columns if column.endswith("LSS")]
        if not lss_columns:
            logger.info("No LSS columns found; best model computation skipped")
            return dataset

        best = dataset.copy()
        best["best model"] = dataset[lss_columns].idxmin(axis=1).str.replace(" LSS", "")
        best["worst model"] = dataset[lss_columns].idxmax(axis=1).str.replace(" LSS", "")
        return best
