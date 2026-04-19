CREATE TABLE IF NOT EXISTS keeling_curve (
    date TEXT PRIMARY KEY,
    co2_ppm REAL,
    co2_trend REAL,
    yoy_change REAL,
    acceleration REAL
);

CREATE TABLE IF NOT EXISTS calcofi_observations (
    region_id TEXT,
    date TEXT,
    depth_category TEXT,
    temp_c REAL,
    salinity REAL,
    o2_ml_l REAL,
    chlorophyll REAL,
    nitrate REAL,
    phosphate REAL,
    larvae_count REAL
);

CREATE TABLE IF NOT EXISTS scripps_pier (
    timestamp TEXT,
    temp_c REAL,
    o2_mg_l REAL,
    chlorophyll_ug_l REAL,
    salinity REAL,
    calibration_trigger INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sst_observations (
    region_id TEXT,
    date TEXT,
    sst_c REAL,
    sst_anomaly_c REAL,
    anomaly_8wk_avg REAL,
    bleaching_risk INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS coral_bleaching_alerts (
    region_id TEXT,
    date TEXT,
    dhw REAL,
    alert_level INTEGER,
    bleaching_probability REAL,
    region_alert_critical INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ocean_color (
    region_id TEXT,
    date TEXT,
    chlorophyll_mg_m3 REAL,
    water_clarity TEXT,
    hypoxia_flag INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS region_daily_features (
    region_id TEXT,
    date TEXT,
    sst_current REAL,
    sst_anomaly REAL,
    sst_anomaly_30d_avg REAL,
    sst_acceleration REAL,
    bleaching_risk_flag INTEGER,
    o2_current REAL,
    o2_deviation REAL,
    o2_trend_90d REAL,
    hypoxia_risk REAL,
    hypoxia_flag INTEGER,
    chlorophyll_anomaly REAL,
    larvae_count_trend REAL,
    dhw_current REAL,
    bleaching_alert_level INTEGER,
    co2_regional_ppm REAL,
    co2_yoy_acceleration REAL,
    nitrate_anomaly REAL,
    phosphate_anomaly REAL,
    scientific_event_flag INTEGER,
    active_situation_reports INTEGER,
    stress_composite REAL,
    sst_anomaly_7d_avg REAL,
    sst_anomaly_90d_avg REAL,
    sst_anomaly_365d_avg REAL,
    o2_current_7d_avg REAL,
    o2_current_30d_avg REAL,
    o2_current_365d_avg REAL,
    sst_anomaly_yoy_delta REAL,
    o2_current_yoy_delta REAL,
    chlorophyll_anomaly_yoy_delta REAL
);

CREATE TABLE IF NOT EXISTS regions (
    id TEXT PRIMARY KEY,
    name TEXT,
    lat REAL,
    lon REAL,
    current_score REAL,
    days_to_threshold INTEGER,
    funding_gap REAL DEFAULT 0,
    primary_threat TEXT,
    alert_level TEXT,
    population_affected INTEGER DEFAULT 0,
    primary_driver TEXT,
    bleaching_alert_level INTEGER DEFAULT 0,
    active_situation_reports INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS region_features (
    region_id TEXT,
    date TEXT,
    sst_anomaly REAL,
    o2_current REAL,
    chlorophyll_anomaly REAL,
    co2_regional_ppm REAL,
    nitrate_anomaly REAL,
    threshold_proximity_score REAL
);
