from __future__ import annotations

import argparse
from pathlib import Path

from ml.models.tipping_point_classifier import TippingPointClassifier, load_training_frame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the THRESHOLD tipping point classifier.")
    parser.add_argument("--data", choices=["real", "synthetic"], default="synthetic")
    parser.add_argument("--input", default="threshold_training_data.csv")
    parser.add_argument("--output", default="ml/saved_models/tipping_point_classifier.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frame = load_training_frame(args.input)
    model = TippingPointClassifier().train(frame)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(output_path)
    print(f"trained tipping-point classifier using {args.data} data -> {output_path}")


if __name__ == "__main__":
    main()
