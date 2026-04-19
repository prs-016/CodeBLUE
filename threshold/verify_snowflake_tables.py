"""
verify_snowflake_tables.py
Checks for the presence and row counts of expected tables in Snowflake.
"""
import os
import urllib.parse
from sqlalchemy import create_engine, text

# ── Load env ─────────────────────────────────────────────────────────────────
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

load_env()

SF_USER    = os.environ["SNOWFLAKE_USER"]
SF_PASS    = urllib.parse.quote_plus(os.environ["SNOWFLAKE_PASSWORD"])
SF_ACCOUNT = os.environ["SNOWFLAKE_ACCOUNT"]
SF_DB      = os.environ.get("SNOWFLAKE_DATABASE", "THRESHOLD_DB")
SF_SCHEMA  = os.environ.get("SNOWFLAKE_SCHEMA", "PUBLIC")
SF_WH      = os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")

sf_url = f"snowflake://{SF_USER}:{SF_PASS}@{SF_ACCOUNT}/{SF_DB}/{SF_SCHEMA}?warehouse={SF_WH}"
engine = create_engine(sf_url)

TABLES = [
    "KEELING_CURVE", "CALCOFI_OBSERVATIONS", "SCRIPPS_PIER", "SST_OBSERVATIONS",
    "CORAL_BLEACHING_ALERTS", "OCEAN_COLOR", "HUMANITARIAN_FUNDING",
    "HDX_FUNDING_NEEDS", "HISTORICAL_DISASTERS", "WORLD_BANK_DISASTER_COSTS",
    "RELIEFWEB_REPORTS", "GDELT_ATTENTION", "SCIENTIFIC_EVENTS",
    "CHARITY_REGISTRY", "CHARITY_REGIONAL_PRESENCE", "GIVEWELL_IMPACT",
    "REGIONS", "FUNDING_ROUNDS", "COUNTERFACTUAL_CASES", "CHARITIES",
    "NEWS_ARTICLES", "MEDIA_ATTENTION", "SOLANA_TRANSACTIONS", "REGION_FEATURES"
]

print(f"Verifying {len(TABLES)} tables in {SF_DB}.{SF_SCHEMA}...")
missing = []
present = []

with engine.connect() as conn:
    for table in TABLES:
        try:
            res = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
            count = res[0]
            print(f"✅ {table:<30} | {count:>8,} rows")
            present.append((table, count))
        except Exception:
            print(f"❌ {table:<30} | MISSING")
            missing.append(table)

print("\nSummary:")
print(f"Total Tables Checked: {len(TABLES)}")
print(f"Present:              {len(present)}")
print(f"Missing:              {len(missing)}")

if not missing:
    print("\n🎉 All datasets are successfully confirmed in Snowflake!")
else:
    print(f"\n⚠️ Missing tables: {', '.join(missing)}")
