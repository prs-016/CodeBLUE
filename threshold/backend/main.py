from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import SessionLocal, engine, get_last_data_refresh, init_db, _upsert_app_meta
from models.region import HealthResponse
from routers import charities, counterfactual, fund, funding, news, regions, risk_assessment, triage, tsunamis
from routers import admin
from services.ml_service import model_registry

logger = logging.getLogger(__name__)


async def _startup_pipeline():
    """Run the live data pipeline once at startup in a background thread."""
    try:
        from datetime import datetime, timezone
        import concurrent.futures
        from data_pipeline import run_pipeline

        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(pool, lambda: run_pipeline(engine))

        with engine.begin() as conn:
            _upsert_app_meta(conn, "last_data_refresh", datetime.now(timezone.utc).isoformat())

        logger.info("Startup pipeline finished: %s", result)
    except Exception as exc:
        logger.warning("Startup pipeline failed (non-fatal): %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    model_registry.load()
    with SessionLocal() as db:
        app.state.last_data_refresh = get_last_data_refresh(db)
    app.state.models_loaded = model_registry.loaded
    # Fire pipeline in background — don't block startup
    asyncio.create_task(_startup_pipeline())
    yield


app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    with SessionLocal() as db:
        last_refresh = get_last_data_refresh(db)
    return HealthResponse(
        status="ok",
        db_connected=True,
        models_loaded=getattr(app.state, "models_loaded", False),
        last_data_refresh=last_refresh,
    )


@app.get(f"{settings.api_v1_str}/health", response_model=HealthResponse, tags=["health"])
def versioned_health_check() -> HealthResponse:
    return health_check()


app.include_router(regions.router, prefix=f"{settings.api_v1_str}/regions", tags=["regions"])
app.include_router(triage.router, prefix=f"{settings.api_v1_str}/triage", tags=["triage"])
app.include_router(funding.router, prefix=f"{settings.api_v1_str}/funding", tags=["funding"])
app.include_router(news.router, prefix=f"{settings.api_v1_str}/news", tags=["news"])
app.include_router(
    counterfactual.router,
    prefix=f"{settings.api_v1_str}/counterfactual",
    tags=["counterfactual"],
)
app.include_router(
    charities.router,
    prefix=f"{settings.api_v1_str}/charities",
    tags=["charities"],
)
app.include_router(fund.router, prefix=f"{settings.api_v1_str}/fund", tags=["fund"])
app.include_router(
    risk_assessment.router,
    prefix=f"{settings.api_v1_str}/risk-assessment",
    tags=["risk-assessment"],
)
app.include_router(admin.router, prefix=f"{settings.api_v1_str}/admin", tags=["admin"])
app.include_router(tsunamis.router, prefix=f"{settings.api_v1_str}/tsunamis", tags=["tsunamis"])
