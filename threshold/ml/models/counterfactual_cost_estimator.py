from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


BASELINES: Dict[str, Dict[str, object]] = {
    "california_current": {
        "optimal_intervention_type": "Fishery resilience and early catch controls",
        "prevention_cost_usd": 8_000_000,
        "recovery_cost_usd": 800_000_000,
        "recovery_breakdown": {"ag_loss": 0, "infra_loss": 20_000_000, "fishery_loss": 780_000_000},
    },
    "great_barrier_reef": {
        "optimal_intervention_type": "Thermal stress reduction and reef monitoring",
        "prevention_cost_usd": 25_000_000,
        "recovery_cost_usd": 400_000_000,
        "recovery_breakdown": {"ag_loss": 15_000_000, "infra_loss": 35_000_000, "fishery_loss": 350_000_000},
    },
    "arabian_sea": {
        "optimal_intervention_type": "Nutrient runoff reduction program",
        "prevention_cost_usd": 50_000_000,
        "recovery_cost_usd": 2_100_000_000,
        "recovery_breakdown": {"ag_loss": 180_000_000, "infra_loss": 320_000_000, "fishery_loss": 1_600_000_000},
    },
    "baltic_sea": {
        "optimal_intervention_type": "Agricultural runoff controls",
        "prevention_cost_usd": 30_000_000,
        "recovery_cost_usd": 890_000_000,
        "recovery_breakdown": {"ag_loss": 120_000_000, "infra_loss": 170_000_000, "fishery_loss": 600_000_000},
    },
    "gulf_of_mexico": {
        "optimal_intervention_type": "Watershed nutrient interception",
        "prevention_cost_usd": 200_000_000,
        "recovery_cost_usd": 2_800_000_000,
        "recovery_breakdown": {"ag_loss": 330_000_000, "infra_loss": 570_000_000, "fishery_loss": 1_900_000_000},
    },
}


@dataclass
class CounterfactualCostEstimator:
    """
    Estimates prevention and recovery costs using hackathon-safe baselines.
    """

    def estimate(self, region_id: str, severity_score: float = 5.0) -> Dict[str, object]:
        baseline = BASELINES.get(region_id, self._generic_baseline(region_id))
        multiplier = max(0.8, severity_score / 6.0)
        prevention_cost = float(baseline["prevention_cost_usd"]) * multiplier
        recovery_cost = float(baseline["recovery_cost_usd"]) * multiplier
        recovery_breakdown = {
            key: round(value * multiplier, 2) for key, value in baseline["recovery_breakdown"].items()
        }
        prevention_breakdown = {
            "monitoring": round(prevention_cost * 0.22, 2),
            "community_programs": round(prevention_cost * 0.38, 2),
            "ecosystem_restoration": round(prevention_cost * 0.40, 2),
        }
        return {
            "prevention_cost_usd": round(prevention_cost, 2),
            "recovery_cost_usd": round(recovery_cost, 2),
            "cost_multiplier": round(recovery_cost / max(prevention_cost, 1), 2),
            "prevention_breakdown": prevention_breakdown,
            "recovery_breakdown": recovery_breakdown,
            "optimal_intervention_type": baseline["optimal_intervention_type"],
        }

    def _generic_baseline(self, region_id: str) -> Dict[str, object]:
        return {
            "optimal_intervention_type": f"Targeted resilience program for {region_id.replace('_', ' ')}",
            "prevention_cost_usd": 18_000_000,
            "recovery_cost_usd": 280_000_000,
            "recovery_breakdown": {"ag_loss": 40_000_000, "infra_loss": 60_000_000, "fishery_loss": 180_000_000},
        }
