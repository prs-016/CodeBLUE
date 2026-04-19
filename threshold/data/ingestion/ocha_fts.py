from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import OCHA_CLIMATE_KEYWORDS, ensure_schema, load_or_synthetic, parse_args, request_with_retry, save_cache, setup_logging, sqlite_connection, write_table


URL = "https://api.hpc.tools/v2/public/fts/flow"
TABLE = "humanitarian_funding"


def transform(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "Year": "year",
        "Donor": "donor",
        "Recipient": "recipient_org",
        "RecipientOrg": "recipient_org",
        "Country": "country",
        "Crisis_Type": "crisis_type",
        "Amount(USD)": "amount_usd",
        "Status": "status",
        "dateCommitted": "date_committed",
    }
    clean = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}).copy()
    for column in ["year", "donor", "recipient_org", "country", "crisis_type", "amount_usd", "status", "date_committed"]:
        if column not in clean.columns:
            clean[column] = None
    clean["crisis_type"] = clean["crisis_type"].fillna("").astype(str)
    mask = clean["crisis_type"].str.lower().apply(lambda value: any(keyword in value for keyword in OCHA_CLIMATE_KEYWORDS))
    clean = clean[mask]
    clean["amount_usd"] = pd.to_numeric(clean["amount_usd"], errors="coerce")
    clean["year"] = pd.to_numeric(clean["year"], errors="coerce").fillna(pd.Timestamp.utcnow().year).astype(int)
    clean["date_committed"] = pd.to_datetime(clean["date_committed"], errors="coerce").fillna(pd.to_datetime(clean["year"].astype(str) + "-06-30"))
    clean["date_committed"] = clean["date_committed"].dt.strftime("%Y-%m-%d")
    return clean[["year", "donor", "recipient_org", "country", "crisis_type", "amount_usd", "status", "date_committed"]]


def main() -> pd.DataFrame:
    args = parse_args("Ingest OCHA FTS flows.")
    logger = setup_logging("ocha_fts")
    conn = sqlite_connection()
    ensure_schema(conn)
    try:
        response = request_with_retry(URL)
        source = "live"
        payload = response.json()
        raw = pd.json_normalize(payload["data"] if isinstance(payload, dict) and "data" in payload else payload)
        frame = transform(raw)
        save_cache(frame, TABLE)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Live fetch failed: %s", exc)
        frame, source = load_or_synthetic(TABLE, TABLE, logger)
        frame = transform(frame)
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source=source, logger=logger)


if __name__ == "__main__":
    main()
