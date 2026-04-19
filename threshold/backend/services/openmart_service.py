from __future__ import annotations

from services.ortho_client import ortho_post


async def search_nonprofits(region_name: str, disaster_type: str) -> list[dict]:
    """Search Openmart for nonprofit orgs relevant to disaster type + region."""
    query_map = {
        "flood": f"flood relief nonprofit {region_name}",
        "wildfire": f"wildfire relief nonprofit {region_name}",
        "drought": f"drought humanitarian nonprofit {region_name}",
        "storm": f"storm disaster relief nonprofit {region_name}",
        "none": f"disaster relief nonprofit {region_name}",
    }
    query = query_map.get(disaster_type, f"disaster relief nonprofit {region_name}")

    try:
        result = await ortho_post(
            "openmart",
            "/api/v1/search",
            body={"query": query, "page_size": 8},
        )
    except Exception:
        return []

    businesses = result.get("businesses") or result.get("results") or result.get("data") or []
    return _normalize(businesses)


def _normalize(businesses: list) -> list[dict]:
    out = []
    for b in businesses:
        if not isinstance(b, dict):
            continue
        name = b.get("name") or b.get("business_name") or ""
        if not name:
            continue
        out.append({
            "name": name,
            "url": b.get("website") or b.get("url") or None,
            "focus": b.get("category") or b.get("tags", [None])[0] or "disaster relief",
            "source": "openmart",
        })
    return out
