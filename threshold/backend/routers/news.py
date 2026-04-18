from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from database import get_db

router = APIRouter()

@router.get("/{region_id}", response_model=List[Dict[str, Any]])
def get_news(
    region_id: str,
    limit: int = 10,
    days_back: int = 30,
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Returns recent news items with urgency scores, sorted by relevance."""
    query = "SELECT * FROM news_reports WHERE region_id = :rid"
    params = {"rid": region_id}
    
    if source and source.lower() != "all":
        query += " AND source_org = :src"
        params["src"] = source
        
    query += " ORDER BY urgency_score DESC, date DESC LIMIT :limit"
    params["limit"] = limit
    
    result = db.execute(text(query), params)
    return [dict(row._mapping) for row in result]

@router.get("/attention-gap/rankings", response_model=List[Dict[str, Any]])
def get_attention_gap(db: Session = Depends(get_db)):
    """Returns all regions with media attention vs crisis severity comparison."""
    result = db.execute(text("""
        SELECT id as region_id, name, current_score as severity_score, alert_level as attention_status
        FROM regions
    """))
    return [dict(row._mapping) for row in result]
