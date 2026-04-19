from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class RefreshResponse(BaseModel):
    status: str
    message: str


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
