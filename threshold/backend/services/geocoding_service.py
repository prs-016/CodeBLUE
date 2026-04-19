from __future__ import annotations

import httpx

from config import settings

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


async def reverse_geocode(lat: float, lon: float) -> dict:
    """Return region_name, country, and admin components for lat/lon."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            GEOCODE_URL,
            params={"latlng": f"{lat},{lon}", "key": settings.google_maps_api_key},
        )
        resp.raise_for_status()
        data = resp.json()

    if data.get("status") != "OK" or not data.get("results"):
        return {"region_name": f"{lat:.2f},{lon:.2f}", "country": "Unknown", "admin_level": "coordinates"}

    result = data["results"][0]
    components = {c["types"][0]: c["long_name"] for c in result.get("address_components", []) if c.get("types")}

    region_name = (
        components.get("administrative_area_level_2")
        or components.get("administrative_area_level_1")
        or components.get("locality")
        or components.get("country")
        or result.get("formatted_address", f"{lat:.2f},{lon:.2f}")
    )
    return {
        "region_name": region_name,
        "country": components.get("country", "Unknown"),
        "admin_level": "county" if "administrative_area_level_2" in components else "region",
    }
