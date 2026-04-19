"""
inspect_snowflake_schemas.py
Iterates through all tables in Snowflake and prints their column names.
"""
import os
import urllib.parse
from sqlalchemy import create_engine, text

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if not os.path.exists(env_path):
        env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    parts = line.split("=", 1)
                    os.environ[parts[0].strip()] = parts[1].strip()

load_env()

SF_USER    = os.environ["SNOWFLAKE_USER"]
SF_PASS    = urllib.parse.quote_plus(os.environ["SNOWFLAKE_PASSWORD"])
SF_ACCOUNT = os.environ["SNOWFLAKE_ACCOUNT"]
SF_DB      = os.environ.get("SNOWFLAKE_DATABASE", "THRESHOLD_DB")
SF_SCHEMA  = os.environ.get("SNOWFLAKE_SCHEMA", "PUBLIC")
SF_WH      = os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")

sf_url = f"snowflake://{SF_USER}:{SF_PASS}@{SF_ACCOUNT}/{SF_DB}/{SF_SCHEMA}?warehouse={SF_WH}"
engine = create_engine(sf_url)

with engine.connect() as conn:
    print(f"--- Snowflake Schema Inspection for {SF_DB}.{SF_SCHEMA} ---")
    
    # 1. Get list of tables
    tables_res = conn.execute(text("SHOW TABLES IN SCHEMA PUBLIC"))
    tables = [row[1] for row in tables_res]
    
    for table_name in tables:
        print(f"\n📊 Dataset: {table_name}")
        cols_res = conn.execute(text(f"DESCRIBE TABLE {table_name}"))
        cols = [row[0] for row in cols_res]
        print(f"   Columns: {', '.join(cols)}")
