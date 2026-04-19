from __future__ import annotations

import json
from pathlib import Path


def summarize_model_artifacts(model_dir: str = "ml/saved_models") -> dict:
    artifacts = {}
    for path in Path(model_dir).glob("*.json"):
        try:
            artifacts[path.name] = json.loads(path.read_text())
        except json.JSONDecodeError:
            artifacts[path.name] = {"status": "unreadable"}
    return artifacts


if __name__ == "__main__":
    print(json.dumps(summarize_model_artifacts(), indent=2))
