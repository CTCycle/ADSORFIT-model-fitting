from __future__ import annotations

import os

from nicegui import app

from ADSORFIT.app.api import api_router
from ADSORFIT.app.client.main import create_interface


###############################################################################
app.title = "ADSORFIT Backend"
app.version = "0.1.0"
app.description = "FastAPI application for ADSORFIT model fitting workflows."

reload_flag = os.getenv("RELOAD", "false").lower() == "true"
app.config.add_run_config(
    reload=reload_flag,
    title="ADSORFIT Model Fitting",
    viewport="width=device-width, initial-scale=1",
    favicon=None,
    dark=False,
    language="en-US",
    binding_refresh_interval=0.1,
    reconnect_timeout=3.0,
    tailwind=True,
    prod_js=True,
    show_welcome_message=False,
)

create_interface()
app.include_router(api_router)
