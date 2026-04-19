from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from models.region import TriageItem


router = APIRouter()


@router.get(
    "/",
    response_model=list[TriageItem],
    summary="Get the triage queue",
)
def get_triage_queue(
    sort_by: str = Query("days_to_threshold"),
    order: str = Query("asc"),
    threat_type: Optional[str] = Query(default=None),
    min_gap: Optional[float] = Query(default=None),
    max_days: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[TriageItem]:
    safe_columns = {
        "days_to_threshold": "days_to_threshold",
        "current_score": "current_score",
        "funding_gap": "funding_gap",
        "population_affected": "population_affected",
    }
    order_column = safe_columns.get(sort_by, "days_to_threshold")
    order_direction = "ASC" if order.lower() == "asc" else "DESC"

    query = """
        SELECT
            id, name, current_score, days_to_threshold, funding_gap,
            primary_threat AS threat_type, population_affected, primary_driver,
            ROUND(funding_gap / CAST(MAX(population_affected, 1) AS REAL), 4) AS impact_value
        FROM regions
        WHERE 1=1
    """
    params: dict[str, object] = {}
    if threat_type:
        query += " AND primary_threat = :threat_type"
        params["threat_type"] = threat_type
    if min_gap is not None:
        query += " AND funding_gap >= :min_gap"
        params["min_gap"] = min_gap
    if max_days is not None:
        query += " AND days_to_threshold <= :max_days"
        params["max_days"] = max_days
    query += f" ORDER BY {order_column} {order_direction}, current_score DESC LIMIT 50"

    rows = db.execute(text(query), params).fetchall()
    return [TriageItem(**dict(row._mapping)) for row in rows]
