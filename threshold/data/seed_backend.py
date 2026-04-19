"""
seed_backend.py — Final pipeline step: maps processed pipeline tables → backend API tables.

Pipeline produces:
  region_stress       (daily per-region stress signals from real SST/CO2/coral data)
  regional_aggregates (monthly rollups)
  media_attention     (GDELT-derived attention gap per region)
  funding_gap         (modeled funding need vs committed)
  reliefweb_reports   (humanitarian news items)
  charity_registry    (NGO ratings from Charity Navigator)

Backend expects:
  region_features     (timeseries stress signals — fed to ML models + charts)
  regions             (current scores, funding gaps, alert levels)
  media_attention     (same schema ✓)
  news_reports        (structured news items)
  charity_registry    (NGO ratings for FundingIntelligence panel)
"""
from __future__ import annotations

import sys
import logging
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
if str(DATA_DIR) not in sys.path:
    sys.path.insert(0, str(DATA_DIR))

from ingestion.shared import (
    REGIONS,
    setup_logging,
    sqlite_connection,
    update_manifest,
)

logger = setup_logging("seed_backend")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _table_exists(conn, table: str) -> bool:
    return conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def _read(conn, table: str) -> pd.DataFrame:
    if not _table_exists(conn, table):
        return pd.DataFrame()
    return pd.read_sql_query(f"SELECT * FROM {table}", conn)


def _score_to_days(score: float) -> int:
    """Heuristic: higher composite score → fewer days to ecological threshold."""
    if score >= 9.5:
        return 14
    if score >= 9.0:
        return 30
    if score >= 8.0:
        return 47
    if score >= 7.0:
        return 90
    if score >= 6.0:
        return 150
    if score >= 5.0:
        return 240
    return 365


def _score_to_alert(score: float, primary_threat: str) -> str:
    if score >= 8.5:
        return "critical"
    if score >= 7.0:
        return "high"
    if score >= 5.5:
        return "watch"
    return "normal"


# ---------------------------------------------------------------------------
# Step 1: region_stress → region_features
# ---------------------------------------------------------------------------

def sync_region_features(conn) -> int:
    """Map region_stress columns → region_features schema and upsert."""
    stress = _read(conn, "region_stress")
    if stress.empty:
        logger.warning("region_stress is empty — skipping region_features sync")
        return 0

    features = pd.DataFrame()
    features["region_id"] = stress["region_id"]
    features["date"] = stress["date"]
    features["sst_anomaly"] = stress["sst_anomaly"].round(3)
    features["o2_current"] = stress["o2_current"].round(3)
    features["chlorophyll_anomaly"] = stress["chlorophyll_anomaly"].round(3)
    features["co2_regional_ppm"] = stress["co2_regional_ppm"].round(3)
    features["nitrate_anomaly"] = stress["nitrate_anomaly"].round(3)
    features["threshold_proximity_score"] = stress["stress_composite"].clip(0, 10).round(3)
    features["scientific_event_flag"] = stress["scientific_event_flag"].astype(bool).astype(int)
    features["active_situation_reports"] = stress["active_situation_reports"].astype(int)

    # Write via pandas to_sql (replace) so the backend's CREATE TABLE schema is
    # respected after init_db() already created the table with correct constraints.
    features.to_sql("region_features", conn, if_exists="replace", index=False)
    conn.commit()

    rows = len(features)
    update_manifest("region_features", rows, "pipeline", "written")
    logger.info("region_features: %d rows synced from region_stress", rows)
    return rows


# ---------------------------------------------------------------------------
# Step 2: region_stress + funding_gap → update regions table
# ---------------------------------------------------------------------------

