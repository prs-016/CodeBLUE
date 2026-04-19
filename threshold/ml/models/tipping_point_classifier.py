from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.model_selection import KFold
except Exception:  # pragma: no cover - optional dependency
    RandomForestRegressor = None
    mean_absolute_error = None
    mean_squared_error = None
    r2_score = None
    KFold = None


FEATURE_COLUMNS = [
    "t_degc",
    "o2ml_l",
    "salnty",
    "chlora",
    "no3um",
    "po4um",
    "sio3um",
    "wind_spd",
    "barometer",
    "goldstein",
    "numarts",
]

DISPLAY_NAMES = {
    "t_degc": "Water Temp (°C)",
    "o2ml_l": "Dissolved Oxygen",
    "salnty": "Salinity",
    "chlora": "Chlorophyll",
    "no3um": "Nitrate (µM)",
    "po4um": "Phosphate",
    "sio3um": "Silicate",
    "wind_spd": "Wind Speed",
    "barometer": "Pressure (mbar)",
    "goldstein": "Political Stability",
    "numarts": "Media Volume",
}


@dataclass
class TippingPointClassifier:
    """
    Assigns a Threshold Proximity Score (0.0-10.0) to each region.

    The implementation prefers a tree model when scikit-learn is available and
    falls back to a deterministic weighted heuristic when it is not. That keeps
    the hackathon demo functional in constrained environments while preserving a
    consistent interface for the backend.
    """

    feature_columns: List[str] = field(default_factory=lambda: FEATURE_COLUMNS.copy())
    model: object | None = None
    feature_baselines: Dict[str, float] = field(default_factory=dict)
    feature_spans: Dict[str, float] = field(default_factory=dict)
    feature_importances_: Dict[str, float] = field(default_factory=dict)
    metrics_: Dict[str, float] = field(default_factory=dict)
    is_trained: bool = False

    def train(self, frame: pd.DataFrame, target_column: str = "threshold_proximity_score") -> "TippingPointClassifier":
        working = frame.copy()
        X = working[self.feature_columns].fillna(0.0)
        y = working[target_column].fillna(0.0)
        self.feature_baselines = {column: float(X[column].median()) for column in self.feature_columns}
        self.feature_spans = {
            column: float(max(X[column].max() - X[column].min(), 1.0)) for column in self.feature_columns
        }

        if RandomForestRegressor is not None and len(X) >= 10:
            self.model = RandomForestRegressor(
                n_estimators=120,
                max_depth=8,
                random_state=42,
            )
            self.model.fit(X, y)
            self.feature_importances_ = {
                column: float(weight)
                for column, weight in zip(self.feature_columns, self.model.feature_importances_)
            }
            self.metrics_ = self._cross_validate(X, y)
        else:
            heuristic_weights = np.array([0.19, 0.07, 0.11, 0.05, 0.12, 0.08, 0.13, 0.09, 0.07, 0.05, 0.04])
            self.feature_importances_ = {
                column: float(weight) for column, weight in zip(self.feature_columns, heuristic_weights)
            }
            self.model = None
            self.metrics_ = {"rmse": 0.0, "mae": 0.0, "r2": 0.0}

        self.is_trained = True
        return self

    def predict(self, features: pd.DataFrame | Dict[str, float]) -> Dict[str, object]:
        if not self.is_trained:
            self._prime_defaults()

        frame = self._coerce_frame(features)
        raw_score = self._predict_scores(frame)[0]
        explanation = self.explain(frame.iloc[0].to_dict())
        primary_driver = max(explanation, key=explanation.get)

        return {
            "threshold_proximity_score": round(float(np.clip(raw_score, 0.0, 10.0)), 2),
            "feature_importances": explanation,
            "confidence": round(self._confidence(frame.iloc[0].to_dict()), 2),
            "primary_driver": self._format_driver(primary_driver, frame.iloc[0][primary_driver]),
        }

    def explain(self, features: Dict[str, float]) -> Dict[str, float]:
        if not self.is_trained:
            self._prime_defaults()

        contributions: Dict[str, float] = {}
        for column in self.feature_columns:
            baseline = self.feature_baselines.get(column, 0.0)
            span = self.feature_spans.get(column, 1.0)
            importance = self.feature_importances_.get(column, 0.0)
            delta = (float(features.get(column, 0.0)) - baseline) / span
            contributions[column] = round(float(delta * importance), 4)
        return contributions

    def save(self, path: str | Path) -> None:
        payload = {
            "feature_columns": self.feature_columns,
            "feature_baselines": self.feature_baselines,
            "feature_spans": self.feature_spans,
            "feature_importances": self.feature_importances_,
            "metrics": self.metrics_,
            "is_trained": self.is_trained,
        }
        Path(path).write_text(json.dumps(payload, indent=2))

    def load(self, path: str | Path) -> "TippingPointClassifier":
        payload = json.loads(Path(path).read_text())
        self.feature_columns = payload["feature_columns"]
        self.feature_baselines = payload["feature_baselines"]
        self.feature_spans = payload["feature_spans"]
        self.feature_importances_ = payload["feature_importances"]
        self.metrics_ = payload["metrics"]
        self.is_trained = payload["is_trained"]
        self.model = None
        return self

    def _cross_validate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        if KFold is None or len(X) < 10:
            return {"rmse": 0.0, "mae": 0.0, "r2": 0.0}

        splitter = KFold(n_splits=5, shuffle=True, random_state=42)
        rmses: List[float] = []
        maes: List[float] = []
        r2s: List[float] = []

        for train_idx, test_idx in splitter.split(X):
            model = RandomForestRegressor(n_estimators=90, max_depth=8, random_state=42)
            model.fit(X.iloc[train_idx], y.iloc[train_idx])
            predictions = model.predict(X.iloc[test_idx])
            rmses.append(float(np.sqrt(mean_squared_error(y.iloc[test_idx], predictions))))
            maes.append(float(mean_absolute_error(y.iloc[test_idx], predictions)))
            r2s.append(float(r2_score(y.iloc[test_idx], predictions)))

        return {
            "rmse": round(float(np.mean(rmses)), 4),
            "mae": round(float(np.mean(maes)), 4),
            "r2": round(float(np.mean(r2s)), 4),
        }

    def _predict_scores(self, frame: pd.DataFrame) -> np.ndarray:
        prepared = frame[self.feature_columns].fillna(0.0)
        if self.model is not None:
            return self.model.predict(prepared)

        values = prepared.to_numpy(dtype=float)
        weights = np.array([0.19, 0.07, -0.11, -0.05, 0.12, 0.08, 0.13, 0.09, 0.07, 0.05, -0.04])
        normalized = []
        for index, column in enumerate(self.feature_columns):
            baseline = self.feature_baselines.get(column, 0.0)
            span = self.feature_spans.get(column, 1.0)
            normalized.append((values[:, index] - baseline) / span)
        normalized_values = np.vstack(normalized).T
        scores = 5.0 + normalized_values @ weights * 12.0
        return np.clip(scores, 0.0, 10.0)

    def _coerce_frame(self, features: pd.DataFrame | Dict[str, float]) -> pd.DataFrame:
        if isinstance(features, pd.DataFrame):
            frame = features.copy()
        else:
            frame = pd.DataFrame([features])
        for column in self.feature_columns:
            if column not in frame:
                frame[column] = self.feature_baselines.get(column, 0.0)
        return frame[self.feature_columns]

    def _confidence(self, features: Dict[str, float]) -> float:
        deviations = []
        for column in self.feature_columns:
            span = self.feature_spans.get(column, 1.0)
            baseline = self.feature_baselines.get(column, 0.0)
            deviations.append(min(abs(float(features.get(column, baseline)) - baseline) / span, 1.0))
        novelty = float(np.mean(deviations)) if deviations else 0.0
        return max(0.55, 0.95 - novelty * 0.25)

    def _format_driver(self, feature_name: str, value: float) -> str:
        label = DISPLAY_NAMES.get(feature_name, feature_name)
        if feature_name in {"sst_anomaly_30d_avg", "sst_acceleration"}:
            return f"{label} {value:+.2f}°C"
        if feature_name in {"o2_current", "o2_trend_90d"}:
            return f"{label} {value:.2f} ml/L"
        if feature_name == "dhw_current":
            return f"{label} {value:.1f} DHW"
        if feature_name == "co2_yoy_acceleration":
            return f"{label} {value * 100:+.1f}% YoY"
        return f"{label} {value:+.2f}"

    def _prime_defaults(self) -> None:
        self.feature_baselines = {column: 0.0 for column in self.feature_columns}
        self.feature_spans = {column: 1.0 for column in self.feature_columns}
        self.feature_importances_ = {
            column: weight
            for column, weight in zip(
                self.feature_columns,
                [0.19, 0.07, 0.11, 0.05, 0.12, 0.08, 0.13, 0.09, 0.07, 0.05, 0.04],
            )
        }
        self.metrics_ = {"rmse": 0.0, "mae": 0.0, "r2": 0.0}
        self.is_trained = True


def load_training_frame(csv_path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(csv_path)
    missing = [column for column in FEATURE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Training data missing required features: {missing}")
    if "threshold_proximity_score" not in frame.columns:
        raise ValueError("Training data must include threshold_proximity_score")
    return frame


def model_fn(model_dir: str) -> TippingPointClassifier:
    model = TippingPointClassifier()
    model_path = Path(model_dir) / "tipping_point_classifier.json"
    if model_path.exists():
        model.load(model_path)
    else:
        model._prime_defaults()
    return model


def predict_fn(input_data: Dict[str, float] | Iterable[Dict[str, float]], model: TippingPointClassifier):
    if isinstance(input_data, dict):
        return model.predict(input_data)
    return [model.predict(item) for item in input_data]
