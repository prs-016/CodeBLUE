from __future__ import annotations

import argparse
import json
import logging
import math
import os
import sqlite3
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import parse_qs, urlparse

import numpy as np
import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = BASE_DIR / "cache"
SCHEMA_DIR = BASE_DIR / "schemas"
MANIFEST_PATH = BASE_DIR / "data_manifest.json"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

REGIONS = {
    "california_current": {
        "lat": (30, 48),
        "lon": (-130, -117),
        "name": "California Current",
        "primary_datasets": ["calcofi", "scripps_pier", "noaa_sst"],
        "primary_threat": "acidification",
        "star_case_study": "California Sardine Collapse (1940s-1950s)",
        "countries": ["United States", "Mexico"],
    },
    "great_barrier_reef": {
        "lat": (-25, -10),
        "lon": (142, 155),
        "name": "Great Barrier Reef",
        "primary_datasets": ["noaa_sst", "coral_reef_watch", "nasa_ocean_color"],
        "primary_threat": "thermal",
        "star_case_study": "GBR Mass Bleaching Event (2016)",
        "countries": ["Australia"],
    },
    "arabian_sea": {
        "lat": (8, 25),
        "lon": (55, 78),
        "name": "Arabian Sea",
        "primary_datasets": ["noaa_sst", "nasa_ocean_color", "gdelt"],
        "primary_threat": "hypoxia",
        "star_case_study": "Arabian Sea Dead Zone Expansion (2008-present)",
        "countries": ["India", "Pakistan", "Oman", "Yemen", "Somalia"],
    },
    "baltic_sea": {
        "lat": (53, 66),
        "lon": (9, 30),
        "name": "Baltic Sea",
        "primary_datasets": ["noaa_sst", "nasa_ocean_color"],
        "primary_threat": "hypoxia",
        "star_case_study": "Baltic Hypoxic Dead Zone (ongoing)",
        "countries": ["Sweden", "Finland", "Poland", "Estonia", "Latvia", "Lithuania", "Denmark", "Germany"],
    },
    "mekong_delta": {
        "lat": (8, 15),
        "lon": (103, 110),
        "name": "Mekong Delta",
        "primary_datasets": ["noaa_sst", "nasa_ocean_color", "reliefweb"],
        "primary_threat": "hypoxia",
        "star_case_study": "Mekong Fishery Collapse Risk",
        "countries": ["Vietnam", "Cambodia"],
    },
    "coral_triangle": {
        "lat": (-10, 10),
        "lon": (115, 145),
        "name": "Coral Triangle",
        "primary_datasets": ["noaa_sst", "coral_reef_watch", "nasa_ocean_color"],
        "primary_threat": "thermal",
        "star_case_study": "Coral Triangle Bleaching (2010)",
        "countries": ["Indonesia", "Philippines", "Malaysia", "Papua New Guinea", "Timor-Leste", "Solomon Islands"],
    },
    "bengal_bay": {
        "lat": (8, 22),
        "lon": (79, 100),
        "name": "Bay of Bengal",
        "primary_datasets": ["noaa_sst", "reliefweb", "gdelt"],
        "primary_threat": "thermal",
        "star_case_study": "Bengal Bay Cyclone Intensification",
        "countries": ["Bangladesh", "India", "Myanmar", "Sri Lanka"],
    },
    "gulf_of_mexico": {
        "lat": (18, 30),
        "lon": (-98, -80),
        "name": "Gulf of Mexico",
        "primary_datasets": ["nasa_ocean_color", "noaa_sst", "emdat"],
        "primary_threat": "hypoxia",
        "star_case_study": "Gulf Dead Zone (annual expansion)",
        "countries": ["United States", "Mexico", "Cuba"],
    },
}

COUNTRY_TO_REGION = {
    country: region_id
    for region_id, meta in REGIONS.items()
    for country in meta["countries"]
}

OCHA_CLIMATE_KEYWORDS = [
    "flood",
    "drought",
    "cyclone",
    "marine",
    "coastal",
    "fishery",
    "climate",
    "heatwave",
    "bleaching",
]

PRESS_KEYWORDS = ["marine heatwave", "bleaching", "dead zone", "record temperature", "hypoxia", "coral"]

