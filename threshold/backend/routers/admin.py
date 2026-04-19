from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from database import engine, SessionLocal, _upsert_app_meta

logger = logging.getLogger(__name__)

router = APIRouter()

_pipeline_running = False


class RefreshResponse(BaseModel):
    status: str
    message: str
    started_at: str | None = None
    result: dict | None = None


def _run_and_record():
    global _pipeline_running
    try:
        from data_pipeline import run_pipeline
        result = run_pipeline(engine)
        with engine.begin() as conn:
            _upsert_app_meta(conn, "last_data_refresh", datetime.now(timezone.utc).isoformat())
        logger.info("Data pipeline finished: %s", result)
    except Exception as exc:
        logger.error("Data pipeline failed: %s", exc)
    finally:
        _pipeline_running = False


@router.post("/refresh-data", response_model=RefreshResponse, tags=["admin"])
def trigger_data_refresh(background_tasks: BackgroundTasks) -> RefreshResponse:
    """
    Trigger the live data pipeline to fetch NOAA / GDELT / ReliefWeb data
    and write it to Snowflake (or SQLite). Runs in the background.
    """
    global _pipeline_running
    if _pipeline_running:
        raise HTTPException(status_code=409, detail="Pipeline already running")

    _pipeline_running = True
    background_tasks.add_task(_run_and_record)
    return RefreshResponse(
        status="accepted",
        message="Pipeline started in background. Check /health for last_data_refresh timestamp.",
        started_at=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/refresh-data/sync", response_model=RefreshResponse, tags=["admin"])
def trigger_data_refresh_sync() -> RefreshResponse:
    """
    Synchronous version — waits for the pipeline to complete and returns results.
    Use only for debugging; prefer the async endpoint in production.
    """
    global _pipeline_running
    if _pipeline_running:
        raise HTTPException(status_code=409, detail="Pipeline already running")

    _pipeline_running = True
    try:
        from data_pipeline import run_pipeline
        result = run_pipeline(engine)
        with engine.begin() as conn:
            _upsert_app_meta(conn, "last_data_refresh", datetime.now(timezone.utc).isoformat())
        return RefreshResponse(
            status="ok",
            message="Pipeline completed successfully.",
            started_at=datetime.now(timezone.utc).isoformat(),
            result=result,
        )
    except Exception as exc:
        logger.error("Data pipeline failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        _pipeline_running = False
