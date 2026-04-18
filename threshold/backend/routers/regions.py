from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
from ..database import get_db

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
def get_all_regions(db: Session = Depends(get_db)):
    """Returns list of all regions with current threshold status."""
    result = db.execute(text("""
        SELECT id, name, lat, lon, current_score as threshold_proximity_score, 
               days_to_threshold, funding_gap, primary_threat, alert_level, population_affected
        FROM regions
    """))
    return [dict(row._mapping) for row in result]

@router.get("/{region_id}", response_model=Dict[str, Any])
def get_region(region_id: str, db: Session = Depends(get_db)):
    """Returns full region intelligence brief including score breakdown."""
    reg = db.execute(text("SELECT * FROM regions WHERE id = :rid"), {"rid": region_id}).fetchone()
    if not reg:
        raise HTTPException(status_code=404, detail="Region not found")
        
    return dict(reg._mapping)

@router.get("/{region_id}/trajectory", response_model=Dict[str, Any])
def get_region_trajectory(region_id: str, db: Session = Depends(get_db)):
    """Returns 730-day predicted score trajectory with confidence intervals."""
    # Mocking prediction from Snowflake ML / SageMaker proxy
    return {
        "region_id": region_id,
        "days_to_threshold": 47,
        "trajectory": [
            {"date": f"2025-01-{i:02d}", "predicted_score": min(10.0, 8.0 + (i * 0.05))}
            for i in range(1, 31)
        ]
    }

@router.get("/{region_id}/stress-signals", response_model=List[Dict[str, Any]])
def get_stress_signals(region_id: str, db: Session = Depends(get_db)):
    """Returns time series for all stress indicators."""
    result = db.execute(text("""
        SELECT date, sst_anomaly, o2_current, chlorophyll_anomaly, 
               co2_regional_ppm, nitrate_anomaly, threshold_proximity_score
        FROM region_features
        WHERE region_id = :rid
        ORDER BY date DESC LIMIT 365
    """), {"rid": region_id})
    return [dict(row._mapping) for row in result]
