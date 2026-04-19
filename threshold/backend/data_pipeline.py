"""
data_pipeline.py — DISABLED.

Data is managed directly in Snowflake via the Snowflake UI.
This pipeline no longer fetches or writes anything.
All API routes read from Snowflake (or local SQLite for development).
"""
from __future__ import annotations

from sqlalchemy.engine import Engine


def run_pipeline(engine: Engine | None = None) -> dict[str, int]:
    return {
        "status": "disabled",
        "message": "Pipeline writes are disabled. Data is managed via Snowflake UI.",
    }


if __name__ == "__main__":
    print(run_pipeline())