CHARITY_TARGETS = [
    {"ein": "52-1693387", "name": "WWF"},
    {"ein": "53-0242652", "name": "The Nature Conservancy"},
    {"ein": "52-1497470", "name": "Conservation International"},
    {"ein": "23-7245152", "name": "Ocean Conservancy"},
    {"ein": "26-1737731", "name": "Coral Restoration Foundation"},
    {"ein": "RW3W-WORLDFISH", "name": "WorldFish Center"},
    {"ein": "23-7423641", "name": "CARE International"},
    {"ein": "13-3843435", "name": "WFP USA"},
    {"ein": "26-2502530", "name": "Oceana"},
    {"ein": "BCI-LOOKUP", "name": "Blue Carbon Initiative"},
    {"ein": "95-4685501", "name": "Reef Check"},
    {"ein": "81-3519176", "name": "Global Fishing Watch"},
    {"ein": "77-0055541", "name": "Surfrider Foundation"},
    {"ein": "77-0065355", "name": "Sea Shepherd"},
    {"ein": "11-6107128", "name": "Environmental Defense Fund"},
    {"ein": "IUCN-LOOKUP", "name": "IUCN"},
    {"ein": "52-1617061", "name": "Rare Conservation"},
    {"ein": "MSC-LOOKUP", "name": "Marine Stewardship Council"},
    {"ein": "RW3W-CTI", "name": "Coral Triangle Initiative"},
    {"ein": "52-2102482", "name": "The Ocean Foundation"},
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def setup_logging(name: str) -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
    )
    return logging.getLogger(name)


def parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--dry-run", action="store_true", help="Validate and transform without writing outputs.")
    return parser.parse_args()


def sqlite_path_from_env() -> Path:
    database_url = os.getenv("DATABASE_URL", "sqlite:///./threshold.db")
    if database_url.startswith("sqlite:///"):
        raw = database_url.replace("sqlite:///", "", 1)
        path = Path(raw)
    else:
        parsed = urlparse(database_url)
        path = Path(parsed.path)
    if not path.is_absolute():
        path = (BASE_DIR.parent / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def sqlite_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(sqlite_path_from_env())
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    for schema_name in ["region_stress.sql", "funding_gap.sql", "news_signals.sql", "charity_registry.sql"]:
        sql_path = SCHEMA_DIR / schema_name
        if sql_path.exists():
            conn.executescript(sql_path.read_text())
    conn.commit()


def ensure_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def update_manifest(table: str, rows: int, source: str, status: str, detail: dict[str, Any] | None = None) -> None:
    manifest = {}
    if MANIFEST_PATH.exists():
        try:
            manifest = json.loads(MANIFEST_PATH.read_text())
        except json.JSONDecodeError:
            manifest = {}
    manifest[table] = {
        "rows": int(rows),
        "last_updated": utc_now(),
        "source": source,
        "status": status,
        **(detail or {}),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True))


def write_table(
    df: pd.DataFrame,
    table: str,
    conn: sqlite3.Connection | None,
    *,
    dry_run: bool,
    source: str,
    logger: logging.Logger,
    if_exists: str = "replace",
    index: bool = False,
    manifest_detail: dict[str, Any] | None = None,
) -> pd.DataFrame:
    if not dry_run and conn is not None:
        df.to_sql(table, conn, if_exists=if_exists, index=index)
        conn.commit()
    update_manifest(table, len(df), source, "dry-run" if dry_run else "written", manifest_detail)
    logger.info("%s rows prepared for %s via %s", len(df), table, source)
    return df


def cache_csv_path(name: str) -> Path:
    return CACHE_DIR / f"{name}.csv"


def cache_json_path(name: str) -> Path:
    return CACHE_DIR / f"{name}.json"


def save_cache(df: pd.DataFrame, cache_name: str) -> None:
    path = cache_csv_path(cache_name)
    ensure_directory(path)
    df.to_csv(path, index=False)


def load_cache(cache_name: str) -> pd.DataFrame | None:
    path = cache_csv_path(cache_name)
    if path.exists():
        return pd.read_csv(path)
    return None


def request_with_retry(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    allow_redirects: bool = True,
) -> requests.Response:
    if os.getenv("THRESHOLD_SKIP_LIVE_FETCH") == "1":
        raise RuntimeError("Live fetch disabled by THRESHOLD_SKIP_LIVE_FETCH")
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout,
                allow_redirects=allow_redirects,
            )
            response.raise_for_status()
            return response
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(2**attempt)
    raise RuntimeError(f"Failed to fetch {url}") from last_error


def parse_csv_text(text: str, *, comment_prefix: str | None = None) -> pd.DataFrame:
    lines = text.splitlines()
    if comment_prefix:
        lines = [line for line in lines if not line.startswith(comment_prefix)]
    return pd.read_csv(pd.io.common.StringIO("\n".join(lines)))


