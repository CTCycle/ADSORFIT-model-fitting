from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

import pandas as pd

from ADSORFIT.src.packages.configurations import DatabaseSettings, configurations
from ADSORFIT.src.packages.logger import logger
from ADSORFIT.src.packages.singleton import singleton


class DatabaseBackend(Protocol):
    db_path: str | None

    # -------------------------------------------------------------------------
    def initialize_database(self) -> None:
        ...

    # -------------------------------------------------------------------------
    def load_from_database(self, table_name: str) -> pd.DataFrame:
        ...

    # -------------------------------------------------------------------------
    def save_into_database(self, df: pd.DataFrame, table_name: str) -> None:
        ...

    # -------------------------------------------------------------------------
    def upsert_into_database(self, df: pd.DataFrame, table_name: str) -> None:
        ...

    # -------------------------------------------------------------------------
    def export_all_tables_as_csv(
        self, export_dir: str, chunksize: int | None = None
    ) -> None:
        ...

    # -------------------------------------------------------------------------
    def delete_all_data(self) -> None:
        ...


BackendFactory = Callable[[DatabaseSettings], DatabaseBackend]


# -----------------------------------------------------------------------------
def build_sqlite_backend(settings: DatabaseSettings) -> DatabaseBackend:
    from ADSORFIT.src.packages.utils.repository.sqlite import SQLiteRepository

    return SQLiteRepository(settings)


BACKEND_FACTORIES: dict[str, BackendFactory] = {
    "sqlite": build_sqlite_backend,
}


###############################################################################
@singleton
class ADSORFITDatabase:
    def __init__(self) -> None:
        self.settings = configurations.database
        self.backend = self._build_backend(self.settings.selected_database)

    # -------------------------------------------------------------------------
    def _build_backend(self, backend_name: str) -> DatabaseBackend:
        key = backend_name.strip().lower()
        if key not in BACKEND_FACTORIES:
            raise RuntimeError(f"Unsupported database backend requested: {backend_name}")
        logger.info("Initializing %s database backend", key)
        factory = BACKEND_FACTORIES[key]
        return factory(self.settings)

    # -------------------------------------------------------------------------
    @property
    def db_path(self) -> str | None:
        return getattr(self.backend, "db_path", None)

    # -------------------------------------------------------------------------
    def initialize_database(self) -> None:
        self.backend.initialize_database()

    # -------------------------------------------------------------------------
    def load_from_database(self, table_name: str) -> pd.DataFrame:
        return self.backend.load_from_database(table_name)

    # -------------------------------------------------------------------------
    def save_into_database(self, df: pd.DataFrame, table_name: str) -> None:
        self.backend.save_into_database(df, table_name)

    # -------------------------------------------------------------------------
    def upsert_into_database(self, df: pd.DataFrame, table_name: str) -> None:
        self.backend.upsert_into_database(df, table_name)

    # -------------------------------------------------------------------------
    def export_all_tables_as_csv(
        self, export_dir: str, chunksize: int | None = None
    ) -> None:
        self.backend.export_all_tables_as_csv(export_dir, chunksize)

    # -------------------------------------------------------------------------
    def delete_all_data(self) -> None:
        self.backend.delete_all_data()


###############################################################################
database = ADSORFITDatabase()
