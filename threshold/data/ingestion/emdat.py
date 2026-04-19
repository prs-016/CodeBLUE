from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import ensure_schema, load_or_synthetic, parse_args, save_cache, setup_logging, sqlite_connection, write_table


TABLE = "historical_disasters"


def transform(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "Year": "year",
        "Country": "country",
        "Disaster_Type": "disaster_type",
        "Disaster Type": "disaster_type",
        "Deaths": "deaths",
        "Affected": "total_affected",
        "Economic_Loss(USD)": "economic_loss_usd_2024",
        "Insured_Loss(USD)": "insured_loss_usd_2024",
    }
    clean = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}).copy()
    for col in ["year", "country", "disaster_type", "deaths", "total_affected", "economic_loss_usd_2024", "insured_loss_usd_2024"]:
        if col not in clean.columns:
            clean[col] = None
    clean["year"] = pd.to_numeric(clean["year"], errors="coerce")
    for col in ["deaths", "total_affected", "economic_loss_usd_2024", "insured_loss_usd_2024"]:
        clean[col] = pd.to_numeric(clean[col], errors="coerce").fillna(0.0)
    inflation_multiplier = 1.0 + ((2024 - clean["year"].fillna(2024)) * 0.025)
    clean["economic_loss_usd_2024"] = clean["economic_loss_usd_2024"] * inflation_multiplier
    clean["insured_loss_usd_2024"] = clean["insured_loss_usd_2024"] * inflation_multiplier
    return clean[["year", "country", "disaster_type", "deaths", "total_affected", "economic_loss_usd_2024", "insured_loss_usd_2024"]]


def main() -> pd.DataFrame:
    args = parse_args("Load EM-DAT historical disasters.")
    logger = setup_logging("emdat")
    conn = sqlite_connection()
    ensure_schema(conn)
    csv_path = os.getenv("EMDAT_CSV_PATH")
    try:
        if not csv_path or not Path(csv_path).exists():
            raise RuntimeError("EMDAT_CSV_PATH missing or file not found")
        source = "live"
        frame = transform(pd.read_csv(csv_path))
        save_cache(frame, TABLE)
    except Exception as exc:  # noqa: BLE001
        logger.warning("EM-DAT file unavailable: %s", exc)
        frame, source = load_or_synthetic(TABLE, TABLE, logger)
        frame = transform(frame)
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source=source, logger=logger)


if __name__ == "__main__":
    main()
