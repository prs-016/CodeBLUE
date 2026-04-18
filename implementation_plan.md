# Implementation Plan - Project THRESHOLD (Code Blue)

**Code Blue** is building **THRESHOLD**: The Bloomberg Terminal for Climate Aid. We are executing the full, uncompromised vision, integrating 18 unique datasets across ocean science, humanitarian ledgers, and financial infrastructure.

---

## The Core Concept
THRESHOLD calculates a visceral "Days to Threshold" countdown for impending ecological disasters by piping oceanographic warning signals (Scripps) into machine learning models. It exposes the gap between actual risk and committed funding, and provides a direct, blockchain-verifiable conduit to trigger fund deployments to verified NGOs before the window closes.

---

## 1. The 18 Datasets & APIs (The Ingestion Layer)
We will pipe the following 18 datasets through **Databricks** into **Snowflake**:

### 🌊 Ocean Science (The Signal)
1. **Keeling Curve (Atmospheric CO2)**: Scripps CSV dataset
2. **CalCOFI (Ocean Metrics)**: Temperature, salinity, oxygen
3. **Scripps Pier Observatory**: Real-time coastal sensors
4. **NOAA ERDDAP**: Global Sea Surface Temperature anomalies
5. **NOAA Coral Reef Watch**: Bleaching alert levels
6. **NASA Ocean Color**: Hypoxic dead zone tracking

### 💰 Humanitarian & Financial (The Gap)
7. **OCHA Financial Tracking System (FTS)**: Tracks every humanitarian donation worldwide
8. **HDX (Humanitarian Data Exchange)**: People in Need vs Funds Required
9. **World Bank Climate Disaster Data**: Economic impact of past disasters (Counterfactuals)
10. **EM-DAT**: Historical disaster database (Deaths & Loss)

### 📰 Media & News (The Buzz)
11. **ReliefWeb**: UN humanitarian situation reports
12. **GDELT Project**: Real-time news media attention
13. **NASA/NOAA Press Releases**: Structured scientific announcements

### 🏥 Charity Verification (The Actors)
14. **Charity Navigator API**: Charity financial health & transparency
15. **ReliefWeb 3W Database**: Maps charities to operating regions
16. **GiveWell Research Data**: Calculates "Impact Multipliers"

### 🔗 Execution & Transparency (The Loop)
17. **Stripe API**: Payment processing for the THRESHOLD FUND
18. **Solana Blockchain**: On-chain public ledger transparency via Web3.js

---

## 2. The THRESHOLD Engine (The "Brain")
Our Intelligence layer avoids simplifications and runs 3 live Python models + LLM integration:
1. **Tipping Point Classifier**: XGBoost model trained on CalCOFI data to output a Threshold Proximity Score (0–10).
2. **Days to Threshold (DTT) Forecaster**: Facebook Prophet/LSTM time-series model projecting the exact crossing date.
3. **Counterfactual Engine**: SciKit-Learn Regression model mapping EM-DAT damage costs to early Scripps indicators to show the cost of waiting.
4. **Crisis Auditor (Gemini 1.5)**: Feed GDELT and ReliefWeb articles into Google Gemini 1.5 Flash to extract structured JSON sentiment summaries comparing crisis severity vs. media attention.

---

## 3. The "Code Blue" Dashboard (The "UI")
A premium, mission-control Next.js interface:
- **War Room Globe**: A pulsing 3D visualization (Globe.gl) mapping risk nodes globally in real-time.
- **Triage Queue**: A ranked table of global regions sorted by "Days to Threshold" and "Funding Gap."
- **Historical Scrub**: Interactive D3.js timeline scrubbers analyzing true events (California Sardine Collapse, Great Barrier Reef Bleaching, Arabian Sea Dead Zone, Baltic Sea Hypoxia).
- **Disbursement Ledger (THRESHOLD FUND)**: Stripe integration driving real Solana on-chain transactions to verified charities.

---

## Technical Stack Architecture

| Layer | Technology |
| :--- | :--- |
| **Frontend** | Next.js 14+, Tailwind CSS, Framer Motion, Globe.gl, D3.js |
| **Backend** | Python (FastAPI) |
| **LLM** | Google Gemini 1.5 Pro/Flash |
| **Database** | Snowflake (Full Data Warehousing) |
| **Data Flow** | Databricks (Ingestion, Normalization, Feature Engineering) |
| **Web3 / Pay** | True Solana Smart Contracts/Ledger & Stripe Payment API |

---

## Execution Roadmap for Subagents
1. **API Keys & Devnet**: Secure keys for NewsAPI, Gemini, Stripe, Charity Navigator, ReliefWeb, and prepare a Solana Devnet wallet.
2. **Databricks Pipelines**: Ingest all 18 sources into Delta Tables.
3. **Snowflake Feature Store**: Join tables mapping Scripps indicators globally against World Bank financial data.
4. **ML Training**: Build the XGBoost, Prophet, and Regression models.
5. **Backend Assembly**: Complete the FastAPI endpoints for all features.
6. **Next.js UI & Web3**: Build the Globe, the Triage Table, the D3 Scrubbers, and finalize the Stripe-to-Solana fund transfer loop.
