from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import app  # noqa: E402


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert payload["db_connected"] is True
        assert payload["models_loaded"] is True


def test_regions_endpoints() -> None:
    with TestClient(app) as client:
        regions = client.get("/api/v1/regions")
        assert regions.status_code == 200
        data = regions.json()
        assert len(data) >= 8
        assert data[0]["threshold_proximity_score"] >= data[-1]["threshold_proximity_score"]

        region = client.get("/api/v1/regions/great_barrier_reef")
        assert region.status_code == 200
        region_payload = region.json()
        assert region_payload["primary_driver"].startswith("SST Anomaly")

        trajectory = client.get("/api/v1/regions/great_barrier_reef/trajectory")
        assert trajectory.status_code == 200
        assert len(trajectory.json()["trajectory"]) == 12

        signals = client.get("/api/v1/regions/great_barrier_reef/stress-signals")
        assert signals.status_code == 200
        assert len(signals.json()) >= 30


def test_triage_filters() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/triage",
            params={"threat_type": "thermal", "max_days": 120, "sort_by": "current_score", "order": "desc"},
        )
        assert response.status_code == 200
        items = response.json()
        assert items
        assert all(item["threat_type"] == "thermal" for item in items)
        assert all(item["days_to_threshold"] <= 120 for item in items)


def test_funding_endpoints_and_contribution_flow() -> None:
    with TestClient(app) as client:
        gap = client.get("/api/v1/funding/gap")
        assert gap.status_code == 200
        assert any(item["region_id"] == "arabian_sea" for item in gap.json())

        rounds = client.get("/api/v1/funding/rounds")
        assert rounds.status_code == 200
        round_id = rounds.json()[0]["id"]

        round_detail = client.get(f"/api/v1/funding/rounds/{round_id}")
        assert round_detail.status_code == 200
        assert round_detail.json()["remaining_gap"] >= 0

        contribution = client.post(
            f"/api/v1/funding/rounds/{round_id}/contribute",
            json={"amount_usd": 50, "donor_email": "judge@example.com"},
        )
        assert contribution.status_code == 200
        contribution_payload = contribution.json()
        assert contribution_payload["status"] == "success"
        assert contribution_payload["blockchain_hash"].startswith("sol_")

        impact = client.get("/api/v1/funding/impact")
        assert impact.status_code == 200
        assert impact.json()


def test_news_counterfactual_and_charities() -> None:
    with TestClient(app) as client:
        attention = client.get("/api/v1/news/attention-gap")
        assert attention.status_code == 200
        assert attention.json()[0]["attention_gap"] >= attention.json()[-1]["attention_gap"]

        news = client.get("/api/v1/news/great_barrier_reef", params={"source": "reliefweb"})
        assert news.status_code == 200
        assert all(item["source_type"] == "reliefweb" for item in news.json())

        cases = client.get("/api/v1/counterfactual/cases")
        assert cases.status_code == 200
        assert any(case["case_id"] == "gbr_2016" for case in cases.json())

        case_detail = client.get("/api/v1/counterfactual/cases/gbr_2016")
        assert case_detail.status_code == 200
        assert len(case_detail.json()["timeline"]) == 3

        estimate = client.get("/api/v1/counterfactual/estimate/great_barrier_reef")
        assert estimate.status_code == 200
        assert estimate.json()["cost_multiplier"] > 1

        charities = client.get("/api/v1/charities", params={"min_score": 85})
        assert charities.status_code == 200
        assert charities.json()

        charity = client.get("/api/v1/charities/52-1693387")
        assert charity.status_code == 200
        assert charity.json()["eligible_for_disbursement"] is True


def test_fund_endpoints() -> None:
    with TestClient(app) as client:
        create = client.post(
            "/api/v1/fund/rounds",
            json={
                "region_id": "bengal_bay",
                "title": "Bay of Bengal Rapid Response",
                "target_amount": 1500000,
                "deadline": "2026-09-01T00:00:00Z",
            },
        )
        assert create.status_code == 200
        round_id = create.json()["round_id"]

        disburse = client.post(f"/api/v1/fund/disburse/{round_id}/1")
        assert disburse.status_code == 200
        assert disburse.json()["solana_tx"].startswith("sol_")

        transactions = client.get("/api/v1/fund/transactions")
        assert transactions.status_code == 200
        assert transactions.json()

        transparency = client.get("/api/v1/fund/transparency")
        assert transparency.status_code == 200
        assert transparency.json()["total_transactions"] >= 1
