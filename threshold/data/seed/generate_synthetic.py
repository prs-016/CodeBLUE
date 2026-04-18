import os
import sqlite3
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Mocking Databricks/Snowflake pipeline sink for local hackathon demo
DATABASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'threshold.db'))

DEMO_REGIONS_CONFIG = {
    "great_barrier_reef": {
        "name": "Great Barrier Reef",
        "current_score": 8.4,
        "days_to_threshold": 47,
        "funding_gap": 8400000,
        "primary_threat": "thermal",
        "drama_level": "CRITICAL",
        "lat": -18.2, "lon": 147.7,
        "population_affected": 240000
    },
    "mekong_delta": {
        "name": "Mekong Delta",
        "current_score": 7.1,
        "days_to_threshold": 180,
        "funding_gap": 9600000,
        "primary_threat": "hypoxia",
        "drama_level": "HIGH",
        "lat": 10.0, "lon": 105.5,
        "population_affected": 17000000
    },
    "arabian_sea": {
        "name": "Arabian Sea",
        "current_score": 6.8,
        "days_to_threshold": 290,
        "funding_gap": 12000000,
        "primary_threat": "hypoxia",
        "drama_level": "HIGH",
        "lat": 15.0, "lon": 65.0,
        "population_affected": 8500000
    },
    "california_current": {
        "name": "California Current",
        "current_score": 5.2,
        "days_to_threshold": 520,
        "funding_gap": 3200000,
        "primary_threat": "acidification",
        "drama_level": "MEDIUM",
        "lat": 36.0, "lon": -122.0,
        "population_affected": 4200000
    },
    "baltic_sea": {
        "name": "Baltic Sea",
        "current_score": 4.5,
        "days_to_threshold": 800,
        "funding_gap": 1500000,
        "primary_threat": "nutrient",
        "drama_level": "MEDIUM",
        "lat": 57.0, "lon": 19.0,
        "population_affected": 1400000
    },
    "coral_triangle": {
        "name": "Coral Triangle",
        "current_score": 8.1,
        "days_to_threshold": 65,
        "funding_gap": 15000000,
        "primary_threat": "thermal",
        "drama_level": "CRITICAL",
        "lat": 0.0, "lon": 120.0,
        "population_affected": 120000000
    },
    "bengal_bay": {
        "name": "Bay of Bengal",
        "current_score": 3.8,
        "days_to_threshold": 1200,
        "funding_gap": 0,
        "primary_threat": "thermal",
        "drama_level": "LOW",
        "lat": 15.0, "lon": 90.0,
        "population_affected": 400000000
    },
    "gulf_of_mexico": {
        "name": "Gulf of Mexico",
        "current_score": 6.2,
        "days_to_threshold": 400,
        "funding_gap": 6000000,
        "primary_threat": "hypoxia",
        "drama_level": "HIGH",
        "lat": 25.0, "lon": -90.0,
        "population_affected": 15000000
    }
}

def generate_schema(cursor):
    tables = [
        """CREATE TABLE IF NOT EXISTS regions (
            id TEXT PRIMARY KEY,
            name TEXT,
            lat REAL,
            lon REAL,
            current_score REAL,
            days_to_threshold INTEGER,
            funding_gap REAL,
            primary_threat TEXT,
            alert_level TEXT,
            population_affected INTEGER
        )""",
        """CREATE TABLE IF NOT EXISTS region_features (
            region_id TEXT,
            date TEXT,
            sst_anomaly REAL,
            o2_current REAL,
            chlorophyll_anomaly REAL,
            co2_regional_ppm REAL,
            nitrate_anomaly REAL,
            threshold_proximity_score REAL
        )""",
        """CREATE TABLE IF NOT EXISTS funding_rounds (
            id TEXT PRIMARY KEY,
            region_id TEXT,
            target_amount REAL,
            raised_amount REAL,
            status TEXT,
            deadline TEXT,
            cost_multiplier REAL
        )""",
        """CREATE TABLE IF NOT EXISTS counterfactual_cases (
            case_id TEXT PRIMARY KEY,
            region_id TEXT,
            event_name TEXT,
            year_crossed INTEGER,
            prevention_cost REAL,
            recovery_cost REAL,
            cost_multiplier REAL
        )""",
        """CREATE TABLE IF NOT EXISTS news_reports (
            id TEXT PRIMARY KEY,
            region_id TEXT,
            title TEXT,
            source_org TEXT,
            date TEXT,
            body_summary TEXT,
            url TEXT,
            urgency_score REAL
        )""",
        """CREATE TABLE IF NOT EXISTS charity_registry (
            ein TEXT PRIMARY KEY,
            region_id TEXT,
            name TEXT,
            overall_score REAL
        )"""
    ]
    for table in tables:
        cursor.execute(table)