def month_range(start: str, end: str) -> pd.DatetimeIndex:
    return pd.date_range(start=start, end=end, freq="MS")


def daily_range(start: str, end: str) -> pd.DatetimeIndex:
    return pd.date_range(start=start, end=end, freq="D")


def synthetic_keeling_curve() -> pd.DataFrame:
    dates = daily_range("1958-03-29", "2024-12-31")
    year_fraction = (dates.year - 1958) + (dates.dayofyear - 1) / 365.25
    co2 = 315.71 + (year_fraction * 1.62) + np.sin((dates.dayofyear / 365.25) * 2 * np.pi) * 3.2
    df = pd.DataFrame({"date": dates, "co2_ppm": np.round(co2, 2)})
    df["co2_trend"] = df["co2_ppm"].rolling(30, min_periods=1).mean()
    df["yoy_change"] = df["co2_ppm"].pct_change(365).fillna(0.0)
    rate = df["co2_ppm"].diff(365)
    prior_rate = rate.shift(365).replace(0, np.nan)
    df["acceleration"] = ((rate - prior_rate) / prior_rate).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return df


def synthetic_calcofi() -> pd.DataFrame:
    dates = month_range("1949-01-01", "2024-12-01")
    records: list[dict[str, Any]] = []
    depth_categories = [(0, "surface"), (50, "mid"), (150, "deep")]
    for idx, date in enumerate(dates):
        for depth_m, depth_category in depth_categories:
            warming = idx / 12 * 0.018
            seasonal = math.sin((date.month / 12) * 2 * math.pi) * 0.8
            temp = 12.8 + warming + seasonal - (depth_m * 0.01)
            o2 = 6.5 - (idx / 12 * 0.012) - (depth_m * 0.004)
            larvae = max(25, 240 - idx * 0.08 + (seasonal * 30))
            nitrate = 2.2 + max(0, depth_m / 40) + (idx / len(dates))
            phosphate = 0.28 + max(0, depth_m / 600) + (idx / len(dates) * 0.1)
            records.append(
                {
                    "region_id": "california_current",
                    "date": date.strftime("%Y-%m-%d"),
                    "depth_category": depth_category,
                    "temp_c": round(temp, 3),
                    "salinity": round(33.4 + (depth_m * 0.0015), 3),
                    "o2_ml_l": round(max(1.2, o2), 3),
                    "chlorophyll": round(0.6 + max(0, seasonal * 0.3), 3),
                    "nitrate": round(nitrate, 3),
                    "phosphate": round(phosphate, 3),
                    "larvae_count": round(larvae, 1),
                }
            )
    return pd.DataFrame(records)


def synthetic_scripps_pier() -> pd.DataFrame:
    dates = pd.date_range(end=datetime.now(), periods=7 * 24 * 4, freq="15min")
    base = np.linspace(15.8, 16.6, len(dates))
    df = pd.DataFrame(
        {
            "timestamp": dates,
            "temp_c": np.round(base + np.sin(np.arange(len(dates)) / 20) * 0.4, 3),
            "o2_mg_l": np.round(8.2 - np.linspace(0, 0.4, len(dates)), 3),
            "chlorophyll_ug_l": np.round(1.4 + np.sin(np.arange(len(dates)) / 12) * 0.08, 3),
            "salinity": np.round(33.5 + np.sin(np.arange(len(dates)) / 15) * 0.05, 3),
        }
    )
    return df


def synthetic_sst() -> pd.DataFrame:
    dates = daily_range("2019-01-01", "2024-12-31")
    records: list[dict[str, Any]] = []
    southern = {"great_barrier_reef", "coral_triangle"}
    el_nino_years = {1983, 1998, 2010, 2016, 2023}
    for region_id, region in REGIONS.items():
        midpoint_temp = 23 if region_id in {"baltic_sea"} else 27 if "reef" in region_id or region_id == "coral_triangle" else 25
        for idx, date in enumerate(dates):
            phase_shift = 0 if region_id not in southern else math.pi
            seasonal = math.sin((date.timetuple().tm_yday / 365.25) * 2 * math.pi + phase_shift) * 1.5
            warming = ((date.year - 2019) + (date.dayofyear / 365.25)) * 0.018
            anomaly = 0.6 + seasonal * 0.15 + warming
            if date.year in el_nino_years:
                anomaly += 0.8
            if region_id in {"great_barrier_reef", "coral_triangle"} and date.year >= 2023:
                anomaly += 0.7
            records.append(
                {
                    "region_id": region_id,
                    "date": date.strftime("%Y-%m-%d"),
                    "sst_c": round(midpoint_temp + seasonal + warming, 3),
                    "sst_anomaly_c": round(anomaly, 3),
                }
            )
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["anomaly_8wk_avg"] = (
        df.sort_values("date")
        .groupby("region_id")["sst_anomaly_c"]
        .transform(lambda s: s.rolling(56, min_periods=1).mean())
        .round(3)
    )
    df["bleaching_risk"] = df["anomaly_8wk_avg"] > 1.5
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return df


