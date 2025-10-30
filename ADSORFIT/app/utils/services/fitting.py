from __future__ import annotations

import inspect
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from ADSORFIT.app.logger import logger
from ADSORFIT.app.utils.services.models import AdsorptionModels


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
