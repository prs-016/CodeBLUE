from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException

from models.risk_assessment import (
    CharityResult,
    DisasterInference,
    EnrichRiskResponse,
    Headline,
    QuickRiskResponse,
    RiskAssessmentRequest,
    WeatherSummary,
)
from services.disaster_inference import infer_disaster
from services.gdelt_service import get_headlines
from services.geocoding_service import reverse_geocode
from services.precip_service import get_weather


router = APIRouter()


@router.post(
    "/quick",
    response_model=QuickRiskResponse,
    summary="Geocode + weather + disaster inference",
)
async def risk_quick(req: RiskAssessmentRequest) -> QuickRiskResponse:
    try:
        geo = await reverse_geocode(req.lat, req.lon)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Geocoding failed: {exc}") from exc

    try:
        weather_raw = await get_weather(req.lat, req.lon)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Weather fetch failed: {exc}") from exc

    disaster_raw = infer_disaster(weather_raw)

    return QuickRiskResponse(
        region_name=geo["region_name"],
        country=geo["country"],
        lat=req.lat,
        lon=req.lon,
        weather=WeatherSummary(**weather_raw),
        disaster=DisasterInference(**disaster_raw),
    )


@router.post(
    "/enrich",
    response_model=EnrichRiskResponse,
    summary="News headlines + charity lookup (run after /quick)",
)
async def risk_enrich(req: RiskAssessmentRequest) -> EnrichRiskResponse:
    # Re-run geocode (fast, cached by Maps) and infer disaster so this endpoint
    # is independently callable from the frontend.
    try:
        geo = await reverse_geocode(req.lat, req.lon)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Geocoding failed: {exc}") from exc

    try:
        weather_raw = await get_weather(req.lat, req.lon)
    except Exception:
        weather_raw = {}
    disaster_raw = infer_disaster(weather_raw)
    disaster_type = disaster_raw["disaster_type"]
    region_name = geo["region_name"]

    from services.gemini_service import search_charities
    
    # Fire news + charities in parallel
    results = await asyncio.gather(
        get_headlines(region_name, disaster_type),
        search_charities(region_name, disaster_type),
        return_exceptions=True,
    )
    headlines_raw, gemini_raw = results

    errors: dict[str, str | None] = {"news": None, "charities": None}

    headlines: list[Headline] = []
    if isinstance(headlines_raw, Exception):
        errors["news"] = str(headlines_raw)
    else:
        headlines = [Headline(**h) for h in (headlines_raw or [])]

    charities: list[CharityResult] = []
    if isinstance(gemini_raw, Exception):
        errors["charities"] = str(gemini_raw)
    else:
        charities = [CharityResult(**c) for c in (gemini_raw or [])]

    # Deduplicate charities by name
    seen: set[str] = set()
    unique_charities: list[CharityResult] = []
    for c in charities:
        if c.name.lower() not in seen:
            seen.add(c.name.lower())
            unique_charities.append(c)

    return EnrichRiskResponse(
        region_name=region_name,
        lat=req.lat,
        lon=req.lon,
        disaster_type=disaster_type,
        headlines=headlines,
        charities=unique_charities,
        errors=errors,
    )
