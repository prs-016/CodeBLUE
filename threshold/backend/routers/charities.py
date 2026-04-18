from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from ..database import get_db

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
def get_charities(
    region_id: Optional[str] = None,
    min_score: float = 0.0,
    db: Session = Depends(get_db)
):
    """Returns verified charities matching criteria with scores."""
    query = "SELECT * FROM charity_registry WHERE overall_score >= :min_score"
    params = {"min_score": min_score}
    
    if region_id:
        query += " AND region_id = :rid"
        params["rid"] = region_id
        
    result = db.execute(text(query), params)
    return [dict(row._mapping) for row in result]

@router.get("/{ein}", response_model=Dict[str, Any])
def get_charity(ein: str, db: Session = Depends(get_db)):
    """Returns full charity profile."""
    res = db.execute(text("SELECT * FROM charity_registry WHERE ein = :ein"), {"ein": ein}).fetchone()
    if not res:
        raise HTTPException(404, "Charity not found")
    return dict(res._mapping)
