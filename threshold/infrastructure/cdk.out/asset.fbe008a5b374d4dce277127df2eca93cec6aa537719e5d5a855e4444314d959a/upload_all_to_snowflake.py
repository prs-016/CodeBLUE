"""
upload_all_to_snowflake.py

Downloads / generates all 16 THRESHOLD datasets using the existing
synthetic + API pipeline in data/ingestion/shared.py, then uploads
every table to Snowflake in one shot.

Run from the repo root:
    python3 threshold/upload_all_to_snowflake.py
"""
import os
import sys
import urllib.parse
from pathlib import Path

# ── Resolve paths ──────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).resolve().parent          # threshold/
INGESTION   = REPO_ROOT / "data" / "ingestion"
sys.path.insert(0, str(INGESTION))
sys.path.insert(0, str(REPO_ROOT / "backend"))

# ── Load .env ─────────────────────────────────────────────────────────────────
ENV_FILE = REPO_ROOT / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

import pandas as pd
from sqlalchemy import create_engine, text

# ── Snowflake connection ───────────────────────────────────────────────────────
SF_USER    = os.environ["SNOWFLAKE_USER"]
SF_PASS    = urllib.parse.quote_plus(os.environ["SNOWFLAKE_PASSWORD"])
SF_ACCOUNT = os.environ["SNOWFLAKE_ACCOUNT"]
SF_DB      = os.environ.get("SNOWFLAKE_DATABASE", "THRESHOLD_DB")
SF_SCHEMA  = os.environ.get("SNOWFLAKE_SCHEMA", "PUBLIC")
SF_WH      = os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")

sf_url = f"snowflake://{SF_USER}:{SF_PASS}@{SF_ACCOUNT}/{SF_DB}/{SF_SCHEMA}?warehouse={SF_WH}"

print("🔌 Connecting to Snowflake …")
sf_engine = create_engine(sf_url, future=True)
with sf_engine.connect() as conn:
    ver = conn.execute(text("SELECT CURRENT_VERSION()")).fetchone()[0]
print(f"✅ Connected — Snowflake {ver}\n")

# ── Import the shared synthetic generators ────────────────────────────────────
from shared import SYNTHETIC_FACTORIES  # type: ignore
from seed_data import (  # type: ignore
    REGION_SEED, FUNDING_ROUND_SEED, COUNTERFACTUAL_CASE_SEED,
    CHARITY_SEED, NEWS_SEED, ATTENTION_SEED, SOLANA_TX_SEED,
    _generate_region_features as _gen_features,
)

# ── Helper ─────────────────────────────────────────────────────────────────────
def upload(df: pd.DataFrame, table: str, *, note: str = "") -> None:
    sf_table = table.upper()
    rows = len(df)
    if rows == 0:
        print(f"  ⏭  {sf_table} — empty, skipping")
        return
    # Snowflake doesn't allow Python bool — cast to int
    for col in df.select_dtypes(include="bool").columns:
        df[col] = df[col].astype(int)
    
    # Explicitly drop the table first to avoid reflection issues in Snowflake
    with sf_engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {sf_table}"))
        conn.commit()

    df.to_sql(
        sf_table, sf_engine, if_exists="append", # "append" after we dropped it manually
        index=False, chunksize=5000, method="multi",
    )
    print(f"  ✅ {sf_table:<42} {rows:>7,} rows  {note}")

print("=" * 60)
print("UPLOADING SYNTHETIC SCIENCE DATASETS")
print("=" * 60)

# ── 1-6: Ocean science tables (all in SYNTHETIC_FACTORIES) ───────────────────
SCIENCE_TABLES = [
    "keeling_curve",
    "calcofi_observations",
    "scripps_pier",
    "sst_observations",
    "coral_bleaching_alerts",
    "ocean_color",
]
for table in SCIENCE_TABLES:
    df = SYNTHETIC_FACTORIES[table]()
    upload(df, table)

print()
print("=" * 60)
print("UPLOADING HUMANITARIAN & FUNDING DATASETS")
print("=" * 60)

FUNDING_TABLES = [
    "humanitarian_funding",
    "hdx_funding_needs",
    "historical_disasters",
    "world_bank_disaster_costs",
]
for table in FUNDING_TABLES:
    df = SYNTHETIC_FACTORIES[table]()
    upload(df, table)

print()
print("=" * 60)
print("UPLOADING NEWS & MEDIA DATASETS")
print("=" * 60)

NEWS_TABLES = [
    "reliefweb_reports",
    "gdelt_attention",
    "scientific_events",
]
for table in NEWS_TABLES:
    df = SYNTHETIC_FACTORIES[table]()
    upload(df, table)

print()
print("=" * 60)
print("UPLOADING CHARITY & VERIFICATION DATASETS")
print("=" * 60)

CHARITY_TABLES = [
    "charity_registry",
    "charity_regional_presence",
    "givewell_impact",
]
for table in CHARITY_TABLES:
    df = SYNTHETIC_FACTORIES[table]()
    upload(df, table)

print()
print("=" * 60)
print("UPLOADING CORE APPLICATION TABLES (from seed_data)")
print("=" * 60)

upload(pd.DataFrame(REGION_SEED), "REGIONS", note="(core regions)")
upload(pd.DataFrame(FUNDING_ROUND_SEED), "FUNDING_ROUNDS")
upload(pd.DataFrame(COUNTERFACTUAL_CASE_SEED), "COUNTERFACTUAL_CASES")
upload(pd.DataFrame(CHARITY_SEED), "CHARITIES")
upload(pd.DataFrame(NEWS_SEED), "NEWS_ARTICLES")
upload(pd.DataFrame(ATTENTION_SEED, columns=["region_id","threshold_score","attention_score"]), "MEDIA_ATTENTION")
upload(pd.DataFrame(SOLANA_TX_SEED), "SOLANA_TRANSACTIONS")

print()
print("=" * 60)
print("UPLOADING REGION STRESS FEATURES (3yr daily timeseries)")
print("=" * 60)
# This is the big one — 8 regions × 1095 days = ~8,760 rows
features_df = pd.DataFrame(_gen_features())
upload(features_df, "REGION_FEATURES", note="(3-year daily timeseries)")

print()
print("🎉 ALL TABLES UPLOADED TO SNOWFLAKE!")
print(f"   → THRESHOLD_DB.PUBLIC in account {SF_ACCOUNT}")
print(f"   → Verify at: https://app.snowflake.com/")
