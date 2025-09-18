from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ADSORFIT.app.configuration import Configuration
from ADSORFIT.app.constants import DATASET_PATH
from ADSORFIT.app.logger import logger
from ADSORFIT.app.utils.data.processing import (
    AdsorptionDataProcessor,
    DatasetAdapter,
    DEFAULT_COLUMN_MAPPING,
)
from ADSORFIT.app.utils.data.serializer import DataSerializer
from ADSORFIT.app.utils.solver.fitting import ModelSolver
from ADSORFIT.app.client.workers import (
    ThreadWorker,
    check_thread_status,
    update_progress_callback,
)


###############################################################################
class DatasetEvents:
    def __init__(self, configuration: Configuration) -> None:
        self.configuration = configuration
        self.serializer = DataSerializer()

    # -------------------------------------------------------------------------
    def load_dataset(
        self,
        dataset_path: str | None = None,
        detect_columns: bool | None = None,
        progress_callback: Any | None = None,
        worker: ThreadWorker | None = None,
    ) -> dict[str, Any]:
        check_thread_status(worker)
        config = self.configuration.get_configuration()
        target_path = Path(dataset_path or config.get("datasetPath", DATASET_PATH))
        detect = detect_columns if detect_columns is not None else config.get("detectCols", True)

        dataset = pd.read_csv(target_path, sep=None, engine="python")
        update_progress_callback(1, 3, progress_callback)
        check_thread_status(worker)

        processor = AdsorptionDataProcessor(dataset)
        processed, columns, stats = processor.preprocess(detect)

        self.serializer.save_raw_dataset(dataset)
        self.serializer.save_processed_dataset(processed)

        self.configuration.update_values(
            {
                "datasetPath": str(target_path),
                "detectCols": detect,
                "experimentColumn": columns.experiment,
                "temperatureColumn": columns.temperature,
                "pressureColumn": columns.pressure,
                "uptakeColumn": columns.uptake,
            }
        )

        update_progress_callback(3, 3, progress_callback)
        logger.info("Dataset %s loaded with %d experiments", target_path.name, processed.shape[0])
        return {
            "path": str(target_path),
            "stats": stats,
            "columns": columns.as_dict(),
            "processed": processed,
        }

    # -------------------------------------------------------------------------
    def export_database(self, target_dir: Path) -> Path:
        from ADSORFIT.app.utils.data.database import database

        database.export_tables(target_dir)
        return target_dir

    # -------------------------------------------------------------------------
    def clear_database(self) -> None:
        from ADSORFIT.app.utils.data.database import database

        database.delete_all_data()


###############################################################################
class FittingEvents:
    def __init__(self, configuration: Configuration) -> None:
        self.configuration = configuration
        self.serializer = DataSerializer()
        self.solver = ModelSolver()
        self.adapter = DatasetAdapter()

    # -------------------------------------------------------------------------
    def run_fitting(
        self,
        progress_callback: Any | None = None,
        worker: ThreadWorker | None = None,
    ) -> dict[str, Any]:
        check_thread_status(worker)
        config = self.configuration.get_configuration()
        model_config = self.configuration.get_model_configuration()
        if not model_config:
            raise ValueError("No adsorption models selected; enable at least one model.")

        processed = self.serializer.load_processed_dataset()
        if processed.empty:
            logger.info("No processed dataset found; reloading from disk")
            dataset_path = config.get("datasetPath", DATASET_PATH)
            dataset = pd.read_csv(dataset_path, sep=None, engine="python")
            processor = AdsorptionDataProcessor(dataset)
            processed, _, _ = processor.preprocess(config.get("detectCols", True))
            self.serializer.save_processed_dataset(processed)

        pressure_col = config.get("pressureColumn", DEFAULT_COLUMN_MAPPING["pressure"])
        uptake_col = config.get("uptakeColumn", DEFAULT_COLUMN_MAPPING["uptake"])
        max_iterations = int(config.get("maxIterations", 50000))

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
