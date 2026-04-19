from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import load_or_synthetic, parse_args, parse_csv_text, request_with_retry, save_cache, setup_logging, sqlite_connection, ensure_schema, write_table


URL = "https://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/in_situ_co2/daily/daily_in_situ_co2_mlo.csv"
TABLE = "keeling_curve"


def transform(df: pd.DataFrame) -> pd.DataFrame:
    if 'date' not in df.columns and all(c in df.columns for c in ['Yr', 'Mn', 'Dy']):
        df["date"] = pd.to_datetime(df[['Yr', 'Mn', 'Dy']].rename(columns={'Yr': 'year', 'Mn': 'month', 'Dy': 'day'}), errors="coerce")
    elif 'date' not in df.columns:
        date_col = next((col for col in df.columns if "date" in col.lower()), df.columns[0])
        df = df.rename(columns={date_col: "date"})
    
    co2_col = "co2_ppm" if "co2_ppm" in df.columns else next((col for col in df.columns if "co2" in col.lower()), df.columns[-1])
    clean = df[["date", co2_col]].rename(columns={co2_col: "co2_ppm"}).copy()
    clean["co2_ppm"] = pd.to_numeric(clean["co2_ppm"], errors="coerce").replace(-99.99, np.nan).ffill()
    clean = clean.dropna(subset=["date", "co2_ppm"]).sort_values("date")
    clean["co2_trend"] = clean["co2_ppm"].rolling(30, min_periods=1).mean()
    clean["yoy_change"] = clean["co2_ppm"].pct_change(365).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    rate_this_year = clean["co2_ppm"].diff(365)
    rate_last_year = rate_this_year.shift(365).replace(0, np.nan)
    clean["acceleration"] = ((rate_this_year - rate_last_year) / rate_last_year).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    clean["date"] = clean["date"].dt.strftime("%Y-%m-%d")
    return clean.round(6)


def main() -> pd.DataFrame:
    args = parse_args("Ingest the Scripps Keeling Curve dataset.")
    logger = setup_logging("keeling_curve")
    conn = sqlite_connection()
    ensure_schema(conn)
    try:
        response = request_with_retry(URL)
        source = "live"
        import io
        lines = response.text.splitlines()
        data_lines = [l for l in lines if not l.startswith('%') and l.strip()]
        raw_df = pd.read_csv(io.StringIO('\n'.join(data_lines)), names=['Yr', 'Mn', 'Dy', 'co2_ppm', 'NB', 'scale', 'sta'], skipinitialspace=True)
        frame = transform(raw_df)
        save_cache(frame, TABLE)
    except Exception as exc:  # noqa: BLE001
        import traceback; traceback.print_exc()
        logger.warning("Live fetch failed: %s", exc)
        frame, source = load_or_synthetic(TABLE, TABLE, logger)
        frame = transform(frame)
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source=source, logger=logger)


if __name__ == "__main__":
    main()
