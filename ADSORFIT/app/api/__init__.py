from __future__ import annotations

from fastapi import APIRouter

from ADSORFIT.app.api.endpoints import fitting


api_router = APIRouter(prefix="/api")
api_router.include_router(fitting.router, prefix="/fitting")
