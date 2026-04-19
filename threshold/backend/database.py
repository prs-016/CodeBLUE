from __future__ import annotations
from typing import Optional

from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from config import settings

def _get_engine():
    if settings.snowflake_account and settings.snowflake_user:
        try:
            print("Sponsor Integration Active: Establishing dynamic connection to Snowflake Warehouse...")
            snowflake_url = f"snowflake://{settings.snowflake_user}:{settings.snowflake_password}@{settings.snowflake_account}/{settings.snowflake_database}/{settings.snowflake_schema}"
            return create_engine(snowflake_url, future=True)
        except Exception as e:
            print(f"Warning: Snowflake connection failed, falling back to SQLite. Error: {e}")
            
    print("Executing locally with SQLite proxy datastore.")
    return create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
        future=True,
    )

engine = _get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


REGION_SEED = [
    {
        "id": "great_barrier_reef",
        "name": "Great Barrier Reef",
        "lat": -18.2871,
        "lon": 147.6992,
        "current_score": 8.4,
        "days_to_threshold": 47,
        "funding_gap": 8_400_000,
        "primary_threat": "thermal",
        "alert_level": "critical",
        "population_affected": 4_200_000,
        "primary_driver": "SST Anomaly +2.3°C above 30yr baseline",
        "trend_summary": "DHW 9.1, NOAA Alert Level 4, bleaching risk elevated",
    },
    {
        "id": "mekong_delta",
        "name": "Mekong Delta",
        "lat": 10.0452,
        "lon": 105.7469,
        "current_score": 7.1,
        "days_to_threshold": 180,
        "funding_gap": 9_600_000,
        "primary_threat": "hypoxia",
        "alert_level": "high",
        "population_affected": 17_500_000,
        "primary_driver": "Dissolved O2 at 2.8ml/L (threshold: 2.0)",
        "trend_summary": "Oxygen falling while nutrient load remains elevated",
    },
    {
        "id": "arabian_sea",
        "name": "Arabian Sea",
        "lat": 17.0,
        "lon": 66.0,
        "current_score": 6.8,
        "days_to_threshold": 290,
        "funding_gap": 12_000_000,
        "primary_threat": "hypoxia",
        "alert_level": "high",
        "population_affected": 8_600_000,
        "primary_driver": "Expanding dead zone — O2 3.1ml/L declining at -0.08/yr",
        "trend_summary": "Low oxygen event footprint expanding across fisheries",
    },
    {
        "id": "california_current",
        "name": "California Current",
        "lat": 39.0,
        "lon": -124.0,
        "current_score": 5.2,
        "days_to_threshold": 520,
        "funding_gap": 3_200_000,
        "primary_threat": "acidification",
        "alert_level": "watch",
        "population_affected": 1_800_000,
        "primary_driver": "CO2 acceleration +3.4% YoY above trend",
        "trend_summary": "Pier calibration stable; long-run acidification rising",
    },
    {
        "id": "gulf_of_mexico",
        "name": "Gulf of Mexico",
        "lat": 24.0,
        "lon": -90.0,
        "current_score": 6.1,
        "days_to_threshold": 365,
        "funding_gap": 7_200_000,
        "primary_threat": "hypoxia",
        "alert_level": "high",
        "population_affected": 6_100_000,
        "primary_driver": "Chlorophyll bloom 4.2x seasonal baseline",
        "trend_summary": "Dead zone season approaching with elevated nutrient load",
    },
    {
        "id": "coral_triangle",
        "name": "Coral Triangle",
        "lat": 0.0,
        "lon": 128.0,
        "current_score": 7.8,
        "days_to_threshold": 95,
        "funding_gap": 11_000_000,
        "primary_threat": "thermal",
        "alert_level": "critical",
        "population_affected": 9_400_000,
        "primary_driver": "SST Anomaly +1.8°C, DHW 6.4 and rising",
        "trend_summary": "Thermal stress building across coral systems",
    },
    {
        "id": "baltic_sea",
        "name": "Baltic Sea",
        "lat": 58.8,
        "lon": 19.5,
        "current_score": 4.8,
        "days_to_threshold": 730,
        "funding_gap": 4_100_000,
        "primary_threat": "hypoxia",
        "alert_level": "watch",
        "population_affected": 2_700_000,
        "primary_driver": "Persistent hypoxic zone — O2 3.8ml/L",
        "trend_summary": "Chronic stress but slower near-term acceleration",
    },
    {
        "id": "bengal_bay",
        "name": "Bay of Bengal",
        "lat": 15.0,
        "lon": 89.0,
        "current_score": 5.9,
        "days_to_threshold": 410,
        "funding_gap": 8_800_000,
        "primary_threat": "thermal",
        "alert_level": "watch",
        "population_affected": 12_300_000,
        "primary_driver": "SST Anomaly +1.4°C, cyclone intensification risk",
        "trend_summary": "Heat load and cyclone exposure increasing together",
    },
]


