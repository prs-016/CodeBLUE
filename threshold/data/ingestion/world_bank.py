from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import COUNTRY_TO_REGION, ensure_schema, load_or_synthetic, parse_args, request_with_retry, save_cache, setup_logging, sqlite_connection, write_table


URL_TEMPLATE = "https://api.worldbank.org/v2/country/{country}/indicator/EN.CLC.MDAT.ZS"
TABLE = "world_bank_disaster_costs"


def transform(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "country": "country",
        "date": "year",
        "value": "gdp_impact_pct",
        "event": "event",
        "ag_loss_usd": "ag_loss_usd",
        "infra_loss_usd": "infra_loss_usd",
        "recovery_expenditure_usd": "recovery_expenditure_usd",
    }
    clean = df.rename(columns=rename_map).copy()
    for col in ["country", "year", "event", "gdp_impact_pct", "ag_loss_usd", "infra_loss_usd", "recovery_expenditure_usd"]:
        if col not in clean.columns:
            clean[col] = None
    clean["year"] = pd.to_numeric(clean["year"], errors="coerce")
    clean["gdp_impact_pct"] = pd.to_numeric(clean["gdp_impact_pct"], errors="coerce")
    clean["ag_loss_usd"] = clean["gdp_impact_pct"].fillna(0).mul(1_500_000_000)
    clean["infra_loss_usd"] = clean["gdp_impact_pct"].fillna(0).mul(3_200_000_000)
    clean["recovery_expenditure_usd"] = clean["ag_loss_usd"] * 0.45 + clean["infra_loss_usd"] * 0.25
    clean["event"] = clean["event"].fillna("Climate disaster cost proxy")
    return clean[["country", "year", "event", "gdp_impact_pct", "ag_loss_usd", "infra_loss_usd", "recovery_expenditure_usd"]]


def fetch_live(logger) -> pd.DataFrame:
    frames = []
    for country in sorted(COUNTRY_TO_REGION):
        code = country[:3].lower()
        response = request_with_retry(URL_TEMPLATE.format(country=code), params={"format": "json", "per_page": 100})
        payload = response.json()
        if not isinstance(payload, list) or len(payload) < 2:
            continue
        rows = pd.DataFrame(payload[1])
        if rows.empty:
            continue
        rows["country"] = country
        frames.append(rows)
    if not frames:
        raise RuntimeError("No World Bank responses returned")
    return pd.concat(frames, ignore_index=True)


def main() -> pd.DataFrame:
    args = parse_args("Ingest World Bank disaster cost indicators.")
    logger = setup_logging("world_bank")
    conn = sqlite_connection()
    ensure_schema(conn)
    try:
        source = "live"
        frame = transform(fetch_live(logger))
        save_cache(frame, TABLE)
    except Exception as exc:  # noqa: BLE001
        logger.warning("World Bank fetch failed: %s", exc)
        frame, source = load_or_synthetic(TABLE, TABLE, logger)
        frame = transform(frame)
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source=source, logger=logger)


if __name__ == "__main__":
    main()
