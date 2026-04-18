# Implementation Plan - Project THRESHOLD (Code Blue)

**Code Blue** is building **THRESHOLD**: The Bloomberg Terminal for Climate Aid. 

## The Core Concept
THRESHOLD calculates a visceral "Days to Threshold" countdown for impending ecological disasters by piping oceanographic warning signals into machine learning models. It exposes the gap between actual risk and committed funding, and provides a direct, blockchain-verifiable conduit to trigger fund deployments to verified NGOs before the window closes.

---

## Technical Stack Architecture

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React, Vite, Tailwind CSS, Globe.gl, D3.js |
| **Backend** | Python (FastAPI), SQLAlchemy (SQLite for Hackathon) |
| **Machine Learning** | XGBoost, Prophet/LSTM, SciKit-Learn Regression, Marimo Notebooks |
| **Data Ingestion** | Python Async scripts writing to SQLite |
| **Web3 / Pay** | True Solana Smart Contracts/Ledger & Stripe Payment API |

---

## Folder Structure (`threshold/`)
The platform uses the following highly decoupled structure to allow 11 parallel sub-agents to build the modules simultaneously:

- `data/`
  - `ingestion/`: 12 distinct data extractors (Keeling Curve, CalCOFI, NOAA, ReliefWeb, etc.)
  - `processing/`: Feature engineering, aggregation, funding gap calculation
  - `schemas/`: SQLite SQL table definitions
  - `seed/`: Synthetic data generator `generate_synthetic.py`
- `ml/`
  - `models/`: Tipping point, Forecaster, Counterfactual estimators
  - `notebooks/`: Marimo analysis notebooks
- `backend/`
  - `routers/`: 7 FastAPI routers (regions, triage, funding, news, counterfactual, charities, fund)
  - `services/`: Stripe, Solana, ML, ReliefWeb, GDELT integrations
- `frontend/`
  - `src/components/`: Modular React components grouped by functionality (Globe, Triage, RegionBrief, Counterfactual, FundingGap, Fund)
- `blockchain/`
  - `programs/`: Solana Rust smart contracts (`threshold_fund`)
- `docs/`
  - Sphinx configuration

---

## Execution Logic (The 11 Sub-Agents)
The swarm is divided into 11 specialized autonomous agents:
1. **Sub-Agent 1 (Data Ingestion)**: Extracts datasets into a local SQLite mirror.
2. **Sub-Agent 2 (Feature Engineering)**: Aggregates signals into the 8 core THRESHOLD regions.
3. **Sub-Agent 3 (ML Models)**: Builds the XGBoost classifier, Prophet forecaster, and Counterfactual estimator.
4. **Sub-Agent 4 (FastAPI Backend)**: Manages all `backend/routers/` and services.
5. **Sub-Agent 5 (Frontend Globe)**: Builds the `Globe.gl` dark-mode landing page and core UI shell.
6. **Sub-Agent 6 (Frontend Triage)**: Builds `TriageQueue` and the comprehensive `RegionBrief` dashboards.
7. **Sub-Agent 7 (Frontend Counterfactual & Radar)**: Builds the D3 TimelineScrubber and FundingGapRadar.
8. **Sub-Agent 8 (Frontend Funding)**: Builds the Stripe checkout and Donation modals.
9. **Sub-Agent 9 (Blockchain)**: Deploys the Solana instructions tracking impact.
10. **Sub-Agent 10 (Synthetic Data)**: Engineers the flawless hackathon demo seed script.
11. **Sub-Agent 11 (DevOps/Integration)**: Manages `docker-compose.yml` and stitches the swarm's code into one unified app.

> [!IMPORTANT]
> The orchestrator rule is strict: **Do not build anything sequentially that can be built in parallel.** All dependencies are mocked via schemas until the final Step 1-5 Integration Phase.
