from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import COUNTRY_TO_REGION, ensure_schema, load_or_synthetic, parse_args, request_with_retry, save_cache, setup_logging, sqlite_connection, write_table


URL = "https://api.reliefweb.int/v1/reports"
TABLE = "reliefweb_reports"
DISASTER_TYPES = {"Flood", "Drought", "Cyclone", "Tropical Storm", "Marine Ecosystem"}


def transform(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        country = row.get("country") or row.get("fields.primary_country.name")
        disaster_type = row.get("disaster_type") or row.get("fields.disaster_type.name")
        if disaster_type not in DISASTER_TYPES:
            continue
        region_id = COUNTRY_TO_REGION.get(country)
        rows.append(
            {
                "id": row.get("id"),
                "title": row.get("title") or row.get("fields.title"),
                "date": row.get("date") or row.get("fields.date.created"),
                "country": country,
                "disaster_type": disaster_type,
                "source_org": row.get("source") or row.get("fields.source[0].name"),
                "body_summary": (row.get("body") or row.get("fields.body-html") or "")[:400],
                "url": row.get("url") or row.get("fields.url"),
                "crisis_active_flag": bool(region_id),
                "region_id": region_id,
            }
        )
    clean = pd.DataFrame(rows)
    if clean.empty:
        return clean.reindex(columns=["id", "title", "date", "country", "disaster_type", "source_org", "body_summary", "url", "crisis_active_flag", "region_id"])
    clean["date"] = pd.to_datetime(clean["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    return clean


def fetch_live() -> pd.DataFrame:
    offset = 0
    frames = []
    while True:
        response = request_with_retry(URL, params={"appname": "threshold-datahacks", "limit": 50, "offset": offset})
        payload = response.json()
        data = payload.get("data", [])
        if not data:
            break
        frames.append(pd.json_normalize(data))
        offset += 50
        if offset >= 200:
            break
    if not frames:
        raise RuntimeError("No ReliefWeb reports")
    return pd.concat(frames, ignore_index=True)


def main() -> pd.DataFrame:
    args = parse_args("Ingest ReliefWeb reports.")
    logger = setup_logging("reliefweb")
    conn = sqlite_connection()
    ensure_schema(conn)
    try:
        source = "live"
        frame = transform(fetch_live())
        save_cache(frame, TABLE)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ReliefWeb fetch failed: %s", exc)
        frame, source = load_or_synthetic(TABLE, TABLE, logger)
        frame = transform(frame)
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source=source, logger=logger)


if __name__ == "__main__":
    main()
