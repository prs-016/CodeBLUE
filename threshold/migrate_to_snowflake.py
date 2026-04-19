"""
migrate_to_snowflake.py — One-shot script to push local SQLite data into Snowflake.

Run from the backend/ directory:
    pip install snowflake-sqlalchemy pandas sqlalchemy
    python migrate_to_snowflake.py

Or from inside the Docker container:
    docker exec -it threshold-backend-1 python migrate_to_snowflake.py
"""
import os
import urllib.parse
import pandas as pd
from sqlalchemy import create_engine, text, inspect

# ── Load env (works whether you use python-dotenv or raw os.environ) ──────────
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass  # env vars must be set externally

# ── Source: local SQLite ──────────────────────────────────────────────────────
SQLITE_PATH = os.getenv("SQLITE_PATH", "./threshold.db")
sqlite_engine = create_engine(f"sqlite:///{SQLITE_PATH}", connect_args={"check_same_thread": False})

# ── Destination: Snowflake ────────────────────────────────────────────────────
SF_USER      = os.environ["SNOWFLAKE_USER"]
SF_PASSWORD  = urllib.parse.quote_plus(os.environ["SNOWFLAKE_PASSWORD"])
SF_ACCOUNT   = os.environ["SNOWFLAKE_ACCOUNT"]
SF_DB        = os.environ.get("SNOWFLAKE_DATABASE", "THRESHOLD_DB")
SF_SCHEMA    = os.environ.get("SNOWFLAKE_SCHEMA", "PUBLIC")
SF_WH        = os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")

sf_url = (
    f"snowflake://{SF_USER}:{SF_PASSWORD}@{SF_ACCOUNT}"
    f"/{SF_DB}/{SF_SCHEMA}?warehouse={SF_WH}"
)
sf_engine = create_engine(sf_url, future=True)

# ── Verify Snowflake connection ───────────────────────────────────────────────
print("Connecting to Snowflake…")
with sf_engine.connect() as conn:
    result = conn.execute(text("SELECT CURRENT_VERSION()")).fetchone()
    print(f"✓ Snowflake connected — version {result[0]}")

# ── Get all tables from SQLite ────────────────────────────────────────────────
inspector = inspect(sqlite_engine)
tables = inspector.get_table_names()
print(f"\nFound {len(tables)} tables in SQLite: {tables}")

# ── Migrate each table ────────────────────────────────────────────────────────
for table in tables:
    print(f"\n→ Migrating table: {table}")
    try:
        df = pd.read_sql_table(table, con=sqlite_engine)
        row_count = len(df)

        if row_count == 0:
            print(f"  (skipping — empty table)")
            continue

        # Write to Snowflake — 'replace' drops & recreates, 'append' adds rows
        df.to_sql(
            name=table.upper(),  # Snowflake convention: uppercase table names
            con=sf_engine,
            if_exists="replace",  # change to "append" to keep existing rows
            index=False,
            chunksize=5000,       # batch large tables (region_features has 8k+ rows)
            method="multi",
        )
        print(f"  ✓ {row_count:,} rows uploaded to THRESHOLD_DB.PUBLIC.{table.upper()}")
    except Exception as e:
        print(f"  ✗ Error migrating {table}: {e}")

print("\n✅ Migration complete! Verify in Snowflake UI:")
print(f"   https://app.snowflake.com/  →  THRESHOLD_DB  →  PUBLIC")
