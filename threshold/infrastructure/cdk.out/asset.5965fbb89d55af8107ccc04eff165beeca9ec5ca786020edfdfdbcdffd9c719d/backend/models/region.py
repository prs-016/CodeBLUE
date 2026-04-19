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
    latest_co2_ppm: Optional[float] = None
    latest_dhw: Optional[float] = None
    latest_bleaching_alert: Optional[float] = None
    latest_nitrate_anomaly: Optional[float] = None


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
    sst_anomaly: Optional[float] = None
    o2_current: Optional[float] = None
    chlorophyll_anomaly: Optional[float] = None
    co2_regional_ppm: Optional[float] = None
    nitrate_anomaly: Optional[float] = None
    threshold_proximity_score: Optional[float] = None
    scientific_event_flag: bool = False
    active_situation_reports: int = 0
    dhw_current: Optional[float] = None
    bleaching_alert_level: Optional[float] = None


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
