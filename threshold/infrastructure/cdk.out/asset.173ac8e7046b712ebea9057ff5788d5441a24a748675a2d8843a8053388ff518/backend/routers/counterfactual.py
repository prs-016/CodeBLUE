from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from models.counterfactual import (
    CounterfactualCaseDetail,
    CounterfactualCaseSummary,
    CounterfactualEstimate,
)
from services.ml_service import model_registry


router = APIRouter()


@router.get(
    "/cases",
    response_model=list[CounterfactualCaseSummary],
    summary="List case studies",
)
def get_cases(db: Session = Depends(get_db)) -> list[CounterfactualCaseSummary]:
    rows = db.execute(
        text(
            """
            SELECT case_id, region_id, event_name, year_crossed, prevention_cost, recovery_cost, cost_multiplier
            FROM counterfactual_cases
            ORDER BY year_crossed DESC
            """
        )
    ).fetchall()
    return [CounterfactualCaseSummary(**dict(row._mapping)) for row in rows]


@router.get(
    "/cases/{case_id}",
    response_model=CounterfactualCaseDetail,
    summary="Get one case study",
)
def get_case(case_id: str, db: Session = Depends(get_db)) -> CounterfactualCaseDetail:
    row = db.execute(
        text("SELECT * FROM counterfactual_cases WHERE case_id = :case_id"),
        {"case_id": case_id},
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Case study not found")

    case = dict(row._mapping)
    
    ew_date = case.get("early_warning_date")
    tc_date = case.get("threshold_crossed_date")
    year_crossed = case.get("year_crossed", 2020)
    
    timeline = []
    if ew_date:
        timeline.append({"date": ew_date, "event": "Critical Stress Signals Detected", "score": 5.5})
    if tc_date:
        timeline.append({"date": tc_date, "event": "System Threshold Crossed", "score": 8.0})
        
    timeline.append({
        "date": f"{year_crossed + 1}-01-15", 
        "event": "Recovery & Rebuilding Phase", 
        "score": 10.0
    })
    
    case["timeline"] = timeline

    return CounterfactualCaseDetail(**case)


@router.get(
    "/estimate/{region_id}",
    response_model=CounterfactualEstimate,
    summary="Estimate live counterfactual costs",
)
def estimate_costs(region_id: str, db: Session = Depends(get_db)) -> CounterfactualEstimate:
    try:
        return CounterfactualEstimate(**model_registry.counterfactual_estimate(db, region_id))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Region not found") from exc
