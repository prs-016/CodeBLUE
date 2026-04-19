"""
ml/processing/snowflake_query.py
Extracts and joins CALCOFI data from Snowflake for ML training.
"""
import os
import urllib.parse
import pandas as pd
from sqlalchemy import create_engine, text

def get_snowflake_engine():
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    env = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    parts = line.split("=", 1)
                    env[parts[0].strip()] = parts[1].strip()
    
    user = env.get("SNOWFLAKE_USER")
    password = urllib.parse.quote_plus(env.get("SNOWFLAKE_PASSWORD", ""))
    account = env.get("SNOWFLAKE_ACCOUNT")
    warehouse = env.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
    
    # We use the CALCOFI database specifically for this pipeline
    db = "CALCOFI"
    schema = "PUBLIC"
    
    url = f"snowflake://{user}:{password}@{account}/{db}/{schema}?warehouse={warehouse}"
    return create_engine(url)

def extract_training_data() -> pd.DataFrame:
    engine = get_snowflake_engine()
    
    query = """
    WITH Features AS (
        SELECT 
            DATE, 
            T_DEGC, O2ML_L, SALNTY, CHLORA, NO3UM, PO4UM, SIO3UM, 
            WIND_SPD, BAROMETER,
            LAT_DEC, LON_DEC
        FROM CALCOFI_TSUNAMI_FEATURES
    ),
    Narrative AS (
        SELECT 
            TO_DATE(CAST(DATE AS STRING), 'YYYYMMDD') as DATE, 
            AVG(GOLDSTEIN) as GOLDSTEIN, 
            SUM(NUMARTS) as NUMARTS
        FROM GDELT
        GROUP BY 1
    ),
    GroundTruth AS (
        SELECT 
            TO_DATE(CONCAT(
                CAST(YEAR AS INT), '-', 
                LPAD(CAST(MONTH AS INT), 2, '0'), '-', 
                LPAD(CAST(DAY AS INT), 2, '0')
            )) as DATE,
            MAX(TS_INTENSITY) as TS_INTENSITY
        FROM TSUNAMI_DATASET
        WHERE YEAR IS NOT NULL AND MONTH IS NOT NULL AND DAY IS NOT NULL
        GROUP BY 1
    )
    SELECT 
        f.*,
        COALESCE(n.GOLDSTEIN, 0) as GOLDSTEIN,
        COALESCE(n.NUMARTS, 0) as NUMARTS,
        COALESCE(t.TS_INTENSITY, 0) as TS_INTENSITY
    FROM Features f
    LEFT JOIN Narrative n ON f.DATE = n.DATE
    LEFT JOIN GroundTruth t ON f.DATE = t.DATE
    """
    
    print("Fetching training data from Snowflake (CALCOFI)...")
    df = pd.read_sql(query, engine)
    
    # Snowflake often returns uppercase columns, force to lowercase for consistency
    df.columns = [c.lower() for c in df.columns]
    
    # Map TS_INTENSITY to a 0-10 Proximity Score
    df["threshold_proximity_score"] = (df["ts_intensity"] + 5).clip(0, 10)
    
    # Ensure all feature columns and target are numeric
    feature_cols = [
        "t_degc", "o2ml_l", "salnty", "chlora", "no3um", "po4um", "sio3um", 
        "wind_spd", "barometer", "goldstein", "numarts", "threshold_proximity_score"
    ]
    for col in feature_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    
    return df

if __name__ == "__main__":
    df = extract_training_data()
    df.to_csv("calcofi_training_data.csv", index=False)
    print(f"Extracted {len(df)} rows to calcofi_training_data.csv")