FUNDING_ROUND_SEED = [
    {
        "id": "round_gbr_001",
        "region_id": "great_barrier_reef",
        "title": "GBR Thermal Stress Rapid Response",
        "target_amount": 10_000_000,
        "raised_amount": 1_600_000,
        "status": "active",
        "deadline": "2026-06-30T00:00:00Z",
        "cost_multiplier": 16.0,
        "partner_ein": "52-1693387",
    },
    {
        "id": "round_mekong_001",
        "region_id": "mekong_delta",
        "title": "Mekong Oxygen Recovery Program",
        "target_amount": 12_000_000,
        "raised_amount": 2_400_000,
        "status": "active",
        "deadline": "2026-08-15T00:00:00Z",
        "cost_multiplier": 8.0,
        "partner_ein": "worldfish-center",
    },
]


COUNTERFACTUAL_CASE_SEED = [
    {
        "case_id": "california_sardine",
        "region_id": "california_current",
        "event_name": "California Sardine Collapse",
        "year_crossed": 1947,
        "prevention_cost": 8_000_000,
        "recovery_cost": 800_000_000,
        "cost_multiplier": 100.0,
        "early_warning_date": "1939-01-01",
        "threshold_crossed_date": "1947-06-01",
        "data_source": "CalCOFI 1949 retrospective analysis",
    },
    {
        "case_id": "gbr_2016",
        "region_id": "great_barrier_reef",
        "event_name": "GBR Mass Bleaching Event",
        "year_crossed": 2016,
        "prevention_cost": 25_000_000,
        "recovery_cost": 400_000_000,
        "cost_multiplier": 16.0,
        "early_warning_date": "2014-01-01",
        "threshold_crossed_date": "2016-02-01",
        "data_source": "NOAA Coral Reef Watch + EM-DAT",
    },
    {
        "case_id": "arabian_sea_dead_zone",
        "region_id": "arabian_sea",
        "event_name": "Arabian Sea Dead Zone Expansion",
        "year_crossed": 2008,
        "prevention_cost": 50_000_000,
        "recovery_cost": 2_100_000_000,
        "cost_multiplier": 42.0,
        "early_warning_date": "2000-01-01",
        "threshold_crossed_date": "2008-01-01",
        "data_source": "NASA Ocean Color + World Bank",
    },
]


CHARITY_SEED = [
    {
        "ein": "52-1693387",
        "region_id": "great_barrier_reef",
        "name": "WWF",
        "overall_score": 89.4,
        "financial_score": 91.2,
        "accountability_score": 87.6,
        "program_expense_ratio": 0.824,
        "active_regions": "great_barrier_reef,coral_triangle",
    },
    {
        "ein": "53-0242652",
        "region_id": "california_current",
        "name": "The Nature Conservancy",
        "overall_score": 92.1,
        "financial_score": 93.8,
        "accountability_score": 91.1,
        "program_expense_ratio": 0.861,
        "active_regions": "california_current,gulf_of_mexico",
    },
    {
        "ein": "worldfish-center",
        "region_id": "mekong_delta",
        "name": "WorldFish Center",
        "overall_score": 84.0,
        "financial_score": 82.0,
        "accountability_score": 86.0,
        "program_expense_ratio": 0.79,
        "active_regions": "mekong_delta,bengal_bay",
    },
]


