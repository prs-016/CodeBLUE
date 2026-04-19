from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import ensure_schema, load_or_synthetic, parse_args, request_with_retry, save_cache, setup_logging, sqlite_connection, write_table


URL = "https://coralreefwatch.noaa.gov/product/5km/index.php"
TABLE = "coral_bleaching_alerts"


def transform(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "Region": "region_name",
        "Date": "date",
        "DHW": "dhw",
        "Alert_Level": "alert_level",
        "region_id": "region_id",
    }
    clean = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}).copy()
    if "region_id" not in clean.columns:
        clean["region_id"] = clean.get("region_name", "").astype(str).str.lower().str.replace(" ", "_")
    clean["date"] = pd.to_datetime(clean["date"], errors="coerce")
    clean["dhw"] = pd.to_numeric(clean["dhw"], errors="coerce")
    clean["alert_level"] = pd.to_numeric(clean["alert_level"], errors="coerce").fillna(0).astype(int)
    clean["bleaching_probability"] = (clean["dhw"].fillna(0) / 10).clip(0, 1)
    clean["region_alert_critical"] = clean["alert_level"] >= 4
    clean = clean.dropna(subset=["region_id", "date"])
    clean["date"] = clean["date"].dt.strftime("%Y-%m-%d")
    return clean[["region_id", "date", "dhw", "alert_level", "bleaching_probability", "region_alert_critical"]].round(6)


def main() -> pd.DataFrame:
    args = parse_args("Ingest NOAA Coral Reef Watch alerts.")
    logger = setup_logging("coral_reef_watch")
    conn = sqlite_connection()
    ensure_schema(conn)
    try:
        response = request_with_retry(URL, params={"format": "json"})
        source = "live"
        payload = response.json() if "application/json" in response.headers.get("Content-Type", "") else json.loads(response.text)
        frame = transform(pd.DataFrame(payload))
        save_cache(frame, TABLE)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Live fetch failed: %s", exc)
        frame, source = load_or_synthetic(TABLE, TABLE, logger)
        frame = transform(frame)
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source=source, logger=logger)


if __name__ == "__main__":
    main()
