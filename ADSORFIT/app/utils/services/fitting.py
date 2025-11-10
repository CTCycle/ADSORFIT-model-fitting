from __future__ import annotations

import inspect
import json
from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from ADSORFIT.app.logger import logger
from ADSORFIT.app.utils.repository.serializer import DataSerializer
from ADSORFIT.app.utils.services.models import AdsorptionModels
from ADSORFIT.app.utils.services.processing import (
    AdsorptionDataProcessor,
    DatasetAdapter,
)


###############################################################################
class ModelSolver:
    def __init__(self) -> None:
        self.collection = AdsorptionModels()

    # -------------------------------------------------------------------------
    def single_experiment_fit(
        self,
        pressure: np.ndarray,
        uptake: np.ndarray,
        experiment_name: str,
        configuration: dict[str, Any],
        max_iterations: int,
    ) -> dict[str, dict[str, Any]]:
        """Fit every configured model against a single experiment dataset.

        Keyword arguments:
        pressure -- Pressure observations expressed as a NumPy array.
        uptake -- Measured uptakes corresponding to the pressure values.
        experiment_name -- Identifier of the current experiment, used for logging.
        configuration -- Per-model fitting configuration, including bounds and initial
        guesses.
        max_iterations -- Maximum number of solver evaluations allowed by ``curve_fit``.

        Return value:
        Dictionary keyed by model names containing optimal parameters, errors, and
        diagnostics.
        """
        results: dict[str, dict[str, Any]] = {}
        evaluations = max(1, int(max_iterations))
        for model_name, model_config in configuration.items():
            model = self.collection.get_model(model_name)
            signature = inspect.signature(model)
            param_names = list(signature.parameters.keys())[1:]
            # ``curve_fit`` expects ordered arrays for initial guess and bounds, so we
            # align configuration dictionaries with the model signature parameters.
            initial = [
                model_config.get("initial", {}).get(param, 1.0) for param in param_names
            ]
            lower = [
                model_config.get("min", {}).get(param, 0.0) for param in param_names
            ]
            upper = [
                model_config.get("max", {}).get(param, 100.0) for param in param_names
            ]

            try:
                optimal_params, covariance = curve_fit(
                    model,
                    pressure,
                    uptake,
                    p0=initial,
                    bounds=(lower, upper),
                    maxfev=evaluations,
                    check_finite=True,
                    absolute_sigma=False,
                )
                optimal_list = optimal_params.tolist()
                predicted = model(pressure, *optimal_params)
                # Least squares score is kept for ranking models within the pipeline.
                lss = float(np.sum((uptake - predicted) ** 2, dtype=np.float64))
                errors = (
                    np.sqrt(np.diag(covariance)).tolist()
                    if covariance is not None
                    else None
                )
                results[model_name] = {
                    "optimal_params": optimal_list,
                    "covariance": covariance.tolist()
                    if covariance is not None
                    else None,
                    "errors": errors
                    if errors is not None
                    else [np.nan] * len(param_names),
                    "LSS": lss,
                    "arguments": param_names,
                }
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "Failed to fit experiment %s with model %s",
                    experiment_name,
                    model_name,
                )
                results[model_name] = {
                    "optimal_params": [np.nan] * len(param_names),
                    "covariance": None,
                    "errors": [np.nan] * len(param_names),
                    "LSS": np.nan,
                    "arguments": param_names,
                    "exception": exc,
                }
        return results


###############################################################################
class FittingPipeline:
    def __init__(self) -> None:
        self.serializer = DataSerializer()
        self.solver = ModelSolver()
        self.adapter = DatasetAdapter()

    # -------------------------------------------------------------------------
    def run(
        self,
        dataset_payload: dict[str, Any],
        configuration: dict[str, dict[str, dict[str, float]]],
        max_iterations: int,
        save_best: bool,
        progress_callback: Callable[[int, int], None] | None = None,
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
            raise ValueError(
                "No valid experiments found after preprocessing the dataset."
            )

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

    # -------------------------------------------------------------------------
    def build_dataframe(self, payload: dict[str, Any]) -> pd.DataFrame:
        records = payload.get("records")
        columns = payload.get("columns")
        if isinstance(records, list):
            dataframe = pd.DataFrame.from_records(records, columns=columns)
        else:
            dataframe = pd.DataFrame()
        return dataframe

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    def stringify_sequences(self, dataset: pd.DataFrame) -> pd.DataFrame:
        converted = dataset.copy()
        for column in converted.columns:
            if (
                converted[column]
                .apply(lambda value: isinstance(value, (list, tuple)))
                .any()
            ):
                converted[column] = converted[column].apply(
                    lambda value: json.dumps(value)
                    if isinstance(value, (list, tuple))
                    else value
                )
        return converted

    # -------------------------------------------------------------------------
    def build_preview(self, dataset: pd.DataFrame) -> list[dict[str, Any]]:
        preview_columns = [
            column for column in dataset.columns if column.endswith("LSS")
        ]
        preview_columns.extend(
            [
                column
                for column in dataset.columns
                if column in {"experiment", "best model", "worst model"}
            ]
        )
        trimmed = dataset.loc[:, dict.fromkeys(preview_columns).keys()]
        limited = trimmed.head(5)
        limited = limited.replace({np.nan: None})
        return limited.to_dict(orient="records")

    # -------------------------------------------------------------------------
    def bulk_data_fitting(
        self,
        dataset: pd.DataFrame,
        configuration: dict[str, Any],
        pressure_col: str,
        uptake_col: str,
        max_iterations: int,
        progress_callback: Any | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """Iterate over the dataset and fit every experiment with the configured models.

        Keyword arguments:
        dataset -- Tabular collection of experiments with embedded pressure and uptake
        arrays.
        configuration -- Collection of model-specific fitting parameters and bounds.
        pressure_col -- Column storing the pressure measurements per experiment row.
        uptake_col -- Column storing the uptake measurements per experiment row.
        max_iterations -- Maximum number of solver evaluations passed to the single
        experiment fitter.
        progress_callback -- Optional callable receiving the processed experiment count
        and total experiments.

        Return value:
        Dictionary mapping model names to the list of fitting results produced for each
        experiment.
        """
        results: dict[str, list[dict[str, Any]]] = {
            model: [] for model in configuration.keys()
        }
        total_experiments = dataset.shape[0]
        for index, row in dataset.iterrows():
            pressure = np.asarray(row[pressure_col], dtype=np.float64)
            uptake = np.asarray(row[uptake_col], dtype=np.float64)
            experiment_name = row.get("experiment", f"experiment_{index}")
            # Reuse the single experiment solver to guarantee consistent fitting logic.
            experiment_results = self.single_experiment_fit(
                pressure,
                uptake,
                experiment_name,
                configuration,
                max_iterations,
            )
            for model_name, data in experiment_results.items():
                results[model_name].append(data)

            if progress_callback is not None:
                # Notify the caller after each experiment to enable progress bars or
                # streamed updates in the UI layer.
                progress_callback(index + 1, total_experiments)

        return results