def seed_regions(cursor):
    print("Seeding regions...")
    for rid, data in DEMO_REGIONS_CONFIG.items():
        cursor.execute(
            "INSERT OR REPLACE INTO regions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (rid, data["name"], data["lat"], data["lon"], data["current_score"],
             data["days_to_threshold"], data["funding_gap"], data["primary_threat"],
             data["drama_level"], data["population_affected"])
        )

def seed_timeseries_data(cursor):
    print("Seeding 10 years of synthetic time-series data per region...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 10)
    
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    for rid, config in DEMO_REGIONS_CONFIG.items():
        base_score = max(0, config["current_score"] - 4.0) # Start lower 10 years ago
        trend = (config["current_score"] - base_score) / len(dates)
        
        # Add realistic seasonality
        time_array = np.arange(len(dates))
        seasonality = np.sin(2 * np.pi * time_array / 365) * 0.5
        noise = np.random.normal(0, 0.2, len(dates))
        
        scores = base_score + (trend * time_array) + seasonality + noise
        scores = np.clip(scores, 0, 10.0)
        
        # Override the last value to exactly match config current_score
        scores[-1] = config["current_score"]
        
        records = []
        for i, dt in enumerate(dates):
            sst_anomaly = ((scores[i] / 10.0) * 3.0) + np.random.normal(0, 0.1) # Up to 3.0C anomaly
            o2_current = max(1.0, 7.0 - ((scores[i] / 10.0) * 5.0) + np.random.normal(0, 0.5)) # Hypoxia simulation
            chla = np.random.normal(0, 1) + np.sin(2 * np.pi * i / 180) # Bloom cycles
            co2 = 390.0 + (i / 365.0) * 2.5 + np.random.normal(0, 1) # Keeling trace
            no3 = np.abs(np.random.normal(0, 2) * (scores[i]/5.0)) # Nutrient overload
            
            records.append((
                rid, dt.strftime("%Y-%m-%d"), round(sst_anomaly, 2), round(o2_current, 2),
                round(chla, 2), round(co2, 2), round(no3, 2), round(scores[i], 2)
            ))
            
        cursor.executemany(
            "INSERT INTO region_features VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            records
        )

def seed_funding(cursor):
    print("Seeding funding rounds and counterfactuals...")
    rounds = [
        ("FR_001", "great_barrier_reef", 10000000, 1600000, "Open", (datetime.now() + timedelta(days=47)).strftime("%Y-%m-%d"), 8.5),
        ("FR_002", "coral_triangle", 18000000, 3000000, "Open", (datetime.now() + timedelta(days=65)).strftime("%Y-%m-%d"), 12.0),
        ("FR_003", "california_current", 5000000, 5000000, "Completed", (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"), 4.0),
    ]
    cursor.executemany("INSERT OR REPLACE INTO funding_rounds VALUES (?, ?, ?, ?, ?, ?, ?)", rounds)
    
    cases = [
        ("C_001", "california_current", "Sardine Fishery Collapse", 2015, 4500000, 84000000, 18.6),
        ("C_002", "baltic_sea", "Mass Hypoxia Event", 2018, 12000000, 140000000, 11.6),
        ("C_003", "great_barrier_reef", "Northern Bleaching", 2016, 25000000, 300000000, 12.0)
    ]
    cursor.executemany("INSERT OR REPLACE INTO counterfactual_cases VALUES (?, ?, ?, ?, ?, ?, ?)", cases)

def seed_news_charities(cursor):
    print("Seeding news and charities...")
    for rid in DEMO_REGIONS_CONFIG.keys():
        for i in range(5):
            cursor.execute(
                "INSERT OR REPLACE INTO news_reports VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (f"N_{rid}_{i}", rid, f"Crisis Alert: Conditions worsening in {rid} {i}", "ReliefWeb",
                 (datetime.now() - timedelta(days=random.randint(1,30))).strftime("%Y-%m-%d"),
                 "Conditions have escalated recently. Immediate action recommended...",
                 "https://reliefweb.int/example", round(random.uniform(5.0, 9.5), 1))
            )
            
        cursor.execute(
            "INSERT OR REPLACE INTO charity_registry VALUES (?, ?, ?, ?)",
            (f"EIN_{rid}_1", rid, f"Ocean Protectors {rid}", 98.4)
        )

def main():
    print(f"Connecting to standalone local pipeline DB proxy at: {DATABASE_PATH}")
    db_exists = os.path.exists(DATABASE_PATH)
    if db_exists:
        try:
            os.remove(DATABASE_PATH)
        except:
            pass
        
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    generate_schema(cursor)
    seed_regions(cursor)
    seed_timeseries_data(cursor)
    seed_funding(cursor)
    seed_news_charities(cursor)
    
    conn.commit()
    conn.close()
    
    print("✅ Synthetic staging complete! Pipeline DB primed.")

if __name__ == "__main__":
    main()
