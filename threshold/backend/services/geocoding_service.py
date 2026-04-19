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

    # Aggregate components from all results (least specific to most specific)
    # This prevents 'Unknown' when the primary result is just a Plus Code in a remote area
    components = {}
    for res in reversed(data["results"]):
        for c in res.get("address_components", []):
            if c.get("types"):
                components[c["types"][0]] = c["long_name"]

    # We still want the most specific formatted address as a fallback
    result = data["results"][0]

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
