# Swarm Agent Delegation Manifest

This document maps the **20 AI Subagents** to their explicit operational tracks to build the THRESHOLD platform simultaneously. By dividing the 20-dataset architecture into atomic units, the swarm can execute the 6-month Series A roadmap in 48 hours.

---

## 🗄️ DATA ENGINEERING LAYER (Agents 01-04)

### `Agent 01` (Scripps Data Architect)
**Directive:** You own the core oceanographic signals.
- **Task:** Build Python/PySpark scripts to ingest the **CalCOFI CSV**, **Keeling Curve CO2** data, and the **Scripps Pier** live observatory feed.
- **Output:** Clean Delta tables loaded into Databricks.

### `Agent 02` (NOAA/NASA Data Architect)
**Directive:** You own global remote sensing signals.
- **Task:** Connect to the **NOAA ERDDAP API**, **NOAA Coral Reef Watch REST API**, and **NASA Ocean Color OPeNDAP**. Extract Global SST anomalies and Degree Heating Weeks (DHW).
- **Output:** Normalized global grid data loaded into Databricks.

### `Agent 03` (Humanitarian Data Architect)
**Directive:** You own the historical and financial disaster facts.
- **Task:** Connect to the **OCHA FTS API**, **HDX API**, **World Bank CSVs**, and **EM-DAT** datasets. Map historical disaster costs and current global humanitarian funding flows.
- **Output:** Clean financial alignment tables loaded into Databricks.

### `Agent 04` (Snowflake Warehouse Lead)
**Directive:** You bridge Databricks to the rest of the application.
- **Task:** Establish the Snowflake connection. Ingest the Delta Tables from Agents 01-03. Design the final relational schema (`region_stress`, `funding_gap`, `historical_events`) for the FastAPI backend and ML models to query.

---

## 🧠 INTELLIGENCE & ML LAYER (Agents 05-08)

### `Agent 05` (Lead Applied Scientist - Classifier)
**Directive:** Build the Threshold Proximity Score.
- **Task:** Pull the CalCOFI and NOAA datasets from Snowflake. Train an **XGBoost Classifier** to detect the multi-variate signature (Temp/O2/Salinity) that precedes an ecological collapse (e.g., hypoxia/coral bleaching). Output a live 0-10 score per region.

### `Agent 06` (Time-Series Scientist - Forecaster)
**Directive:** Build the Countdown.
- **Task:** Train a **Facebook Prophet / LSTM** model on historical oceanographic trends. Predict the exact "Days to Threshold" crossing date for the regions scored by Agent 05.

### `Agent 07` (Econometrics Scientist - Counterfactuals)
**Directive:** Build the cost model.
- **Task:** Use **SciKit-Learn Regression** mapped against EM-DAT and World Bank data to calculate the exact dollar cost of "Late Recovery" vs. "Early Intervention" for the UI's Counterfactual Engine.

### `Agent 08` (LLM Engineer - The Crisis Auditor)
**Directive:** You own the semantic text analysis.
- **Task:** Route the **ReliefWeb API** and **GDELT Media Attention API** feeds into **Google Gemini 1.5 Flash**. Write the prompt logic that parses these feeds into structured JSON comparing "Actual Crisis Severity" against "Media Excitement/Funding."

---

## ⚙️ BACKEND & CLOUD LAYER (Agents 09-12)

### `Agent 09` (Backend Lead - FastAPI Core)
**Directive:** Stand up the backend infrastructure.
- **Task:** Configure the Python FastAPI server in `/backend/app`. Setup CORS, routing middleware, `.env` loading, and the Snowflake connector utility.

### `Agent 10` (API Developer - Region Triage)
**Directive:** Serve the core ML data.
- **Task:** Build `<GET> /api/regions` (returns the global array of Regions + Days to Threshold) and `<GET> /api/region/{id}` (full drill-down stats). Wire directly to Agent 04's Snowflake schema.

### `Agent 11` (API Developer - Charity Verification)
**Directive:** Identify the actors.
- **Task:** Build the API pipelines connecting to **Charity Navigator API**, **GlobalGiving API**, and **ReliefWeb 3W**. Create an internal endpoint that returns an array of verified global/local charities eligible to receive funds for a specific region.

### `Agent 12` (API Developer - News & NLP Stream)
**Directive:** Serve the news feeds.
- **Task:** Create `<GET> /api/intelligence/{region}` which calls Agent 08's Gemini logic on the fly and streams the structured sentiment and media news headlines to the Frontend.

---

## 💸 WEB3 & PAYMENTS LAYER (Agents 13-15)

### `Agent 13` (Web3 Dev - Solana Payouts)
**Directive:** You handle the immediate crypto routing.
- **Task:** Set up `@solana/web3.js` in the backend. Write the logic that takes a target Charity Wallet Address and fires a USDC transfer on Devnet/Mainnet, returning the transaction hash to the frontend.

### `Agent 14` (FinTech Dev - Stripe Routing)
**Directive:** You handle traditional fiat routing.
- **Task:** Integrate the **Stripe Connect API**. Create the `<POST> /api/checkout` session that allows a user to "Fund" a threshold gap, routing fiat directly to the connected bank account of an NGO verified by Agent 11.

### `Agent 15` (Compliance Dev - Grassroots KYC)
**Directive:** Ensure local funds don't go to bad actors.
- **Task:** Build the **Grassroots KYC Protocol** logic. Cross-reference GlobalGiving local NGO ID tags against ReliefWeb geographical data to flag safe, unbanked/grassroots charities for Agent 13's Solana wallet transfers.

---

## 🖥️ FRONTEND LAYER (Agents 16-19)

### `Agent 16` (Frontend Lead - Next.js Core)
**Directive:** Establish the War Room.
- **Task:** Scaffold the Next.js 14 App Router. Configure **Tailwind CSS** and Framer Motion. Build the global layout, navigation, and the dark/neon "Mission Control" aesthetic. 

### `Agent 17` (WebGL Engineer - The Globe)
**Directive:** Build the Hackathon "Wow" Factor.
- **Task:** Implement **Globe.gl** or Three.js in a full-screen Next.js component. Pull data from Agent 10's `/api/regions` and map pulsing, color-coded spikes based on the "Threshold Proximity Score." Include tooltip hovers.

### `Agent 18` (Data Viz Engineer - Dashboard & Scrubbers)
**Directive:** Tell the story.
- **Task:** Build the **Triage Queue Table**. More importantly, build the **Counterfactual Engine** using D3.js—a timeline scrubber where judges can slide through historical disasters (like the Sardine Collapse) to see the money lost.

### `Agent 19` (Frontend Dev - Payments UI)
**Directive:** Close the loop.
- **Task:** Build the **Funding Gap UX**. Include buttons that let users deploy capital to close the gap. Handle the Stripe Checkout UI redirects and build the live **Disbursement Ledger** showing Agent 13's Solana transaction hashes scrolling in real-time.

---

## 🚀 DEVOPS & INTEGRATION (Agent 20)

### `Agent 20` (DevOps Lead)
**Directive:** Keep the swarm online and deployed.
- **Task:** Write the GitHub Actions CI/CD workflows. Deploy the FastAPI backend and Next.js frontend to **AWS** via Vercel or EC2 instance. Resolve cross-agent merge conflicts, verify env vars, and guarantee the demo is 100% bug-free for judging over 24 hours.
