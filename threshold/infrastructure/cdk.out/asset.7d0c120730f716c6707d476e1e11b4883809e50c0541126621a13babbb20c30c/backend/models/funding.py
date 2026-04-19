from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class FundingGapItem(BaseModel):
    region_id: str
    name: str
    threshold_score: float
    funding_gap: float
    threat_type: str
    population_affected: int
    attention_gap: float
    coverage_ratio: float
    primary_driver: str = ""


class FundingRoundSummary(BaseModel):
    id: str
    region_id: str
    region_name: str
    title: str
    target_amount: float
    raised_amount: float
    status: str
    deadline: str
    cost_multiplier: float
    threat_type: str


class FundingRoundDetail(FundingRoundSummary):
    partner_ein: Optional[str] = None
    remaining_gap: float
    partner_name: Optional[str] = None


class ContributionRequest(BaseModel):
    amount_usd: float = Field(gt=0, examples=[50])
    donor_email: Optional[str] = Field(default=None, examples=["donor@example.com"])


class ContributionResponse(BaseModel):
    status: str
    round_id: str
    amount_usd: float
    stripe_payment_intent: str
    stripe_status: str
    blockchain_hash: str
    blockchain_status: str


class FundingImpactItem(BaseModel):
    case_id: str
    region_id: str
    event_name: str
    prevention_cost: float
    recovery_cost: float
    cost_multiplier: float


class FundingRoundCreateRequest(BaseModel):
    region_id: str
    title: str
    target_amount: float = Field(gt=0)
    deadline: str
    partner_ein: Optional[str] = None
