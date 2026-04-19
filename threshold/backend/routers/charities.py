from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from models.charity import CharityDetail, CharitySummary


router = APIRouter()


@router.get(
    "/",
    response_model=list[CharitySummary],
    summary="List verified charities",
)
def get_charities(
    region_id: Optional[str] = Query(default=None),
    min_score: float = Query(default=0.0, ge=0.0, le=100.0),
    db: Session = Depends(get_db),
) -> list[CharitySummary]:
    query = """
        SELECT ein, name, overall_score, region_id
        FROM charity_registry
        WHERE overall_score >= :min_score
    """
    params: dict[str, object] = {"min_score": min_score}
    if region_id:
        query += " AND region_id = :region_id"
        params["region_id"] = region_id
    query += " ORDER BY overall_score DESC"
    rows = db.execute(text(query), params).fetchall()
    return [CharitySummary(**dict(row._mapping)) for row in rows]


@router.get(
    "/{ein}",
    response_model=CharityDetail,
    summary="Get one charity profile",
)
def get_charity(ein: str, db: Session = Depends(get_db)) -> CharityDetail:
    row = db.execute(
        text("SELECT * FROM charity_registry WHERE ein = :ein"),
        {"ein": ein},
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Charity not found")
    data = dict(row._mapping)
    data["active_regions"] = [part for part in (data.get("active_regions") or "").split(",") if part]
    data["eligible_for_disbursement"] = (
        (data.get("overall_score") or 0) >= 75 and (data.get("accountability_score") or 0) >= 80
    )
    return CharityDetail(**data)