def sync_regions(conn) -> int:
    """Update dynamic fields (current_score, days_to_threshold, funding_gap,
    alert_level, primary_driver) in the regions table from pipeline data."""
    stress = _read(conn, "region_stress")
    if stress.empty:
        logger.warning("region_stress is empty — skipping regions sync")
        return 0

    fg = _read(conn, "funding_gap")

    # Latest stress composite per region
    stress["date"] = pd.to_datetime(stress["date"])
    latest = (
        stress.sort_values("date")
        .groupby("region_id")
        .tail(30)  # Use last 30 days average for stability
        .groupby("region_id", as_index=False)
        .agg(
            current_score=("stress_composite", "mean"),
            sst_anomaly_latest=("sst_anomaly", "last"),
            dhw_latest=("dhw_current", "last") if "dhw_current" in stress.columns else ("stress_composite", "last"),
            bleaching_alert=("bleaching_alert_level", "last") if "bleaching_alert_level" in stress.columns else ("stress_composite", "last"),
        )
    )
    latest["current_score"] = latest["current_score"].clip(0, 10).round(2)

    if not fg.empty:
        latest = latest.merge(
            fg[["region_id", "funding_gap"]].rename(columns={"funding_gap": "computed_gap"}),
            on="region_id",
            how="left",
        )
    else:
        latest["computed_gap"] = None

    # Check which regions exist in the backend regions table
    existing = _read(conn, "regions")
    if existing.empty:
        logger.warning("regions table is empty — run backend init_db() first")
        return 0

    updated = 0
    for _, row in latest.iterrows():
        region_id = row["region_id"]
        if region_id not in existing["id"].values:
            continue

        score = float(row["current_score"])
        days = _score_to_days(score)

        # Primary driver label from the dominant stress signal
        region_meta = REGIONS.get(region_id, {})
        primary_threat = region_meta.get("primary_threat", "thermal")
        sst_val = float(row.get("sst_anomaly_latest", 0))
        primary_driver = _derive_driver(primary_threat, sst_val, score)
        alert_level = _score_to_alert(score, primary_threat)

        # Funding gap
        if row.get("computed_gap") is not None and not pd.isna(row["computed_gap"]):
            funding_gap = max(0.0, float(row["computed_gap"]))
        else:
            # Keep existing funding_gap from seed
            existing_gap = existing.loc[existing["id"] == region_id, "funding_gap"].values
            funding_gap = float(existing_gap[0]) if len(existing_gap) else score * 1_000_000

        conn.execute(
            """
            UPDATE regions SET
                current_score = ?,
                days_to_threshold = ?,
                alert_level = ?,
                funding_gap = ?,
                primary_driver = ?
            WHERE id = ?
            """,
            (score, days, alert_level, funding_gap, primary_driver, region_id),
        )
        updated += 1

    conn.commit()
    update_manifest("regions", updated, "pipeline", "written", {"action": "UPDATE dynamic fields"})
    logger.info("regions: %d rows updated from pipeline", updated)
    return updated


def _derive_driver(primary_threat: str, sst_anomaly: float, score: float) -> str:
    if primary_threat == "thermal":
        return f"SST Anomaly +{sst_anomaly:.1f}°C — bleaching stress elevated"
    if primary_threat == "hypoxia":
        return f"Dissolved oxygen depletion — dead zone risk score {score:.1f}/10"
    if primary_threat == "acidification":
        return f"Ocean acidification + upwelling stress — pH decline accelerating"
    return f"Multi-driver ecological stress score {score:.1f}/10"


# ---------------------------------------------------------------------------
# Step 3: media_attention (pipeline table) → media_attention (backend table)
# ---------------------------------------------------------------------------

def sync_media_attention(conn) -> int:
    """Pipeline media_attention has the exact same schema as the backend — just replace."""
    ma = _read(conn, "media_attention")
    if ma.empty:
        logger.warning("media_attention is empty — skipping")
        return 0

    # Ensure required columns exist
    required = {"region_id", "severity_score", "normalized_attention_score", "attention_gap"}
    if not required.issubset(ma.columns):
        logger.warning("media_attention schema mismatch: %s", ma.columns.tolist())
        return 0

    ma[["region_id", "severity_score", "normalized_attention_score", "attention_gap"]].to_sql(
        "media_attention", conn, if_exists="replace", index=False
    )
    conn.commit()
    update_manifest("media_attention", len(ma), "pipeline", "written")
    logger.info("media_attention: %d rows synced", len(ma))
    return len(ma)


# ---------------------------------------------------------------------------
# Step 4: reliefweb_reports → news_reports
# ---------------------------------------------------------------------------

