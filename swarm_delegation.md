# Swarm Agent Delegation Manifest

This document maps the **11 AI Sub-Agents** to their explicit operational tracks based on the Code Blue master prompt. All sub-agents work seamlessly in parallel, depending only on defined data schemas until the final integration phase.

---

### SUB-AGENT 1 — Data Ingestion Pipeline
**Directory:** `threshold/data/ingestion/`
**Directive:** Build every data ingestion script. Fetch, normalize, and save to SQLite.
- `keeling_curve.py` (CO2 ppm)
- `calcofi.py` (Ocean Metrics)
- `noaa_sst.py` (SST Anomalies)
- `coral_reef_watch.py` (DHW Alert Levels)
- `ocha_fts.py` (Humanitarian Funding)
- `reliefweb.py` (Situation Reports)
- `gdelt.py` (Media Attention Scores)
- `emdat.py` (Historical Disasters)
- `charity_navigator.py` (Verified NGO Data)

### SUB-AGENT 2 — Feature Engineering & Aggregation
**Directory:** `threshold/data/processing/`
**Directive:** Build the transformation layer producing the ML-ready feature store for the 8 core THRESHOLD regions.
- `feature_engineering.py`: Normalizes 7d/30d/90d rolling windows.
- `regional_aggregator.py`: Handles proxy interpolations.
- `funding_gap_calculator.py`: Computes funding and coverage gaps.
- `media_attention_scorer.py`: Computes crisis vs. media attention gap.

### SUB-AGENT 3 — ML Models & Notebooks
**Directory:** `threshold/ml/`
**Directive:** Build the 3 ML models and beautiful Marimo notebooks.
- `tipping_point_classifier.py` (XGBoost Regressor)
- `days_to_threshold_forecaster.py` (Facebook Prophet + LSTM Ensemble)
- `counterfactual_cost_estimator.py` (SciKit-Learn Regression mapped to EM-DAT)
- `notebooks/`: Marimo data exploration files for judges (`tipping_point_analysis.py`).

### SUB-AGENT 4 — FastAPI Backend
**Directory:** `threshold/backend/`
**Directive:** Build the full API with realistic mocking schemas.
- **Routers:** `/regions`, `/triage`, `/funding`, `/news`, `/counterfactual`, `/charities`, `/fund`.
- **Services:** `ml_service.py`, `stripe_service.py`, `solana_service.py`.

### SUB-AGENT 5 — Frontend: Globe & Navigation
**Directory:** `threshold/frontend/`
**Directive:** Build the `WarRoomGlobe.jsx` landing page.
- Colorize regions from Teal to Pulsing Red based on `threshold_proximity_score`.
- Immersive dark-navy UI with JetBrains Mono numbers.

### SUB-AGENT 6 — Frontend: Triage Queue & Region Brief
**Directory:** `threshold/frontend/`
**Directive:** Build the core analytical React components.
- `TriageQueue.jsx`: Sortable emergency tables.
- `RegionBrief.jsx`: D3.js line charts for stress signals (`StressSignalDashboard.jsx`) and branching futures (`BranchingPaths.jsx`).

### SUB-AGENT 7 — Frontend: Counterfactuals & Radar
**Directory:** `threshold/frontend/`
**Directive:** Build the high-complexity D3.js visualizations.
- `TimelineScrubber.jsx`: Interactive historical scrubber computing real-time late-recovery cost multipliers.
- `FundingGapRadar.jsx`: Force-directed bubble chart marking "OVERFUNDED" vs "DANGER ZONE".

### SUB-AGENT 8 — Frontend: THRESHOLD FUND
**Directory:** `threshold/frontend/`
**Directive:** Build the transparent stripe payment loop.
- `FundDashboard.jsx`: Active funding rounds.
- `DonationModal.jsx`: Stripe Elements integration with live impact calculators ("$50 = 2.3 hectares of reef protected").

### SUB-AGENT 9 — Blockchain: Solana Smart Contract
**Directory:** `threshold/blockchain/`
**Directive:** Write the Rust smart contract logic.
- `settings` / `lib.rs`: Solana instructions for `record_contribution`, `disburse_tranche`, `record_impact`.
- `client/interact.js`: Web3 connections for FastAPI backend.

### SUB-AGENT 10 — Data: Synthetic Generator
**Directory:** `threshold/data/seed/`
**Directive:** Engineer the exact deterministic dataset for the hackathon deployment.
- `generate_synthetic.py`: Must load Great Barrier Reef with `current_score: 8.4`, `CRITICAL` status for the demo impact and immediately simulate 10 years of oceanographic/NGO metrics.

### SUB-AGENT 11 — DevOps & Integration
**Directory:** `threshold/`
**Directive:** Connect the swarm's work into `docker-compose.yml`.
- Execute all integration step validations (e.g., `frontend/src/utils/api.js`).
- Manage deployment scripts and `docker-compose up` flow so judges can spin up the full 5-container stack instantly.
