from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ADSORFIT.app.constants import DATASET_PATH
from ADSORFIT.app.logger import logger
from ADSORFIT.app.utils.data.processing import (
    AdsorptionDataProcessor,
    DatasetAdapter,
    DEFAULT_COLUMN_MAPPING,
)
from ADSORFIT.app.utils.data.serializer import DataSerializer
from ADSORFIT.app.utils.solver.fitting import ModelSolver
from ADSORFIT.app.configuration import Configuration
from ADSORFIT.app.client.workers import (
    ThreadWorker,
    check_thread_status,
    update_progress_callback,
)


###############################################################################
class DatasetEvents:
    def __init__(self, configuration: dict[str, Any]) -> None:
        self.configuration = configuration
        self.serializer = DataSerializer()

    # -------------------------------------------------------------------------
    def update_configuration(self, configuration: dict[str, Any]) -> None:
        self.configuration = configuration

    # -------------------------------------------------------------------------
    def load_dataset(
        self,
        dataset_path: str | None = None,
        detect_columns: bool | None = None,
        progress_callback: Any | None = None,
        worker: ThreadWorker | None = None,
    ) -> dict[str, Any]:
        check_thread_status(worker)
        config = self.configuration
        target_path = Path(dataset_path or config.get("dataset_path", DATASET_PATH))
        detect = detect_columns if detect_columns is not None else config.get("detect_cols", True)

        dataset = pd.read_csv(target_path, sep=None, engine="python")
        update_progress_callback(1, 3, progress_callback)
        check_thread_status(worker)

        processor = AdsorptionDataProcessor(dataset)
        processed, columns, stats = processor.preprocess(detect)

        self.serializer.save_raw_dataset(dataset)
        self.serializer.save_processed_dataset(processed)

        update_progress_callback(3, 3, progress_callback)
        logger.info("Dataset %s loaded with %d experiments", target_path.name, processed.shape[0])
        return {
            "path": str(target_path),
            "stats": stats,
            "columns": columns.as_dict(),
            "detect_cols": detect,
        }

    # -------------------------------------------------------------------------
    def export_database(self, target_dir: Path) -> Path:
        from ADSORFIT.app.utils.data.database import database

        database.export_all_tables_as_csv(str(target_dir))
        return target_dir

    # -------------------------------------------------------------------------
    def clear_database(self) -> None:
        from ADSORFIT.app.utils.data.database import database

        database.delete_all_data()


###############################################################################
class FittingEvents:
    LANGMUIR_KEY = "select_langmuir"
    SIPS_KEY = "select_sips"
    FREUNDLICH_KEY = "select_freundlich"
    TEMKIN_KEY = "select_temkin"

    MODEL_DEFAULTS = {
        "LANGMUIR": {
            "initial": {"K": 0.000001, "qsat": 1.0},
            "min": {"K": 0.0, "qsat": 0.0},
            "max": {"K": 100.0, "qsat": 100.0},
        },
        "SIPS": {
            "initial": {"K": 0.000001, "qsat": 1.0, "N": 1.0},
            "min": {"K": 0.0, "qsat": 0.0, "N": 0.0},
            "max": {"K": 100.0, "qsat": 100.0, "N": 50.0},
        },
        "FREUNDLICH": {
            "initial": {"K": 0.000001, "qsat": 1.0},
            "min": {"K": 0.0, "qsat": 0.0},
            "max": {"K": 100.0, "qsat": 100.0},
        },
        "TEMKIN": {
            "initial": {"K": 0.000001, "B": 1.0},
            "min": {"K": 0.0, "B": 0.0},
            "max": {"K": 100.0, "B": 100.0},
        },
    }

    def __init__(self, configuration: dict[str, Any]) -> None:
        self.configuration = configuration
        self.serializer = DataSerializer()
        self.solver = ModelSolver()
        self.adapter = DatasetAdapter()

    # -------------------------------------------------------------------------
    def update_configuration(self, configuration: dict[str, Any]) -> None:
        self.configuration = configuration

    # -------------------------------------------------------------------------
    def _build_model_configuration(self) -> dict[str, Any]:
        config = self.configuration
        model_configuration: dict[str, Any] = {}

        def compute_bounds(key_prefix: str, defaults: dict[str, Any]) -> dict[str, Any]:
            current = defaults.copy()
            initial = current["initial"].copy()
            minimum = current["min"].copy()
            maximum = current["max"].copy()
            for param in minimum:
                low_key = f"min_{key_prefix}_{param.lower()}"
                high_key = f"max_{key_prefix}_{param.lower()}"
                if low_key in config:
                    minimum[param] = config[low_key]
                if high_key in config:
                    maximum[param] = config[high_key]
                initial[param] = (minimum[param] + maximum[param]) / 2
            return {"initial": initial, "min": minimum, "max": maximum}

        selections = {
            "LANGMUIR": (self.LANGMUIR_KEY, "lang", self.MODEL_DEFAULTS["LANGMUIR"]),
            "SIPS": (self.SIPS_KEY, "sips", self.MODEL_DEFAULTS["SIPS"]),
            "FREUNDLICH": (self.FREUNDLICH_KEY, "freundlich", self.MODEL_DEFAULTS["FREUNDLICH"]),
            "TEMKIN": (self.TEMKIN_KEY, "temkin", self.MODEL_DEFAULTS["TEMKIN"]),
        }

        for model_name, (flag_key, prefix, defaults) in selections.items():
            if config.get(flag_key, False):
                model_configuration[model_name] = compute_bounds(prefix, defaults)

        return model_configuration

    # -------------------------------------------------------------------------
    def run_fitting(
        self,
        progress_callback: Any | None = None,
        worker: ThreadWorker | None = None,
    ) -> dict[str, Any]:
        check_thread_status(worker)
        config = self.configuration
        model_config = self._build_model_configuration()

        if not model_config:
            raise ValueError("No adsorption models selected; enable at least one model.")

        processed = self.serializer.load_processed_dataset()
        if processed.empty:
            logger.info("No processed dataset found; reloading from disk")
            dataset_path = config.get("dataset_path", DATASET_PATH)
            dataset = pd.read_csv(dataset_path, sep=None, engine="python")
            processor = AdsorptionDataProcessor(dataset)
            processed, _, _ = processor.preprocess(config.get("detect_cols", True))
            self.serializer.save_processed_dataset(processed)

        pressure_col = config.get("pressure_column", DEFAULT_COLUMN_MAPPING["pressure"])
        uptake_col = config.get("uptake_column", DEFAULT_COLUMN_MAPPING["uptake"])
        max_iterations = int(config.get("max_iterations", 50000))

        def _progress(current: int, total: int) -> None:
            check_thread_status(worker)
            update_progress_callback(current, total, progress_callback)

        results = self.solver.bulk_data_fitting(
            processed,
            model_config,
            pressure_col,
            uptake_col,
            max_iterations,
            progress_callback=_progress,
        )

        combined = self.adapter.combine_results(results, processed)
        best = self.adapter.compute_best_models(combined)
        self.serializer.save_fitting_results(combined)
        self.serializer.save_best_fit(best)

        logger.info("Fitting completed for %d experiments", processed.shape[0])
        return {"results": combined, "best": best}