def synthetic_coral_bleaching() -> pd.DataFrame:
    dates = month_range("2014-01-01", "2024-12-01")
    records = []
    for region_id in ["great_barrier_reef", "coral_triangle"]:
        for date in dates:
            dhw = max(0, (date.year - 2014) * 0.35 + (0.5 if date.month in {1, 2, 3} else 0))
            if date.year in {2016, 2023, 2024}:
                dhw += 4.2
            alert = min(4, int(dhw // 2))
            records.append(
                {
                    "region_id": region_id,
                    "date": date.strftime("%Y-%m-%d"),
                    "dhw": round(dhw, 3),
                    "alert_level": alert,
                    "bleaching_probability": round(min(1.0, dhw / 10), 3),
                    "region_alert_critical": alert >= 4,
                }
            )
    return pd.DataFrame(records)


def synthetic_ocean_color() -> pd.DataFrame:
    dates = month_range("2010-01-01", "2024-12-01")
    records = []
    for region_id in ["great_barrier_reef", "coral_triangle", "arabian_sea", "baltic_sea", "mekong_delta", "gulf_of_mexico"]:
        for idx, date in enumerate(dates):
            seasonal = 1.5 + abs(math.sin((date.month / 12) * 2 * math.pi)) * 2.4
            multiplier = 2.3 if region_id in {"arabian_sea", "gulf_of_mexico", "baltic_sea", "mekong_delta"} else 1.0
            chlorophyll = seasonal * multiplier + (idx / len(dates))
            records.append(
                {
                    "region_id": region_id,
                    "date": date.strftime("%Y-%m-%d"),
                    "chlorophyll_mg_m3": round(chlorophyll, 3),
                    "water_clarity": "Low" if chlorophyll > 5 else "Medium" if chlorophyll > 2.5 else "High",
                }
            )
    return pd.DataFrame(records)


def synthetic_humanitarian_funding() -> pd.DataFrame:
    years = list(range(2020, 2025))
    samples = [
        ("USA", "UNHCR", "Bangladesh", "Climate/Flood", 4200000, "Paid"),
        ("EU", "WFP", "Somalia", "Drought", 8100000, "Paid"),
        ("Germany", "WWF", "Philippines", "Marine", 350000, "Pledged"),
        ("Japan", "CARE International", "Vietnam", "Coastal", 1900000, "Paid"),
        ("UK", "Ocean Conservancy", "Mexico", "Fishery", 850000, "Pledged"),
    ]
    records = []
    for year in years:
        for donor, recipient, country, crisis_type, amount, status in samples:
            records.append(
                {
                    "year": year,
                    "donor": donor,
                    "recipient_org": recipient,
                    "country": country,
                    "crisis_type": crisis_type,
                    "amount_usd": float(amount + (year - 2020) * 120000),
                    "status": status,
                    "date_committed": f"{year}-06-15",
                }
            )
    return pd.DataFrame(records)


def synthetic_hdx() -> pd.DataFrame:
    rows = [
        ("Bangladesh", 7200000, 412000000, 198000000),
        ("Philippines", 5100000, 318000000, 201000000),
        ("Vietnam", 6200000, 220000000, 84000000),
        ("Australia", 950000, 120000000, 45000000),
        ("Mexico", 1800000, 160000000, 36000000),
    ]
    records = []
    for year in range(2020, 2025):
        for country, people, required, received in rows:
            gap = required - received
            records.append(
                {
                    "year": year,
                    "country": country,
                    "people_in_need": people,
                    "funds_required_usd": required,
                    "funds_received_usd": received,
                    "gap_usd": gap,
                    "coverage_ratio": round(received / required, 3),
                }
            )
    return pd.DataFrame(records)


def synthetic_emdat() -> pd.DataFrame:
    records = [
        (2016, "Australia", "Extreme Temp", 0, 0, 3200000000, 350000000),
        (2004, "Indonesia", "Flood/Storm", 227898, 2200000, 9900000000, 1900000000),
        (2019, "Bangladesh", "Cyclone", 12, 500000, 980000000, 210000000),
        (2018, "Vietnam", "Flood", 54, 2100000, 640000000, 100000000),
        (2021, "United States", "Marine Heatwave", 0, 180000, 1400000000, 400000000),
    ]
    return pd.DataFrame(
        records,
        columns=[
            "year",
            "country",
            "disaster_type",
            "deaths",
            "total_affected",
            "economic_loss_usd_2024",
            "insured_loss_usd_2024",
        ],
    )


def synthetic_world_bank() -> pd.DataFrame:
    records = [
        ("Philippines", 2013, "Typhoon Haiyan", 0.8, 1200000000, 6700000000, 3100000000),
        ("Bangladesh", 2017, "Coastal Flooding", 0.4, 440000000, 890000000, 430000000),
        ("Vietnam", 2020, "Delta Salinity Shock", 0.3, 210000000, 340000000, 180000000),
        ("Australia", 2016, "GBR Bleaching", 0.2, 125000000, 210000000, 75000000),
    ]
    return pd.DataFrame(
        records,
        columns=[
            "country",
            "year",
            "event",
            "gdp_impact_pct",
            "ag_loss_usd",
            "infra_loss_usd",
            "recovery_expenditure_usd",
        ],
    )


def synthetic_reliefweb_reports() -> pd.DataFrame:
    rows = [
        (3847291, "Bangladesh: Coastal Flooding Situation Report #4", "2024-01-12", "Bangladesh", "Flood", "OCHA"),
        (3847292, "Philippines: Coral Triangle Marine Heatwave Update", "2024-02-07", "Philippines", "Marine Ecosystem", "UNEP"),
        (3847293, "Vietnam: Mekong Delta Salinity Situation Report", "2024-03-09", "Vietnam", "Flood", "FAO"),
    ]
    records = []
    for report_id, title, date, country, disaster_type, source_org in rows:
        region_id = COUNTRY_TO_REGION.get(country)
        records.append(
            {
                "id": report_id,
                "title": title,
                "date": date,
                "country": country,
                "disaster_type": disaster_type,
                "source_org": source_org,
                "body_summary": f"{title} summary",
                "url": f"https://reliefweb.int/report/{report_id}",
                "crisis_active_flag": bool(region_id),
                "region_id": region_id,
            }
        )
    return pd.DataFrame(records)


def synthetic_gdelt() -> pd.DataFrame:
    months = pd.date_range("2023-01-01", "2024-12-01", freq="MS")
    region_base = {
        "great_barrier_reef": 8.1,
        "gulf_of_mexico": 7.2,
        "california_current": 4.4,
        "coral_triangle": 5.3,
        "bengal_bay": 3.9,
        "mekong_delta": 2.8,
        "arabian_sea": 1.9,
        "baltic_sea": 2.6,
    }
    records = []
    for region_id, base_score in region_base.items():
        for month in months:
            article_count = int(base_score * 18 + (month.month % 4) * 7)
            records.append(
                {
                    "region_id": region_id,
                    "year_month": month.strftime("%Y-%m"),
                    "article_count": article_count,
                    "avg_tone": round(-0.5 + (base_score / 10), 3),
                    "attention_score": round(base_score, 3),
                    "top_keywords": "climate;marine;bleaching" if "reef" in region_id or region_id == "coral_triangle" else "flood;fisheries;coastal",
                }
            )
    return pd.DataFrame(records)


def synthetic_scientific_events() -> pd.DataFrame:
    records = [
        ("2016-02-01", "NOAA", "Great Barrier Reef bleaching alert reaches Level 2", "bleaching", "great_barrier_reef"),
        ("2023-08-14", "NASA", "Marine heatwave intensifies in Coral Triangle", "marine heatwave", "coral_triangle"),
        ("2024-07-01", "NOAA", "Dead zone forecast elevated in Gulf of Mexico", "dead zone", "gulf_of_mexico"),
        ("2024-03-10", "NASA", "Hypoxia signal expanding in Arabian Sea", "hypoxia", "arabian_sea"),
    ]
    return pd.DataFrame(records, columns=["date", "agency", "title", "event_type", "region_id"]).assign(
        url=lambda df: df["agency"].str.lower().map(
            {"nasa": "https://www.nasa.gov/rss/dyn/ocean_stories.rss", "noaa": "https://www.noaa.gov/media-releases.rss"}
        )
    )


def synthetic_charity_registry() -> pd.DataFrame:
    records = [
        ("52-1693387", "WWF - World Wide Fund for Nature", 89.4, 91.2, 87.6, 0.824, "coral_triangle,great_barrier_reef"),
        ("53-0242652", "The Nature Conservancy", 92.1, 93.5, 90.8, 0.842, "california_current"),
        ("26-1737731", "Coral Restoration Foundation", 88.2, 86.1, 88.5, 0.801, "great_barrier_reef"),
        ("23-7245152", "Ocean Conservancy", 85.6, 84.0, 86.0, 0.775, "gulf_of_mexico"),
        ("81-3519176", "Global Fishing Watch", 84.4, 82.0, 88.2, 0.761, "arabian_sea"),
    ]
    df = pd.DataFrame(
        records,
        columns=[
            "ein",
            "name",
            "overall_score",
            "financial_score",
            "accountability_score",
            "program_expense_ratio",
            "active_regions",
        ],
    )
    df["eligible_for_disbursement"] = (df["overall_score"] >= 75) & (df["accountability_score"] >= 80)
    return df


def synthetic_charity_presence() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("WorldFish", "Bangladesh", "bengal_bay", "Food Security", "Active", "2024-01-15"),
            ("WorldFish", "Vietnam", "mekong_delta", "Food Security", "Active", "2024-01-15"),
            ("Coral Triangle Initiative", "Philippines", "coral_triangle", "Marine Ecosystem", "Active", "2024-01-15"),
            ("CARE International", "Vietnam", "mekong_delta", "Displacement", "Active", "2024-01-15"),
        ],
        columns=["organization", "country", "region_id", "sector", "status", "last_verified"],
    )


