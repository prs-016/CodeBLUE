from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import ensure_schema, load_or_synthetic, parse_args, request_with_retry, save_cache, setup_logging, sqlite_connection, write_table


URL = "https://oceandata.sci.gsfc.nasa.gov/"
TABLE = "ocean_color"


def transform(df: pd.DataFrame, conn) -> pd.DataFrame:
    rename_map = {
        "Date": "date",
        "date": "date",
        "Chlorophyll(mg/m3)": "chlorophyll_mg_m3",
        "chlorophyll": "chlorophyll_mg_m3",
        "Water_Clarity": "water_clarity",
        "region_id": "region_id",
    }
    clean = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}).copy()
    for column in ["region_id", "date", "chlorophyll_mg_m3", "water_clarity"]:
        if column not in clean.columns:
            clean[column] = None
    clean["date"] = pd.to_datetime(clean["date"], errors="coerce")
    clean["chlorophyll_mg_m3"] = pd.to_numeric(clean["chlorophyll_mg_m3"], errors="coerce")
    clean = clean.dropna(subset=["region_id", "date", "chlorophyll_mg_m3"]).sort_values(["region_id", "date"])
    try:
        o2_df = pd.read_sql_query("SELECT region_id, date, sst_anomaly_c FROM sst_observations", conn)
    except Exception:  # noqa: BLE001
        o2_df = pd.DataFrame(columns=["region_id", "date", "sst_anomaly_c"])
    o2_df["date"] = pd.to_datetime(o2_df["date"], errors="coerce")
    o2_proxy = o2_df.rename(columns={"sst_anomaly_c": "o2_proxy"})
    merged = clean.merge(o2_proxy, on=["region_id", "date"], how="left")
    merged["o2_proxy"] = 4.5 - merged["o2_proxy"].fillna(0) * 1.3
    baseline = merged.groupby("region_id")["chlorophyll_mg_m3"].transform("median")
    merged["hypoxia_flag"] = (merged["chlorophyll_mg_m3"] > baseline * 2) & (merged["o2_proxy"] < 2.0)
    merged["date"] = merged["date"].dt.strftime("%Y-%m-%d")
    return merged[["region_id", "date", "chlorophyll_mg_m3", "water_clarity", "hypoxia_flag"]].round(6)


def main() -> pd.DataFrame:
    args = parse_args("Ingest NASA Ocean Color data.")
    logger = setup_logging("nasa_ocean_color")
    conn = sqlite_connection()
    ensure_schema(conn)
    user = os.getenv("NASA_EARTHDATA_USER")
    password = os.getenv("NASA_EARTHDATA_PASS")
    try:
        if not user or not password:
            raise RuntimeError("NASA Earthdata credentials unavailable")
        response = request_with_retry(URL, headers={"Accept": "text/csv"})
        source = "live"
        tables = pd.read_html(response.text)
        if not tables:
            raise RuntimeError("No NASA Ocean Color tables found")
        raw = tables[0]
        frame = transform(raw, conn)
        save_cache(frame, TABLE)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Live fetch failed: %s", exc)
        frame, source = load_or_synthetic(TABLE, TABLE, logger)
        frame = transform(frame, conn)
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source=source, logger=logger)


if __name__ == "__main__":
    main()
