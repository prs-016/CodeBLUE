from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import assign_region_from_lat_lon, ensure_schema, load_or_synthetic, parse_args, request_with_retry, save_cache, setup_logging, sqlite_connection, synthetic_frame, write_table


KAGGLE_DATASET = "sohier/calcofi"
CALCOFI_URL = "https://calcofi.org/data/"
TABLE = "calcofi_observations"


def depth_bucket(depth: float) -> str:
    if depth <= 20:
        return "surface"
    if depth <= 100:
        return "mid"
    return "deep"


def transform(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "Sta_ID": "station_id",
        "Date": "date",
        "Depthm": "depth_m",
        "T_degC": "temp_c",
        "Salnty": "salinity",
        "O2ml_L": "o2_ml_l",
        "ChlorA": "chlorophyll",
        "NO3uM": "nitrate",
        "PO4uM": "phosphate",
        "Larvae_Count": "larvae_count",
        "lat": "lat",
        "lon": "lon",
        "Latitude": "lat",
        "Longitude": "lon",
    }
    existing = {k: v for k, v in rename_map.items() if k in df.columns}
    clean = df.rename(columns=existing).copy()
    for column in ["date", "depth_m", "temp_c", "salinity", "o2_ml_l", "chlorophyll", "nitrate", "phosphate", "larvae_count", "lat", "lon"]:
        if column not in clean.columns:
            clean[column] = None
    clean["date"] = pd.to_datetime(clean["date"], errors="coerce")
    clean["depth_m"] = pd.to_numeric(clean["depth_m"], errors="coerce")
    numeric_cols = ["temp_c", "salinity", "o2_ml_l", "chlorophyll", "nitrate", "phosphate", "larvae_count", "lat", "lon"]
    clean[numeric_cols] = clean[numeric_cols].apply(pd.to_numeric, errors="coerce")
    clean["region_id"] = clean.apply(lambda row: assign_region_from_lat_lon(row.get("lat"), row.get("lon")), axis=1)
    clean["region_id"] = clean["region_id"].fillna("california_current")
    clean["depth_category"] = clean["depth_m"].fillna(0).apply(depth_bucket)
    grouped = (
        clean.dropna(subset=["date", "temp_c", "o2_ml_l"])
        .groupby(["region_id", clean["date"].dt.strftime("%Y-%m-%d"), "depth_category"], dropna=False)
        .agg(
            temp_c=("temp_c", "mean"),
            salinity=("salinity", "mean"),
            o2_ml_l=("o2_ml_l", "mean"),
            chlorophyll=("chlorophyll", "mean"),
            nitrate=("nitrate", "mean"),
            phosphate=("phosphate", "mean"),
            larvae_count=("larvae_count", "mean"),
        )
        .reset_index()
        .rename(columns={"date": "date"})
    )
    return grouped.round(6)


def fetch_kaggle_dataset(logger) -> pd.DataFrame | None:
    if not os.getenv("KAGGLE_USERNAME") or not os.getenv("KAGGLE_KEY"):
        return None
    kaggle_path = DATA_DIR / "cache" / "calcofi_kaggle"
    kaggle_path.mkdir(parents=True, exist_ok=True)
    command = ["kaggle", "datasets", "download", "-d", KAGGLE_DATASET, "-p", str(kaggle_path), "--unzip"]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        csv_files = list(kaggle_path.glob("*.csv"))
        if csv_files:
            return pd.read_csv(csv_files[0])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Kaggle fetch unavailable: %s", exc)
    return None


def main() -> pd.DataFrame:
    args = parse_args("Ingest CalCOFI observations.")
    logger = setup_logging("calcofi")
    conn = sqlite_connection()
    ensure_schema(conn)
    source = "live"
    try:
        raw = fetch_kaggle_dataset(logger)
        if raw is None:
            response = request_with_retry(CALCOFI_URL)
            tables = pd.read_html(response.text)
            if not tables:
                raise RuntimeError("No CalCOFI tables found")
            raw = tables[0]
        frame = transform(raw)
        save_cache(frame, TABLE)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Live fetch failed: %s", exc)
        frame, source = load_or_synthetic(TABLE, TABLE, logger)
        frame = transform(frame)
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source=source, logger=logger)


if __name__ == "__main__":
    main()
