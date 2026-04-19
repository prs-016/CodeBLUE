from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class CharitySummary(BaseModel):
    ein: str
    name: str
    overall_score: float
    region_id: Optional[str] = None
    focus: Optional[str] = None
    url: Optional[str] = None

class CharityDetail(CharitySummary):
    financial_score: Optional[float] = None
    accountability_score: Optional[float] = None
    program_expense_ratio: Optional[float] = None
    active_regions: list[str] = []
    eligible_for_disbursement: bool
