from __future__ import annotations

import io
import os
from typing import Any

import pandas as pd


###############################################################################
class DatasetService:
    def __init__(self) -> None:
        self.allowed_extensions = {".csv", ".xls", ".xlsx"}

    #-------------------------------------------------------------------------------
    def load_from_bytes(self, payload: bytes, filename: str | None) -> tuple[dict[str, Any], str]:
        if not payload:
            raise ValueError("Uploaded dataset is empty.")

        dataframe = self.read_dataframe(payload, filename)
        serializable = dataframe.where(pd.notna(dataframe), None)
        dataset_payload: dict[str, Any] = {
            "columns": list(serializable.columns),
            "records": serializable.to_dict(orient="records"),
            "row_count": int(serializable.shape[0]),
        }
        summary = self.format_dataset_summary(dataframe)
        return dataset_payload, summary

    #-------------------------------------------------------------------------------
    def read_dataframe(self, payload: bytes, filename: str | None) -> pd.DataFrame:
        extension = ""
        if isinstance(filename, str):
            extension = os.path.splitext(filename)[1].lower()

        if extension and extension not in self.allowed_extensions:
            raise ValueError(f"Unsupported file type: {extension}")

        buffer = io.BytesIO(payload)

        if extension in {".xls", ".xlsx"}:
            buffer.seek(0)
            dataframe = pd.read_excel(buffer, sheet_name=0)
        else:
            buffer.seek(0)
            dataframe = pd.read_csv(buffer)

        if dataframe.empty:
            raise ValueError("Uploaded dataset is empty.")

        return dataframe

    #-------------------------------------------------------------------------------
    def format_dataset_summary(self, dataframe: pd.DataFrame) -> str:
        rows, columns = dataframe.shape
        total_nans = int(dataframe.isna().sum().sum())
        column_summaries: list[str] = []
        for column in dataframe.columns:
            dtype = dataframe[column].dtype
            missing = int(dataframe[column].isna().sum())
            column_summaries.append(
                f"- {column}: dtype={dtype}, missing={missing}"
            )

        summary_lines = [
            f"Rows: {rows}",
            f"Columns: {columns}",
            f"NaN cells: {total_nans}",
            "Column details:",
            *column_summaries,
        ]
        return "\n".join(summary_lines)
