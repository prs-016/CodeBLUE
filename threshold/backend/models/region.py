from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    db_connected: bool = Field(examples=[True])
    models_loaded: bool = Field(examples=[True])
    last_data_refresh: Optional[str] = Field(default=None, examples=["2026-04-18T20:10:00Z"])


class RegionSummary(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    threshold_proximity_score: float
    days_to_threshold: int
    funding_gap: float
    primary_threat: str
    alert_level: str
    population_affected: int
    primary_driver: str


class RegionDetail(RegionSummary):
    trend_summary: str
    latest_sst_anomaly: float
    latest_o2_current: float
    latest_chlorophyll_anomaly: float
    active_situation_reports: int


class TrajectoryPoint(BaseModel):
    date: str
    predicted_score: float
    confidence_low: float
    confidence_high: float


class RegionTrajectory(BaseModel):
    region_id: str
    days_to_threshold: int
    crossing_date: str
    confidence_interval_low: int
    confidence_interval_high: int
    primary_driver: str
    trajectory: list[TrajectoryPoint]


class StressSignalPoint(BaseModel):
    date: str
    sst_anomaly: float
    o2_current: float
    chlorophyll_anomaly: float
    co2_regional_ppm: float
    nitrate_anomaly: float
    threshold_proximity_score: float
    scientific_event_flag: bool
    active_situation_reports: int


class TriageItem(BaseModel):
    id: str
    name: str
    current_score: float
    days_to_threshold: int
    funding_gap: float
    threat_type: str
    population_affected: int
    impact_value: float
    primary_driver: str
