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
# ML model imports — resolved via sys.path so the backend does not need to be
# installed as a package and the ml/ directory at the project root is found
# regardless of the working directory the server is launched from.
# ---------------------------------------------------------------------------
_ML_AVAILABLE = False
_TippingPointClassifier = None
_DaysToThresholdForecaster = None
_CounterfactualCostEstimator = None

try:
    # The backend runs from <project_root>/backend/.
    # The ml/ package lives at <project_root>/ml/.
    _backend_dir = os.path.dirname(os.path.abspath(__file__))               # …/backend/services
    _project_root = os.path.abspath(os.path.join(_backend_dir, "..", "..")) # …/threshold
    _ml_models_dir = os.path.join(_project_root, "ml", "models")

    for _path in (_project_root, _ml_models_dir):
        if _path not in sys.path:
            sys.path.insert(0, _path)

    from tipping_point_classifier import TippingPointClassifier as _TippingPointClassifier
    from days_to_threshold_forecaster import DaysToThresholdForecaster as _DaysToThresholdForecaster
    from counterfactual_cost_estimator import CounterfactualCostEstimator as _CounterfactualCostEstimator

    _ML_AVAILABLE = True
    logger.info("ML models imported successfully from %s", _ml_models_dir)
except Exception as exc:
    logger.warning("ML models could not be imported — falling back to simple math. Reason: %s", exc)


