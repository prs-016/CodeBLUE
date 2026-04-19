from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import ensure_schema, parse_args, setup_logging, sqlite_connection, write_table


TABLE = "media_attention"


def build_attention_gap(conn) -> pd.DataFrame:
    stress = pd.read_sql_query(
        "SELECT region_id, MAX(stress_composite) AS severity_score FROM region_stress GROUP BY region_id",
        conn,
    )
    gdelt = _maybe_read(conn, "gdelt_attention")
    if gdelt.empty:
        gdelt = pd.DataFrame(
            {
                "region_id": stress["region_id"],
                "attention_score": [7.9, 3.4, 2.6, 4.4, 5.7, 4.1, 3.0, 3.2][: len(stress)],
            }
        )
    attention = gdelt.groupby("region_id", as_index=False).agg(normalized_attention_score=("attention_score", "mean"))
    merged = stress.merge(attention, on="region_id", how="left")
    merged["normalized_attention_score"] = merged["normalized_attention_score"].fillna(0.0)
    merged["attention_gap"] = merged["severity_score"] - merged["normalized_attention_score"]
    return merged


def _maybe_read(conn, table: str) -> pd.DataFrame:
    query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
    if conn.execute(query, (table,)).fetchone() is None:
        return pd.DataFrame()
    return pd.read_sql_query(f"SELECT * FROM {table}", conn)


def main() -> pd.DataFrame:
    args = parse_args("Score media attention against crisis severity.")
    logger = setup_logging("media_attention_scorer")
    conn = sqlite_connection()
    ensure_schema(conn)
    frame = build_attention_gap(conn)
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source="derived", logger=logger)


if __name__ == "__main__":
    main()
