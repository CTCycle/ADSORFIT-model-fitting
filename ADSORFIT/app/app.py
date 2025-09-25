from __future__ import annotations

import gradio as gr
from fastapi import FastAPI

from ADSORFIT.app.api import api_router
from ADSORFIT.app.client.main import create_interface


###############################################################################
app = FastAPI(
    title="ADSORFIT Backend",
    version="0.1.0",
    description="FastAPI application for ADSORFIT model fitting workflows.",
)

ui_app = create_interface()
app.include_router(api_router)
app = gr.mount_gradio_app(app, ui_app, path="/ui")