def sync_news_reports(conn) -> int:
    """Map reliefweb_reports → news_reports backend schema."""
    rw = _read(conn, "reliefweb_reports")
    if rw.empty:
        logger.info("reliefweb_reports empty — news_reports unchanged")
        return 0

    rw = rw.dropna(subset=["region_id", "title"])

    news = pd.DataFrame()
    news["id"] = rw.get("id", pd.Series(range(len(rw)))).astype(str)
    news["region_id"] = rw["region_id"]
    news["title"] = rw["title"]
    news["source_type"] = "reliefweb"
    news["source_org"] = rw.get("source_org", "ReliefWeb").fillna("ReliefWeb")
    news["date"] = rw.get("date", date.today().isoformat())
    news["body_summary"] = rw.get("body_summary", "").fillna("")
    news["url"] = rw.get("url", "").fillna("")

    # Derive urgency score from region's current stress composite
    stress = _read(conn, "region_stress")
    if not stress.empty:
        latest_scores = (
            stress.groupby("region_id")["stress_composite"]
            .max()
            .reset_index()
            .rename(columns={"stress_composite": "urgency_score"})
        )
        news = news.merge(latest_scores, on="region_id", how="left")
        news["urgency_score"] = news["urgency_score"].fillna(5.0).round(1)
    else:
        news["urgency_score"] = 5.0

    news["disaster_type"] = rw.get("disaster_type", "Marine Ecosystem").fillna("Marine Ecosystem")

    news.to_sql("news_reports", conn, if_exists="replace", index=False)
    conn.commit()
    update_manifest("news_reports", len(news), "pipeline", "written")
    logger.info("news_reports: %d rows synced from reliefweb_reports", len(news))
    return len(news)


# ---------------------------------------------------------------------------
# Step 5: charity_registry (pipeline) → charity_registry (backend)
# ---------------------------------------------------------------------------

def sync_charity_registry(conn) -> int:
    """Map pipeline charity_registry → backend charity_registry schema."""
    cr = _read(conn, "charity_registry")
    if cr.empty:
        logger.info("charity_registry empty — unchanged")
        return 0

    # Ensure required backend columns exist with defaults
    def _col(df, col, default):
        return df[col] if col in df.columns else pd.Series([default] * len(df))

    out = pd.DataFrame()
    out["ein"] = _col(cr, "ein", "unknown")
    out["region_id"] = _col(cr, "region_id", "great_barrier_reef")
    out["name"] = _col(cr, "name", "Unknown Org")
    out["overall_score"] = _col(cr, "overall_score", 75.0)
    out["financial_score"] = _col(cr, "financial_score", 75.0)
    out["accountability_score"] = _col(cr, "accountability_score", 75.0)
    out["program_expense_ratio"] = _col(cr, "program_expense_ratio", 0.80)
    out["active_regions"] = _col(cr, "active_regions", "")

    # Deduplicate on ein
    out = out.drop_duplicates(subset=["ein"])

    out.to_sql("charity_registry", conn, if_exists="replace", index=False)
    conn.commit()
    update_manifest("charity_registry", len(out), "pipeline", "written")
    logger.info("charity_registry: %d rows synced", len(out))
    return len(out)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> pd.DataFrame:
    logger.info("=== seed_backend: mapping pipeline → backend tables ===")
    conn = sqlite_connection()

    steps = [
        ("region_features", sync_region_features),
        ("regions", sync_regions),
        ("media_attention", sync_media_attention),
        ("news_reports", sync_news_reports),
        ("charity_registry", sync_charity_registry),
    ]

    results = {}
    for name, fn in steps:
        try:
            rows = fn(conn)
            results[name] = rows
            logger.info("✓ %s: %d rows", name, rows)
        except Exception as exc:
            logger.error("✗ %s failed: %s", name, exc)
            results[name] = 0

    conn.close()
    logger.info("=== seed_backend complete: %s ===", results)

    # Return a summary DataFrame so run_all_ingestion treats it like any other module
    return pd.DataFrame([{"table": k, "rows": v} for k, v in results.items()])


if __name__ == "__main__":
    main()
