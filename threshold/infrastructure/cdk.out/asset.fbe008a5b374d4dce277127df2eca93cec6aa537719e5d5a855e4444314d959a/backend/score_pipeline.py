"""
score_pipeline.py — Scientific threshold proximity scoring.

Replaces the forgotten arbitrary formula with scores grounded in:

  IPCC AR6 WG2 Ch.3  → SST thermal stress  (1 °C = coral bleach threshold, 3 °C = catastrophic)
  EPA / NOAA          → Dissolved-O2 hypoxia (<2 mg/L = <1.4 ml/L = hypoxic zone)
  NOAA CRW            → DHW scale (4 = watch, 8 = Alert-1, 16 = Alert-2 / severe mortality)
  IPCC acidification  → CO2 trajectory (280 ppm pre-industrial → 560 ppm = aragonite dissolution)
  GDELT (Snowflake)   → Per-region political conflict index (ecosystem pressure proxy)
  Nutrient stress     → Chlorophyll + nitrate anomaly magnitude

Reads: REGION_FEATURES (existing measured columns), GDELT (already in Snowflake).
Writes: THRESHOLD_PROXIMITY_SCORE updated in place via MERGE.
Also updates: REGIONS.current_score, REGIONS.alert_level, REGIONS.days_to_threshold.
"""
from __future__ import annotations

import logging
from typing import Dict

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# ---------------------------------------------------------------------------
# Region bounding boxes (for GDELT spatial query)
# ---------------------------------------------------------------------------
REGION_META: Dict[str, dict] = {
    "great_barrier_reef": {"lat": (-25, -10), "lon": (142, 155), "threat": "thermal"},
    "coral_triangle":     {"lat": (-10,  10), "lon": (115, 145), "threat": "thermal"},
    "mekong_delta":       {"lat": (  8,  15), "lon": (103, 110), "threat": "hypoxia"},
    "arabian_sea":        {"lat": (  8,  25), "lon": ( 55,  78), "threat": "hypoxia"},
    "bengal_bay":         {"lat": (  8,  22), "lon": ( 79, 100), "threat": "thermal"},
    "california_current": {"lat": ( 30,  48), "lon": (-130,-117), "threat": "acidification"},
    "gulf_of_mexico":     {"lat": ( 18,  30), "lon": ( -98, -80), "threat": "hypoxia"},
    "baltic_sea":         {"lat": ( 53,  66), "lon": (   9,  30), "threat": "hypoxia"},
}

# ---------------------------------------------------------------------------
# Threat-type weights — each column of weights sums to 1.0
# Based on which stressor is primary for each ecosystem type
# ---------------------------------------------------------------------------
THREAT_WEIGHTS = {
    #                     sst    o2    dhw   alert  co2   nutrient  conflict
    "thermal":      dict(sst=0.30, o2=0.14, dhw=0.24, alert=0.14, co2=0.08, nutrient=0.05, conflict=0.05),
    "hypoxia":      dict(sst=0.12, o2=0.38, dhw=0.04, alert=0.02, co2=0.10, nutrient=0.26, conflict=0.08),
    "acidification":dict(sst=0.18, o2=0.20, dhw=0.04, alert=0.02, co2=0.38, nutrient=0.12, conflict=0.06),
}


# ---------------------------------------------------------------------------
# Step 1: Query GDELT (already in Snowflake) for per-region conflict index
# ---------------------------------------------------------------------------
def fetch_gdelt_conflict_scores(engine: Engine) -> Dict[str, float]:
    """
    Aggregate GDELT events inside each region's bounding box (post-1990).
    Returns a 0–1 conflict index per region.
      Goldstein scale: -10 (destabilising) → +10 (cooperative)
      We invert and normalise so higher conflict → higher pressure score.
    """
    logger.info("Querying GDELT conflict index per region …")
    scores: Dict[str, float] = {}

    with engine.connect() as conn:
        for region_id, meta in REGION_META.items():
            lat_min, lat_max = sorted(meta["lat"])
            lon_min, lon_max = sorted(meta["lon"])
            row = conn.execute(
                text("""
                    SELECT
                        AVG(GOLDSTEIN)   AS avg_goldstein,
                        SUM(NUMARTS)     AS total_numarts,
                        COUNT(*)         AS event_count
                    FROM GDELT
                    WHERE ACTIONGEOLAT  BETWEEN :lat_min AND :lat_max
                      AND ACTIONGEOLONG BETWEEN :lon_min AND :lon_max
                      AND DATE >= 19900101
                """),
                {"lat_min": lat_min, "lat_max": lat_max,
                 "lon_min": lon_min, "lon_max": lon_max},
            ).fetchone()

            if row and row[0] is not None:
                goldstein = float(row[0])
                # -10 → conflict_index=1.0 ; +10 → 0.0 ; neutral(0) → 0.33
                conflict_index = max(0.0, min(1.0, (5.0 - goldstein) / 15.0))
                logger.info(
                    "  %s: goldstein=%.3f  numarts=%s  events=%s  → conflict=%.3f",
                    region_id, goldstein, row[1], row[2], conflict_index,
                )
            else:
                conflict_index = 0.33  # neutral fallback
                logger.warning("  %s: no GDELT data in bounding box, using neutral 0.33", region_id)

            scores[region_id] = conflict_index

    return scores


