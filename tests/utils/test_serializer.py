from __future__ import annotations

import os
import tempfile

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ADSORFIT.app.utils.repository.database import database
from ADSORFIT.app.utils.repository.serializer import DataSerializer


@pytest.fixture
def temporary_database(monkeypatch: pytest.MonkeyPatch):
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "test.db")
        engine = create_engine(f"sqlite:///{path}", future=True)
        session_factory = sessionmaker(bind=engine, future=True)

        monkeypatch.setattr(database, "db_path", path, raising=False)
        monkeypatch.setattr(database, "engine", engine, raising=False)
        monkeypatch.setattr(database, "Session", session_factory, raising=False)

        yield engine

        engine.dispose()


def test_fitting_results_serialization_round_trip(temporary_database) -> None:
    serializer = DataSerializer()
    dataset = pd.DataFrame(
        {
            "experiment": ["A"],
            "temperature [K]": [300.0],
            "pressure [Pa]": [[1.0, 2.0, 3.0]],
            "uptake [mol/g]": [[0.1, 0.2, 0.3]],
        }
    )

    serializer.save_fitting_results(dataset)

    with temporary_database.connect() as conn:
        stored = pd.read_sql_table("ADSORPTION_FITTING_RESULTS", conn)

    assert stored.loc[0, "pressure [Pa]"] == "1.0,2.0,3.0"
    assert stored.loc[0, "uptake [mol/g]"] == "0.1,0.2,0.3"

    loaded = serializer.load_fitting_results()

    assert loaded.loc[0, "pressure [Pa]"] == [1.0, 2.0, 3.0]
    assert loaded.loc[0, "uptake [mol/g]"] == [0.1, 0.2, 0.3]
