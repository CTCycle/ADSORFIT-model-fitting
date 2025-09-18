from __future__ import annotations

import pandas as pd

from TokenBenchy.app.utils.data.database import database


# [DATA SERIALIZATION]
###############################################################################
class DataSerializer:
    def __init__(self) -> None:
        pass

    # -------------------------------------------------------------------------
    def load_local_metrics(self) -> pd.DataFrame:
        # Local per-text, per-tokenizer stats
        return database.load_from_database("TOKENIZATION_LOCAL_STATS")
    # -------------------------------------------------------------------------
    def load_global_metrics(self) -> pd.DataFrame:
        return database.load_from_database("TOKENIZATION_GLOBAL_METRICS")

    # -------------------------------------------------------------------------
    def load_vocabularies(self) -> pd.DataFrame:
        return database.load_from_database("VOCABULARY")

    # -------------------------------------------------------------------------
    def load_text_dataset(self) -> pd.DataFrame:
        return database.load_from_database("TEXT_DATASET")

    # -------------------------------------------------------------------------
    def save_text_dataset(self, dataset: pd.DataFrame) -> None:
        database.save_into_database(dataset, "TEXT_DATASET")

    # -------------------------------------------------------------------------
    def save_dataset_statistics(self, dataset: pd.DataFrame) -> None:
        database.upsert_into_database(dataset, "TEXT_DATASET_STATISTICS")

    # -------------------------------------------------------------------------
    def save_vocabulary_tokens(self, dataset: pd.DataFrame) -> None:
        database.upsert_into_database(dataset, "VOCABULARY")

    # -------------------------------------------------------------------------
    def save_vocabulary_statistics(self, dataset: pd.DataFrame) -> None:
        database.save_into_database(dataset, "VOCABULARY_STATISTICS")

    # -------------------------------------------------------------------------
    def save_local_metrics(self, dataset: pd.DataFrame) -> None:
        database.save_into_database(dataset, "TOKENIZATION_LOCAL_STATS")

    # -------------------------------------------------------------------------
    def save_NSL_benchmark(self, dataset: pd.DataFrame) -> None:
        database.save_into_database(dataset, "NSL_RESULTS")

    # -------------------------------------------------------------------------
    def save_global_metrics(self, dataset: pd.DataFrame) -> None:
        database.upsert_into_database(dataset, "TOKENIZATION_GLOBAL_METRICS")


