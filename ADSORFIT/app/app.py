from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from nicegui import ui

from ADSORFIT.app.configurations import configurations
from ADSORFIT.app.api.endpoints.datasets import router as dataset_router
from ADSORFIT.app.api.endpoints.fitting import router as fit_router
from ADSORFIT.app.client.interface import create_interface
from ADSORFIT.app.logger import logger
from ADSORFIT.app.utils.repository.database import database


###############################################################################
# initialize the database if it has not been created
if not os.path.exists(database.db_path):
    logger.info("Database not found, creating instance and making all tables")
    database.initialize_database()
    logger.info("ADSORFIT database has been initialized successfully.")

app = FastAPI(
    title=configurations.ui.title,
    version="0.1.0",
    description="FastAPI backend",
)

app.include_router(dataset_router)
app.include_router(fit_router)

###############################################################################
create_interface()
ui_settings = configurations.ui
ui.run_with(
    app,
    mount_path=ui_settings.mount_path,
    title=ui_settings.title,
    show_welcome_message=ui_settings.show_welcome_message,
    reconnect_timeout=ui_settings.reconnect_timeout_seconds,
)

@app.get("/")
def redirect_to_ui() -> RedirectResponse:
    return RedirectResponse(url=ui_settings.redirect_path)
