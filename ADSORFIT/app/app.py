from __future__ import annotations

from nicegui import app

from ADSORFIT.app.api import api_router
from ADSORFIT.app.client.main import create_interface


###############################################################################
app.title = "ADSORFIT Backend"
app.version = "0.1.0"
app.description = "FastAPI application for ADSORFIT model fitting workflows."

create_interface()
app.include_router(api_router)
