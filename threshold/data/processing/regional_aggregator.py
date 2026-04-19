from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import ensure_schema, parse_args, setup_logging, sqlite_connection, write_table


TABLE = "regional_aggregates"


def build_aggregates(conn) -> pd.DataFrame:
    frame = pd.read_sql_query("SELECT * FROM region_stress", conn)
    if frame.empty:
        raise RuntimeError("region_stress is empty")
    frame["date"] = pd.to_datetime(frame["date"])
    monthly = (
        frame.assign(year_month=frame["date"].dt.to_period("M").astype(str))
        .groupby(["region_id", "year_month"], as_index=False)
        .agg(
            stress_composite=("stress_composite", "mean"),
            sst_anomaly=("sst_anomaly", "mean"),
            o2_current=("o2_current", "mean"),
            active_situation_reports=("active_situation_reports", "max"),
        )
    )
    return monthly


def main() -> pd.DataFrame:
    args = parse_args("Aggregate regional features into monthly windows.")
    logger = setup_logging("regional_aggregator")
    conn = sqlite_connection()
    ensure_schema(conn)
    frame = build_aggregates(conn)
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source="derived", logger=logger)


if __name__ == "__main__":
    main()
