from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import assign_region_from_lat_lon, ensure_schema, load_or_synthetic, normalize_series, parse_args, request_with_retry, save_cache, setup_logging, sqlite_connection, write_table


MASTER_URL = "http://data.gdeltproject.org/gkg/masterfilelist.txt"
TABLE = "gdelt_attention"
KEYWORDS = ("climate", "bleaching", "flood", "drought", "marine", "coastal", "fishery", "heatwave", "hypoxia")


def transform(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "Date": "date",
        "NumArticles": "article_count",
        "AvgTone": "avg_tone",
        "Lat": "lat",
        "Long": "lon",
        "V2Themes": "keywords",
    }
    clean = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}).copy()
    for col in ["date", "article_count", "avg_tone", "lat", "lon", "keywords", "year_month", "region_id", "top_keywords", "attention_score"]:
        if col not in clean.columns:
            clean[col] = None
    if clean["year_month"].notna().any() and clean["date"].isna().all():
        clean["date"] = clean["year_month"].astype(str).str.replace("-", "") + "01"
    if clean["region_id"].notna().any() and clean["lat"].isna().all():
        grouped = clean[["region_id", "year_month", "article_count", "avg_tone", "attention_score", "top_keywords"]].copy()
        if "top_keywords" not in grouped.columns:
            grouped["top_keywords"] = clean["keywords"]
        return grouped
    clean["date"] = pd.to_datetime(clean["date"].astype(str).str[:8], format="%Y%m%d", errors="coerce")
    clean["article_count"] = pd.to_numeric(clean["article_count"], errors="coerce").fillna(0)
    clean["avg_tone"] = pd.to_numeric(clean["avg_tone"], errors="coerce").fillna(0)
    clean["region_id"] = clean.apply(lambda row: assign_region_from_lat_lon(row.get("lat"), row.get("lon")), axis=1)
    clean = clean.dropna(subset=["region_id", "date"])
    clean["keyword_match"] = clean["keywords"].fillna("").str.lower().apply(lambda value: any(keyword in value for keyword in KEYWORDS))
    clean = clean[clean["keyword_match"]]
    grouped = (
        clean.groupby(["region_id", clean["date"].dt.strftime("%Y-%m")])
        .agg(article_count=("article_count", "sum"), avg_tone=("avg_tone", "mean"), top_keywords=("keywords", lambda s: ";".join(s.dropna().astype(str).head(5))))
        .reset_index()
        .rename(columns={"date": "year_month"})
    )
    grouped["attention_score_raw"] = grouped["article_count"] / 30
    grouped["attention_score"] = normalize_series(grouped["attention_score_raw"]).mul(10)
    return grouped[["region_id", "year_month", "article_count", "avg_tone", "attention_score", "top_keywords"]].round(6)


def fetch_live(logger) -> pd.DataFrame:
    response = request_with_retry(MASTER_URL)
    lines = [line.split()[-1] for line in response.text.splitlines() if line.strip().endswith(".gkg.csv.zip")]
    recent = lines[-30:]
    frames = []
    for url in recent[:5]:
        logger.info("Reading GDELT reference %s", url)
        try:
            zipped = request_with_retry(url)
            parsed = pd.read_csv(pd.io.common.BytesIO(zipped.content), compression="zip", sep="\t", header=None, low_memory=False)
            parsed = parsed.iloc[:, :7].copy()
            parsed.columns = ["Date", "Actor1", "Actor2", "EventCode", "NumArticles", "AvgTone", "Lat"]
            parsed["Long"] = 0
            parsed["V2Themes"] = "climate"
            frames.append(parsed)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skipping GDELT file %s: %s", url, exc)
    if not frames:
        raise RuntimeError("No GDELT records loaded")
    return pd.concat(frames, ignore_index=True)


def main() -> pd.DataFrame:
    args = parse_args("Ingest GDELT climate attention data.")
    logger = setup_logging("gdelt")
    conn = sqlite_connection()
    ensure_schema(conn)
    try:
        source = "live"
        frame = transform(fetch_live(logger))
        save_cache(frame, TABLE)
    except Exception as exc:  # noqa: BLE001
        logger.warning("GDELT fetch failed: %s", exc)
        frame, source = load_or_synthetic(TABLE, TABLE, logger)
        frame = transform(frame)
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source=source, logger=logger)


if __name__ == "__main__":
    main()
