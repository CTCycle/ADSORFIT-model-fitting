from __future__ import annotations

import os
from typing import Any

import pandas as pd
import sqlalchemy
from sqlalchemy import Column, Float, Integer, String, UniqueConstraint, create_engine
from sqlalchemy import inspect, text
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

from ADSORFIT.src.packages.configurations import configurations
from ADSORFIT.src.packages.constants import DATA_PATH
from ADSORFIT.src.packages.logger import logger
from ADSORFIT.src.packages.singleton import singleton


Base = declarative_base()


###############################################################################
class RouletteSeries(Base):
    __tablename__ = "ROULETTE_SERIES"
    id = Column(Integer, primary_key=True)
    extraction = Column(Integer)
    color = Column(String)
    color_code = Column(Integer)
    position = Column(Integer)
    __table_args__ = (UniqueConstraint("id"),)


###############################################################################
class PredictedGames(Base):
    __tablename__ = "PREDICTED_GAMES"
    id = Column(Integer, primary_key=True)
    checkpoint = Column(String)
    extraction = Column(Integer)
    predicted_action = Column(String)
    __table_args__ = (UniqueConstraint("id"),)


###############################################################################
@singleton
class ADSORFITDatabase:
    def __init__(self) -> None:
        self.db_path = os.path.join(DATA_PATH, "database.db")
        self.engine: Engine = sqlalchemy.create_engine(
            f"sqlite:///{self.db_path}", echo=False, future=True
        )

        self.Session = sessionmaker(bind=self.engine, future=True)
        self.insert_batch_size = configurations.database.insert_batch_size

    # -------------------------------------------------------------------------
    def initialize_database(self) -> None:
        with self.engine.begin():
            pass

    # -------------------------------------------------------------------------
    def get_table_class(self, table_name: str) -> Any:
        for cls in Base.__subclasses__():
            if hasattr(cls, "__tablename__") and cls.__tablename__ == table_name:
                return cls
        raise ValueError(f"No table class found for name {table_name}")

    # -------------------------------------------------------------------------
    def upsert_dataframe(self, df: pd.DataFrame, table_cls) -> None:
        table = table_cls.__table__
        session = self.Session()
        try:
            unique_cols = []
            for uc in table.constraints:
                if isinstance(uc, UniqueConstraint):
                    unique_cols = uc.columns.keys()
                    break
            if not unique_cols:
                raise ValueError(f"No unique constraint found for {table_cls.__name__}")

            # Batch insertions for speed
            records = df.to_dict(orient="records")
            for i in range(0, len(records), self.insert_batch_size):
                batch = records[i : i + self.insert_batch_size]
                stmt = insert(table).values(batch)
                # Columns to update on conflict
                update_cols = {
                    c: getattr(stmt.excluded, c)  # type: ignore
                    for c in batch[0]
                    if c not in unique_cols
                }
                stmt = stmt.on_conflict_do_update(
                    index_elements=unique_cols, set_=update_cols
                )
                session.execute(stmt)
                session.commit()
            session.commit()
        finally:
            session.close()

    # -------------------------------------------------------------------------
    def load_from_database(self, table_name: str) -> pd.DataFrame:
        with self.engine.connect() as conn:
            inspector = inspect(conn)
            if not inspector.has_table(table_name):
                logger.warning("Table %s does not exist", table_name)
                return pd.DataFrame()

            data = pd.read_sql_table(table_name, conn)

        return data

    # -------------------------------------------------------------------------
    def save_into_database(self, df: pd.DataFrame, table_name: str) -> None:
        with self.engine.begin() as conn:
            inspector = inspect(conn)
            if inspector.has_table(table_name):
                conn.execute(sqlalchemy.text(f'DELETE FROM "{table_name}"'))
            df.to_sql(table_name, conn, if_exists="append", index=False)

    # -------------------------------------------------------------------------
    def upsert_into_database(self, df: pd.DataFrame, table_name: str) -> None:
        table_cls = self.get_table_class(table_name)
        self.upsert_dataframe(df, table_cls)

    # -------------------------------------------------------------------------
    def export_all_tables_as_csv(
        self, export_dir: str, chunksize: int | None = None
    ) -> None:
        target = os.path.abspath(export_dir)
        os.makedirs(target, exist_ok=True)
        inspector = inspect(self.engine)
        with self.engine.connect() as conn:
            for table_name in inspector.get_table_names():
                query = sqlalchemy.text(f'SELECT * FROM "{table_name}"')
                csv_path = os.path.join(target, f"{table_name}.csv")
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
                            csv_path,
                            index=False,
                            encoding="utf-8",
                            sep=",",  # empty table
                        )
                else:
                    df = pd.read_sql(query, conn)
                    df.to_csv(csv_path, index=False, encoding="utf-8", sep=",")
        logger.info("All tables exported to CSV at %s", target)

    # -------------------------------------------------------------------------
    def delete_all_data(self) -> None:
        inspector = inspect(self.engine)
        with self.engine.begin() as conn:
            for table_name in inspector.get_table_names():
                conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))


###############################################################################
database = ADSORFITDatabase()
