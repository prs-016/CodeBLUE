from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ml.models.days_to_threshold_forecaster import DaysToThresholdForecaster


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a threshold crossing forecast.")
    parser.add_argument("--data", choices=["real", "synthetic"], default="synthetic")
    parser.add_argument("--input", default="region_history.csv")
    parser.add_argument("--output", default="ml/saved_models/forecaster_projection.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    history = pd.read_csv(args.input)
    forecast = DaysToThresholdForecaster().predict(history)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(forecast, indent=2))
    print(f"generated days-to-threshold forecast using {args.data} data -> {output_path}")


if __name__ == "__main__":
    main()
