from __future__ import annotations

import os
from collections.abc import Callable
from typing import Protocol

import pandas as pd

from ADSORFIT.src.packages.configurations import DatabaseSettings, configurations
from ADSORFIT.src.packages.logger import logger
from ADSORFIT.src.packages.singleton import singleton
from ADSORFIT.src.packages.utils.repository.sqlite import SQLiteRepository


###############################################################################
class DatabaseBackend(Protocol):
    db_path: str | None

    # -------------------------------------------------------------------------
    def initialize_database(self) -> None: ...

    # -------------------------------------------------------------------------
    def load_from_database(self, table_name: str) -> pd.DataFrame: ...

    # -------------------------------------------------------------------------
    def save_into_database(self, df: pd.DataFrame, table_name: str) -> None: ...

    # -------------------------------------------------------------------------
    def upsert_into_database(self, df: pd.DataFrame, table_name: str) -> None: ...

    # -------------------------------------------------------------------------
    def count_rows(self, table_name: str) -> int: ...


BackendFactory = Callable[[DatabaseSettings], DatabaseBackend]


# -----------------------------------------------------------------------------
def build_sqlite_backend(settings: DatabaseSettings) -> DatabaseBackend:
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
            raise RuntimeError(
                f"Unsupported database backend requested: {backend_name}"
            )
        logger.info("Initializing %s database backend", key)
        factory = BACKEND_FACTORIES[key]
        return factory(self.settings)

    # -------------------------------------------------------------------------
    @property
    def db_path(self) -> str | None:
        return getattr(self.backend, "db_path", None)

    # -------------------------------------------------------------------------
    def initialize_database(self) -> None:
        self.server.initialize_database()

    # -------------------------------------------------------------------------
    def requires_sqlite_initialization(self) -> bool:
        if self.settings.selected_database != "sqlite":
            return False
        if not self.db_path:
            return False
        return not os.path.exists(self.db_path)

    # -------------------------------------------------------------------------
    def load_from_database(self, table_name: str) -> pd.DataFrame:
        return self.server.load_from_database(table_name)

    # -------------------------------------------------------------------------
    def save_into_database(self, df: pd.DataFrame, table_name: str) -> None:
        self.server.save_into_database(df, table_name)

    # -------------------------------------------------------------------------
    def upsert_into_database(self, df: pd.DataFrame, table_name: str) -> None:
        self.server.upsert_into_database(df, table_name)

    # -------------------------------------------------------------------------
    def count_rows(self, table_name: str) -> int:
        return self.server.count_rows(table_name)


###############################################################################
database = ADSORFITDatabase()
