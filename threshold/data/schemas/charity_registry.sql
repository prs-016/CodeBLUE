CREATE TABLE IF NOT EXISTS charity_registry (
    ein TEXT PRIMARY KEY,
    name TEXT,
    overall_score REAL,
    financial_score REAL,
    accountability_score REAL,
    program_expense_ratio REAL,
    active_regions TEXT,
    eligible_for_disbursement INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS charity_regional_presence (
    organization TEXT,
    country TEXT,
    region_id TEXT,
    sector TEXT,
    status TEXT,
    last_verified TEXT
);

CREATE TABLE IF NOT EXISTS givewell_impact (
    organization TEXT,
    cost_per_outcome REAL,
    outcome_type TEXT,
    evidence_quality TEXT,
    year INTEGER
);
