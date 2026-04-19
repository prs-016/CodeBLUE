from __future__ import annotations

import httpx

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"


async def get_headlines(region_name: str, disaster_type: str, max_records: int = 5) -> list[dict]:
    """Fetch recent headlines from GDELT DOC 2.0 API (free, no key)."""
    keyword = region_name
    if disaster_type not in ("none", "unknown"):
        keyword = f"{region_name} {disaster_type}"

    params = {
        "query": keyword,
        "mode": "artlist",
        "maxrecords": str(max_records),
        "format": "json",
        "timespan": "72h",
        "sort": "datedesc",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
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
