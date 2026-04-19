from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class CounterfactualTimelinePoint(BaseModel):
    date: str
    event: str
    score: float


class CounterfactualCaseSummary(BaseModel):
    case_id: str
    region_id: str
    event_name: str
    year_crossed: int
    prevention_cost: float
    recovery_cost: float
    cost_multiplier: float


class CounterfactualCaseDetail(CounterfactualCaseSummary):
    early_warning_date: Optional[str] = None
    threshold_crossed_date: Optional[str] = None
    data_source: Optional[str] = None
    timeline: list[CounterfactualTimelinePoint] = []


class CounterfactualEstimate(BaseModel):
    region_id: str
    region_name: str
    prevention_cost_usd: float
    recovery_cost_usd: float
    cost_multiplier: float
    optimal_intervention_type: str
    prevention_breakdown: dict[str, float]
    recovery_breakdown: dict[str, float]
