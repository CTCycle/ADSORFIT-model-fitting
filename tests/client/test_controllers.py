from __future__ import annotations

import io
import os
import sys
from dataclasses import dataclass
from typing import Any

import pytest

sys.path.append(os.path.abspath("."))

from ADSORFIT.app.client import controllers

try:
    from nicegui.events import UploadEventArguments
except ModuleNotFoundError:  # pragma: no cover
    UploadEventArguments = None  # type: ignore


@dataclass
class DummyUploadFile:
    name: str
    content_type: str
    data: bytes

    async def read(self) -> bytes:
        return self.data


@pytest.mark.skipif(UploadEventArguments is None, reason="NiceGUI is not available")
def test_extract_file_payload_handles_new_upload_event() -> None:
    event = UploadEventArguments(sender=object(), client=object(), file=DummyUploadFile("data.csv", "text/csv", b"alpha,beta"))
    result, filename = controllers.extract_file_payload(event)
    assert result == b"alpha,beta"
    assert filename == "data.csv"


def test_extract_file_payload_handles_legacy_upload_event(monkeypatch: pytest.MonkeyPatch) -> None:
    class LegacyUploadEvent:
        def __init__(self) -> None:
            self.content = io.BytesIO(b"legacy")
            self.name = "folder/legacy.csv"

    monkeypatch.setattr(controllers, "UploadEventArguments", LegacyUploadEvent)

    result, filename = controllers.extract_file_payload(LegacyUploadEvent())

    assert result == b"legacy"
    assert filename == "legacy.csv"


def test_load_dataset_success(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"data": b"values", "orig_name": "dataset.csv"}

    def fake_post_file(route: str, file_bytes: bytes, filename: str | None) -> tuple[bool, dict[str, Any] | None, str]:
        assert route == "datasets/load"
        assert file_bytes == b"values"
        assert filename == "dataset.csv"
        return True, {"status": "success", "dataset": {"columns": ["a"], "records": [[1]]}, "summary": "loaded"}, ""

    monkeypatch.setattr(controllers, "post_file", fake_post_file)

    dataset, message = controllers.load_dataset(payload)
    assert dataset == {"columns": ["a"], "records": [[1]]}
    assert message == "loaded"


def test_load_dataset_handles_backend_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"data": b"values", "orig_name": "dataset.csv"}

    def fake_post_file(route: str, file_bytes: bytes, filename: str | None) -> tuple[bool, dict[str, Any] | None, str]:
        return False, None, "backend unavailable"

    monkeypatch.setattr(controllers, "post_file", fake_post_file)

    dataset, message = controllers.load_dataset(payload)
    assert dataset is None
    assert message == "[ERROR] backend unavailable"


def test_load_dataset_handles_invalid_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"data": b"values", "orig_name": "dataset.csv"}

    def fake_post_file(route: str, file_bytes: bytes, filename: str | None) -> tuple[bool, dict[str, Any] | None, str]:
        return True, {"status": "success", "dataset": "invalid", "summary": None}, ""

    monkeypatch.setattr(controllers, "post_file", fake_post_file)

    dataset, message = controllers.load_dataset(payload)
    assert dataset is None
    assert message == "[ERROR] Backend returned an invalid dataset payload."
