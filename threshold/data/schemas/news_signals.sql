CREATE TABLE IF NOT EXISTS reliefweb_reports (
    id INTEGER PRIMARY KEY,
    title TEXT,
    date TEXT,
    country TEXT,
    disaster_type TEXT,
    source_org TEXT,
    body_summary TEXT,
    url TEXT,
    crisis_active_flag INTEGER DEFAULT 0,
    region_id TEXT
);

CREATE TABLE IF NOT EXISTS gdelt_attention (
    region_id TEXT,
    year_month TEXT,
    article_count INTEGER,
    avg_tone REAL,
    attention_score REAL,
    top_keywords TEXT
);

CREATE TABLE IF NOT EXISTS scientific_events (
    date TEXT,
    agency TEXT,
    title TEXT,
    event_type TEXT,
    region_id TEXT,
    url TEXT
);

CREATE TABLE IF NOT EXISTS media_attention (
    region_id TEXT,
    year_month TEXT,
    normalized_attention_score REAL,
    threshold_proximity_score REAL,
    attention_gap REAL,
    article_count INTEGER,
    avg_tone REAL
);

CREATE TABLE IF NOT EXISTS news_reports (
    id TEXT PRIMARY KEY,
    region_id TEXT,
    title TEXT,
    source_org TEXT,
    date TEXT,
    body_summary TEXT,
    url TEXT,
    urgency_score REAL,
    signal_type TEXT
);