class DemoModelRegistry:
    def __init__(self) -> None:
        self.loaded = False
        self._classifier = None
        self._forecaster = None
        self._estimator = None

    def load(self) -> None:
        if _ML_AVAILABLE:
            try:
                import pathlib
                # Look for saved model weights next to the model source files
                _model_dir = pathlib.Path(os.path.abspath(__file__)).parents[2] / "ml" / "models"
                _saved = _model_dir / "tipping_point_classifier.json"

                self._classifier = _TippingPointClassifier()
                if _saved.exists():
                    self._classifier.load(_saved)
                    logger.info("TippingPointClassifier loaded from %s", _saved)
                else:
                    self._classifier._prime_defaults()
                    logger.info("TippingPointClassifier using heuristic defaults (no saved weights)")

                self._forecaster = _DaysToThresholdForecaster()
                self._estimator = _CounterfactualCostEstimator()
                logger.info("ML model instances ready.")
            except Exception as exc:
                logger.warning("Failed to instantiate ML models: %s", exc)
                self._classifier = None
                self._forecaster = None
                self._estimator = None
        self.loaded = True

    # ------------------------------------------------------------------
    # region_trajectory
    # ------------------------------------------------------------------

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

        # Attempt ML path -----------------------------------------------
        if self._forecaster is not None:
            try:
                import pandas as pd

                rows = db.execute(
                    text(
                        """
                        SELECT date, threshold_proximity_score
                        FROM region_features
                        WHERE region_id = :region_id
                          AND date >= date('now', '-180 days')
                        ORDER BY date ASC
                        """
                    ),
                    {"region_id": region_id},
                ).fetchall()

                if len(rows) >= 14:
                    history_df = pd.DataFrame(
                        [{"date": r[0], "threshold_proximity_score": float(r[1])} for r in rows]
                    )
                    result = self._forecaster.predict(history_df)

                    days_to_threshold = int(result["days_to_threshold"])
                    crossing_date = result["crossing_date"]
                    ci_low = int(result["confidence_interval_low"])
                    ci_high = int(result["confidence_interval_high"])

                    trajectory: List[Dict] = []
                    for point in result.get("trajectory_data", []):
                        score = float(point["predicted_score"])
                        trajectory.append(
                            {
                                "date": point["date"],
                                "predicted_score": score,
                                "confidence_low": round(max(0.0, score - 0.5), 2),
                                "confidence_high": round(min(10.0, score + 0.5), 2),
                            }
                        )

                    return {
                        "region_id": region_id,
                        "days_to_threshold": days_to_threshold,
                        "crossing_date": crossing_date,
                        "confidence_interval_low": ci_low,
                        "confidence_interval_high": ci_high,
                        "primary_driver": region_map["primary_driver"],
                        "trajectory": trajectory,
                    }
                else:
                    logger.debug(
                        "Insufficient feature rows for %s (%d rows) — using simple-math fallback.",
                        region_id,
                        len(rows),
                    )
            except Exception as exc:
                logger.warning("DaysToThresholdForecaster failed for %s: %s", region_id, exc)

        # Simple-math fallback ------------------------------------------
        return self._simple_trajectory(region_id, region_map)

    def _simple_trajectory(self, region_id: str, mapping) -> dict:
        today = date.today()
        base_score = float(mapping["current_score"])
        days_to_threshold = int(mapping["days_to_threshold"])
        trajectory = []
        for step in range(0, 12):
            projected_date = today + timedelta(days=step * 30)
            projected_score = min(
                10.0, base_score + (step * (8.0 - base_score) / max(1, days_to_threshold / 30))
            )
            trajectory.append(
                {
                    "date": projected_date.isoformat(),
                    "predicted_score": round(projected_score, 2),
                    "confidence_low": round(max(0.0, projected_score - 0.5), 2),
                    "confidence_high": round(min(10.0, projected_score + 0.5), 2),
                }
            )

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
            text(
                """
                SELECT name, current_score, primary_threat
                FROM regions
                WHERE id = :region_id
                """
            ),
            {"region_id": region_id},
        ).fetchone()
        if row is None:
            raise LookupError(region_id)

        mapping = row._mapping
        region_name = mapping["name"]
        current_score = float(mapping["current_score"])

        # Attempt ML path -----------------------------------------------
        if self._estimator is not None:
            try:
                result = self._estimator.estimate(region_id, severity_score=current_score)
                return {
                    "region_id": region_id,
                    "region_name": region_name,
                    "prevention_cost_usd": result["prevention_cost_usd"],
                    "recovery_cost_usd": result["recovery_cost_usd"],
                    "cost_multiplier": result["cost_multiplier"],
                    "optimal_intervention_type": result["optimal_intervention_type"],
                    "prevention_breakdown": result["prevention_breakdown"],
                    "recovery_breakdown": result["recovery_breakdown"],
                }
            except Exception as exc:
                logger.warning("CounterfactualCostEstimator failed for %s: %s", region_id, exc)

        # Simple-math fallback ------------------------------------------
        return self._simple_counterfactual(region_id, region_name, current_score, mapping["primary_threat"])

    def _simple_counterfactual(
        self, region_id: str, region_name: str, score: float, primary_threat: str
    ) -> dict:
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
    # score_region  (new method)
    # ------------------------------------------------------------------

    def score_region(self, region_id: str, db: Session) -> dict:
        """
        Score a region using the TippingPointClassifier.

        Queries the latest row from region_features and maps the DB columns
        to the classifier's feature space. Falls back to a simple score dict
        if the classifier is unavailable or the query fails.
        """
        row = db.execute(
            text(
                """
                SELECT sst_anomaly, o2_current, chlorophyll_anomaly,
                       nitrate_anomaly, threshold_proximity_score,
                       dhw_current, bleaching_alert_level
                FROM region_features
                WHERE region_id = :region_id
                ORDER BY date DESC
                LIMIT 1
                """
            ),
            {"region_id": region_id},
        ).fetchone()

        if row is None:
            raise LookupError(region_id)

        r = row._mapping
        sst_anomaly = float(r["sst_anomaly"])
        o2_current = float(r["o2_current"])
        chlorophyll_anomaly = float(r["chlorophyll_anomaly"])
        nitrate_anomaly = float(r["nitrate_anomaly"])
        dhw_current = float(r["dhw_current"] or 0.0)
        bleaching_alert_level = float(r["bleaching_alert_level"] or 0.0)
        hypoxia_risk = max(0.0, (5.0 - o2_current) / 3.0)

        features: Dict[str, float] = {
            "sst_anomaly_30d_avg": sst_anomaly,
            "sst_acceleration": 0.0,
            "o2_current": o2_current,
            "o2_trend_90d": 0.0,
            "hypoxia_risk": hypoxia_risk,
            "chlorophyll_anomaly": chlorophyll_anomaly,
            "dhw_current": dhw_current,
            "bleaching_alert_level": bleaching_alert_level,
            "co2_yoy_acceleration": 0.0,
            "nitrate_anomaly": nitrate_anomaly,
            "larvae_count_trend": 0.0,
        }

        if self._classifier is not None:
            try:
                result = self._classifier.predict(features)
                result["region_id"] = region_id
                return result
            except Exception as exc:
                logger.warning("TippingPointClassifier failed for %s: %s", region_id, exc)

        # Fallback — return the stored score from the DB row.
        stored_score = float(r["threshold_proximity_score"])
        return {
            "region_id": region_id,
            "threshold_proximity_score": round(stored_score, 2),
            "feature_importances": {},
            "confidence": 0.7,
            "primary_driver": "stored score (ML unavailable)",
        }


model_registry = DemoModelRegistry()
