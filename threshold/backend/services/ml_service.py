from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session


class DemoModelRegistry:
    def __init__(self) -> None:
        self.loaded = False

    def load(self) -> None:
        self.loaded = True

    def region_trajectory(self, db: Session, region_id: str) -> dict:
        row = db.execute(
            text(
                """
                SELECT id, current_score, days_to_threshold, primary_driver
                FROM regions
                WHERE id = :region_id
                """
            ),
            {"region_id": region_id},
        ).fetchone()
        if row is None:
            raise LookupError(region_id)

        mapping = row._mapping
        today = date.today()
        trajectory = []
        base_score = float(mapping["current_score"])
        days_to_threshold = int(mapping["days_to_threshold"])
        for step in range(0, 12):
            projected_date = today + timedelta(days=step * 30)
            projected_score = min(10.0, base_score + (step * (8.0 - base_score) / max(1, days_to_threshold / 30)))
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
        score = float(mapping["current_score"])
        prevention_cost = round(4_000_000 + score * 2_500_000, 2)
        recovery_cost = round(prevention_cost * (4 + score / 2), 2)
        return {
            "region_id": region_id,
            "region_name": mapping["name"],
            "prevention_cost_usd": prevention_cost,
            "recovery_cost_usd": recovery_cost,
            "cost_multiplier": round(recovery_cost / prevention_cost, 2),
            "optimal_intervention_type": f"{mapping['primary_threat']} resilience package",
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


model_registry = DemoModelRegistry()
