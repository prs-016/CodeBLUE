from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from models.region import RegionDetail, RegionSummary, RegionTrajectory, StressSignalPoint
from services.ml_service import model_registry


router = APIRouter()


@router.get(
    "/",
    response_model=list[RegionSummary],
    summary="List regions",
)
def get_all_regions(db: Session = Depends(get_db)) -> list[RegionSummary]:
    rows = db.execute(
        text(
            """
            SELECT id, name, lat, lon, current_score, days_to_threshold, funding_gap,
                   primary_threat, alert_level, population_affected, primary_driver
            FROM regions
            ORDER BY current_score DESC, days_to_threshold ASC
            """
        )
    ).fetchall()
    return [
        RegionSummary(
            id=row.id,
            name=row.name,
            lat=row.lat,
            lon=row.lon,
            threshold_proximity_score=row.current_score,
            days_to_threshold=row.days_to_threshold,
            funding_gap=row.funding_gap,
            primary_threat=row.primary_threat,
            alert_level=row.alert_level,
            population_affected=row.population_affected,
            primary_driver=row.primary_driver,
        )
        for row in rows
    ]


@router.get(
    "/{region_id}",
    response_model=RegionDetail,
    summary="Get one region brief",
)
def get_region(region_id: str, db: Session = Depends(get_db)) -> RegionDetail:
    region = db.execute(
        text("SELECT * FROM regions WHERE id = :region_id"),
        {"region_id": region_id},
    ).fetchone()
    if region is None:
        raise HTTPException(status_code=404, detail="Region not found")

    latest_feature = db.execute(
        text(
            """
            SELECT sst_anomaly, o2_current, chlorophyll_anomaly, active_situation_reports
            FROM region_features
            WHERE region_id = :region_id
            ORDER BY date DESC
            LIMIT 1
            """
        ),
        {"region_id": region_id},
    ).fetchone()
    if latest_feature is None:
        raise HTTPException(status_code=404, detail="Region features not found")

    return RegionDetail(
        id=region.id,
        name=region.name,
        lat=region.lat,
        lon=region.lon,
        threshold_proximity_score=region.current_score,
        days_to_threshold=region.days_to_threshold,
        funding_gap=region.funding_gap,
        primary_threat=region.primary_threat,
        alert_level=region.alert_level,
        population_affected=region.population_affected,
        primary_driver=region.primary_driver,
        trend_summary=region.trend_summary,
        latest_sst_anomaly=latest_feature.sst_anomaly,
        latest_o2_current=latest_feature.o2_current,
        latest_chlorophyll_anomaly=latest_feature.chlorophyll_anomaly,
        active_situation_reports=latest_feature.active_situation_reports,
    )


@router.get(
    "/{region_id}/trajectory",
    response_model=RegionTrajectory,
    summary="Get threshold trajectory",
)
def get_region_trajectory(region_id: str, db: Session = Depends(get_db)) -> RegionTrajectory:
    try:
        return RegionTrajectory(**model_registry.region_trajectory(db, region_id))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Region not found") from exc


@router.get(
    "/{region_id}/stress-signals",
    response_model=list[StressSignalPoint],
    summary="Get recent region signals",
)
def get_stress_signals(region_id: str, db: Session = Depends(get_db)) -> list[StressSignalPoint]:
    rows = db.execute(
        text(
            """
            SELECT date, sst_anomaly, o2_current, chlorophyll_anomaly,
                   co2_regional_ppm, nitrate_anomaly, threshold_proximity_score,
                   scientific_event_flag, active_situation_reports,
                   dhw_current, bleaching_alert_level
            FROM region_features
            WHERE region_id = :region_id
            ORDER BY date ASC
            LIMIT 2000
            """
        ),
        {"region_id": region_id},
    ).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="Region signals not found")
    return [
        StressSignalPoint(
            date=row.date,
            sst_anomaly=row.sst_anomaly,
            o2_current=row.o2_current,
            chlorophyll_anomaly=row.chlorophyll_anomaly,
            co2_regional_ppm=row.co2_regional_ppm,
            nitrate_anomaly=row.nitrate_anomaly,
            threshold_proximity_score=row.threshold_proximity_score,
            scientific_event_flag=bool(row.scientific_event_flag),
            active_situation_reports=row.active_situation_reports,
            dhw_current=getattr(row, "dhw_current", None),
            bleaching_alert_level=getattr(row, "bleaching_alert_level", None),
        )
        for row in rows
    ]
