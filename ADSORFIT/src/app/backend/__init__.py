from __future__ import annotations

from fastapi import APIRouter

from ADSORFIT.src.app.backend.endpoints import datasets, fitting

api_router = APIRouter(prefix="/api")
api_router.include_router(datasets.router, prefix="/datasets")
api_router.include_router(fitting.router, prefix="/fitting")