NEWS_SEED = [
    {
        "id": "rw-gbr-1",
        "region_id": "great_barrier_reef",
        "title": "Great Barrier Reef bleaching conditions worsen",
        "source_type": "reliefweb",
        "source_org": "OCHA",
        "date": "2026-04-10",
        "body_summary": "Field updates confirm severe bleaching stress across northern reef sections.",
        "url": "https://reliefweb.int/report/example-gbr",
        "urgency_score": 9.3,
        "disaster_type": "Marine Ecosystem",
    },
    {
        "id": "gdelt-arabian-1",
        "region_id": "arabian_sea",
        "title": "Limited coverage despite expanding Arabian Sea dead zone",
        "source_type": "gdelt",
        "source_org": "GDELT",
        "date": "2026-04-12",
        "body_summary": "Low article volume persists while fisheries report oxygen stress impacts.",
        "url": "https://data.gdeltproject.org/gkg/",
        "urgency_score": 5.1,
        "disaster_type": "Marine Ecosystem",
    },
    {
        "id": "rw-mekong-1",
        "region_id": "mekong_delta",
        "title": "Mekong Delta livelihoods under pressure from low oxygen events",
        "source_type": "reliefweb",
        "source_org": "ReliefWeb",
        "date": "2026-04-08",
        "body_summary": "Communities report declining catches and higher water management costs.",
        "url": "https://reliefweb.int/report/example-mekong",
        "urgency_score": 7.8,
        "disaster_type": "Flood",
    },
]


ATTENTION_SEED = [
    ("great_barrier_reef", 8.4, 7.9),
    ("mekong_delta", 7.1, 3.4),
    ("arabian_sea", 6.8, 2.6),
    ("california_current", 5.2, 4.4),
    ("gulf_of_mexico", 6.1, 5.7),
    ("coral_triangle", 7.8, 4.1),
    ("baltic_sea", 4.8, 3.0),
    ("bengal_bay", 5.9, 3.2),
]

