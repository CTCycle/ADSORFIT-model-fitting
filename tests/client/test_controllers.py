from __future__ import annotations

import io
import os
import sys
from dataclasses import dataclass
from typing import Any

import pytest

sys.path.append(os.path.abspath("."))

from ADSORFIT.app.client import controllers


@dataclass
class DummyUploadFile:
    name: str
    content_type: str
    data: bytes

    async def read(self) -> bytes:
        return self.data


class DummyEvent:
    def __init__(self, file: DummyUploadFile) -> None:
        self.file = file


def test_extract_file_payload_handles_new_upload_event() -> None:
    controller = controllers.ClientController()
    event = DummyEvent(DummyUploadFile("data.csv", "text/csv", b"alpha,beta"))
    result, filename = controller.extract_file_payload(event)
    assert result == b"alpha,beta"
    assert filename == "data.csv"


def test_extract_file_payload_handles_legacy_upload_event() -> None:
    class LegacyUploadEvent:
        def __init__(self) -> None:
            self.content = io.BytesIO(b"legacy")
            self.name = "folder/legacy.csv"

    controller = controllers.ClientController()
    result, filename = controller.extract_file_payload(LegacyUploadEvent())

    assert result == b"legacy"
    assert filename == "legacy.csv"


def test_load_dataset_success(monkeypatch: pytest.MonkeyPatch) -> None:
    controller = controllers.ClientController()
    payload = {"data": b"values", "orig_name": "dataset.csv"}

    def fake_post_file(
        self: controllers.ClientController,
        route: str,
        file_bytes: bytes,
        filename: str | None,
    ) -> tuple[bool, dict[str, Any] | None, str]:
        assert route == "datasets/load"
        assert file_bytes == b"values"
        assert filename == "dataset.csv"
        return (
            True,
            {
                "status": "success",
                "dataset": {"columns": ["a"], "records": [[1]]},
                "summary": "loaded",
            },
            "",
        )

    monkeypatch.setattr(controllers.ClientController, "post_file", fake_post_file)

    dataset, message = controller.load_dataset(payload)
    assert dataset == {"columns": ["a"], "records": [[1]]}
    assert message == "loaded"


def test_load_dataset_handles_backend_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    controller = controllers.ClientController()
    payload = {"data": b"values", "orig_name": "dataset.csv"}

    def fake_post_file(
        self: controllers.ClientController,
        route: str,
        file_bytes: bytes,
        filename: str | None,
    ) -> tuple[bool, dict[str, Any] | None, str]:
        return False, None, "backend unavailable"

    monkeypatch.setattr(controllers.ClientController, "post_file", fake_post_file)

    dataset, message = controller.load_dataset(payload)
    assert dataset is None
    assert message == "[ERROR] backend unavailable"


def test_load_dataset_handles_invalid_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    controller = controllers.ClientController()
    payload = {"data": b"values", "orig_name": "dataset.csv"}

    def fake_post_file(
        self: controllers.ClientController,
        route: str,
        file_bytes: bytes,
        filename: str | None,
    ) -> tuple[bool, dict[str, Any] | None, str]:
        return True, {"status": "success", "dataset": "invalid", "summary": None}, ""

    monkeypatch.setattr(controllers.ClientController, "post_file", fake_post_file)

    dataset, message = controller.load_dataset(payload)
    assert dataset is None
    assert message == "[ERROR] Backend returned an invalid dataset payload."