def synthetic_givewell() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("WWF", 21.5, "reef hectare protected", "medium", 2024),
            ("WorldFish Center", 4.2, "fishing family-month supported", "medium", 2024),
            ("Ocean Conservancy", 0.48, "kg biomass preserved", "low", 2024),
        ],
        columns=["organization", "cost_per_outcome", "outcome_type", "evidence_quality", "year"],
    )


SYNTHETIC_FACTORIES: dict[str, Callable[[], pd.DataFrame]] = {
    "keeling_curve": synthetic_keeling_curve,
    "calcofi_observations": synthetic_calcofi,
    "scripps_pier": synthetic_scripps_pier,
    "sst_observations": synthetic_sst,
    "coral_bleaching_alerts": synthetic_coral_bleaching,
    "ocean_color": synthetic_ocean_color,
    "humanitarian_funding": synthetic_humanitarian_funding,
    "hdx_funding_needs": synthetic_hdx,
    "historical_disasters": synthetic_emdat,
    "world_bank_disaster_costs": synthetic_world_bank,
    "reliefweb_reports": synthetic_reliefweb_reports,
    "gdelt_attention": synthetic_gdelt,
    "scientific_events": synthetic_scientific_events,
    "charity_registry": synthetic_charity_registry,
    "charity_regional_presence": synthetic_charity_presence,
    "givewell_impact": synthetic_givewell,
}


