from __future__ import annotations

import httpx

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"


async def _query_gdelt(client: httpx.AsyncClient, query: str, timespan: str, max_records: int) -> list[dict]:
    params = {
        "query": query,
        "mode": "artlist",
        "maxrecords": str(max_records),
        "format": "json",
        "timespan": timespan,
        "sort": "datedesc",
    }
    try:
        resp = await client.get(GDELT_DOC_API, params=params)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    articles = data.get("articles") or []
    return [
        {
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "source": a.get("domain", ""),
            "published_at": a.get("seendate", ""),
        }
        for a in articles
        if a.get("title")
    ]


async def get_headlines(region_name: str, disaster_type: str, max_records: int = 5) -> list[dict]:
    """Fetch recent headlines from GDELT DOC 2.0 API (free, no key).
    Falls back to progressively broader queries if the specific one returns nothing.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. Specific query: region + disaster over 7 days
        if disaster_type not in ("none", "unknown", "marine"):
            query = f"{region_name} {disaster_type}"
            results = await _query_gdelt(client, query, "7d", max_records)
            if results:
                return results

        # 2. Region + environment keywords over 14 days
        eco_query = f"{region_name} environment ecology climate"
        results = await _query_gdelt(client, eco_query, "14d", max_records)
        if results:
            return results

        # 3. Just the region name over 30 days
        results = await _query_gdelt(client, region_name, "30d", max_records)
        return results
