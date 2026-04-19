from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import PRESS_KEYWORDS, REGIONS, ensure_schema, load_or_synthetic, parse_args, request_with_retry, save_cache, setup_logging, sqlite_connection, write_table


SOURCES = {
    "NASA": "https://www.nasa.gov/rss/dyn/ocean_stories.rss",
    "NOAA": "https://www.noaa.gov/media-releases.rss",
}
TABLE = "scientific_events"


def infer_region(text: str) -> str | None:
    lower = text.lower()
    for region_id, meta in REGIONS.items():
        if meta["name"].lower() in lower or region_id.replace("_", " ") in lower:
            return region_id
    if "great barrier reef" in lower:
        return "great_barrier_reef"
    return None


def transform(entries: list[dict[str, str]]) -> pd.DataFrame:
    rows = []
    for entry in entries:
        text = f"{entry['title']} {entry.get('summary', '')}".lower()
        if not any(keyword in text for keyword in PRESS_KEYWORDS):
            continue
        rows.append(
            {
                "date": entry["date"],
                "agency": entry["agency"],
                "title": entry["title"],
                "event_type": next((keyword for keyword in PRESS_KEYWORDS if keyword in text), "ocean"),
                "region_id": infer_region(text),
                "url": entry["url"],
            }
        )
    return pd.DataFrame(rows)


def fetch_feed(agency: str, url: str) -> list[dict[str, str]]:
    root = ET.fromstring(request_with_retry(url).text)
    entries = []
    for item in root.findall(".//item"):
        entries.append(
            {
                "agency": agency,
                "title": item.findtext("title", default=""),
                "summary": item.findtext("description", default=""),
                "date": item.findtext("pubDate", default=""),
                "url": item.findtext("link", default=url),
            }
        )
    return entries


def main() -> pd.DataFrame:
    args = parse_args("Ingest NASA and NOAA scientific press releases.")
    logger = setup_logging("nasa_noaa_press")
    conn = sqlite_connection()
    ensure_schema(conn)
    try:
        entries = []
        for agency, url in SOURCES.items():
            entries.extend(fetch_feed(agency, url))
        source = "live"
        frame = transform(entries)
        save_cache(frame, TABLE)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Press feed fetch failed: %s", exc)
        frame, source = load_or_synthetic(TABLE, TABLE, logger)
        frame = transform(frame.to_dict("records"))
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source=source, logger=logger)


if __name__ == "__main__":
    main()
