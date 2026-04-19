from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import COUNTRY_TO_REGION, ensure_schema, load_or_synthetic, parse_args, request_with_retry, save_cache, setup_logging, sqlite_connection, write_table


URL = "https://api.reliefweb.int/v1/organizations"
TABLE = "charity_regional_presence"


def transform(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        country = row.get("country") or row.get("fields.country.name")
        region_id = COUNTRY_TO_REGION.get(country)
        if not region_id:
            continue
        rows.append(
            {
                "organization": row.get("organization") or row.get("fields.name"),
                "country": country,
                "region_id": region_id,
                "sector": row.get("sector") or row.get("fields.primary_type.name") or "Climate",
                "status": row.get("status") or "Active",
                "last_verified": row.get("last_verified") or pd.Timestamp.utcnow().strftime("%Y-%m-%d"),
            }
        )
    return pd.DataFrame(rows)


def fetch_live() -> pd.DataFrame:
    response = request_with_retry(URL, params={"appname": "threshold-datahacks", "limit": 200})
    payload = response.json()
    return pd.json_normalize(payload.get("data", []))


def main() -> pd.DataFrame:
    args = parse_args("Ingest ReliefWeb 3W organization presence.")
    logger = setup_logging("reliefweb_3w")
    conn = sqlite_connection()
    ensure_schema(conn)
    try:
        source = "live"
        frame = transform(fetch_live())
        save_cache(frame, TABLE)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ReliefWeb 3W fetch failed: %s", exc)
        frame, source = load_or_synthetic(TABLE, TABLE, logger)
        frame = transform(frame)
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source=source, logger=logger)


if __name__ == "__main__":
    main()