SOLANA_TX_SEED = [
    {
        "tx_hash": "5KtPk3LbVqRdFn2Xwm8YePvhZJsNcU7oAiCdGqWxBHrT1yRmDsLpVoEf6jMnKa4",
        "from_wallet": "Donor7xKpQ2mNvRsFtWxBzYcLnHaEiDgJoUk9bPqCdAm",
        "to_wallet": "threshold-demo-program",
        "amount_usdc": 25000.0,
        "memo": "THRESHOLD FUND: GBR Tranche 1 — Reef restoration",
        "round_id": "gbr-2026-q2",
        "tranche": 1,
        "timestamp": "2026-03-15T09:14:22Z",
        "status": "confirmed",
    },
    {
        "tx_hash": "3RnYwHqMbPdF7sLvKzXcNtAoEiGjUm2WxBrDfCvQpTs8kJeRhZaVgLnYoPqiDwMx",
        "from_wallet": "Donor3mVbNxQwLsRfPkYzAoEiGjUdCvTh9WcXnBpDmJa",
        "to_wallet": "threshold-demo-program",
        "amount_usdc": 10000.0,
        "memo": "THRESHOLD FUND: Coral Triangle Tranche 1 — Fisheries monitoring",
        "round_id": "coral-triangle-2026-q2",
        "tranche": 1,
        "timestamp": "2026-03-22T14:37:55Z",
        "status": "confirmed",
    },
    {
        "tx_hash": "9QpZhFjKwNxBmLsYvRtDcAiEoGbUn4WkXeVgJdCqPrTs7mHaRfZoLnYoPqiDwKx",
        "from_wallet": "Donor9nWxKpQ2mNvRsFtBzYcLnHaEiDgJoUk9bPqCdBm",
        "to_wallet": "threshold-demo-program",
        "amount_usdc": 50000.0,
        "memo": "THRESHOLD FUND: GBR Tranche 2 — Emergency bleaching response",
        "round_id": "gbr-2026-q2",
        "tranche": 2,
        "timestamp": "2026-04-01T11:08:43Z",
        "status": "confirmed",
    },
    {
        "tx_hash": "7MnBvCxPqRsFtWxAoEiGjUk2dYzLhDcNmJaKpZwHfTs6eRbQoLvYgPqiDwKxZn",
        "from_wallet": "Donor2kVbNxQwLsRfPkYzAoEiGjUdCvTh9WcXnBpDmJa",
        "to_wallet": "threshold-demo-program",
        "amount_usdc": 15000.0,
        "memo": "THRESHOLD FUND: Mekong Delta Tranche 1 — Water quality sensors",
        "round_id": "gbr-2026-q2",
        "tranche": 1,
        "timestamp": "2026-04-08T16:22:11Z",
        "status": "confirmed",
    },
    {
        "tx_hash": "2LpYhEjNwMxAmKsZvRtBcAiDoGbUn5WkXeVgJdCqPrTs8mHaRfZoLnYoPqiDwKy",
        "from_wallet": "Donor5pXbKwQmNvLsFtRzYcAnHaEiDgJoUk7bPqCdAm",
        "to_wallet": "threshold-demo-program",
        "amount_usdc": 7500.0,
        "memo": "THRESHOLD FUND: Arabian Sea Tranche 1 — Dead zone mapping",
        "round_id": "coral-triangle-2026-q2",
        "tranche": 1,
        "timestamp": "2026-04-14T08:55:30Z",
        "status": "confirmed",
    },
]


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS app_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS regions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    lat REAL NOT NULL,
                    lon REAL NOT NULL,
                    current_score REAL NOT NULL,
                    days_to_threshold INTEGER NOT NULL,
                    funding_gap REAL NOT NULL,
                    primary_threat TEXT NOT NULL,
                    alert_level TEXT NOT NULL,
                    population_affected INTEGER NOT NULL,
                    primary_driver TEXT NOT NULL,
                    trend_summary TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS funding_rounds (
                    id TEXT PRIMARY KEY,
                    region_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    target_amount REAL NOT NULL,
                    raised_amount REAL NOT NULL,
                    status TEXT NOT NULL,
                    deadline TEXT NOT NULL,
                    cost_multiplier REAL NOT NULL,
                    partner_ein TEXT,
                    FOREIGN KEY(region_id) REFERENCES regions(id)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS region_features (
                    region_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    sst_anomaly REAL NOT NULL,
                    o2_current REAL NOT NULL,
                    chlorophyll_anomaly REAL NOT NULL,
                    co2_regional_ppm REAL NOT NULL,
                    nitrate_anomaly REAL NOT NULL,
                    threshold_proximity_score REAL NOT NULL,
                    scientific_event_flag INTEGER NOT NULL DEFAULT 0,
                    active_situation_reports INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (region_id, date),
                    FOREIGN KEY(region_id) REFERENCES regions(id)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS counterfactual_cases (
                    case_id TEXT PRIMARY KEY,
                    region_id TEXT NOT NULL,
                    event_name TEXT NOT NULL,
                    year_crossed INTEGER NOT NULL,
                    prevention_cost REAL NOT NULL,
                    recovery_cost REAL NOT NULL,
                    cost_multiplier REAL NOT NULL,
                    early_warning_date TEXT,
                    threshold_crossed_date TEXT,
                    data_source TEXT,
                    FOREIGN KEY(region_id) REFERENCES regions(id)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS news_reports (
                    id TEXT PRIMARY KEY,
                    region_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_org TEXT NOT NULL,
                    date TEXT NOT NULL,
                    body_summary TEXT NOT NULL,
                    url TEXT NOT NULL,
                    urgency_score REAL NOT NULL,
                    disaster_type TEXT,
                    FOREIGN KEY(region_id) REFERENCES regions(id)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS charity_registry (
                    ein TEXT PRIMARY KEY,
                    region_id TEXT,
                    name TEXT NOT NULL,
                    overall_score REAL NOT NULL,
                    financial_score REAL,
                    accountability_score REAL,
                    program_expense_ratio REAL,
                    active_regions TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS media_attention (
                    region_id TEXT PRIMARY KEY,
                    severity_score REAL NOT NULL,
                    normalized_attention_score REAL NOT NULL,
                    attention_gap REAL NOT NULL,
                    FOREIGN KEY(region_id) REFERENCES regions(id)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS stripe_transactions (
                    payment_intent_id TEXT PRIMARY KEY,
                    amount_usd REAL NOT NULL,
                    donor_email_hash TEXT,
                    round_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS solana_transactions (
                    tx_hash TEXT PRIMARY KEY,
                    from_wallet TEXT NOT NULL,
                    to_wallet TEXT NOT NULL,
                    amount_usdc REAL NOT NULL,
                    memo TEXT NOT NULL,
                    round_id TEXT NOT NULL,
                    tranche INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL
                )
                """
            )
        )
        _ensure_column(conn, "regions", "primary_driver", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "regions", "trend_summary", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "funding_rounds", "title", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "funding_rounds", "partner_ein", "TEXT")
        _ensure_column(conn, "region_features", "scientific_event_flag", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(conn, "region_features", "active_situation_reports", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(conn, "counterfactual_cases", "early_warning_date", "TEXT")
        _ensure_column(conn, "counterfactual_cases", "threshold_crossed_date", "TEXT")
        _ensure_column(conn, "counterfactual_cases", "data_source", "TEXT")
        _ensure_column(conn, "news_reports", "source_type", "TEXT NOT NULL DEFAULT 'reliefweb'")
        _ensure_column(conn, "news_reports", "disaster_type", "TEXT")
        _ensure_column(conn, "charity_registry", "financial_score", "REAL")
        _ensure_column(conn, "charity_registry", "accountability_score", "REAL")
        _ensure_column(conn, "charity_registry", "program_expense_ratio", "REAL")
        _ensure_column(conn, "charity_registry", "active_regions", "TEXT")

    seed_demo_data()


def seed_demo_data() -> None:
    with engine.begin() as conn:
        region_count = conn.execute(text("SELECT COUNT(*) FROM regions")).scalar_one()
        if region_count == 0:
            conn.execute(
                text(
                    """
                    INSERT INTO regions (
                        id, name, lat, lon, current_score, days_to_threshold, funding_gap,
                        primary_threat, alert_level, population_affected, primary_driver, trend_summary
                    ) VALUES (
                        :id, :name, :lat, :lon, :current_score, :days_to_threshold, :funding_gap,
                        :primary_threat, :alert_level, :population_affected, :primary_driver, :trend_summary
                    )
                    """
                ),
                REGION_SEED,
            )

        round_count = conn.execute(text("SELECT COUNT(*) FROM funding_rounds")).scalar_one()
        if round_count == 0:
            conn.execute(
                text(
                    """
                    INSERT INTO funding_rounds (
                        id, region_id, title, target_amount, raised_amount, status, deadline,
                        cost_multiplier, partner_ein
                    ) VALUES (
                        :id, :region_id, :title, :target_amount, :raised_amount, :status, :deadline,
                        :cost_multiplier, :partner_ein
                    )
                    """
                ),
                FUNDING_ROUND_SEED,
            )

        case_count = conn.execute(text("SELECT COUNT(*) FROM counterfactual_cases")).scalar_one()
        if case_count == 0:
            conn.execute(
                text(
                    """
                    INSERT INTO counterfactual_cases (
                        case_id, region_id, event_name, year_crossed, prevention_cost,
                        recovery_cost, cost_multiplier, early_warning_date, threshold_crossed_date, data_source
                    ) VALUES (
                        :case_id, :region_id, :event_name, :year_crossed, :prevention_cost,
                        :recovery_cost, :cost_multiplier, :early_warning_date, :threshold_crossed_date, :data_source
                    )
                    """
                ),
                COUNTERFACTUAL_CASE_SEED,
            )

        charity_count = conn.execute(text("SELECT COUNT(*) FROM charity_registry")).scalar_one()
        if charity_count == 0:
            conn.execute(
                text(
                    """
                    INSERT INTO charity_registry (
                        ein, region_id, name, overall_score, financial_score,
                        accountability_score, program_expense_ratio, active_regions
                    ) VALUES (
                        :ein, :region_id, :name, :overall_score, :financial_score,
                        :accountability_score, :program_expense_ratio, :active_regions
                    )
                    """
                ),
                CHARITY_SEED,
            )

        news_count = conn.execute(text("SELECT COUNT(*) FROM news_reports")).scalar_one()
        if news_count == 0:
            conn.execute(
                text(
                    """
                    INSERT INTO news_reports (
                        id, region_id, title, source_type, source_org, date,
                        body_summary, url, urgency_score, disaster_type
                    ) VALUES (
                        :id, :region_id, :title, :source_type, :source_org, :date,
                        :body_summary, :url, :urgency_score, :disaster_type
                    )
                    """
                ),
                NEWS_SEED,
            )

        conn.execute(
            text(
                """
                INSERT OR REPLACE INTO region_features (
                    region_id, date, sst_anomaly, o2_current, chlorophyll_anomaly,
                    co2_regional_ppm, nitrate_anomaly, threshold_proximity_score,
                    scientific_event_flag, active_situation_reports
                ) VALUES (
                    :region_id, :date, :sst_anomaly, :o2_current, :chlorophyll_anomaly,
                    :co2_regional_ppm, :nitrate_anomaly, :threshold_proximity_score,
                    :scientific_event_flag, :active_situation_reports
                )
                """
            ),
            list(_generate_region_features()),
        )

        attention_count = conn.execute(text("SELECT COUNT(*) FROM media_attention")).scalar_one()
        if attention_count == 0:
            conn.execute(
                text(
                    """
                    INSERT INTO media_attention (
                        region_id, severity_score, normalized_attention_score, attention_gap
                    ) VALUES (
                        :region_id, :severity_score, :normalized_attention_score, :attention_gap
                    )
                    """
                ),
                [
                    {
                        "region_id": region_id,
                        "severity_score": severity,
                        "normalized_attention_score": attention,
                        "attention_gap": round(severity - attention, 2),
                    }
                    for region_id, severity, attention in ATTENTION_SEED
                ],
            )

        solana_count = conn.execute(text("SELECT COUNT(*) FROM solana_transactions")).scalar_one()
        if solana_count == 0:
            conn.execute(
                text(
                    """
                    INSERT INTO solana_transactions (
                        tx_hash, from_wallet, to_wallet, amount_usdc, memo,
                        round_id, tranche, timestamp, status
                    ) VALUES (
                        :tx_hash, :from_wallet, :to_wallet, :amount_usdc, :memo,
                        :round_id, :tranche, :timestamp, :status
                    )
                    """
                ),
                SOLANA_TX_SEED,
            )

        _upsert_app_meta(conn, "last_data_refresh", datetime.now(timezone.utc).isoformat())


def _generate_region_features() -> Iterator[dict[str, Any]]:
    """Generate 3 years of daily regional stress signals with realistic El Niño patterns."""
    import math

    today = date.today()
    # 3-year lookback (1095 days) — captures 2023 El Niño, warming trend, seasonality
    total_days = 1095
    start_date = today - timedelta(days=total_days - 1)

    # El Niño events: start → peak month (1-indexed), intensity multiplier
    EL_NINO_WINDOWS = [
        (date(2023, 6, 1), date(2024, 3, 1), 1.0),   # 2023–24 moderate El Niño
    ]
    HIGH_ALERT_REGIONS = {"great_barrier_reef", "mekong_delta"}

    for region in REGION_SEED:
        base_score = region["current_score"]
        region_id = region["id"]

        for day_offset in range(total_days):
            point_date = start_date + timedelta(days=day_offset)

            # Fractional year position for seasonality (0→1 over calendar year)
            day_of_year = point_date.timetuple().tm_yday
            seasonal = math.sin(2 * math.pi * (day_of_year / 365.0 - 0.25))

            # Long-term warming trend: +0.003 score/day across 3 years
            trend = day_offset * 0.003 / total_days * base_score

            # El Niño boost
            el_nino_boost = 0.0
            for el_start, el_end, intensity in EL_NINO_WINDOWS:
                if el_start <= point_date <= el_end:
                    # Gaussian peak around midpoint of event
                    midpoint = el_start + (el_end - el_start) / 2
                    days_from_mid = abs((point_date - midpoint).days)
                    duration = (el_end - el_start).days / 2
                    el_nino_boost = intensity * math.exp(-0.5 * (days_from_mid / max(duration, 1)) ** 2)
                    break

            # Build per-metric values
            sst_base = base_score / 4.5
            sst_anomaly = round(
                sst_base + seasonal * 0.55 + trend * 0.4 + el_nino_boost * 0.8,
                3,
            )
            o2_current = round(
                max(1.2, 5.8 - (base_score / 2.0) - seasonal * 0.15 - el_nino_boost * 0.3),
                3,
            )
            chlorophyll_anomaly = round(
                max(0.1, 1.0 + seasonal * base_score / 4.0 + el_nino_boost * 0.5),
                3,
            )
            co2_regional_ppm = round(418.0 + day_offset * (2.5 / 365), 3)  # ~2.5 ppm/yr rise
            nitrate_anomaly = round(max(0.1, 0.3 + seasonal * 1.2 + el_nino_boost * 0.4), 3)

            # Threshold proximity score: drives toward current_score with trend + events
            score = max(
                0.0,
                min(
                    10.0,
                    base_score - 1.5 + trend + el_nino_boost * 1.2 + seasonal * 0.4,
                ),
            )

            scientific_flag = 1 if (el_nino_boost > 0.5 or score > base_score) else 0
            situation_reports = 2 if region_id in HIGH_ALERT_REGIONS else (1 if score > 6.0 else 0)

            yield {
                "region_id": region_id,
                "date": point_date.isoformat(),
                "sst_anomaly": sst_anomaly,
                "o2_current": o2_current,
                "chlorophyll_anomaly": chlorophyll_anomaly,
                "co2_regional_ppm": co2_regional_ppm,
                "nitrate_anomaly": nitrate_anomaly,
                "threshold_proximity_score": round(score, 3),
                "scientific_event_flag": scientific_flag,
                "active_situation_reports": situation_reports,
            }


def _upsert_app_meta(conn: Any, key: str, value: str) -> None:
    conn.execute(
        text(
            """
            INSERT INTO app_meta (key, value) VALUES (:key, :value)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """
        ),
        {"key": key, "value": value},
    )


def _ensure_column(conn: Any, table_name: str, column_name: str, column_sql: str) -> None:
    existing_columns = {
        row[1]
        for row in conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    }
    if column_name not in existing_columns:
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"))


def get_last_data_refresh(db: Session) -> Optional[str]:
    row = db.execute(
        text("SELECT value FROM app_meta WHERE key = 'last_data_refresh'")
    ).fetchone()
    return row[0] if row else None
