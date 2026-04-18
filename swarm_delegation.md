# Swarm Agent Delegation Manifest

This document maps the **20 AI Subagents** to their explicit operational tracks to build the THRESHOLD platform simultaneously. By dividing the 20-dataset architecture into atomic units, the swarm can execute the massive roadmap in 48 hours.

---

## 🗄️ DATA ENGINEERING LAYER (Agents 01-04) - Located in `threshold/data/`

### `Agent 01` (Scripps Data Architect)
**Directive:** You own the core oceanographic signals.
- **Task:** Build Python/PySpark scripts to ingest the **CalCOFI CSV**, **Keeling Curve CO2** data, and the **Scripps Pier** live feed in `threshold/data/ingestion/`.

### `Agent 02` (NOAA/NASA Data Architect)
**Directive:** You own global remote sensing signals.
- **Task:** Connect to the **NOAA ERDDAP API**, **NOAA Coral Reef Watch REST API**, and **NASA Ocean Color OPeNDAP**.

### `Agent 03` (Humanitarian Data Architect)
**Directive:** You own the historical and financial disaster facts.
- **Task:** Connect to the **OCHA FTS API**, **HDX API**, **World Bank CSVs**, and **EM-DAT** datasets.

### `Agent 04` (Snowflake Warehouse Lead)
**Directive:** You bridge Databricks to the rest of the application.
- **Task:** Establish the Snowflake connection. Design the final relational schema for the FastAPI backend and ML models to query.

---

## 🧠 INTELLIGENCE & ML LAYER (Agents 05-08) - Located in `threshold/ml/`

### `Agent 05` (Lead Applied Scientist - Classifier)
**Directive:** Build the Threshold Proximity Score.
- **Task:** Train an **XGBoost Classifier** in `threshold/ml/models/tipping_point_classifier.py` to detect signatures that precede an ecological collapse.

### `Agent 06` (Time-Series Scientist - Forecaster)
**Directive:** Build the Countdown.
- **Task:** Train a **Prophet / LSTM** model on historical trends to predict the exact "Days to Threshold" crossing date.

### `Agent 07` (Econometrics Scientist - Counterfactuals)
**Directive:** Build the cost model.
- **Task:** Use **SciKit-Learn Regression** mapped against EM-DAT data to calculate the dollar cost of "Late Recovery" vs. "Early Intervention".

### `Agent 08` (LLM Engineer - The Crisis Auditor)
**Directive:** You own the semantic text analysis.
- **Task:** Route the **ReliefWeb** and **GDELT** feeds into **Google Gemini 1.5 Flash** for sentiment analysis comparing crisis severity against media excitement.

---

## ⚙️ BACKEND & CLOUD LAYER (Agents 09-12) - Located in `threshold/backend/`

### `Agent 09` (Backend Lead - FastAPI Core)
**Directive:** Stand up the backend infrastructure.
- **Task:** Maintain the Python FastAPI server in `threshold/backend/main.py`. Setup CORS, routing context, database connections (`database.py`), and configuration (`config.py`).

### `Agent 10` (API Developer - Region Triage)
**Directive:** Serve the core ML data.
- **Task:** Build `<GET> /api/regions` mapping to `routers/regions.py` and implement the triage logic in `routers/triage.py`.

### `Agent 11` (API Developer - Charity Verification)
**Directive:** Identify the actors.
- **Task:** Build the API pipelines connecting to **Charity Navigator**, **GlobalGiving**, and **ReliefWeb 3W** in `routers/charities.py`.

### `Agent 12` (API Developer - News & NLP Stream)
**Directive:** Serve the news feeds.
- **Task:** Create logic in `routers/news.py` to stream structured Gemini sentiment and media news headlines. Also manage the counterfactual endpoint logic in `routers/counterfactual.py`.

---

## 💸 WEB3 & PAYMENTS LAYER (Agents 13-15) - Located in `threshold/blockchain/` & `threshold/backend/`

### `Agent 13` (Web3 Dev - Solana Payouts)
**Directive:** Handle crypto routing.
- **Task:** Maintain the compiled Rust smart contracts in `threshold/blockchain/programs/threshold_fund/src/lib.rs` and the Node interaction script at `threshold/blockchain/client/interact.js`.

### `Agent 14` (FinTech Dev - Stripe Routing)
**Directive:** Handle traditional fiat routing.
- **Task:** Integrate the **Stripe Connect API** in `threshold/backend/routers/fund.py` to allow users to "Fund" a threshold gap directly.

### `Agent 15` (Compliance Dev - Grassroots KYC)
**Directive:** Ensure local funds don't go to bad actors.
- **Task:** Build the **Grassroots KYC Protocol** logic in `routers/funding.py` and `charities.py`, comparing GlobalGiving data against local operational tags.

---

## 🖥️ FRONTEND LAYER (Agents 16-19) - Located in `threshold/frontend/`

### `Agent 16` (Frontend Lead - React/Vite Core)
**Directive:** Establish the War Room layout.
- **Task:** Maintain the Vite/React app logic in `threshold/frontend/src/App.jsx`. Manage **Tailwind CSS** configurations and routing pages (`Home.jsx`, `FundPage.jsx`, etc.).

### `Agent 17` (WebGL Engineer - The Globe)
**Directive:** Build the Hackathon "Wow" Factor.
- **Task:** Implement `WarRoomGlobe.jsx`, mapping pulsing, color-coded spikes based on the "Threshold Proximity Score." 

### `Agent 18` (Data Viz Engineer - Dashboard & Scrubbers)
**Directive:** Tell the story.
- **Task:** Build the `TriageQueue.jsx` components and the `FundingGapRadar.jsx` interactive visualizations using D3/Recharts.

### `Agent 19` (Frontend Dev - Payments UI)
**Directive:** Close the loop.
- **Task:** Build the `FundDashboard.jsx` UI. Handle the Stripe Checkout UI redirects and the live ledger showing Solana transaction hashes.

---

## 🚀 DEVOPS & INTEGRATION (Agent 20) - Located in `threshold/` ROOT

### `Agent 20` (DevOps Lead)
**Directive:** Keep the swarm online and deployed.
- **Task:** Manage `threshold/docker-compose.yml`, write any GitHub Actions, and deploy the entire multi-container stack. Keep everything highly available for hackathon judging.
