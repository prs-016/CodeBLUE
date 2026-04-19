from __future__ import annotations
from typing import Optional

import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)
from datetime import datetime, timezone
from typing import Any, Iterator
import urllib.parse

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from config import settings


def _get_engine():
    if settings.snowflake_account and settings.snowflake_user:
        try:
            print("Sponsor Integration Active: Establishing dynamic connection to Snowflake Warehouse...")
            safe_password = urllib.parse.quote_plus(settings.snowflake_password)
            warehouse = settings.snowflake_warehouse or "COMPUTE_WH"
            snowflake_url = f"snowflake://{settings.snowflake_user}:{safe_password}@{settings.snowflake_account}/{settings.snowflake_database}/{settings.snowflake_schema}?warehouse={warehouse}"
            eng = create_engine(snowflake_url, future=True)
            with eng.connect() as test_conn:
                pass
            return eng
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
        _ensure_column(conn, "region_features", "dhw_current", "REAL NOT NULL DEFAULT 0")
        _ensure_column(conn, "region_features", "bleaching_alert_level", "REAL NOT NULL DEFAULT 0")
        _ensure_column(conn, "counterfactual_cases", "early_warning_date", "TEXT")
        _ensure_column(conn, "counterfactual_cases", "threshold_crossed_date", "TEXT")
        _ensure_column(conn, "counterfactual_cases", "data_source", "TEXT")
        _ensure_column(conn, "news_reports", "source_type", "TEXT NOT NULL DEFAULT 'reliefweb'")
        _ensure_column(conn, "news_reports", "disaster_type", "TEXT")
        _ensure_column(conn, "charity_registry", "financial_score", "REAL")
        _ensure_column(conn, "charity_registry", "accountability_score", "REAL")
        _ensure_column(conn, "charity_registry", "program_expense_ratio", "REAL")
        _ensure_column(conn, "charity_registry", "active_regions", "TEXT")


def _upsert_app_meta(conn: Any, key: str, value: str) -> None:
    if conn.dialect.name == "snowflake":
        conn.execute(
            text(
                """
                MERGE INTO app_meta USING (SELECT :key as k, :value as v) src
                ON app_meta.key = src.k
                WHEN MATCHED THEN UPDATE SET value = src.v
                WHEN NOT MATCHED THEN INSERT (key, value) VALUES (src.k, src.v)
                """
            ),
            {"key": key, "value": value},
        )
    else:
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
    if conn.dialect.name == "snowflake":
        query = f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name.upper()}'"
        existing_columns = {row[0].lower() for row in conn.execute(text(query)).fetchall()}
    else:
        existing_columns = {
            row[1].lower()
            for row in conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
        }
    if column_name.lower() not in existing_columns:
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"))


def get_last_data_refresh(db: Session) -> Optional[str]:
    row = db.execute(
        text("SELECT value FROM app_meta WHERE key = 'last_data_refresh'")
    ).fetchone()
    return row[0] if row else None
