# THRESHOLD: The 18 Datasets & Execution Roadmap

To build the uncompromised **THRESHOLD** architecture, your 20 subagents must connect exactly 18 distinct data sources, process them through Databricks, and warehouse them in Snowflake. 

Here is the exact dataset inventory, required APIs, and the step-by-step master roadmap.

---

## Part 1: The 18 Critical Datasets & APIs

### 🌊 Ocean Science & Climate (The Signal)
1. **Keeling Curve (Atmospheric CO2)**: Daily measurements from Mauna Loa. Provides the macro stress amplifier. *(Access: Scripps CSV downloads)*
2. **CalCOFI (Ocean Metrics)**: Temperature, salinity, oxygen, nutrients from 1949–present. The core historical training set for the ML model. *(Access: Kaggle or CalCOFI.org CSV/NetCDF)*
3. **Scripps Pier Observatory**: Real-time sensor readings for coastal data. Powers the live "Present Horizon" dashboard for the California Coast. *(Access: EcoObs UCSD API/CSV)*
4. **NOAA ERDDAP**: Global Sea Surface Temperature anomalies. Enables scaling the ML model globally outside of the CalCOFI Pacific region. *(Access: NOAA ERDDAP REST API)*
5. **NOAA Coral Reef Watch**: Degree Heating Weeks (DHW) and bleaching alert levels. *(Access: NOAA REST API)*
6. **NASA Ocean Color**: Chlorophyll-A concentrations tracking hypoxic dead zones. *(Access: NASA Earthdata OPeNDAP/API)*

### 💰 Humanitarian & Financial (The Gap)
7. **OCHA Financial Tracking System (FTS)**: Tracks every humanitarian donation worldwide. Computes the "Funding Gap." *(Access: FTS REST API)*
8. **HDX (Humanitarian Data Exchange)**: "People in Need vs Funds Required" dataset. Calibrates the required intervention target amounts. *(Access: HDX CKAN API)*
9. **World Bank Climate Disaster Data**: Economic impact ($) of past disasters. Powers the Counterfactual Cost Estimator. *(Access: World Bank API)*
10. **EM-DAT (Emergency Events Database)**: Deaths, affected populations, and total economic loss from global disasters. *(Access: EM-DAT CSV export)*

### 📰 Media & News (The Buzz)
11. **ReliefWeb**: The UN's humanitarian situation reports mapping what is happening *now*. *(Access: ReliefWeb REST API)*
12. **GDELT Project**: Real-time print/broadcast media scraped for climate events. Generates the "Media Attention Score" to prove the "Funding follows cameras" thesis. *(Access: GDELT Event Database / JSON API)*
13. **NASA/NOAA Press Releases**: Structured announcements for marine heatwaves or scientific events. Confirms threshold crossings. *(Access: RSS Feeds)*

### 🏥 Charity Verification (The Actors)
14. **Charity Navigator**: Evaluates charity financial health and transparency so funds go to safe hands. *(Access: Charity Navigator API)*
15. **ReliefWeb 3W Database**: "Who does What Where" maps charities to physical operating regions (e.g. WorldFish in Mekong). *(Access: ReliefWeb API)*
16. **GiveWell Research Data**: Calculates the true "Impact Multiplier" (e.g., $1 saves X ecosystems). *(Access: GiveWell Public Data Tables)*

### 🔗 Execution & Transparency (The Loop)
17. **Stripe**: The payment processor. Takes the user's money to close the funding gap. *(Access: Stripe API)*
18. **Solana Blockchain**: The transparency ledger. Logs the transaction immutably to prove the funds were deployed to the verified charity. *(Access: Solana Web3.js / RPC Nodes)*

---

## Part 2: Step-by-Step Execution Plan for the Subagents

Assign your 20 subagents to the following sequence. **Do not move to the next step until the prior is complete.**

### STEP 1: API Key Acquisition & Secrets Management
- Register and generate API keys for: `NewsAPI`, `Google Gemini 1.5`, `Stripe`, `Charity Navigator`, and `ReliefWeb`.
- Set up a Solana Devnet wallet and save the RPC endpoint keys.
- Write a `.env` file in the root backend directory storing all keys.

### STEP 2: The Databricks Ingestion Layer
- **Objective:** Extract and load the raw data.
- **Action:** Write Python scripts (Pandas / PySpark) to download the static CSVs (CalCOFI, EM-DAT, HDX) and write API polling scripts to fetch the live data (ERDDAP, GDELT, OCHA).
- **Output:** Push all raw unstructured data into Databricks Delta Tables.

### STEP 3: Feature Engineering & Snowflake Warehousing
- **Objective:** Join the disparate data into ML-ready formats.
- **Action:** Build a pipeline that normalizes Scripps data (Temperature, Salinity, O2) and joins it chronologically with World Bank disaster costs.
- **Output:** Push clean, flat tables into **Snowflake**: `region_stress_indicators`, `historical_cases`, `funding_gap_index`.

### STEP 4: The 3 ML Models (Google Gemini & Python)
- **Model 1 (Classifier):** Train an XGBoost model on CalCOFI data to output a `Threshold Proximity Score (0-10)` predicting dead zones / bleaching.
- **Model 2 (Forecaster):** Train a Facebook Prophet (or LSTM) model on the Time Series data to project the `Days to Threshold` crossing date.
- **Model 3 (Counterfactual):** Use SciKit-Learn Regression mapping EM-DAT damage costs to early Scripps indicator signals. 
- **LLM Pipeline:** Feed GDELT and ReliefWeb articles into **Gemini 1.5 Flash** to extract structured JSON summaries of the "Crisis Vibe" and media tone.

### STEP 5: Backend Assembly (FastAPI)
- **Objective:** Serve the Data to the Frontend.
- **Action:** Create `GET /api/regions` (returns threshold scores), `GET /api/region/{id}` (full drill-down), and `GET /api/funding-gap` (OCHA vs ML prediction).
- **Action:** Create the `POST /api/fund` endpoint integrating the Stripe API checkout session and firing a Solana Web3.js transaction hash to the chain upon success.

### STEP 6: Frontend Development (Next.js)
- **Action:** Scaffold the Next.js App Router workspace.
- **Globe.gl Component:** Hook up the 3D War Room Globe to hit `GET /api/regions` and globally plot pulsing red/orange nodes based on the proximity score.
- **Triage Queue Component:** Build the ranked table sorting regions by Days to Threshold.
- **Counterfactual Timeline Component:** Use D3.js or Recharts to build timeline scrubbers for the Historical Case Studies.
- **Charity Funding UI:** Build the "Donate to Close Gap" UI, featuring the Stripe checkout portal and the live Solana transaction ledger underneath.

### STEP 7: E2E Integration Testing
- Start the FastAPI backend.
- Start the Next.js frontend.
- Click a region on the globe -> Select "Deploy $10k to WorldFish" -> Follow the Stripe Sandbox flow -> Verify the Solana transaction hash appears on the UI.
