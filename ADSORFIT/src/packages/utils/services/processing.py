from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import get_close_matches
from typing import Any

import numpy as np
import pandas as pd

from ADSORFIT.src.packages.configurations import configurations
from ADSORFIT.src.packages.constants import DEFAULT_DATASET_COLUMN_MAPPING
from ADSORFIT.src.packages.logger import logger


###############################################################################
@dataclass
class DatasetColumns:
    experiment: str = DEFAULT_DATASET_COLUMN_MAPPING["experiment"]
    temperature: str = DEFAULT_DATASET_COLUMN_MAPPING["temperature"]
    pressure: str = DEFAULT_DATASET_COLUMN_MAPPING["pressure"]
    uptake: str = DEFAULT_DATASET_COLUMN_MAPPING["uptake"]

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
        """Clean the dataset, infer column mapping, and compute statistics.

        Keyword arguments:
        detect_columns -- Toggle automatic column detection based on heuristics.

        Return value:
        Tuple containing the aggregated dataset, resolved column names, and a
        statistics report.
        """
        if self.dataset.empty:
            raise ValueError("Provided dataset is empty")

        if detect_columns:
            # Column detection harmonizes arbitrary headers with the canonical schema
            # used throughout the pipeline before any filtering happens.
            self.identify_columns()

        cleaned = self.drop_invalid_values(self.dataset)
        grouped = self.aggregate_by_experiment(cleaned)
        stats = self.build_statistics(cleaned, grouped)

        return grouped, self.columns, stats

    # -------------------------------------------------------------------------
    def identify_columns(self) -> None:
        """Infer dataset column names that correspond to canonical adsorption fields.

        Keyword arguments:
        None.

        Return value:
        None.
        """
        cutoff = configurations.server.datasets.column_detection_cutoff
        for attr, pattern in DEFAULT_DATASET_COLUMN_MAPPING.items():
            matched_cols = [
                column
                for column in self.dataset.columns
                if re.search(pattern.split()[0], column, re.IGNORECASE)
            ]
            if matched_cols:
                # Prefer a direct regex match when a close equivalent column exists.
                setattr(self.columns, attr, matched_cols[0])
                continue
            close_matches = get_close_matches(
                pattern,
                list(self.dataset.columns),
                cutoff=cutoff,
            )
            if close_matches:
                # Fallback to fuzzy matching when naming deviates but is still similar.
                setattr(self.columns, attr, close_matches[0])

    # -------------------------------------------------------------------------
    def drop_invalid_values(self, dataset: pd.DataFrame) -> pd.DataFrame:
        """Remove rows containing invalid measurements for the detected adsorption columns.

        Keyword arguments:
        dataset -- Dataset that should be filtered using the resolved column mapping.

        Return value:
        DataFrame limited to valid rows with non-negative measurements and
        temperatures above zero.
        """
        cols = self.columns.as_dict()
        valid = dataset.dropna(subset=list(cols.values()))
        valid = valid[valid[cols["temperature"]].astype(float) > 0]
        valid = valid[valid[cols["pressure"]].astype(float) >= 0]
        valid = valid[valid[cols["uptake"]].astype(float) >= 0]
        return valid.reset_index(drop=True)

    # -------------------------------------------------------------------------
    def aggregate_by_experiment(self, dataset: pd.DataFrame) -> pd.DataFrame:
        """Group cleaned measurements by experiment and compute aggregate metrics.

        Keyword arguments:
        dataset -- Filtered dataset containing valid measurements.

        Return value:
        DataFrame with one row per experiment including pressure and uptake vectors and
        summary stats.
        """
        cols = self.columns.as_dict()
        aggregate = {
            cols["temperature"]: "first",
            cols["pressure"]: list,
            cols["uptake"]: list,
        }
        # ``groupby`` collects all measurements for each experiment so downstream
        # fitting can consume full pressure/uptake vectors.
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
    def build_statistics(self, cleaned: pd.DataFrame, grouped: pd.DataFrame) -> str:
        """Produce a Markdown report describing dataset sizes and cleansing outcomes.

        Keyword arguments:
        cleaned -- Dataset after removing invalid rows.
        grouped -- Aggregated dataset produced by :meth:`aggregate_by_experiment`.

        Return value:
        Markdown-formatted string summarizing per-column usage and high-level
        metrics.
        """
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
        """Append model fitting metrics and parameters to the processed dataset.

        Keyword arguments:
        fitting_results -- Mapping of model names to experiment-level fitting
        diagnostics.
        dataset -- Aggregated dataset to be enriched with fitting outputs.

        Return value:
        DataFrame with additional columns per model containing LSS and parameter
        estimates.
        """
        if not fitting_results:
            logger.warning("No fitting results were provided")
            return dataset

        result_df = dataset.copy()
        for model_name, entries in fitting_results.items():
            if not entries:
                logger.info("Model %s produced no entries", model_name)
                continue
            params = entries[0].get("arguments", [])
            # Columns for each model store experiment-level metrics aligned by order.
            result_df[f"{model_name} LSS"] = [
                entry.get("LSS", np.nan) for entry in entries
            ]
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
        """Determine the best and worst model per experiment based on least squares scores.

        Keyword arguments:
        dataset -- Dataset containing least squares score columns for each model.

        Return value:
        DataFrame extended with ``best model`` and ``worst model`` columns.
        """
        lss_columns = [column for column in dataset.columns if column.endswith("LSS")]
        if not lss_columns:
            logger.info("No LSS columns found; best model computation skipped")
            return dataset

        best = dataset.copy()
        # Minimum LSS identifies the best fitting model per experiment while the
        # maximum highlights underperforming fits for diagnostics.
        best["best model"] = dataset[lss_columns].idxmin(axis=1).str.replace(" LSS", "")
        best["worst model"] = (
            dataset[lss_columns].idxmax(axis=1).str.replace(" LSS", "")
        )
        return best
