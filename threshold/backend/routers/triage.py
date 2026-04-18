from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from ..database import get_db

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
def get_triage_queue(
    sort_by: str = "days_to_threshold", 
    order: str = "asc",
    threat_type: Optional[str] = None,
    min_gap: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Returns paginated ranked list of regions with triage metrics."""
    # Input sanitization for sort_by and order
    safe_columns = {"days_to_threshold", "current_score", "funding_gap", "population_affected"}
    if sort_by not in safe_columns:
        sort_by = "days_to_threshold"
    
    dir_order = "ASC" if order.lower() == "asc" else "DESC"
    
    query = f"""
        SELECT 
            id, name, current_score, days_to_threshold, funding_gap, 
            primary_threat as threat_type, population_affected,
            (funding_gap / CAST(population_affected AS REAL)) as impact_value
        FROM regions
        WHERE 1=1
    """
    params = {}
    
    if threat_type:
        query += " AND primary_threat = :threat"
        params["threat"] = threat_type
    if min_gap is not None:
        query += " AND funding_gap >= :min_gap"
        params["min_gap"] = min_gap
        
    query += f" ORDER BY {sort_by} {dir_order} LIMIT 20"
    
    result = db.execute(text(query), params)
    return [dict(row._mapping) for row in result]
