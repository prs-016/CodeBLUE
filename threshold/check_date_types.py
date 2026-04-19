"""
check_date_types.py
Checks the data types of the DATE columns in the CALCOFI database.
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
SF_WH      = os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")

sf_url = f"snowflake://{SF_USER}:{SF_PASS}@{SF_ACCOUNT}/?warehouse={SF_WH}"
engine = create_engine(sf_url)

with engine.connect() as conn:
    for table in ["CALCOFI_TSUNAMI_FEATURES", "GDELT", "TSUNAMI_DATASET"]:
        print(f"\n--- {table} ---")
        res = conn.execute(text(f"DESCRIBE TABLE CALCOFI.PUBLIC.{table}"))
        for row in res:
            if row[0].upper() == "DATE":
                print(f"Column: {row[0]}, Type: {row[1]}")
            if row[0].upper() in ["YEAR", "MONTH", "DAY"]:
                print(f"Column: {row[0]}, Type: {row[1]}")
