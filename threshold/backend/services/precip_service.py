from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from services.ortho_client import ortho_post


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hours_ago_iso(hours: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _extract_latest(data: dict) -> float:
    """Pull the most recent value from an Ortho/Precip hourly response."""
    features = data.get("features") or data.get("data") or []
    if not features:
        return 0.0
    last = features[-1]
    props = last.get("properties") if isinstance(last, dict) else {}
    for key in ("value", "amount", "speed", "temperature", "soilMoisture"):
        if key in props:
            val = props[key]
            return float(val) if val is not None else 0.0
    if isinstance(last, (int, float)):
        return float(last)
    return 0.0


async def get_weather(lat: float, lon: float) -> dict:
    start = _hours_ago_iso(48)
    end = _now_iso()
    coord_args = {"latitude": str(lat), "longitude": str(lon)}
    range_args = {**coord_args, "start": start, "end": end}

    rainfall_task = ortho_post("precip", "/api/v1/last-48", query=coord_args)
    soil_task = ortho_post("precip", "/api/v1/soil-moisture-hourly", query=range_args)
    wind_task = ortho_post("precip", "/api/v1/wind-speed-gust-hourly", query=range_args)
    temp_task = ortho_post("precip", "/api/v1/temperature-hourly", query=range_args)

    results = await asyncio.gather(rainfall_task, soil_task, wind_task, temp_task, return_exceptions=True)

    rainfall_raw, soil_raw, wind_raw, temp_raw = results

    def safe_extract(raw, default=0.0) -> float:
        if isinstance(raw, Exception):
            return default
        return _extract_latest(raw)

    # rainfall last-48 may return a direct value or features list
    rainfall_mm = 0.0
    if not isinstance(rainfall_raw, Exception):
        features = rainfall_raw.get("features") or rainfall_raw.get("data") or []
        if features:
            last = features[-1]
            props = last.get("properties", {}) if isinstance(last, dict) else {}
            rainfall_mm = float(props.get("totalPrecipitation") or props.get("value") or props.get("amount") or 0.0)
        elif "totalPrecipitation" in rainfall_raw:
            rainfall_mm = float(rainfall_raw["totalPrecipitation"] or 0.0)

    soil_pct = safe_extract(soil_raw) / 100.0  # API returns 0-100, we want 0-1
    wind_ms = safe_extract(wind_raw)
    temp_c = safe_extract(temp_raw)

    return {
        "rainfall_mm_last_48h": round(rainfall_mm, 2),
        "soil_moisture_pct": round(max(0.0, min(1.0, soil_pct)), 3),
        "wind_speed_gust_ms": round(wind_ms, 2),
        "temperature_c": round(temp_c, 1),
    }
