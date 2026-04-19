from __future__ import annotations
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath('backend'))

from database import engine
from sqlalchemy import text
import pandas as pd

try:
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM CALCOFI.PUBLIC.TSUNAMI_DATASET"), conn)
        
    print(f"Total Events: {len(df)}")
    
    # Simple summary depending on columns
    # Find column names mappings as done in _normalize_row
    def pick_col(cols, *candidates):
        for c in candidates:
            for col in cols:
                if c.lower() == col.lower():
                    return col
        return None

    cols = df.columns
    year_col = pick_col(cols, "year", "yr")
    mag_col = pick_col(cols, "eq_mag_ms", "eq_mag_mw", "eq_mag_mb", "eq_magnitude", "magnitude", "mag")
    height_col = pick_col(cols, "maximum_water_height", "max_water_height", "wave_height", "runup_ht", "max_wave_height")
    death_col = pick_col(cols, "total_deaths", "deaths", "death_total", "deaths_total")
    country_col = pick_col(cols, "country", "country_name")
    cause_col = pick_col(cols, "cause_code", "cause", "tsu_cause_code", "source_of_tsunami")

    if year_col:
        valid_years = pd.to_numeric(df[year_col], errors="coerce").dropna()
        if not valid_years.empty:
             print(f"Year Range: {int(valid_years.min())} to {int(valid_years.max())}")
             
    if mag_col:
        valid_mags = pd.to_numeric(df[mag_col], errors="coerce").dropna()
        if not valid_mags.empty:
             print(f"Magnitudes: Min {valid_mags.min():.2f}, Max {valid_mags.max():.2f}, Avg {valid_mags.mean():.2f}")
             
    if height_col:
        valid_heights = pd.to_numeric(df[height_col], errors="coerce").dropna()
        if not valid_heights.empty:
             print(f"Max Water Heights: Min {valid_heights.min():.2f}m, Max {valid_heights.max():.2f}m, Avg {valid_heights.mean():.2f}m")
             
    if death_col:
        valid_deaths = pd.to_numeric(df[death_col], errors="coerce").dropna()
        if not valid_deaths.empty:
             print(f"Recorded Deaths: Total {int(valid_deaths.sum())}, Max in single event {int(valid_deaths.max())}")
             
    if country_col:
        top_countries = df[country_col].value_counts().head(5)
        print(f"Top 5 Countries Affected: {top_countries.to_dict()}")
        
    if cause_col:
        top_causes = df[cause_col].value_counts().head(5)
        print(f"Top 5 Recorded Causes: {top_causes.to_dict()}")

except Exception as e:
    import traceback
    traceback.print_exc()
