from __future__ import annotations

from pydantic import BaseModel


class RiskAssessmentRequest(BaseModel):
    lat: float
    lon: float


class WeatherSummary(BaseModel):
    rainfall_mm_last_48h: float
    soil_moisture_pct: float
    wind_speed_gust_ms: float
    temperature_c: float


class DisasterInference(BaseModel):
    disaster_type: str
    risk_level: str
    trigger_factors: list[str]
    pin_color: str


class QuickRiskResponse(BaseModel):
    region_name: str
    country: str
    lat: float
    lon: float
    weather: WeatherSummary
    disaster: DisasterInference


class Headline(BaseModel):
    title: str
    url: str
    source: str
    published_at: str


class CharityResult(BaseModel):
    name: str
    url: str | None = None
    focus: str
    source: str


class EnrichRiskResponse(BaseModel):
    region_name: str
    lat: float
    lon: float
    disaster_type: str
    headlines: list[Headline]
    charities: list[CharityResult]
    errors: dict[str, str | None]
