"""
reliefweb_service.py — ReliefWeb API v2 integration.

Fetches disaster reports and situation updates relevant to THRESHOLD ocean/coastal regions.
Falls back to Snowflake cached data (news_reports table) when the API is unavailable.
Docs: https://apidoc.reliefweb.int/
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

RELIEFWEB_API_BASE = "https://api.reliefweb.int/v2"

# Map our region IDs to ReliefWeb-relevant country ISO codes and disaster keywords
REGION_FILTER_MAP: dict[str, dict[str, Any]] = {
    "great_barrier_reef": {
        "countries": ["AUS"],
        "keywords": ["Great Barrier Reef", "coral bleaching", "marine heatwave", "ocean acidification"],
        "disaster_types": ["Flash Flood", "Drought", "Tropical Cyclone"],
    },
    "gulf_of_mexico": {
        "countries": ["USA", "MEX"],
        "keywords": ["Gulf of Mexico", "dead zone", "hypoxia", "oil spill", "hurricane"],
        "disaster_types": ["Tropical Cyclone", "Flash Flood", "Storm Surge"],
    },
    "california_current": {
        "countries": ["USA"],
        "keywords": ["California Current", "Pacific marine heatwave", "upwelling", "sardine"],
        "disaster_types": ["Drought", "Flash Flood", "Cold Wave"],
    },
    "coral_triangle": {
        "countries": ["IDN", "PHL", "PNG", "SLB", "TLS", "MYS"],
        "keywords": ["Coral Triangle", "reef bleaching", "ocean acidification", "fisheries collapse"],
        "disaster_types": ["Tropical Cyclone", "Flash Flood", "Tsunami"],
    },
    "bengal_bay": {
        "countries": ["BGD", "IND", "MMR"],
        "keywords": ["Bay of Bengal", "storm surge", "cyclone", "coastal flooding", "mangrove"],
        "disaster_types": ["Tropical Cyclone", "Flash Flood", "Storm Surge"],
    },
    "mekong_delta": {
        "countries": ["VNM", "KHM", "LAO", "THA"],
        "keywords": ["Mekong Delta", "salinity intrusion", "river flooding", "low oxygen", "fisheries"],
        "disaster_types": ["Flash Flood", "Drought", "Storm Surge"],
    },
    "arabian_sea": {
        "countries": ["IND", "PAK", "OMN", "YEM"],
        "keywords": ["Arabian Sea", "dead zone", "hypoxia", "cyclone", "monsoon flooding"],
        "disaster_types": ["Tropical Cyclone", "Flash Flood", "Drought"],
    },
    "baltic_sea": {
        "countries": ["SWE", "FIN", "EST", "LVA", "LTU", "POL", "DEU", "DNK"],
        "keywords": ["Baltic Sea", "eutrophication", "algal bloom", "dead zone", "hypoxia"],
        "disaster_types": ["Flash Flood", "Cold Wave", "Storm Surge"],
    },
}

# ReliefWeb urgency → our urgency score mapping
DISASTER_URGENCY: dict[str, float] = {
    "Tropical Cyclone": 9.5,
    "Storm Surge": 9.0,
    "Flash Flood": 8.5,
    "Tsunami": 9.8,
    "Drought": 7.5,
    "Cold Wave": 6.5,
    "Heat Wave": 8.0,
    "Marine Ecosystem": 8.0,
}


class ReliefWebService:
    def __init__(self, appname: str = "threshold-datahacks"):
        self.appname = appname
        self.base_url = RELIEFWEB_API_BASE

    def fetch_reports(
        self,
        region_id: str,
        days_back: int = 90,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Fetch situation reports from ReliefWeb for a given region."""
        region_cfg = REGION_FILTER_MAP.get(region_id)
        if not region_cfg:
            return []

        cutoff = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00+00:00")

        payload: dict[str, Any] = {
            "limit": limit,
            "sort": [{"date.created": "desc"}],
            "fields": {
                "include": [
                    "title",
                    "date",
                    "country",
                    "disaster_type",
                    "source",
                    "body",
                    "url",
                    "status",
                    "file",
                ]
            },
            "filter": {
                "operator": "AND",
                "conditions": [
                    {
                        "operator": "OR",
                        "conditions": [
                            {"field": "country.iso3", "value": region_cfg["countries"]},
                        ],
                    },
                    {"field": "date.created", "value": {"from": cutoff}, "operator": ">="},
                ],
            },
        }

        try:
            response = httpx.post(
                f"{self.base_url}/reports",
                params={"appname": self.appname},
                json=payload,
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
            return self._normalize_reports(data.get("data", []), region_id)
        except Exception as exc:
            logger.warning("ReliefWeb API fetch failed for %s: %s", region_id, exc)
            return []

    def fetch_disasters(
        self,
        region_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Fetch active disaster entries relevant to a region."""
        region_cfg = REGION_FILTER_MAP.get(region_id)
        if not region_cfg:
            return []

        payload: dict[str, Any] = {
            "limit": limit,
            "sort": [{"date.created": "desc"}],
            "fields": {
                "include": ["name", "date", "country", "type", "glide", "status", "url"]
            },
            "filter": {
                "operator": "AND",
                "conditions": [
                    {"field": "country.iso3", "value": region_cfg["countries"]},
                    {"field": "status", "value": ["alert", "ongoing"]},
                ],
            },
        }

        try:
            response = httpx.post(
                f"{self.base_url}/disasters",
                params={"appname": self.appname},
                json=payload,
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as exc:
            logger.warning("ReliefWeb disaster fetch failed for %s: %s", region_id, exc)
            return []

    def _normalize_reports(
        self, raw_items: list[dict], region_id: str
    ) -> list[dict[str, Any]]:
        """Convert ReliefWeb API response items to our news_reports schema."""
        results = []
        for item in raw_items:
            fields = item.get("fields", {})
            disaster_types = fields.get("disaster_type", [])
            dtype = disaster_types[0].get("name") if disaster_types else "Marine Ecosystem"
            sources = fields.get("source", [])
            source_org = sources[0].get("name", "ReliefWeb") if sources else "ReliefWeb"
            body = fields.get("body", "") or ""
            results.append(
                {
                    "id": f"rw-{item['id']}",
                    "region_id": region_id,
                    "title": fields.get("title", ""),
                    "source_type": "reliefweb",
                    "source_org": source_org,
                    "date": (fields.get("date") or {}).get("created", "")[:10],
                    "body_summary": body[:500].strip(),
                    "url": fields.get("url", f"https://reliefweb.int/report/{item['id']}"),
                    "urgency_score": DISASTER_URGENCY.get(dtype, 6.0),
                    "disaster_type": dtype,
                }
            )
        return results

    def sync_to_snowflake(self, db: Session, region_id: str, days_back: int = 90) -> int:
        """Fetch live reports and upsert into the news_reports table. Returns row count inserted."""
        reports = self.fetch_reports(region_id, days_back=days_back)
        if not reports:
            return 0

        dialect = db.bind.dialect.name if db.bind else "unknown"
        inserted = 0
        for report in reports:
            if dialect == "snowflake":
                db.execute(
                    text(
                        """
                        MERGE INTO news_reports USING (
                            SELECT :id AS id
                        ) src ON news_reports.id = src.id
                        WHEN NOT MATCHED THEN INSERT (
                            id, region_id, title, source_type, source_org, date,
                            body_summary, url, urgency_score, disaster_type
                        ) VALUES (
                            :id, :region_id, :title, :source_type, :source_org, :date,
                            :body_summary, :url, :urgency_score, :disaster_type
                        )
                        """
                    ),
                    report,
                )
            else:
                db.execute(
                    text(
                        """
                        INSERT OR IGNORE INTO news_reports
                            (id, region_id, title, source_type, source_org, date,
                             body_summary, url, urgency_score, disaster_type)
                        VALUES
                            (:id, :region_id, :title, :source_type, :source_org, :date,
                             :body_summary, :url, :urgency_score, :disaster_type)
                        """
                    ),
                    report,
                )
            inserted += 1
        db.commit()
        return inserted


reliefweb_service = ReliefWebService()
