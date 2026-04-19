from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import ensure_schema, load_or_synthetic, parse_args, request_with_retry, save_cache, setup_logging, sqlite_connection, write_table


URL = "https://data.humdata.org/api/3/action/datastore_search"
TABLE = "hdx_funding_needs"


def transform(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "Year": "year",
        "Country": "country",
        "People_in_Need": "people_in_need",
        "Funds_Required(USD)": "funds_required_usd",
        "Funds_Received(USD)": "funds_received_usd",
        "Gap(USD)": "gap_usd",
    }
    clean = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}).copy()
    for col in ["year", "country", "people_in_need", "funds_required_usd", "funds_received_usd", "gap_usd"]:
        if col not in clean.columns:
            clean[col] = None
    for col in ["people_in_need", "funds_required_usd", "funds_received_usd", "gap_usd"]:
        clean[col] = pd.to_numeric(clean[col], errors="coerce")
    clean["year"] = pd.to_numeric(clean["year"], errors="coerce").fillna(pd.Timestamp.utcnow().year).astype(int)
    clean["coverage_ratio"] = (clean["funds_received_usd"] / clean["funds_required_usd"]).replace([float("inf"), -float("inf")], 0).fillna(0)
    return clean[["year", "country", "people_in_need", "funds_required_usd", "funds_received_usd", "gap_usd", "coverage_ratio"]]


def main() -> pd.DataFrame:
    args = parse_args("Ingest HDX funding needs.")
    logger = setup_logging("hdx")
    conn = sqlite_connection()
    ensure_schema(conn)
    try:
        response = request_with_retry(URL)
        source = "live"
        payload = response.json()
        records = payload.get("result", {}).get("records", [])
        frame = transform(pd.DataFrame(records))
        save_cache(frame, TABLE)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Live fetch failed: %s", exc)
        frame, source = load_or_synthetic(TABLE, TABLE, logger)
        frame = transform(frame)
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source=source, logger=logger)


if __name__ == "__main__":
    main()
