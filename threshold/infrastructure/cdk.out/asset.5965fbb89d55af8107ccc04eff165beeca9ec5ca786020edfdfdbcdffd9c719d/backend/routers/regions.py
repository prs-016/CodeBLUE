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
    "/bio-overlay",
    summary="CalCOFI biological stress points for globe overlay",
)
def get_bio_overlay(db: Session = Depends(get_db)):
    """
    Returns per-region ocean bio-stress readings as geographic point clusters
    derived from CalCOFI (Scripps IOC) sensor data. Used to render the
    chlorophyll / dissolved-oxygen stress layer on the 3-D globe.
    """
    import math

    rows = db.execute(
        text("""
            SELECT r.id, r.name, r.lat, r.lon,
                   rf.chlorophyll_anomaly, rf.o2_current, rf.sst_anomaly
            FROM regions r
            JOIN region_features rf ON rf.region_id = r.id
            WHERE rf.date = (
                SELECT MAX(rf2.date) FROM region_features rf2 WHERE rf2.region_id = r.id
            )
        """)
    ).fetchall()

    # Spread each region centre into a cluster of CalCOFI-style measurement points
    offsets = [
        (0, 0), (0.6, 0.6), (-0.6, 0.6), (0.6, -0.6), (-0.6, -0.6),
        (1.1, 0), (0, 1.1), (-1.1, 0), (0, -1.1),
    ]
    points = []
    for row in rows:
        m = row._mapping
        lat = float(m["lat"])
        lon = float(m["lon"])
        lng_scale = math.cos(lat * math.pi / 180) or 1.0
        chlora = float(m["chlorophyll_anomaly"] or 0.0)
        o2 = float(m["o2_current"] or 5.0)
        sst = float(m["sst_anomaly"] or 0.0)
        for i, (dlat, dlng_raw) in enumerate(offsets):
            jitter_lat = ((i * 0.17) % 0.25) - 0.12
            jitter_lng = ((i * 0.23) % 0.25) - 0.12
            points.append({
                "lat": round(lat + dlat + jitter_lat, 4),
                "lng": round(lon + dlng_raw / lng_scale + jitter_lng, 4),
                "chlorophyll_anomaly": round(chlora, 3),
                "o2_current": round(o2, 3),
                "sst_anomaly": round(sst, 3),
                "region_id": m["id"],
                "region_name": m["name"],
            })
    return points


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
            SELECT sst_anomaly, o2_current, chlorophyll_anomaly, active_situation_reports,
                   co2_regional_ppm, dhw_current, bleaching_alert_level, nitrate_anomaly
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

    f = latest_feature._mapping
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
        latest_sst_anomaly=f["sst_anomaly"],
        latest_o2_current=f["o2_current"],
        latest_chlorophyll_anomaly=f["chlorophyll_anomaly"],
        active_situation_reports=f["active_situation_reports"],
        latest_co2_ppm=f.get("co2_regional_ppm"),
        latest_dhw=f.get("dhw_current"),
        latest_bleaching_alert=f.get("bleaching_alert_level"),
        latest_nitrate_anomaly=f.get("nitrate_anomaly"),
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
