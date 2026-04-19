from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import ensure_schema, load_or_synthetic, parse_args, parse_csv_text, request_with_retry, save_cache, setup_logging, sqlite_connection, write_table


URL = "https://mooring.ucsd.edu/cgi-bin/getDailyData.pl"
TABLE = "scripps_pier"


def transform(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "Timestamp": "timestamp",
        "Temp(C)": "temp_c",
        "O2(mg/L)": "o2_mg_l",
        "Chlorophyll(ug/L)": "chlorophyll_ug_l",
        "Salinity": "salinity",
    }
    clean = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}).copy()
    for column in ["timestamp", "temp_c", "o2_mg_l", "chlorophyll_ug_l", "salinity"]:
        if column not in clean.columns:
            clean[column] = None
    clean["timestamp"] = pd.to_datetime(clean["timestamp"], errors="coerce")
    for col in ["temp_c", "o2_mg_l", "chlorophyll_ug_l", "salinity"]:
        clean[col] = pd.to_numeric(clean[col], errors="coerce")
    clean = clean.dropna(subset=["timestamp"]).sort_values("timestamp")
    clean["calibration_trigger"] = ((clean["temp_c"] - clean["temp_c"].rolling(24, min_periods=1).mean()).abs() / clean["temp_c"].clip(lower=0.1)) > 0.15
    clean["timestamp"] = clean["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return clean[["timestamp", "temp_c", "o2_mg_l", "chlorophyll_ug_l", "salinity", "calibration_trigger"]].round(6)


def main() -> pd.DataFrame:
    args = parse_args("Ingest Scripps Pier observations.")
    logger = setup_logging("scripps_pier")
    conn = sqlite_connection()
    ensure_schema(conn)
    try:
        response = request_with_retry(URL, params={"format": "csv"})
        source = "live"
        frame = transform(parse_csv_text(response.text))
        save_cache(frame, TABLE)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Live fetch failed: %s", exc)
        frame, source = load_or_synthetic(TABLE, TABLE, logger)
        frame = transform(frame)
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source=source, logger=logger)


if __name__ == "__main__":
    main()
