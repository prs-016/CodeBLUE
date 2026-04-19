"""
snowflake_diagnostic.py
Checks what databases, schemas, and tables are visible to the current Snowflake user.
"""
import os
import urllib.parse
from sqlalchemy import create_engine, text

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        os.environ[parts[0].strip()] = parts[1].strip()

load_env()

SF_USER    = os.environ["SNOWFLAKE_USER"]
SF_PASS    = urllib.parse.quote_plus(os.environ["SNOWFLAKE_PASSWORD"])
SF_ACCOUNT = os.environ["SNOWFLAKE_ACCOUNT"]

sf_url = f"snowflake://{SF_USER}:{SF_PASS}@{SF_ACCOUNT}"
engine = create_engine(sf_url)

with engine.connect() as conn:
    print(f"--- Snowflake Diagnostic for user {SF_USER} ---")
    
    # 1. Current Context
    res = conn.execute(text("SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()")).fetchone()
    print(f"Role:      {res[0]}")
    print(f"Warehouse: {res[1]}")
    print(f"Database:  {res[2]}")
    print(f"Schema:    {res[3]}")
    
    # 2. Visible Databases
    print("\nVisible Databases:")
    for row in conn.execute(text("SHOW DATABASES")):
        print(f" - {row[1]}")
        
    # 3. Check specific database
    target_db = os.environ.get("SNOWFLAKE_DATABASE", "THRESHOLD_DB")
    print(f"\nChecking visibility of {target_db}...")
    try:
        conn.execute(text(f"USE DATABASE {target_db}"))
        print(f"✅ Successfully switched to {target_db}")
        
        print("\nVisible Schemas in this DB:")
        for row in conn.execute(text("SHOW SCHEMAS")):
            print(f" - {row[1]}")
            
        print("\nTables in PUBLIC schema:")
        res = conn.execute(text("SHOW TABLES IN SCHEMA PUBLIC"))
        for row in res:
            print(f" - {row[1]} ({row[4]} rows)")
            
    except Exception as e:
        print(f"❌ Error accessing {target_db}: {e}")
