from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import ensure_schema, parse_args, setup_logging, sqlite_connection, write_table
from processing.constants import STRESS_WEIGHTS


TABLE = "region_stress"


def build_region_stress(conn) -> pd.DataFrame:
    sst = pd.read_sql_query("SELECT * FROM sst_observations", conn)
    co2 = pd.read_sql_query("SELECT * FROM keeling_curve", conn)
    coral = _maybe_read(conn, "coral_bleaching_alerts")
    press = _maybe_read(conn, "scientific_events")
    reliefweb = _maybe_read(conn, "reliefweb_reports")

    if sst.empty:
        raise RuntimeError("sst_observations is empty")

    sst["date"] = pd.to_datetime(sst["date"])
    sst = sst.sort_values(["region_id", "date"])
    sst["sst_current"] = sst["sst_c"]
    sst["sst_anomaly"] = sst["sst_anomaly_c"]
    sst["sst_anomaly_30d_avg"] = sst.groupby("region_id")["sst_anomaly_c"].transform(lambda series: series.rolling(30, min_periods=1).mean())
    sst["sst_acceleration"] = sst.groupby("region_id")["sst_anomaly_c"].diff(30).fillna(0.0)
    sst["bleaching_risk_flag"] = sst.get("bleaching_risk", False).astype(bool)

    co2["date"] = pd.to_datetime(co2["date"])
    co2 = co2[["date", "co2_ppm", "acceleration"]].rename(
        columns={"co2_ppm": "co2_regional_ppm", "acceleration": "co2_yoy_acceleration"}
    )
    stress = sst.merge(co2, on="date", how="left")

    if not coral.empty:
        coral["date"] = pd.to_datetime(coral["date"])
        coral = coral.rename(columns={"dhw": "dhw_current", "alert_level": "bleaching_alert_level"})
        stress = stress.merge(
            coral[["region_id", "date", "dhw_current", "bleaching_alert_level"]],
            on=["region_id", "date"],
            how="left",
        )
    stress["dhw_current"] = stress.get("dhw_current", 0.0).fillna(0.0)
    stress["bleaching_alert_level"] = stress.get("bleaching_alert_level", 0).fillna(0).astype(int)

    stress["o2_current"] = np.where(
        stress["region_id"].isin(["arabian_sea", "baltic_sea", "mekong_delta", "gulf_of_mexico"]),
        4.5 - stress["sst_anomaly_30d_avg"] * 0.8,
        5.6 - stress["sst_anomaly_30d_avg"] * 0.35,
    )
    stress["o2_deviation"] = stress["o2_current"] - stress.groupby("region_id")["o2_current"].transform("mean")
    stress["o2_trend_90d"] = stress.groupby("region_id")["o2_current"].diff(90).fillna(0.0)
    stress["hypoxia_risk"] = np.clip((5.0 - stress["o2_current"]) / 3.0, 0.0, 1.0)
    stress["hypoxia_flag"] = stress["o2_current"] < 2.0
    stress["chlorophyll_anomaly"] = np.clip(stress["sst_anomaly_30d_avg"] * 1.4, 0.0, None)
    stress["larvae_count_trend"] = np.where(stress["region_id"] == "california_current", -0.12 + stress["sst_acceleration"] * -0.2, 0.0)
    stress["nitrate_anomaly"] = np.clip(stress["chlorophyll_anomaly"] * 0.42, 0.0, None)
    stress["phosphate_anomaly"] = np.clip(stress["chlorophyll_anomaly"] * 0.18, 0.0, None)

    if not press.empty:
        press["date"] = pd.to_datetime(press["date"])
        press_counts = press.groupby(["region_id", "date"]).size().reset_index(name="scientific_event_count")
        stress = stress.merge(press_counts, on=["region_id", "date"], how="left")
        stress["scientific_event_flag"] = stress["scientific_event_count"].fillna(0).gt(0)
    else:
        stress["scientific_event_flag"] = False

    if not reliefweb.empty:
        reliefweb["date"] = pd.to_datetime(reliefweb["date"])
        country_map = {
            "great_barrier_reef": "Australia",
            "mekong_delta": "Vietnam",
            "arabian_sea": "India",
            "california_current": "United States",
            "gulf_of_mexico": "United States",
            "coral_triangle": "Philippines",
            "baltic_sea": "Sweden",
            "bengal_bay": "Bangladesh",
        }
        report_counts = reliefweb.groupby(["country", "date"]).size().reset_index(name="active_situation_reports")
        stress["country"] = stress["region_id"].map(country_map)
        stress = stress.merge(report_counts, on=["country", "date"], how="left")
        stress["active_situation_reports"] = stress["active_situation_reports"].fillna(0).astype(int)
    else:
        stress["active_situation_reports"] = 0

    normalized = {}
    for feature in STRESS_WEIGHTS:
        values = stress[feature].astype(float)
        minimum = values.min()
        span = max(values.max() - minimum, 1e-6)
        normalized[feature] = (values - minimum) / span
    stress["stress_composite"] = sum(normalized[column] * weight for column, weight in STRESS_WEIGHTS.items()) * 10
    stress["date"] = stress["date"].dt.strftime("%Y-%m-%d")

    columns = [
        "region_id",
        "date",
        "sst_current",
        "sst_anomaly",
        "sst_anomaly_30d_avg",
        "sst_acceleration",
        "bleaching_risk_flag",
        "o2_current",
        "o2_deviation",
        "o2_trend_90d",
        "hypoxia_risk",
        "hypoxia_flag",
        "chlorophyll_anomaly",
        "larvae_count_trend",
        "dhw_current",
        "bleaching_alert_level",
        "co2_regional_ppm",
        "co2_yoy_acceleration",
        "nitrate_anomaly",
        "phosphate_anomaly",
        "scientific_event_flag",
        "active_situation_reports",
        "stress_composite",
    ]
    return stress[columns].fillna(0.0)


def _maybe_read(conn, table: str) -> pd.DataFrame:
    query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
    if conn.execute(query, (table,)).fetchone() is None:
        return pd.DataFrame()
    return pd.read_sql_query(f"SELECT * FROM {table}", conn)


def main() -> pd.DataFrame:
    args = parse_args("Compute THRESHOLD regional feature matrix.")
    logger = setup_logging("feature_engineering")
    conn = sqlite_connection()
    ensure_schema(conn)
    frame = build_region_stress(conn)
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source="derived", logger=logger)


if __name__ == "__main__":
    main()
