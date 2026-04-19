CREATE TABLE IF NOT EXISTS humanitarian_funding (
    year INTEGER,
    donor TEXT,
    recipient_org TEXT,
    country TEXT,
    crisis_type TEXT,
    amount_usd REAL,
    status TEXT,
    date_committed TEXT
);

CREATE TABLE IF NOT EXISTS hdx_funding_needs (
    year INTEGER,
    country TEXT,
    people_in_need INTEGER,
    funds_required_usd REAL,
    funds_received_usd REAL,
    gap_usd REAL,
    coverage_ratio REAL
);

CREATE TABLE IF NOT EXISTS historical_disasters (
    year INTEGER,
    country TEXT,
    disaster_type TEXT,
    deaths INTEGER,
    total_affected INTEGER,
    economic_loss_usd_2024 REAL,
    insured_loss_usd_2024 REAL
);

CREATE TABLE IF NOT EXISTS world_bank_disaster_costs (
    country TEXT,
    year INTEGER,
    event TEXT,
    gdp_impact_pct REAL,
    ag_loss_usd REAL,
    infra_loss_usd REAL,
    recovery_expenditure_usd REAL
);

CREATE TABLE IF NOT EXISTS funding_gap (
    region_id TEXT,
    as_of_date TEXT,
    modeled_intervention_cost REAL,
    committed_funding REAL,
    funding_gap REAL,
    coverage_ratio REAL,
    impact_per_dollar REAL
);

CREATE TABLE IF NOT EXISTS funding_rounds (
    id TEXT PRIMARY KEY,
    region_id TEXT,
    target_amount REAL,
    raised_amount REAL,
    status TEXT,
    deadline TEXT,
    cost_multiplier REAL
);

CREATE TABLE IF NOT EXISTS counterfactual_cases (
    case_id TEXT PRIMARY KEY,
    region_id TEXT,
    event_name TEXT,
    year_crossed INTEGER,
    prevention_cost REAL,
    recovery_cost REAL,
    cost_multiplier REAL
);
