from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1]
if str(DATA_DIR) not in sys.path:
    sys.path.append(str(DATA_DIR))

from ingestion.shared import COUNTRY_TO_REGION, ensure_schema, parse_args, setup_logging, sqlite_connection, write_table


TABLE = "funding_gap"


def build_funding_gap(conn) -> pd.DataFrame:
    stress = pd.read_sql_query(
        "SELECT region_id, MAX(stress_composite) AS threshold_proximity_score FROM region_stress GROUP BY region_id",
        conn,
    )
    fts = _maybe_read(conn, "humanitarian_funding")
    hdx = _maybe_read(conn, "hdx_funding_needs")
    cases = _maybe_read(conn, "counterfactual_cases")

    if not fts.empty:
        fts["region_id"] = fts["country"].map(COUNTRY_TO_REGION)
        fts = fts.dropna(subset=["region_id"])
        committed = fts.groupby("region_id", as_index=False)["amount_usd"].sum().rename(columns={"amount_usd": "committed_funding"})
    else:
        committed = pd.DataFrame({"region_id": stress["region_id"], "committed_funding": 0.0})

    if not hdx.empty:
        hdx["region_id"] = hdx["country"].map(COUNTRY_TO_REGION)
        hdx = hdx.dropna(subset=["region_id"])
        coverage = hdx.groupby("region_id", as_index=False).agg(coverage_ratio=("coverage_ratio", "mean"))
    else:
        coverage = pd.DataFrame({"region_id": stress["region_id"], "coverage_ratio": 0.25})

    if not cases.empty:
        cases = cases.rename(columns={"prevention_cost": "baseline_prevention", "recovery_cost": "recovery_cost"})
        costs = cases.groupby("region_id", as_index=False).agg(
            baseline_prevention=("baseline_prevention", "mean"),
            recovery_cost=("recovery_cost", "mean"),
        )
    else:
        costs = pd.DataFrame({"region_id": stress["region_id"], "baseline_prevention": 5_000_000, "recovery_cost": 40_000_000})

    merged = stress.merge(committed, on="region_id", how="left").merge(coverage, on="region_id", how="left").merge(costs, on="region_id", how="left")
    merged["coverage_ratio"] = merged["coverage_ratio"].fillna(0.25).clip(lower=0.05)
    merged["modeled_intervention_cost"] = merged["baseline_prevention"].fillna(5_000_000) * (1 / merged["coverage_ratio"])
    merged["committed_funding"] = merged["committed_funding"].fillna(0.0)
    merged["funding_gap"] = merged["modeled_intervention_cost"] - merged["committed_funding"]
    merged["impact_per_dollar"] = (merged["recovery_cost"] - merged["modeled_intervention_cost"]) / merged["modeled_intervention_cost"]
    return merged[
        [
            "region_id",
            "threshold_proximity_score",
            "modeled_intervention_cost",
            "committed_funding",
            "coverage_ratio",
            "funding_gap",
            "impact_per_dollar",
        ]
    ]


def _maybe_read(conn, table: str) -> pd.DataFrame:
    query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
    if conn.execute(query, (table,)).fetchone() is None:
        return pd.DataFrame()
    return pd.read_sql_query(f"SELECT * FROM {table}", conn)


def main() -> pd.DataFrame:
    args = parse_args("Calculate regional funding gaps.")
    logger = setup_logging("funding_gap_calculator")
    conn = sqlite_connection()
    ensure_schema(conn)
    frame = build_funding_gap(conn)
    return write_table(frame, TABLE, conn, dry_run=args.dry_run, source="derived", logger=logger)


if __name__ == "__main__":
    main()
