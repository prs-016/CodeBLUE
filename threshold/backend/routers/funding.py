from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
from ..database import get_db
import uuid

router = APIRouter()

@router.get("/gap", response_model=List[Dict[str, Any]])
def get_funding_gap_radar(db: Session = Depends(get_db)):
    """Returns all regions with funding gap data formatted for radar chart."""
    result = db.execute(text("""
        SELECT 
            id as region_id, name, current_score as threshold_score,
            funding_gap, primary_threat as threat_type, population_affected,
            alert_level as attention_gap
        FROM regions
    """))
    return [dict(row._mapping) for row in result]

@router.get("/rounds", response_model=List[Dict[str, Any]])
def get_funding_rounds(db: Session = Depends(get_db)):
    """Returns all active and completed funding rounds."""
    result = db.execute(text("""
        SELECT fr.*, r.name as region_name, r.primary_threat as threat_type
        FROM funding_rounds fr
        JOIN regions r ON r.id = fr.region_id
    """))
    return [dict(row._mapping) for row in result]

@router.get("/rounds/{round_id}", response_model=Dict[str, Any])
def get_funding_round(round_id: str, db: Session = Depends(get_db)):
    """Returns full funding round details."""
    res = db.execute(text("""
        SELECT fr.*, r.name as region_name, r.primary_threat as threat_type
        FROM funding_rounds fr
        JOIN regions r ON r.id = fr.region_id
        WHERE fr.id = :rid
    """), {"rid": round_id}).fetchone()
    if not res:
        raise HTTPException(404, "Funding round not found")
    return dict(res._mapping)

@router.post("/rounds/{round_id}/contribute")
def post_contribute(round_id: str, payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """Mocks stripe payment intent and triggers Solana recording pipeline."""
    amt = payload.get("amount_usd", 0)
    # Mocking successful payment intent
    return {
        "status": "success",
        "stripe_payment_intent": f"pi_{uuid.uuid4().hex[:20]}",
        "transaction_id": f"tx_{uuid.uuid4().hex}",
        "blockchain_hash": f"sol_{uuid.uuid4().hex}",
        "amount_usd": amt
    }

@router.get("/impact")
def get_impact_registry(db: Session = Depends(get_db)):
    """Returns impact registry — completed rounds with pre/post scores."""
    result = db.execute(text("""
        SELECT * FROM counterfactual_cases
    """))
    return [dict(row._mapping) for row in result]
