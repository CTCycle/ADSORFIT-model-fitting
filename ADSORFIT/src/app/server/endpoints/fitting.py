from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException, status

from ADSORFIT.src.app.server.schemas.fitting import FittingRequest, FittingResponse
from ADSORFIT.src.packages.logger import logger
from ADSORFIT.src.packages.utils.services.fitting import FittingPipeline

router = APIRouter(prefix="/fitting", tags=["fitting"])
pipeline = FittingPipeline()


# -------------------------------------------------------------------------------
@router.post("/run", response_model=FittingResponse, status_code=status.HTTP_200_OK)
async def run_fitting_job(payload: FittingRequest) -> Any:
    logger.info(
        "Received fitting request: iterations=%s, save_best=%s",
        payload.max_iterations,
        payload.save_best,
    )

    try:
        response = await asyncio.to_thread(
            pipeline.run,
            payload.dataset.model_dump(),
            {
                name: config.model_dump()
                for name, config in payload.parameter_bounds.items()
            },
            payload.max_iterations,
            payload.save_best,
        )
    except ValueError as exc:
        logger.warning("Invalid fitting request: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("ADSORFIT fitting job failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete the fitting job.",
        ) from exc

    logger.info(
        "Fitting job completed successfully with %s experiments",
        response.get("processed_rows"),
    )
    return response
