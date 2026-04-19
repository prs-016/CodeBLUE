from __future__ import annotations

import httpx

async def get_weather(lat: float, lon: float) -> dict:
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_gusts_10m&hourly=precipitation,soil_moisture_0_to_1cm&past_days=2"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return {
                "rainfall_mm_last_48h": 0.0,
                "soil_moisture_pct": 0.0,
                "wind_speed_gust_ms": 0.0,
                "temperature_c": 0.0,
            }

    current = data.get("current", {})
    hourly = data.get("hourly", {})
    
    # Rainfall over last 48h
    precip_array = hourly.get("precipitation", [])
    # past_days=2 gives 48 hours of historical data before zero hour
    rainfall_mm = sum(precip_array[:48]) if precip_array else 0.0
    
    # Soil moisture (latest/current)
    soil_moisture_array = hourly.get("soil_moisture_0_to_1cm", [])
    soil_pct = soil_moisture_array[48] if len(soil_moisture_array) > 48 else (soil_moisture_array[-1] if soil_moisture_array else 0.0)
    
    wind_kmh = current.get("wind_gusts_10m", 0.0)
    wind_ms = wind_kmh * (1000 / 3600)  # km/h to m/s
    
    temp_c = current.get("temperature_2m", 0.0)

    return {
        "rainfall_mm_last_48h": round(rainfall_mm, 2),
        "soil_moisture_pct": round(max(0.0, min(1.0, soil_pct)), 3),
        "wind_speed_gust_ms": round(wind_ms, 2),
        "temperature_c": round(temp_c, 1),
    }
