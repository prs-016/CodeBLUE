from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


class TsunamiEvent(BaseModel):
    year: Optional[int] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    magnitude: Optional[float] = None
    max_water_height: Optional[float] = None
    deaths: Optional[int] = None
    country: Optional[str] = None
    location: Optional[str] = None
    cause: Optional[str] = None


def _pick(cols: dict, *candidates):
    for c in candidates:
        if c in cols and cols[c] is not None and str(cols[c]).strip() not in ("", "nan", "None"):
            return cols[c]
    return None


def _normalize_row(mapping) -> Optional[dict]:
    cols = {k.lower(): v for k, v in dict(mapping).items()}

    lat = _pick(cols, "latitude", "lat")
    lng = _pick(cols, "longitude", "lon", "lng", "long")
    year = _pick(cols, "year", "yr")
    magnitude = _pick(cols, "eq_mag_ms", "eq_mag_mw", "eq_mag_mb", "eq_magnitude", "magnitude", "mag")
    max_water_height = _pick(cols, "maximum_water_height", "max_water_height", "wave_height", "runup_ht", "max_wave_height")
    deaths = _pick(cols, "total_deaths", "deaths", "death_total", "deaths_total")
    country = _pick(cols, "country", "country_name")
    location = _pick(cols, "location_name", "location", "area_name", "place")
    cause = _pick(cols, "cause_code", "cause", "tsu_cause_code", "source_of_tsunami")

    if lat is None or lng is None:
        return None

    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (TypeError, ValueError):
        return None

    if not (-90 <= lat_f <= 90) or not (-180 <= lng_f <= 180):
        return None

    return {
        "year": int(float(year)) if year is not None else None,
        "lat": round(lat_f, 4),
        "lng": round(lng_f, 4),
        "magnitude": round(float(magnitude), 2) if magnitude is not None else None,
        "max_water_height": round(float(max_water_height), 2) if max_water_height is not None else None,
        "deaths": int(float(deaths)) if deaths is not None else None,
        "country": str(country).strip() if country else None,
        "location": str(location).strip() if location else None,
        "cause": str(cause).strip() if cause else None,
    }


@router.get("/", response_model=List[TsunamiEvent], summary="List all tsunami events from Snowflake")
def get_tsunamis(db: Session = Depends(get_db)) -> List[TsunamiEvent]:
    try:
        rows = db.execute(text("SELECT * FROM CALCOFI.PUBLIC.TSUNAMI_DATASET")).fetchall()
    except Exception as exc:
        logger.warning("Could not query TSUNAMI_DATASET: %s", exc)
        return []

    events = []
    for row in rows:
        normalized = _normalize_row(row._mapping)
        if normalized:
            events.append(TsunamiEvent(**normalized))

    logger.info("Returning %d tsunami events", len(events))
    return events
