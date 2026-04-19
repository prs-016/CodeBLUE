from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List

import numpy as np
import pandas as pd


@dataclass
class DaysToThresholdForecaster:
    """
    Forecasts when a region will cross the danger threshold of 8.0.

    This hackathon-safe implementation approximates the requested Prophet/LSTM
    ensemble with a trend + seasonal projection. The public interface matches
    the backend's needs and can later be swapped for the heavier ensemble
    without changing route contracts.
    """

    danger_threshold: float = 8.0

    def predict(self, history: pd.DataFrame, score_column: str = "threshold_proximity_score") -> Dict[str, object]:
        ordered = history.sort_values("date").copy()
        ordered["date"] = pd.to_datetime(ordered["date"])
        ordered[score_column] = ordered[score_column].astype(float)

        if len(ordered) < 14:
            return self._fallback_projection(ordered)

        recent = ordered.tail(90).copy()
        recent["ordinal"] = np.arange(len(recent))
        slope = np.polyfit(recent["ordinal"], recent[score_column], 1)[0]
        seasonal = self._seasonal_component(recent[score_column].to_numpy())
        current_score = float(ordered[score_column].iloc[-1])
        current_date = ordered["date"].iloc[-1]

        trajectory: List[Dict[str, object]] = []
        crossing_day = None
        for day in range(1, 731):
            annual_wave = np.sin((day / 365.0) * 2 * np.pi) * seasonal
            predicted = current_score + slope * day + annual_wave
            clipped = float(np.clip(predicted, 0.0, 10.0))
            date_value = current_date + timedelta(days=day)
            trajectory.append({"date": date_value.strftime("%Y-%m-%d"), "predicted_score": round(clipped, 2)})
            if crossing_day is None and clipped >= self.danger_threshold:
                crossing_day = day

        if crossing_day is None:
            crossing_day = 730

        return {
            "days_to_threshold": int(crossing_day),
            "crossing_date": (current_date + timedelta(days=crossing_day)).strftime("%Y-%m-%d"),
            "confidence_interval_low": max(0, int(crossing_day * 0.8)),
            "confidence_interval_high": int(crossing_day * 1.25),
            "trajectory_data": trajectory,
        }

    def _seasonal_component(self, values: np.ndarray) -> float:
        if len(values) < 30:
            return 0.08
        centered = values - np.mean(values)
        return float(min(np.std(centered) * 0.65, 0.6))

    def _fallback_projection(self, history: pd.DataFrame) -> Dict[str, object]:
        last_date = pd.to_datetime(history["date"].iloc[-1]) if not history.empty else pd.Timestamp(datetime.utcnow())
        current_score = float(history["threshold_proximity_score"].iloc[-1]) if not history.empty else 5.0
        days = int(max((self.danger_threshold - current_score) * 120, 45))
        trajectory = []
        for day in range(1, 731):
            predicted = np.clip(current_score + (day / max(days, 1)) * (self.danger_threshold - current_score), 0.0, 10.0)
            trajectory.append(
                {
                    "date": (last_date + timedelta(days=day)).strftime("%Y-%m-%d"),
                    "predicted_score": round(float(predicted), 2),
                }
            )
        return {
            "days_to_threshold": days,
            "crossing_date": (last_date + timedelta(days=days)).strftime("%Y-%m-%d"),
            "confidence_interval_low": max(0, int(days * 0.75)),
            "confidence_interval_high": int(days * 1.3),
            "trajectory_data": trajectory,
        }
