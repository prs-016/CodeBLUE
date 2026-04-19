from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import REGIONS, ensure_schema, load_or_synthetic, parse_args, request_with_retry, save_cache, setup_logging, sqlite_connection, synthetic_frame, write_table


URL = "https://erddap.noaa.gov/erddap/griddap/ncdc_oisst_v2_avhrr_by_time_zlev_lat_lon.csv"
TABLE = "sst_observations"


def transform(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "Date": "date",
        "date": "date",
        "SST(C)": "sst_c",
        "sst": "sst_c",
        "Anomaly(C)": "sst_anomaly_c",
        "anom": "sst_anomaly_c",
        "region_id": "region_id",
    }
    clean = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}).copy()
    for column in ["region_id", "date", "sst_c", "sst_anomaly_c"]:
        if column not in clean.columns:
            clean[column] = None
    clean["date"] = pd.to_datetime(clean["date"], errors="coerce")
    clean["sst_c"] = pd.to_numeric(clean["sst_c"], errors="coerce")
    clean["sst_anomaly_c"] = pd.to_numeric(clean["sst_anomaly_c"], errors="coerce")
    clean = clean.dropna(subset=["region_id", "date", "sst_c", "sst_anomaly_c"]).sort_values(["region_id", "date"])
    clean["anomaly_8wk_avg"] = clean.groupby("region_id")["sst_anomaly_c"].transform(lambda s: s.rolling(56, min_periods=1).mean())
    clean["bleaching_risk"] = clean["anomaly_8wk_avg"] > 1.5
    clean["date"] = clean["date"].dt.strftime("%Y-%m-%d")
    return clean[["region_id", "date", "sst_c", "sst_anomaly_c", "anomaly_8wk_avg", "bleaching_risk"]].round(6)


def fetch_live(logger) -> pd.DataFrame:
    frames = []
    for region_id, region in REGIONS.items():
        params = {
            "time>=": "2019-01-01T00:00:00Z",
            "time<=": "2024-12-31T00:00:00Z",
            "latitude>=": region["lat"][0],
            "latitude<=": region["lat"][1],
            "longitude>=": region["lon"][0],
            "longitude<=": region["lon"][1],
        }
        logger.info("Fetching NOAA ERDDAP slice for %s", region_id)
        response = request_with_retry(URL, params=params)
        parsed = pd.read_csv(pd.io.common.StringIO(response.text))
        if parsed.empty:
            continue
        date_col = next((c for c in parsed.columns if "time" in c.lower() or "date" in c.lower()), parsed.columns[0])
        sst_col = next((c for c in parsed.columns if "sst" in c.lower()), parsed.columns[-1])
        anomaly_col = next((c for c in parsed.columns if "anom" in c.lower()), sst_col)
        frames.append(
            pd.DataFrame(
                {
                    "region_id": region_id,
                    "date": parsed[date_col],
                    "sst_c": parsed[sst_col],
                    "sst_anomaly_c": parsed[anomaly_col],
                }
            )
        )
    if not frames:
        raise RuntimeError("No NOAA SST records returned")
    return pd.concat(frames, ignore_index=True)


def main() -> pd.DataFrame:
    args = parse_args("Ingest NOAA SST anomaly data.")
    logger = setup_logging("noaa_sst")
    conn = sqlite_connection()
    ensure_schema(conn)
    try:
        raw = fetch_live(logger)
        source = "live"
        frame = transform(raw)
        save_cache(frame, TABLE)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Live fetch failed: %s", exc)
        frame, source = load_or_synthetic(TABLE, TABLE, logger)
        frame = transform(frame)
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source=source, logger=logger)


if __name__ == "__main__":
    main()
