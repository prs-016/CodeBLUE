# THRESHOLD (Code Blue) 🌊

[![Frontend](https://img.shields.io/badge/Frontend-Next.js%2014-black?style=flat-square)](https://nextjs.org/)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square)](https://fastapi.tiangolo.com/)
[![Machine Learning](https://img.shields.io/badge/ML-PyTorch%20%7C%20ThresholdNet-EE4C2C?style=flat-square)](https://pytorch.org/)
[![Data Engineering](https://img.shields.io/badge/Data-Snowflake%20%7C%20Databricks-29B5E8?style=flat-square)](https://www.snowflake.com/)
[![Web3](https://img.shields.io/badge/Web3-Solana-14F195?style=flat-square)](https://solana.com/)
[![Compute](https://img.shields.io/badge/Compute-NVIDIA%20T4%20%7C%20Brev.dev-76B900?style=flat-square)](https://brev.dev/)

[**Live Platform Instance (AWS ALB)**](http://thresh-thres-s7ll4ymkr84z-1480452347.us-west-2.elb.amazonaws.com/)

> **Every climate crisis has a point of no return. We find it before you cross it.**

THRESHOLD is a proactive climate crisis intelligence platform acting as the Bloomberg Terminal for Climate Aid.

## The Problem
Climate charity is fundamentally broken. It operates on an emotional, media-driven cycle: a crisis builds invisibly in ocean data for years, the ecological threshold is crossed, the media finally covers the visible human suffering, and donations pour in. By that time, the cost to recover is 10x higher than the cost of prevention. 

*Funding follows cameras, not data.*

## The Solution
THRESHOLD calculates a visceral **"Days to Threshold"** countdown by piping oceanographic warning signals (Scripps Institution of Oceanography) directly into our proprietary `ThresholdNet` PyTorch model. It exposes the gap between actual, scientific risk and committed humanitarian funding. 

When a region enters a critical intervention window, the platform opens a direct **Stripe/Solana** funding loop to route capital immediately to verified global and grassroots NGOs on the ground—bypassing traditional bureaucracy.

## Hackathon Goal Paths
- 🏆 **Primary Track**: Data Analytics 
- 🏆 **Secondary Track**: Machine Learning / AI
- 🎯 **Sponsor Challenges**: Scripps Institute of Oceanography, Databricks, Snowflake, AWS, Solana.

---

## Technical Stack & Architecture

THRESHOLD operates on a complex, low-latency ingestion pipeline connecting 20 distinct APIs and data sources across four pillars, warehoused in **Snowflake** and orchestrated via **Databricks**.

### Machine Learning: `ThresholdNet` & NVIDIA Brev.dev
At the core of THRESHOLD is `ThresholdNet`, a custom deep learning architecture combining LSTM and Multi-Head Attention mechanisms to predict the `threshold_proximity_score`. 

#### **Training Infrastructure**
* **Compute Environment**: [Brev.dev](https://brev.dev/) instances running **NVIDIA T4 GPUs** (`g4dn.xlarge`). We leverage `torch.compile` (PyTorch 2.x) and mixed precision (`torch.amp.autocast`) for maximal hardware utilization.
* **Environment Image**: `nvcr.io/nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04`

#### **Data Pipeline & Temporal Validation**
* **Sliding Window Validation**: We utilize a highly robust 30-timestep sliding window dataset with stride 1 over 3,296 continuous rows spanning 8 distinct global regions (e.g., Great Barrier Reef, California Current, Arabian Sea).
* **Holdout Strategy**: Cross-Region Temporal Holdout (85% Train / 10% Validation / 5% Test) ensuring zero future-data leakage.
* **Loss & Optimization**: Optimized via `HuberLoss` (smooth L1 for robustness to ecosystem anomalies) with `AdamW` and `CosineAnnealingLR` (T_max=100, eta_min=1e-6).

#### **Model Features & Target Metrics**
The model ingests multivariate time-series features directly from Snowflake (`COMPUTE_WH` warehouse):
* `sst_anomaly` (°C above baseline)
* `o2_current` (ml/L dissolved O2)
* `dhw_current` (°C-weeks)
* `bleaching_alert_level` (0-4 CRW scale)
* `co2_regional_ppm` (ppm atmospheric CO₂)
* `chlorophyll_anomaly` (mg/m³ anomaly)
* `nitrate_anomaly` (µmol/L anomaly)
* `conflict_index` (0-1 GDELT Goldstein anomaly)

**Metrics Target**: The primary evaluation metric optimizing network weights is **Validation MAE** (Mean Absolute Error) of the days-to-threshold proximity, dynamically recalibrated via Early Stopping logic (patience = 15 epochs).

---

## The Architecture (20 Datasets & APIs)

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
* **Google Gemini 2.0 Pro/Flash**: Employed for Crisis NLP Auditing to map qualitative crisis reports into structured risk modifiers.

### 4. Charity & Payments (The Loop)
* `Charity Navigator API`
* `GlobalGiving API` (Grassroots NGOs)
* `ReliefWeb 3W Database`
* `GiveWell Impact Metrics`
* `Stripe Connect` (Fiat Payouts)
* `Solana Web3.js` (USDC Wallet Payouts on Devnet/Mainnet)
* `Grassroots KYC Protocol`

## Software Stack
- **Frontend**: Next.js 14, Tailwind CSS, Globe.gl (3D War Room), D3.js.
- **Backend**: Python (FastAPI).
- **Machine Learning Engine**: PyTorch, XGBoost, Prophet, SciKit-Learn Regression.
- **Data Engineering**: Databricks (Ingestion), Snowflake (Warehousing).
- **Web3 Payments**: Solana Devnet / Mainnet.

## How to Run Locally

### Brev.dev Training
You can rapidly launch the training environment via Brev.dev:
```bash
brev open threshold-train
# Environment will auto-configure via brev.yaml with Snowflake variables and JupyterLab
```

*(Local application build instructions to be populated post-build)*

---
*Built with ❤️ for the Earth by Team Code Blue.*
