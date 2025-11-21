from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from ADSORFIT.src.packages.configurations import configurations
from ADSORFIT.src.server.endpoints.datasets import router as dataset_router
from ADSORFIT.src.server.endpoints.fitting import router as fit_router


###############################################################################
fastapi_settings = configurations.server.fastapi
app = FastAPI(
    title=fastapi_settings.title,
    version=fastapi_settings.version,
    description=fastapi_settings.description,
)

app.include_router(dataset_router)
app.include_router(fit_router)

@app.get("/")
def redirect_to_docs() -> RedirectResponse:
    return RedirectResponse(url="/docs")
