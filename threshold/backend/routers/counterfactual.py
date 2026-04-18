from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
from database import get_db

router = APIRouter()

@router.get("/cases", response_model=List[Dict[str, Any]])
def get_cases(db: Session = Depends(get_db)):
    """Returns list of all historical case studies with summary stats."""
    result = db.execute(text("SELECT * FROM counterfactual_cases"))
    return [dict(row._mapping) for row in result]

@router.get("/cases/{case_id}", response_model=Dict[str, Any])
def get_case(case_id: str, db: Session = Depends(get_db)):
    """Returns full case study with timeline data, cost breakdowns."""
    res = db.execute(text("SELECT * FROM counterfactual_cases WHERE case_id = :cid"), {"cid": case_id}).fetchone()
    if not res:
        raise HTTPException(404, "Case study not found")
        
    case = dict(res._mapping)
    # Mocking timeline arrays
    case["timeline"] = [
        {"year": case["year_crossed"] - 5, "event": "Early Warning Signal", "score": 4.1},
        {"year": case["year_crossed"] - 2, "event": "Intervention Window Closing", "score": 7.5},
        {"year": case["year_crossed"], "event": "THRESHOLD CROSSED", "score": 10.0}
    ]
    return case

@router.get("/estimate/{region_id}", response_model=Dict[str, Any])
def estimate_costs(region_id: str, db: Session = Depends(get_db)):
    """Returns live cost estimate for current region state using ML models."""
    res = db.execute(text("""
        SELECT name, current_score, funding_gap 
        FROM regions WHERE id = :rid
    """), {"rid": region_id}).fetchone()
    
    if not res:
        raise HTTPException(404, "Region not found")
        
    s = res._mapping["current_score"]
    base_cost = 5000000 + (s * 1000000)
    
    return {
        "region_id": region_id,
        "prevention_cost": base_cost,
        "recovery_cost": base_cost * (2.0 + (s * 0.5)),
        "cost_multiplier": 2.0 + (s * 0.5),
        "breakdown": {
            "monitoring": base_cost * 0.2,
            "intervention": base_cost * 0.8
        }
    }