# ---------------------------------------------------------------------------
# Step 2: Scientific scoring formula
# ---------------------------------------------------------------------------
def score_from_features(
    sst_anomaly: float,
    o2_current: float,
    dhw: float,
    alert: float,
    co2_ppm: float,
    chlor_anomaly: float,
    nitrate_anomaly: float,
    conflict_index: float,
    threat: str,
) -> float:
    """
    Map physical measurements to a 0–10 threshold proximity score using
    published scientific thresholds.

    References
    ----------
    SST   : IPCC AR6 WG2 Box 3.4  — coral bleaching onset at MMM+1 °C
    O2    : NOAA/EPA — hypoxic zone ≤ 2 mg/L (≈ 1.4 ml/L)
    DHW   : NOAA CRW — alert-2 at 8 DHW, severe mortality at 16 DHW
    CO2   : Caldeira & Wickett 2003 — aragonite dissolution trajectory 280→560 ppm
    GDELT : Goldstein (1992) conflict–cooperation scale
    """
    # --- SST thermal stress (0 = no anomaly, 1 = +3 °C above baseline) ----
    sst_score = min(1.0, max(0.0, sst_anomaly / 3.0))

    # --- Dissolved O2 hypoxia (0 = healthy ≥5 ml/L, 1 = hypoxic ≤1.4 ml/L)
    o2_score = min(1.0, max(0.0, (5.0 - o2_current) / 3.6))

    # --- Degree Heating Weeks (0 = 0 DHW, 1 = severe mortality ≥16 DHW) --
    dhw_score = min(1.0, dhw / 16.0)

    # --- Bleaching alert level (NOAA CRW 0–4 scale → 0–1) ----------------
    alert_score = min(1.0, alert / 4.0)

    # --- CO2 / ocean acidification ----------------------------------------
    # 280 ppm = pre-industrial baseline; 560 ppm = 2× pre-industrial
    co2_score = min(1.0, max(0.0, (co2_ppm - 280.0) / 280.0))

    # --- Nutrient / eutrophication stress (chlor + nitrate anomaly) -------
    nutrient_score = min(1.0, (abs(chlor_anomaly) + abs(nitrate_anomaly) * 0.4) / 3.0)

    # --- Political conflict / ecosystem pressure (GDELT) ------------------
    conflict_score = conflict_index

    w = THREAT_WEIGHTS.get(threat, THREAT_WEIGHTS["hypoxia"])
    raw = (
        sst_score      * w["sst"]      +
        o2_score       * w["o2"]       +
        dhw_score      * w["dhw"]      +
        alert_score    * w["alert"]    +
        co2_score      * w["co2"]      +
        nutrient_score * w["nutrient"] +
        conflict_score * w["conflict"]
    ) * 10.0

    return round(min(10.0, max(0.0, raw)), 3)


# ---------------------------------------------------------------------------
# Step 3: Read features, recompute, write back via MERGE
# ---------------------------------------------------------------------------
def _days_from_score(s: float) -> int:
    # Full 0–10 scale — current data peaks ~5.2 so spread coverage downward
    if s >= 9.0: return 14
    if s >= 8.0: return 30
    if s >= 7.0: return 60
    if s >= 6.0: return 90
    if s >= 5.0: return 150
    if s >= 4.0: return 240
    if s >= 3.0: return 365
    if s >= 2.0: return 500
    return 730


def _alert_from_score(s: float) -> str:
    if s >= 7.0: return "critical"
    if s >= 5.0: return "high"
    if s >= 3.5: return "watch"
    return "normal"


