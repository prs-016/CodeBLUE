from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import CHARITY_TARGETS, ensure_schema, load_or_synthetic, parse_args, request_with_retry, save_cache, setup_logging, sqlite_connection, write_table


URL = "https://api.charitynavigator.org/v2/Organizations"
TABLE = "charity_registry"


def transform(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "charityName": "name",
        "overallScore": "overall_score",
        "financialScore": "financial_score",
        "accountabilityScore": "accountability_score",
        "programExpenseRatio": "program_expense_ratio",
        "ein": "ein",
        "active_regions": "active_regions",
    }
    clean = df.rename(columns=rename_map).copy()
    for col in ["ein", "name", "overall_score", "financial_score", "accountability_score", "program_expense_ratio", "active_regions"]:
        if col not in clean.columns:
            clean[col] = None
    clean["eligible_for_disbursement"] = (pd.to_numeric(clean["overall_score"], errors="coerce") >= 75) & (
        pd.to_numeric(clean["accountability_score"], errors="coerce") >= 80
    )
    return clean[["ein", "name", "overall_score", "financial_score", "accountability_score", "program_expense_ratio", "active_regions", "eligible_for_disbursement"]]


def fetch_live(api_key: str) -> pd.DataFrame:
    frames = []
    headers = {"Charity-Navigator-App-ID": api_key}
    for target in CHARITY_TARGETS:
        if "LOOKUP" in target["ein"] or target["ein"].startswith("RW3W-"):
            continue
        response = request_with_retry(URL, params={"ein": target["ein"]}, headers=headers)
        payload = response.json()
        if isinstance(payload, list) and payload:
            frames.append(pd.DataFrame(payload))
    if not frames:
        raise RuntimeError("No Charity Navigator records")
    return pd.concat(frames, ignore_index=True)


def main() -> pd.DataFrame:
    args = parse_args("Ingest Charity Navigator organization records.")
    logger = setup_logging("charity_navigator")
    conn = sqlite_connection()
    ensure_schema(conn)
    api_key = os.getenv("CHARITY_NAVIGATOR_API_KEY", "")
    try:
        if not api_key:
            raise RuntimeError("CHARITY_NAVIGATOR_API_KEY missing")
        source = "live"
        frame = transform(fetch_live(api_key))
        save_cache(frame, TABLE)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Charity Navigator fetch failed: %s", exc)
        frame, source = load_or_synthetic(TABLE, TABLE, logger)
        frame = transform(frame)
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source=source, logger=logger)


if __name__ == "__main__":
    main()
