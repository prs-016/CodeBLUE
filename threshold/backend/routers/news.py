from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db


router = APIRouter()


@router.get(
    "/attention-gap",
    response_model=list[dict],
    summary="Get attention gap rankings",
)
def get_attention_gap(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT
                r.id AS region_id,
                r.name,
                ma.severity_score,
                ma.normalized_attention_score,
                ma.attention_gap
            FROM media_attention ma
            JOIN regions r ON r.id = ma.region_id
            ORDER BY ma.attention_gap DESC
            """
        )
    ).fetchall()
    return [dict(row._mapping) for row in rows]


@router.get(
    "/{region_id}",
    response_model=list[dict],
    summary="Get region news feed",
)
async def get_news(
    region_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    days_back: int = Query(default=30, ge=1, le=365),
    source: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> list[dict]:
    cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    query = """
        SELECT id, title, source_type, source_org, date, body_summary, url, urgency_score, disaster_type
        FROM news_reports
        WHERE region_id = :region_id
          AND date >= :cutoff_date
    """
    params: dict[str, object] = {"region_id": region_id, "cutoff_date": cutoff_date}
    if source and source.lower() != "all":
        query += " AND source_type = :source"
        params["source"] = source.lower()
    query += " ORDER BY urgency_score DESC, date DESC LIMIT :limit"
    params["limit"] = limit

    rows = db.execute(text(query), params).fetchall()
    base_news = [dict(row._mapping) for row in rows]

    if len(base_news) < 3:
        # Trigger Gemini Live Research
        from services.gemini_service import search_news
        region_row = db.execute(text("SELECT name, primary_threat FROM regions WHERE id = :rid"), {"rid": region_id}).fetchone()
        if region_row:
            import asyncio
            live_news = await search_news(region_row[0], region_row[1])
            return base_news + live_news

    return base_news