def synthetic_frame(table: str) -> pd.DataFrame:
    factory = SYNTHETIC_FACTORIES.get(table)
    if not factory:
        raise KeyError(f"No synthetic factory for table {table}")
    return factory()


def load_or_synthetic(cache_name: str, table: str, logger: logging.Logger) -> tuple[pd.DataFrame, str]:
    cached = load_cache(cache_name)
    if cached is not None:
        logger.warning("Using cached CSV fallback for %s", table)
        return cached, "cache"
    logger.warning("Using synthetic fallback for %s", table)
    return synthetic_frame(table), "synthetic"


def assign_region_from_lat_lon(lat: float | int | None, lon: float | int | None) -> str | None:
    if lat is None or lon is None or pd.isna(lat) or pd.isna(lon):
        return None
    for region_id, region in REGIONS.items():
        if region["lat"][0] <= float(lat) <= region["lat"][1] and region["lon"][0] <= float(lon) <= region["lon"][1]:
            return region_id
    return None


def normalize_series(series: pd.Series) -> pd.Series:
    s_min = series.min()
    s_max = series.max()
    if pd.isna(s_min) or pd.isna(s_max) or s_min == s_max:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - s_min) / (s_max - s_min)


@dataclass
class RunResult:
    table: str
    rows: int
    source: str
    status: str
