from __future__ import annotations

PIN_COLORS = {
    "low": "#27AE60",
    "medium": "#F1C40F",
    "high": "#E67E22",
    "critical": "#C0392B",
}


def infer_disaster(weather: dict) -> dict:
    r = weather.get("rainfall_mm_last_48h", 0.0)
    sm = weather.get("soil_moisture_pct", 0.5)   # 0-1
    w = weather.get("wind_speed_gust_ms", 0.0)    # m/s
    t = weather.get("temperature_c", 20.0)
    w_kmh = w * 3.6

    factors: list[str] = []
    disaster_type = "none"
    risk_level = "low"

    # Flood — heavy rainfall dominates
    if r > 100:
        factors.append(f"extreme rainfall {r:.0f}mm/48h")
        disaster_type, risk_level = "flood", "critical"
    elif r > 50:
        factors.append(f"heavy rainfall {r:.0f}mm/48h")
        disaster_type, risk_level = "flood", "high"
    elif r > 25 and sm > 0.80:
        factors += [f"rain {r:.0f}mm/48h", "saturated soil"]
        disaster_type, risk_level = "flood", "medium"

    # Wildfire — dry + hot + wind (only if no flood)
    elif t > 35 and sm < 0.15 and w_kmh > 50:
        factors += [f"temp {t:.0f}°C", f"soil moisture {sm:.0%}", f"wind {w_kmh:.0f}km/h"]
        disaster_type = "wildfire"
        risk_level = "critical" if w_kmh > 80 else "high"
    elif t > 32 and sm < 0.20:
        factors += [f"temp {t:.0f}°C", "dry conditions"]
        disaster_type, risk_level = "wildfire", "medium"

    # Storm — wind-driven
    elif w_kmh > 90:
        factors.append(f"extreme wind {w_kmh:.0f}km/h")
        disaster_type, risk_level = "storm", "critical"
    elif w_kmh > 60:
        factors.append(f"high wind {w_kmh:.0f}km/h")
        disaster_type, risk_level = "storm", "high"

    # Drought — sustained dry heat
    elif r < 5 and sm < 0.15 and t > 28:
        factors += ["minimal rainfall past 48h", f"soil moisture {sm:.0%}"]
        disaster_type, risk_level = "drought", "medium"

    return {
        "disaster_type": disaster_type,
        "risk_level": risk_level,
        "trigger_factors": factors,
        "pin_color": PIN_COLORS[risk_level],
    }
