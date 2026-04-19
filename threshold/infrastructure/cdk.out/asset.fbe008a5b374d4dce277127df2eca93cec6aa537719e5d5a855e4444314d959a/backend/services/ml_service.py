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
_ThresholdNet = None
_THRESHOLD_NET_AVAILABLE = False

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

try:
    import pathlib as _pl
    _threshold_net_weights = _pl.Path(os.path.abspath(__file__)).parents[2] / "ml" / "saved_models" / "threshold_net_best.pt"
    if _threshold_net_weights.exists():
        import torch as _torch
        from threshold_net import ThresholdNet as _ThresholdNet, REGION_TO_IDX as _REGION_TO_IDX
        _THRESHOLD_NET_AVAILABLE = True
        logger.info("ThresholdNet weights found at %s", _threshold_net_weights)
    else:
        logger.info("ThresholdNet weights not found at %s — upload ml/saved_models/threshold_net_best.pt to enable", _threshold_net_weights)
except Exception as exc:
    logger.warning("ThresholdNet could not be loaded: %s", exc)


class DemoModelRegistry:
    def __init__(self) -> None:
        self.loaded = False
        self._classifier = None
        self._forecaster = None
        self._threshold_net = None
        self._threshold_net_meta: dict = {}   # mean, std, feature_cols from checkpoint

    def load(self) -> None:
        # ── ThresholdNet (BiLSTM + Attention) — preferred if weights exist ──
        if _THRESHOLD_NET_AVAILABLE:
            try:
                import pathlib, torch
                weights_path = pathlib.Path(os.path.abspath(__file__)).parents[2] / "ml" / "saved_models" / "threshold_net_best.pt"
                ckpt = torch.load(weights_path, map_location="cpu", weights_only=False)
                args = ckpt.get("args", {})
                net = _ThresholdNet(
                    hidden_size     = args.get("hidden", 256),
                    num_lstm_layers = args.get("lstm_layers", 2),
                    num_heads       = args.get("heads", 4),
                    mlp_hidden      = args.get("hidden", 256),
                    dropout         = 0.0,   # inference — no dropout
                )
                net.load_state_dict(ckpt["model_state"])
                net.eval()
                self._threshold_net = net
                self._threshold_net_meta = {
                    "mean":         ckpt.get("mean", []),
                    "std":          ckpt.get("std", []),
                    "feature_cols": ckpt.get("feature_cols", []),
                    "val_mae":      ckpt.get("val_mae", None),
                }
                logger.info(
                    "ThresholdNet loaded — val_mae=%.4f",
                    self._threshold_net_meta.get("val_mae") or 0,
                )
            except Exception as exc:
                logger.warning("ThresholdNet load failed: %s", exc)
                self._threshold_net = None

        # ── Legacy TippingPointClassifier fallback ──────────────────────────
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
                        FROM CALCOFI_TSUNAMI_FEATURES
                        WHERE (LAT_DEC - :lat)*(LAT_DEC - :lat) + (LON_DEC - :lon)*(LON_DEC - :lon) < 0.25
                        ORDER BY DATE DESC
                        LIMIT 180
                        """
                    ),
                    {"lat": lat, "lon": lon},
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

    # Prevention/recovery breakdown ratios per threat type
    _BREAKDOWN = {
        "Coral Bleaching":  {"monitoring": 0.22, "thermal_intervention": 0.38, "reef_restoration": 0.40,
                             "fishery_loss": 0.30, "tourism_loss": 0.45, "infra_loss": 0.15, "ag_loss": 0.10},
        "Reef Collapse":    {"monitoring": 0.18, "marine_protected_areas": 0.42, "reef_restoration": 0.40,
                             "fishery_loss": 0.40, "food_security_loss": 0.35, "infra_loss": 0.15, "tourism_loss": 0.10},
        "Hypoxia":          {"monitoring": 0.15, "nutrient_reduction": 0.55, "oxygen_mitigation": 0.30,
                             "fishery_loss": 0.45, "tourism_loss": 0.20, "infra_loss": 0.10, "ag_loss": 0.25},
        "Heatwave":         {"monitoring": 0.20, "fishery_management": 0.50, "habitat_restoration": 0.30,
                             "fishery_loss": 0.50, "tourism_loss": 0.25, "infra_loss": 0.15, "ag_loss": 0.10},
        "Storm Surge":      {"monitoring": 0.25, "coastal_barriers": 0.45, "mangrove_restoration": 0.30,
                             "infra_loss": 0.45, "displacement_cost": 0.30, "ag_loss": 0.15, "fishery_loss": 0.10},
        "Salinity":         {"monitoring": 0.20, "water_management": 0.50, "crop_adaptation": 0.30,
                             "ag_loss": 0.50, "fishery_loss": 0.25, "infra_loss": 0.15, "displacement_cost": 0.10},
        "Dead Zone":        {"monitoring": 0.18, "oxygen_intervention": 0.47, "fishery_management": 0.35,
                             "fishery_loss": 0.55, "food_security_loss": 0.25, "infra_loss": 0.10, "tourism_loss": 0.10},
        "Eutrophication":   {"monitoring": 0.20, "nutrient_reduction": 0.50, "wetland_restoration": 0.30,
                             "fishery_loss": 0.35, "tourism_loss": 0.35, "infra_loss": 0.20, "ag_loss": 0.10},
    }

    def counterfactual_estimate(self, db: Session, region_id: str) -> dict:
        region_row = db.execute(
            text("SELECT name, current_score, primary_threat, funding_gap FROM regions WHERE id = :region_id"),
            {"region_id": region_id},
        ).fetchone()
        if region_row is None:
            raise LookupError(region_id)
        mapping = region_row._mapping
        region_name = mapping["name"]
        current_score = float(mapping["current_score"])
        primary_threat = mapping["primary_threat"]
        funding_gap = float(mapping["funding_gap"] or 0)

        # Pull real historical cases for this region to anchor cost estimates
        case_rows = db.execute(
            text("""
                SELECT prevention_cost, recovery_cost, cost_multiplier, year_crossed, event_name
                FROM counterfactual_cases
                WHERE region_id = :region_id
                ORDER BY year_crossed DESC
                LIMIT 3
            """),
            {"region_id": region_id},
        ).fetchall()

        if case_rows:
            # Anchor on most recent real case, scale by current score
            latest = case_rows[0]._mapping
            scale = 1 + (current_score - 5.0) * 0.15
            prevention_cost = round(float(latest["prevention_cost"]) * scale, 2)
            recovery_cost = round(float(latest["recovery_cost"]) * scale, 2)
            cost_multiplier = round(recovery_cost / max(prevention_cost, 1), 2)
            anchor_note = f"Anchored on {latest['event_name']} ({latest['year_crossed']})"
        else:
            fallback_gap = funding_gap if funding_gap > 0 else 4500000.0
            prevention_cost = round(fallback_gap * 0.4, 2)
            recovery_cost = round(prevention_cost * (4 + current_score / 2), 2)
            cost_multiplier = round(recovery_cost / max(prevention_cost, 1), 2)
            anchor_note = primary_threat

        bd = self._BREAKDOWN.get(primary_threat, self._BREAKDOWN["Hypoxia"])
        prev_keys = [k for k in bd if k != "fishery_loss" and "loss" not in k and "displacement" not in k]
        rec_keys  = [k for k in bd if "loss" in k or "displacement" in k]

        prevention_breakdown = {k: round(prevention_cost * bd[k], 2) for k in prev_keys}
        recovery_breakdown   = {k: round(recovery_cost * bd[k], 2) for k in rec_keys}

        return {
            "region_id": region_id,
            "region_name": region_name,
            "prevention_cost_usd": prevention_cost,
            "recovery_cost_usd": recovery_cost,
            "cost_multiplier": cost_multiplier,
            "optimal_intervention_type": f"{primary_threat} resilience package — {anchor_note}",
            "prevention_breakdown": prevention_breakdown,
            "recovery_breakdown": recovery_breakdown,
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
                FROM CALCOFI_TSUNAMI_FEATURES
                ORDER BY (LAT_DEC - :lat)*(LAT_DEC - :lat) + (LON_DEC - :lon)*(LON_DEC - :lon) ASC, DATE DESC
                LIMIT 1
            ),
            Narrative AS (
                SELECT
                    AVG(GOLDSTEIN) as GOLDSTEIN,
                    SUM(NUMARTS) as NUMARTS
                FROM GDELT
                WHERE ACTIONGEOLAT BETWEEN :lat - 2 AND :lat + 2
                  AND ACTIONGEOLONG BETWEEN :lon - 2 AND :lon + 2
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

        # ── ThresholdNet inference (preferred) ────────────────────────────
        if self._threshold_net is not None:
            try:
                import torch, numpy as np, pathlib as pl
                meta = self._threshold_net_meta
                feat_cols = meta.get("feature_cols", [
                    "sst_anomaly", "o2_current", "dhw_current", "bleaching_alert_level",
                    "co2_regional_ppm", "chlorophyll_anomaly", "nitrate_anomaly", "conflict_index",
                ])
                mean = np.array(meta.get("mean", [0.0] * len(feat_cols)), dtype=np.float32)
                std  = np.array(meta.get("std",  [1.0] * len(feat_cols)), dtype=np.float32)

                # Pull last 30 rows from REGION_FEATURES for the window
                rf_rows = db.execute(
                    text("SELECT * FROM region_features WHERE region_id = :rid ORDER BY date DESC LIMIT 30"),
                    {"rid": region_id},
                ).fetchall()

                if rf_rows:
                    # Map region_features columns to training feature order
                    col_map = {
                        "sst_anomaly": "sst_anomaly", "o2_current": "o2_current",
                        "dhw_current": "dhw_current", "bleaching_alert_level": "bleaching_alert_level",
                        "co2_regional_ppm": "co2_regional_ppm", "chlorophyll_anomaly": "chlorophyll_anomaly",
                        "nitrate_anomaly": "nitrate_anomaly", "conflict_index": "conflict_index",
                    }
                    fill = {"o2_current": 5.0, "co2_regional_ppm": 415.0}
                    window = []
                    for rr in reversed(rf_rows):   # oldest first
                        m = {k: v for k, v in dict(rr._mapping).items()}
                        row_vec = [float(m.get(col_map.get(c, c)) or fill.get(c, 0.0)) for c in feat_cols]
                        window.append(row_vec)

                    arr = np.array(window, dtype=np.float32)
                    arr = (arr - mean) / std
                    x = torch.from_numpy(arr).unsqueeze(0)   # (1, T, F)
                    region_idx = torch.tensor([_REGION_TO_IDX.get(region_id, 0)])

                    with torch.no_grad():
                        score = float(self._threshold_net(x, region_idx).item())

                    return {
                        "region_id": region_id,
                        "threshold_proximity_score": round(score, 3),
                        "confidence": meta.get("val_mae", 0.5),
                        "primary_driver": f"ThresholdNet (BiLSTM+Attention, val_mae={meta.get('val_mae', '?'):.3f})",
                        "breakdown": [
                            {"key": "thermal",      "label": "Water Temperature",  "value": features["t_degc"],    "detail": f"{features['t_degc']:.1f}°C"},
                            {"key": "oxygen",       "label": "Dissolved Oxygen",   "value": features["o2ml_l"],    "detail": f"{features['o2ml_l']:.2f} ml/L"},
                            {"key": "productivity", "label": "Chlorophyll",        "value": features["chlora"],    "detail": f"{features['chlora']:.2f} mg/m³"},
                            {"key": "stability",    "label": "Political Stability","value": features["goldstein"], "detail": f"Goldstein: {features['goldstein']:.1f}"},
                        ],
                        "timestamp": r.get("DATE", date.today()).isoformat() if hasattr(r.get("DATE", None), "isoformat") else str(r.get("DATE", date.today())),
                    }
            except Exception as exc:
                logger.warning("ThresholdNet inference failed: %s", exc)

        # ── Legacy TippingPointClassifier fallback ────────────────────────
        if self._classifier is not None:
            try:
                result = self._classifier.predict(features)
                result["region_id"] = region_id
                result["timestamp"] = r.get("DATE", date.today()).isoformat()
                result["breakdown"] = [
                    {"key": "thermal",      "label": "Water Temperature",  "value": features["t_degc"],    "detail": f"{features['t_degc']:.1f}°C"},
                    {"key": "oxygen",       "label": "Dissolved Oxygen",   "value": features["o2ml_l"],    "detail": f"{features['o2ml_l']:.2f} ml/L"},
                    {"key": "productivity", "label": "Chlorophyll",        "value": features["chlora"],    "detail": f"{features['chlora']:.2f} mg/m³"},
                    {"key": "stability",    "label": "Political Stability","value": features["goldstein"], "detail": f"Goldstein Score: {features['goldstein']:.1f}"},
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