def run_score_update(engine: Engine) -> dict:
    # 1. GDELT conflict scores (one per region, spatial aggregate)
    conflict_scores = fetch_gdelt_conflict_scores(engine)

    # 2. Load all feature rows
    logger.info("Loading REGION_FEATURES …")
    df = pd.read_sql("SELECT * FROM REGION_FEATURES ORDER BY REGION_ID, DATE", engine)
    df.columns = [c.lower() for c in df.columns]
    logger.info("  %d rows loaded across %d regions", len(df), df["region_id"].nunique())

    # 3. Recompute scores
    def _recompute(row):
        region_id = row["region_id"]
        threat = REGION_META.get(region_id, {}).get("threat", "hypoxia")
        return score_from_features(
            sst_anomaly    = float(row.get("sst_anomaly") or 0.0),
            o2_current     = float(row.get("o2_current") or 5.0),
            dhw            = float(row.get("dhw_current") or 0.0),
            alert          = float(row.get("bleaching_alert_level") or 0.0),
            co2_ppm        = float(row.get("co2_regional_ppm") or 415.0),
            chlor_anomaly  = float(row.get("chlorophyll_anomaly") or 0.0),
            nitrate_anomaly= float(row.get("nitrate_anomaly") or 0.0),
            conflict_index = conflict_scores.get(region_id, 0.33),
            threat         = threat,
        )

    df["new_score"] = df.apply(_recompute, axis=1)
    logger.info(
        "New score stats — mean=%.3f  std=%.3f  min=%.3f  max=%.3f",
        df["new_score"].mean(), df["new_score"].std(),
        df["new_score"].min(),  df["new_score"].max(),
    )

    # 4. Write back via staging MERGE (Snowflake-safe)
    updates = df[["region_id", "date", "new_score"]].copy()
    updates.columns = ["REGION_ID", "DATE", "NEW_SCORE"]

    logger.info("Writing %d updated scores to Snowflake …", len(updates))
    with engine.begin() as conn:
        dialect = conn.dialect.name

        if dialect == "snowflake":
            conn.execute(text("""
                CREATE OR REPLACE TEMPORARY TABLE _score_updates (
                    REGION_ID TEXT,
                    DATE      TEXT,
                    NEW_SCORE FLOAT
                )
            """))
            # Batch insert into staging table
            rows = [
                {"rid": r["REGION_ID"], "dt": str(r["DATE"]), "sc": float(r["NEW_SCORE"])}
                for _, r in updates.iterrows()
            ]
            conn.execute(
                text("INSERT INTO _score_updates (REGION_ID, DATE, NEW_SCORE) VALUES (:rid, :dt, :sc)"),
                rows,
            )
            # MERGE into REGION_FEATURES
            conn.execute(text("""
                MERGE INTO REGION_FEATURES rf
                USING _score_updates su
                ON rf.REGION_ID = su.REGION_ID AND rf.DATE = su.DATE
                WHEN MATCHED THEN UPDATE SET
                    THRESHOLD_PROXIMITY_SCORE = su.NEW_SCORE
            """))
            logger.info("MERGE complete.")
        else:
            # SQLite fallback — individual updates
            for _, r in updates.iterrows():
                conn.execute(
                    text("UPDATE region_features SET threshold_proximity_score = :sc WHERE region_id = :rid AND date = :dt"),
                    {"sc": float(r["NEW_SCORE"]), "rid": r["REGION_ID"], "dt": str(r["DATE"])},
                )

    # 5. Update REGIONS table with new aggregate scores
    region_agg = (
        df.sort_values("date")
          .groupby("region_id")
          .tail(30)
          .groupby("region_id")["new_score"]
          .mean()
          .reset_index()
    )
    region_agg.columns = ["region_id", "current_score"]

    logger.info("Updating REGIONS table …")
    with engine.begin() as conn:
        for _, r in region_agg.iterrows():
            score = float(r["current_score"])
            conn.execute(
                text("""
                    UPDATE regions SET
                        current_score     = :score,
                        days_to_threshold = :days,
                        alert_level       = :alert
                    WHERE id = :rid
                """),
                {
                    "score": round(score, 3),
                    "days":  _days_from_score(score),
                    "alert": _alert_from_score(score),
                    "rid":   r["region_id"],
                },
            )
    logger.info("REGIONS updated.")

    summary = {
        "rows_updated": len(df),
        "regions_updated": len(region_agg),
        "score_mean": round(float(df["new_score"].mean()), 3),
        "score_std":  round(float(df["new_score"].std()), 3),
        "score_min":  round(float(df["new_score"].min()), 3),
        "score_max":  round(float(df["new_score"].max()), 3),
        "gdelt_conflict_scores": {k: round(v, 3) for k, v in conflict_scores.items()},
    }
    logger.info("Score update complete: %s", summary)
    return summary


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from database import engine
    result = run_score_update(engine)
    print(result)
