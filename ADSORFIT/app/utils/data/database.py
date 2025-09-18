from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import sqlalchemy
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

from ADSORFIT.app.constants import DATA_PATH
from ADSORFIT.app.logger import logger
from ADSORFIT.app.utils.singleton import singleton


###############################################################################
@singleton
class ADSORFITDatabase:
    def __init__(self) -> None:
        Path(DATA_PATH).mkdir(parents=True, exist_ok=True)
        self.db_path = Path(DATA_PATH) / "ADSORFIT_database.db"
        self.engine: Engine = sqlalchemy.create_engine(
            f"sqlite:///{self.db_path}", echo=False, future=True
        )

    # -------------------------------------------------------------------------
    def initialize_database(self) -> None:
        with self.engine.begin():
            pass

    # -------------------------------------------------------------------------
    def get_table_class(self, table_name: str) -> Any:
        raise ValueError("ADSORFIT tables are created dynamically; declarative classes are not defined")

    # -------------------------------------------------------------------------
    def _upsert_dataframe(self, df: pd.DataFrame, table_cls: Any, batch_size: int | None = None) -> None:
        raise NotImplementedError("Upsert by declarative class is not supported in ADSORFIT")

    # -------------------------------------------------------------------------
    def load_from_database(self, table_name: str) -> pd.DataFrame:
        inspector = inspect(self.engine)
        if table_name not in inspector.get_table_names():
            logger.info("Table %s not found in ADSORFIT database", table_name)
            return pd.DataFrame()
        with self.engine.connect() as conn:
            return pd.read_sql_table(table_name, conn)

    # -------------------------------------------------------------------------
    def save_into_database(self, df: pd.DataFrame, table_name: str) -> None:
        if df.empty:
            logger.warning("Attempted to save empty dataframe to %s", table_name)
            return
        with self.engine.begin() as conn:
            try:
                conn.execute(text(f'DELETE FROM "{table_name}"'))
            except OperationalError:
                pass
            df.to_sql(table_name, conn, if_exists="append", index=False)

    # -------------------------------------------------------------------------
    def upsert_into_database(self, df: pd.DataFrame, table_name: str) -> None:
        if df.empty:
            logger.warning("Attempted to upsert empty dataframe to %s", table_name)
            return
        with self.engine.begin() as conn:
            df.to_sql(table_name, conn, if_exists="append", index=False)

    # -------------------------------------------------------------------------
    def export_all_tables_as_csv(
        self, export_dir: str, chunksize: int | None = None
    ) -> None:
        target = Path(export_dir)
        target.mkdir(parents=True, exist_ok=True)
        inspector = inspect(self.engine)
        with self.engine.connect() as conn:
            for table_name in inspector.get_table_names():
                query = sqlalchemy.text(f'SELECT * FROM "{table_name}"')
                csv_path = target / f"{table_name}.csv"
                if chunksize:
                    first = True
                    for chunk in pd.read_sql(query, conn, chunksize=chunksize):
                        chunk.to_csv(
                            csv_path,
                            index=False,
                            header=first,
                            mode="w" if first else "a",
                            encoding="utf-8",
                            sep=",",
                        )
                        first = False
                    if first:
                        pd.DataFrame().to_csv(
                            csv_path, index=False, encoding="utf-8", sep=","  # empty table
                        )
                else:
                    df = pd.read_sql(query, conn)
                    df.to_csv(csv_path, index=False, encoding="utf-8", sep=",")
        logger.info("All tables exported to CSV at %s", target.resolve())

    # -------------------------------------------------------------------------
    def delete_all_data(self) -> None:
        inspector = inspect(self.engine)
        with self.engine.begin() as conn:
            for table_name in inspector.get_table_names():
                conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))


###############################################################################
database = ADSORFITDatabase()
