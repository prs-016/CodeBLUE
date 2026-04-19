from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import ensure_schema, load_or_synthetic, parse_args, request_with_retry, save_cache, setup_logging, sqlite_connection, write_table


URL = "https://www.givewell.org/charities/top-charities"
TABLE = "givewell_impact"


def transform(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "organization": "organization",
        "cost_per_outcome": "cost_per_outcome",
        "outcome_type": "outcome_type",
        "evidence_quality": "evidence_quality",
        "year": "year",
    }
    clean = df.rename(columns=rename_map).copy()
    if clean.empty:
        clean = pd.DataFrame(columns=["organization", "cost_per_outcome", "outcome_type", "evidence_quality", "year"])
    for col in ["organization", "cost_per_outcome", "outcome_type", "evidence_quality", "year"]:
        if col not in clean.columns:
            clean[col] = None
    return clean[["organization", "cost_per_outcome", "outcome_type", "evidence_quality", "year"]]


def main() -> pd.DataFrame:
    args = parse_args("Ingest GiveWell impact benchmarks.")
    logger = setup_logging("givewell")
    conn = sqlite_connection()
    ensure_schema(conn)
    try:
        source = "live"
        response = request_with_retry(URL)
        tables = pd.read_html(response.text)
        if tables:
            raw = tables[0]
            raw.columns = [str(column).strip().lower().replace(" ", "_") for column in raw.columns]
        else:
            raise RuntimeError("No GiveWell tables found")
        frame = transform(raw)
        save_cache(frame, TABLE)
    except Exception as exc:  # noqa: BLE001
        logger.warning("GiveWell scrape failed: %s", exc)
        frame, source = load_or_synthetic(TABLE, TABLE, logger)
        frame = transform(frame)
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source=source, logger=logger)


if __name__ == "__main__":
    main()
