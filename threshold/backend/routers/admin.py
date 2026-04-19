from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from database import engine

logger = logging.getLogger(__name__)
router = APIRouter()

_score_update_running = False


class RefreshResponse(BaseModel):
    status: str
    message: str
    result: dict | None = None


@router.post("/refresh-data", response_model=RefreshResponse, tags=["admin"])
def trigger_data_refresh() -> RefreshResponse:
    return RefreshResponse(
        status="disabled",
        message="Pipeline writes are disabled. Data is managed via Snowflake UI.",
    )


@router.post("/refresh-data/sync", response_model=RefreshResponse, tags=["admin"])
def trigger_data_refresh_sync() -> RefreshResponse:
    return RefreshResponse(
        status="disabled",
        message="Pipeline writes are disabled. Data is managed via Snowflake UI.",
    )


@router.post("/score-update", response_model=RefreshResponse, tags=["admin"])
def trigger_score_update(background_tasks: BackgroundTasks) -> RefreshResponse:
    """
    Recompute threshold_proximity_score for all REGION_FEATURES rows using
    IPCC/NOAA/EPA scientific thresholds + GDELT conflict signal from Snowflake.
    Runs in the background.
    """
    global _score_update_running
    if _score_update_running:
        raise HTTPException(status_code=409, detail="Score update already running")

    def _run():
        global _score_update_running
        try:
            from score_pipeline import run_score_update
            run_score_update(engine)
        except Exception as exc:
            logger.error("Score update failed: %s", exc)
        finally:
            _score_update_running = False

    _score_update_running = True
    background_tasks.add_task(_run)
    return RefreshResponse(
        status="accepted",
        message="Score update started in background. Uses IPCC/NOAA/EPA thresholds + GDELT conflict signal.",
    )


@router.post("/score-update/sync", response_model=RefreshResponse, tags=["admin"])
def trigger_score_update_sync() -> RefreshResponse:
    """
    Synchronous version — waits for completion and returns the result.
    """
    global _score_update_running
    if _score_update_running:
        raise HTTPException(status_code=409, detail="Score update already running")

    _score_update_running = True
    try:
        from score_pipeline import run_score_update
        result = run_score_update(engine)
        return RefreshResponse(
            status="ok",
            message="Score update complete.",
            result=result,
        )
    except Exception as exc:
        logger.error("Score update failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        _score_update_running = False
