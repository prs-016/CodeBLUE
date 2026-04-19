"""Marimo-style placeholder notebook for cost-estimate inspection."""

from ml.models.counterfactual_cost_estimator import CounterfactualCostEstimator


def run(region_id: str, severity: float = 8.0):
    return CounterfactualCostEstimator().estimate(region_id, severity)
