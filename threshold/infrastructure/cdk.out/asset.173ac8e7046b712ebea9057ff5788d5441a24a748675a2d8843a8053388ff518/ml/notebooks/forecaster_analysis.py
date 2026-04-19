"""Marimo-style placeholder notebook for forecast inspection."""

from ml.models.days_to_threshold_forecaster import DaysToThresholdForecaster


def run(history):
    return DaysToThresholdForecaster().predict(history)
