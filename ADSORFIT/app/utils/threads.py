from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd

from ADSORFIT.app.logger import logger
from ADSORFIT.app.utils.services.processing import (
    AdsorptionDataProcessor,
    DatasetAdapter,
)
from ADSORFIT.app.utils.repository.serializer import DataSerializer
from ADSORFIT.app.utils.services.fitting import ModelSolver


###############################################################################
class FittingWorker:
    def __init__(self) -> None:
        self.serializer = DataSerializer()
        self.solver = ModelSolver()
        self.adapter = DatasetAdapter()

    #-------------------------------------------------------------------------------
    async def run_job(
        self,
        dataset_payload: dict[str, Any],
        configuration: dict[str, dict[str, dict[str, float]]],
        max_iterations: int,
        save_best: bool,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        return await asyncio.to_thread(
            self.execute,
            dataset_payload,
            configuration,
            max_iterations,
            save_best,
            progress_callback,
        )

    #-------------------------------------------------------------------------------
    def execute(
        self,
        dataset_payload: dict[str, Any],
        configuration: dict[str, dict[str, dict[str, float]]],
        max_iterations: int,
        save_best: bool,
        progress_callback: Callable[[int, int], None] | None,
    ) -> dict[str, Any]:
        dataframe = self.build_dataframe(dataset_payload)
        if dataframe.empty:
            raise ValueError("Uploaded dataset is empty.")

        logger.info("Saving raw dataset with %s rows", dataframe.shape[0])
        self.serializer.save_raw_dataset(dataframe)

        processor = AdsorptionDataProcessor(dataframe)
        processed, detected_columns, stats = processor.preprocess(detect_columns=True)

        logger.info("Processed dataset contains %s experiments", processed.shape[0])
        serializable_processed = self.stringify_sequences(processed)
        self.serializer.save_processed_dataset(serializable_processed)

        logger.debug("Detected dataset statistics:\n%s", stats)

        if processed.empty:
            raise ValueError("No valid experiments found after preprocessing the dataset.")

        model_configuration = self.normalize_configuration(configuration)
        logger.debug("Running solver with configuration: %s", model_configuration)

        results = self.solver.bulk_data_fitting(
            processed,
            model_configuration,
            detected_columns.pressure,
            detected_columns.uptake,
            max_iterations,
            progress_callback=progress_callback,
        )

        combined = self.adapter.combine_results(results, processed)
        self.serializer.save_fitting_results(combined)

        best_frame = None
        if save_best:
            best_frame = self.adapter.compute_best_models(combined)
            self.serializer.save_best_fit(best_frame)

        experiment_count = int(processed.shape[0])
        response: dict[str, Any] = {
            "status": "success",
            "processed_rows": experiment_count,
            "models": sorted(model_configuration.keys()),
            "best_model_saved": bool(save_best),
        }

        if best_frame is not None:
            response["best_model_preview"] = self.build_preview(best_frame)

        summary_lines = [
            "[INFO] ADSORFIT fitting completed.",
            f"Experiments processed: {experiment_count}",
        ]
        if save_best:
            summary_lines.append("Best model selection stored in database.")
        response["summary"] = "\n".join(summary_lines)

        return response

    #-------------------------------------------------------------------------------
    def build_dataframe(self, payload: dict[str, Any]) -> pd.DataFrame:
        records = payload.get("records")
        columns = payload.get("columns")
        if isinstance(records, list):
            dataframe = pd.DataFrame.from_records(records, columns=columns)
        else:
            dataframe = pd.DataFrame()
        return dataframe

    #-------------------------------------------------------------------------------
    def normalize_configuration(
        self, configuration: dict[str, dict[str, dict[str, float]]]
    ) -> dict[str, dict[str, dict[str, float]]]:
        normalized: dict[str, dict[str, dict[str, float]]] = {}
        for model_name, config in configuration.items():
            min_values = config.get("min", {})
            max_values = config.get("max", {})
            initial_values = config.get("initial", {})
            normalized_entry: dict[str, dict[str, float]] = {
                "min": {},
                "max": {},
                "initial": {},
            }
            for parameter, lower in min_values.items():
                normalized_entry["min"][parameter] = float(lower)
            for parameter, upper in max_values.items():
                normalized_entry["max"][parameter] = float(upper)
            for parameter, init in initial_values.items():
                normalized_entry["initial"][parameter] = float(init)
            normalized[model_name] = normalized_entry
        return normalized

    #-------------------------------------------------------------------------------
    def stringify_sequences(self, dataset: pd.DataFrame) -> pd.DataFrame:
        converted = dataset.copy()
        for column in converted.columns:
            if converted[column].apply(lambda value: isinstance(value, (list, tuple))).any():
                converted[column] = converted[column].apply(
                    lambda value: json.dumps(value) if isinstance(value, (list, tuple)) else value
                )
        return converted

    #-------------------------------------------------------------------------------
    def build_preview(self, dataset: pd.DataFrame) -> list[dict[str, Any]]:
        preview_columns = [column for column in dataset.columns if column.endswith("LSS")]
        preview_columns.extend([
            column
            for column in dataset.columns
            if column in {"experiment", "best model", "worst model"}
        ])
        trimmed = dataset.loc[:, dict.fromkeys(preview_columns).keys()]
        limited = trimmed.head(5)
        limited = limited.replace({np.nan: None})
        return limited.to_dict(orient="records")
