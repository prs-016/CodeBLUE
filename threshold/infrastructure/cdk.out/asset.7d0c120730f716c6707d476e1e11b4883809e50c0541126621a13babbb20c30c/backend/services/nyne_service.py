from __future__ import annotations

import asyncio

from services.ortho_client import ortho_post


async def _poll(path: str, request_id: str, max_attempts: int = 8, delay: float = 1.5) -> dict:
    for _ in range(max_attempts):
        await asyncio.sleep(delay)
        result = await ortho_post("nyne", path, query={"request_id": request_id})
        status = result.get("status") or result.get("state") or ""
        if status.lower() not in ("pending", "processing", "queued", ""):
            return result
        if result.get("data") or result.get("results") or result.get("companies"):
            return result
    return {}


async def search_relief_orgs(region_name: str, disaster_type: str) -> list[dict]:
    """Use Nyne company search to find disaster relief orgs near a region."""
    industry_map = {
        "flood": "flood relief nonprofit",
        "wildfire": "wildfire relief nonprofit",
        "drought": "drought relief humanitarian",
        "storm": "storm disaster relief nonprofit",
        "none": "disaster relief nonprofit",
    }
    industry = industry_map.get(disaster_type, "disaster relief nonprofit")

    try:
        start = await ortho_post(
            "nyne",
            "/company/search",
            body={"industry": industry, "location": region_name, "max_results": 8},
        )
        request_id = start.get("request_id") or start.get("requestId")
        if not request_id:
            raw = start.get("data") or start.get("companies") or []
            return _normalize_nyne(raw)

        result = await _poll("/company/search", request_id)
    except Exception:
        return []

    raw = result.get("data") or result.get("companies") or result.get("results") or []
    return _normalize_nyne(raw)


def _normalize_nyne(companies: list) -> list[dict]:
    out = []
    for c in companies:
        if not isinstance(c, dict):
            continue
        name = c.get("name") or c.get("company_name") or ""
        if not name:
            continue
        out.append({
            "name": name,
            "url": c.get("website") or c.get("domain") or c.get("url") or None,
            "focus": c.get("industry") or "disaster relief",
            "source": "nyne",
        })
    return out
