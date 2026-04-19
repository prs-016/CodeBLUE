from __future__ import annotations

import logging
import os
import sys
from datetime import date, timedelta
from typing import Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ML model imports — resolved via sys.path
# ---------------------------------------------------------------------------
_ML_AVAILABLE = False
_TippingPointClassifier = None
_DaysToThresholdForecaster = None
_CounterfactualCostEstimator = None

try:
    _backend_dir = os.path.dirname(os.path.abspath(__file__))
    _project_root = os.path.abspath(os.path.join(_backend_dir, "..", ".."))
    _ml_models_dir = os.path.join(_project_root, "ml", "models")

    for _path in (_project_root, _ml_models_dir):
        if _path not in sys.path:
            sys.path.insert(0, _path)

    from tipping_point_classifier import TippingPointClassifier as _TippingPointClassifier
    from days_to_threshold_forecaster import DaysToThresholdForecaster as _DaysToThresholdForecaster

    _ML_AVAILABLE = True
    logger.info("ML models imported successfully from %s", _ml_models_dir)
except Exception as exc:
    logger.warning("ML models could not be imported — falling back to simple math. Reason: %s", exc)


class DemoModelRegistry:
    def __init__(self) -> None:
        self.loaded = False
        self._classifier = None
        self._forecaster = None

    def load(self) -> None:
        if _ML_AVAILABLE:
            try:
                import pathlib
                _model_dir = pathlib.Path(os.path.abspath(__file__)).parents[2] / "ml" / "models"
                _saved = _model_dir / "tipping_point_classifier.json"

                self._classifier = _TippingPointClassifier()
                if _saved.exists():
                    self._classifier.load(_saved)
                    logger.info("TippingPointClassifier loaded from %s", _saved)
                else:
                    self._classifier._prime_defaults()
                    logger.info("TippingPointClassifier using heuristic defaults")

                self._forecaster = _DaysToThresholdForecaster()
                logger.info("ML model instances ready.")
            except Exception as exc:
                logger.warning("Failed to instantiate ML models: %s", exc)
                self._classifier = None
                self._forecaster = None
        self.loaded = True

    # ------------------------------------------------------------------
    # region_trajectory
    # ------------------------------------------------------------------

    REGION_COORDS = {
        "great_barrier_reef": (-18.2, 147.7),
        "gulf_of_mexico": (25.3, -90.4),
        "california_current": (34.0, -120.0),
        "coral_triangle": (-2.4, 122.2),
        "bengal_bay": (14.5, 88.3),
        "mekong_delta": (10.0, 105.8),
        "arabian_sea": (15.5, 65.2),
        "baltic_sea": (58.6, 19.3),
    }

    def region_trajectory(self, db: Session, region_id: str) -> dict:
        region_row = db.execute(
            text(
                """
                SELECT id, current_score, days_to_threshold, primary_driver
                FROM regions
                WHERE id = :region_id
                """
            ),
            {"region_id": region_id},
        ).fetchone()
        if region_row is None:
            raise LookupError(region_id)

        region_map = region_row._mapping

        if self._forecaster is not None:
            try:
                import pandas as pd
                lat, lon = self.REGION_COORDS.get(region_id, (34.0, -120.0))

                rows = db.execute(
                    text(
                        """
                        SELECT DATE, T_DEGC, O2ML_L, SALNTY, CHLORA, NO3UM, BAROMETER
                        FROM CALCOFI.PUBLIC.CALCOFI_TSUNAMI_FEATURES
                        WHERE (LAT_DEC - :lat)*(LAT_DEC - :lat) + (LON_DEC - :lon)*(LON_DEC - :lon) < 0.25
                          AND DATE >= DATEADD(day, -180, CURRENT_DATE())
                        ORDER BY DATE ASC
                        """
                    ),
                    {"lat": lat, "lon": lon, "region_id": region_id},
                ).fetchall()

                if len(rows) >= 14:
                    history_list = []
                    for r in rows:
                        f = {
                            "t_degc": float(r[1] or 15.0),
                            "o2ml_l": float(r[2] or 5.0),
                            "salnty": float(r[3] or 33.5),
                            "chlora": float(r[4] or 0.5),
                            "no3um": float(r[5] or 1.0),
                            "barometer": float(r[6] or 1013.0),
                        }
                        score_obj = self._classifier.predict(f)
                        history_list.append({
                            "date": r[0], 
                            "threshold_proximity_score": score_obj["threshold_proximity_score"]
                        })
                    
                    history_df = pd.DataFrame(history_list)
                    result = self._forecaster.predict(history_df)

                    days_to_threshold = int(result["days_to_threshold"])
                    crossing_date = result["crossing_date"]
                    ci_low = int(result["confidence_interval_low"])
                    ci_high = int(result["confidence_interval_high"])

                    trajectory: List[Dict] = []
                    for point in result.get("trajectory_data", []):
                        score = float(point["predicted_score"])
                        trajectory.append({
                            "date": point["date"],
                            "predicted_score": score,
                            "confidence_low": round(max(0.0, score - 0.5), 2),
                            "confidence_high": round(min(10.0, score + 0.5), 2),
                        })

                    return {
                        "region_id": region_id,
                        "days_to_threshold": days_to_threshold,
                        "crossing_date": crossing_date,
                        "confidence_interval_low": ci_low,
                        "confidence_interval_high": ci_high,
                        "primary_driver": region_map["primary_driver"],
                        "trajectory": trajectory,
                    }
            except Exception as exc:
                logger.warning("DaysToThresholdForecaster failed: %s", exc)

        return self._simple_trajectory(region_id, region_map)

    def _simple_trajectory(self, region_id: str, mapping) -> dict:
        today = date.today()
        base_score = float(mapping["current_score"])
        days_to_threshold = int(mapping["days_to_threshold"])
        trajectory = []
        for step in range(0, 12):
            projected_date = today + timedelta(days=step * 30)
            projected_score = min(10.0, base_score + (step * (8.0 - base_score) / max(1, days_to_threshold / 30)))
            trajectory.append({
                "date": projected_date.isoformat(),
                "predicted_score": round(projected_score, 2),
                "confidence_low": round(max(0.0, projected_score - 0.5), 2),
                "confidence_high": round(min(10.0, projected_score + 0.5), 2),
            })
        return {
            "region_id": region_id,
            "days_to_threshold": days_to_threshold,
            "crossing_date": (today + timedelta(days=days_to_threshold)).isoformat(),
            "confidence_interval_low": max(1, days_to_threshold - 21),
            "confidence_interval_high": days_to_threshold + 34,
            "primary_driver": mapping["primary_driver"],
            "trajectory": trajectory,
        }

    # ------------------------------------------------------------------
    # counterfactual_estimate
    # ------------------------------------------------------------------

    def counterfactual_estimate(self, db: Session, region_id: str) -> dict:
        row = db.execute(
            text("SELECT name, current_score, primary_threat FROM regions WHERE id = :region_id"),
            {"region_id": region_id},
        ).fetchone()
        if row is None:
            raise LookupError(region_id)

        mapping = row._mapping
        region_name = mapping["name"]
        current_score = float(mapping["current_score"])

        return self._simple_counterfactual(region_id, region_name, current_score, mapping["primary_threat"])

    def _simple_counterfactual(self, region_id: str, region_name: str, score: float, primary_threat: str) -> dict:
        prevention_cost = round(4_000_000 + score * 2_500_000, 2)
        recovery_cost = round(prevention_cost * (4 + score / 2), 2)
        return {
            "region_id": region_id,
            "region_name": region_name,
            "prevention_cost_usd": prevention_cost,
            "recovery_cost_usd": recovery_cost,
            "cost_multiplier": round(recovery_cost / prevention_cost, 2),
            "optimal_intervention_type": f"{primary_threat} resilience package",
            "prevention_breakdown": {
                "monitoring": round(prevention_cost * 0.18, 2),
                "local_response": round(prevention_cost * 0.47, 2),
                "ecosystem_restoration": round(prevention_cost * 0.35, 2),
            },
            "recovery_breakdown": {
                "ag_loss": round(recovery_cost * 0.18, 2),
                "infra_loss": round(recovery_cost * 0.31, 2),
                "fishery_loss": round(recovery_cost * 0.24, 2),
                "tourism_loss": round(recovery_cost * 0.27, 2),
            },
        }

    # ------------------------------------------------------------------
    # score_region
    # ------------------------------------------------------------------

    def score_region(self, region_id: str, db: Session) -> dict:
        lat, lon = self.REGION_COORDS.get(region_id, (34.0, -120.0))

        query = text("""
            WITH NearestStation AS (
                SELECT 
                    T_DEGC, O2ML_L, SALNTY, CHLORA, NO3UM, PO4UM, SIO3UM, 
                    WIND_SPD, BAROMETER, DATE
                FROM CALCOFI.PUBLIC.CALCOFI_TSUNAMI_FEATURES
                ORDER BY (LAT_DEC - :lat)*(LAT_DEC - :lat) + (LON_DEC - :lon)*(LON_DEC - :lon) ASC, DATE DESC
                LIMIT 1
            ),
            Narrative AS (
                SELECT 
                    AVG(GOLDSTEIN) as GOLDSTEIN, 
                    SUM(NUMARTS) as NUMARTS
                FROM CALCOFI.PUBLIC.GDELT
                WHERE DATE = (SELECT DATE FROM NearestStation)
            )
            SELECT f.*, COALESCE(n.GOLDSTEIN, 0) as GOLDSTEIN, COALESCE(n.NUMARTS, 0) as NUMARTS
            FROM NearestStation f, Narrative n
        """)

        row = db.execute(query, {"lat": lat, "lon": lon}).fetchone()
        if row is None:
            raise LookupError(region_id)

        r = row._mapping
        features: Dict[str, float] = {
            "t_degc": float(r.get("T_DEGC", 15.0)),
            "o2ml_l": float(r.get("O2ML_L", 5.0)),
            "salnty": float(r.get("SALNTY", 33.5)),
            "chlora": float(r.get("CHLORA", 0.5)),
            "no3um": float(r.get("NO3UM", 1.0)),
            "po4um": float(r.get("PO4UM", 0.1)),
            "sio3um": float(r.get("SIO3UM", 2.0)),
            "wind_spd": float(r.get("WIND_SPD", 10.0)),
            "barometer": float(r.get("BAROMETER", 1013.0)),
            "goldstein": float(r.get("GOLDSTEIN", 0.0)),
            "numarts": float(r.get("NUMARTS", 0.0)),
        }

        if self._classifier is not None:
            try:
                result = self._classifier.predict(features)
                result["region_id"] = region_id
                result["timestamp"] = r.get("DATE", date.today()).isoformat()
                result["breakdown"] = [
                    {"key": "thermal", "label": "Water Temperature", "value": features["t_degc"], "detail": f"{features['t_degc']:.1f}°C"},
                    {"key": "oxygen", "label": "Dissolved Oxygen", "value": features["o2ml_l"], "detail": f"{features['o2ml_l']:.2f} ml/L"},
                    {"key": "productivity", "label": "Chlorophyll", "value": features["chlora"], "detail": f"{features['chlora']:.2f} mg/m³"},
                    {"key": "stability", "label": "Political Stability", "value": features["goldstein"], "detail": f"Goldstein Score: {features['goldstein']:.1f}"},
                ]
                return result
            except Exception as exc:
                logger.warning("Classifier failed: %s", exc)

        return {
            "region_id": region_id,
            "threshold_proximity_score": 5.0,
            "feature_importances": {},
            "confidence": 0.5,
            "primary_driver": "fallback (prediction engine offline)",
        }


model_registry = DemoModelRegistry()
