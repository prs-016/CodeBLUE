# THRESHOLD (Code Blue) 🌊

**Every climate crisis has a point of no return. We find it before you cross it.**

THRESHOLD is a proactive climate crisis intelligence platform acting as the Bloomberg Terminal for Climate Aid. Built for **DataHacks 2026**.

## The Problem
Climate charity is fundamentally broken. It operates on an emotional, media-driven cycle: a crisis builds invisibly in ocean data for years, the ecological threshold is crossed, the media finally covers the visible human suffering, and donations pour in. By that time, the cost to recover is 10x higher than the cost of prevention. 

*Funding follows cameras, not data.*

## The Solution
THRESHOLD calculates a visceral **"Days to Threshold"** countdown by piping oceanographic warning signals (Scripps Institution of Oceanography) directly into Machine Learning models. It exposes the gap between actual, scientific risk and committed humanitarian funding. 

When a region enters a critical intervention window, the platform opens a direct **Stripe/Solana** funding loop to route capital immediately to verified global and grassroots NGOs on the ground—bypassing traditional bureaucracy.

## Hackathon Goal Paths
- 🏆 **Primary Track**: Data Analytics 
- 🏆 **Secondary Track**: Machine Learning / AI
- 🎯 **Sponsor Challenges**: Scripps Institute of Oceanography, Databricks, Snowflake, AWS, Solana.

## The Architecture (20 Datasets & APIs)
THRESHOLD operates on a complex ingestion pipeline connecting 20 distinct APIs and data sources across four pillars.

### 1. Ocean Science (The Signal)
* `Scripps Keeling Curve (CO2)`
* `CalCOFI (Ocean Metrics)`
* `Scripps Pier Observatory`
* `NOAA ERDDAP Global SST`
* `NOAA Coral Reef Watch`
* `NASA Ocean Color`

### 2. Humanitarian & Financial (The Gap)
* `OCHA Financial Tracking System`
* `HDX (People in Need)`
* `World Bank Climate Disaster Data`
* `EM-DAT Historical Disasters`

### 3. Media & News (The Buzz)
* `ReliefWeb API`
* `GDELT Project (Media Attention)`
* `NASA/NOAA Press RSS`

### 4. Charity & Payments (The Loop)
* `Charity Navigator API`
* `GlobalGiving API` (Grassroots NGOs)
* `ReliefWeb 3W Database`
* `GiveWell Impact Metrics`
* `Stripe Connect` (Fiat Payouts)
* `Solana Web3.js` (USDC Wallet Payouts)
* `Grassroots KYC Protocol`

## Technical Stack
- **Frontend**: Next.js 14, Tailwind CSS, Globe.gl (3D War Room), D3.js.
- **Backend**: Python (FastAPI).
- **Machine Learning**: XGBoost, Prophet/LSTM, SciKit-Learn Regression.
- **Artificial Intelligence**: Google Gemini 1.5 Pro/Flash (Crisis NLP Auditing).
- **Data Engineering**: Databricks (Ingestion), Snowflake (Warehousing).
- **Web3**: Solana Devnet / Mainnet.

## How to Run Locally
*(To be populated post-build)*

---
*Built with ❤️ for the Earth by Team Code Blue.*