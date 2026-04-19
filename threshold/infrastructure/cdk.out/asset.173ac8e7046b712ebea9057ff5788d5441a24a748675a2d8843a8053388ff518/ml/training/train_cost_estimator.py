from __future__ import annotations

import argparse
import json
from pathlib import Path

from ml.models.counterfactual_cost_estimator import CounterfactualCostEstimator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a counterfactual cost estimate snapshot.")
    parser.add_argument("--data", choices=["real", "synthetic"], default="synthetic")
    parser.add_argument("--region", default="great_barrier_reef")
    parser.add_argument("--severity", type=float, default=8.4)
    parser.add_argument("--output", default="ml/saved_models/counterfactual_estimate.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    estimate = CounterfactualCostEstimator().estimate(args.region, args.severity)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(estimate, indent=2))
    print(f"generated counterfactual estimate using {args.data} data -> {output_path}")


if __name__ == "__main__":
    main()
