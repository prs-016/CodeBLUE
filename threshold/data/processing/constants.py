from __future__ import annotations

import sys
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import REGIONS  # noqa: E402


STRESS_WEIGHTS = {
    "sst_anomaly_30d_avg": 0.25,
    "hypoxia_risk": 0.20,
    "bleaching_alert_level": 0.20,
    "chlorophyll_anomaly": 0.10,
    "co2_yoy_acceleration": 0.10,
    "larvae_count_trend": 0.08,
    "nitrate_anomaly": 0.07,
}

