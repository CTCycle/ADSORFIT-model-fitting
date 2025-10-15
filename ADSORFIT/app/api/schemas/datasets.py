from __future__ import annotations

from pydantic import BaseModel, Field

from ADSORFIT.app.api.schemas.fitting import DatasetPayload


###############################################################################
class DatasetLoadResponse(BaseModel):
    status: str = Field(default="success")
    summary: str
    dataset: DatasetPayload | None = None
