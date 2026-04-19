from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from config import settings
from database import engine, get_db

logger = logging.getLogger(__name__)
router = APIRouter()

_score_update_running = False


class RefreshResponse(BaseModel):
    status: str
    message: str
    result: dict | None = None


@router.get("/data-sources", summary="Live data source statistics")
def get_data_sources(db: Session = Depends(get_db)):
    """
    Returns row counts and status for every data source feeding THRESHOLD —
    CalCOFI (Scripps), GDELT (Snowflake), and Gemini. Displayed in the
    war-room HUD so judges can see the live data pipeline at a glance.
    """
    sources = []

    # ── CalCOFI (Scripps IOC) ──────────────────────────────────────────────
    try:
        count = db.execute(text("SELECT COUNT(*) FROM CALCOFI_TSUNAMI_FEATURES")).scalar()
        sources.append({
            "name": "CalCOFI Ocean Biometrics",
            "provider": "Scripps Institution of Oceanography",
            "storage": "Snowflake",
            "rows": int(count),
            "status": "live",
            "metrics": "Temp · O₂ · Salinity · Chlorophyll · Nitrate",
        })
    except Exception:
        try:
            count = db.execute(text("SELECT COUNT(*) FROM region_features")).scalar()
            sources.append({
                "name": "CalCOFI / NOAA Ocean Features",
                "provider": "Scripps IOC + NOAA",
                "storage": "local",
                "rows": int(count),
                "status": "live",
                "metrics": "SST · O₂ · Chlorophyll · DHW · CO₂",
            })
        except Exception:
            pass

    # ── GDELT (Snowflake) ──────────────────────────────────────────────────
    try:
        count = db.execute(text("SELECT COUNT(*) FROM GDELT")).scalar()
        sources.append({
            "name": "GDELT Global Events",
            "provider": "GDELT Project",
            "storage": "Snowflake",
            "rows": int(count),
            "status": "live",
            "metrics": "Conflict index · Goldstein scale · Media volume",
        })
    except Exception:
        sources.append({
            "name": "GDELT Global Events",
            "provider": "GDELT Project",
            "storage": "Snowflake",
            "rows": None,
            "status": "snowflake",
            "metrics": "Conflict index · Goldstein scale",
        })

    # ── Gemini API ─────────────────────────────────────────────────────────
    sources.append({
        "name": "Gemini 2.0 Flash + 2.5 Flash",
        "provider": "Google AI",
        "storage": "API",
        "rows": None,
        "status": "grounded" if settings.gemini_api_key else "not_configured",
        "metrics": "Grounded news search · Charity discovery",
    })

    return {
        "sources": sources,
        "snowflake_database": settings.snowflake_database,
    }


@router.get("/solana-status", summary="Server Solana keypair status and balance")
def get_solana_status():
    """Returns the server keypair pubkey and devnet balance — use this to fund the keypair for live on-chain txs."""
    from services.solana_service import solana_service
    if not solana_service.is_ready or not solana_service.keypair:
        return {"ready": False, "pubkey": None, "balance_sol": None, "fund_command": None}
    pubkey = str(solana_service.keypair.pubkey())
    balance_sol = None
    try:
        resp = solana_service.client.get_balance(solana_service.keypair.pubkey())
        balance_sol = round(resp.value / 1e9, 4)
    except Exception:
        pass
    return {
        "ready": solana_service.is_ready,
        "pubkey": pubkey,
        "balance_sol": balance_sol,
        "fund_command": f"solana airdrop 2 {pubkey} --url devnet",
    }


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
