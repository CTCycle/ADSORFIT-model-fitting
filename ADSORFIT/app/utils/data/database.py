from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from ADSORFIT.app.constants import DATA_PATH
from ADSORFIT.app.logger import logger
from ADSORFIT.app.utils.singleton import singleton


###############################################################################
@singleton
class ADSORFITDatabase:
    def __init__(self) -> None:
        Path(DATA_PATH).mkdir(parents=True, exist_ok=True)
        self.db_path = Path(DATA_PATH) / "ADSORFIT_database.db"
        self.engine: Engine = create_engine(f"sqlite:///{self.db_path}", future=True)

    # -------------------------------------------------------------------------
    def initialize_database(self) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("PRAGMA foreign_keys = ON"))

    # -------------------------------------------------------------------------
    def write_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        if_exists: str = "replace",
    ) -> None:
        if df.empty:
            logger.warning("Attempted to write empty dataframe to table %s", table_name)
            return
        with self.engine.begin() as conn:
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)

    # -------------------------------------------------------------------------
    def read_dataframe(self, table_name: str) -> pd.DataFrame:
        inspector = inspect(self.engine)
        if table_name not in inspector.get_table_names():
            logger.info("Table %s not found in ADSORFIT database", table_name)
            return pd.DataFrame()
        with self.engine.begin() as conn:
            return pd.read_sql_table(table_name, conn)

    # -------------------------------------------------------------------------
    def delete_table(self, table_name: str) -> None:
        inspector = inspect(self.engine)
        if table_name not in inspector.get_table_names():
            return
        with self.engine.begin() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))

    # -------------------------------------------------------------------------
    def delete_all_data(self) -> None:
        inspector = inspect(self.engine)
        for table in inspector.get_table_names():
            self.delete_table(table)

    # -------------------------------------------------------------------------
    def export_tables(self, export_dir: Path) -> None:
        export_dir.mkdir(parents=True, exist_ok=True)
        inspector = inspect(self.engine)
        with self.engine.begin() as conn:
            for table_name in inspector.get_table_names():
                df = pd.read_sql_table(table_name, conn)
                target = export_dir / f"{table_name}.csv"
                df.to_csv(target, index=False, encoding="utf-8")
        logger.info("Exported tables to %s", export_dir)


###############################################################################
database = ADSORFITDatabase()
