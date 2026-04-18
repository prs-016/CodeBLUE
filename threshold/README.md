# THRESHOLD 
**A Three-Horizon Climate Crisis Intelligence Platform**  
*Built by Code Blue for DataHacks 2025*

```text
Build the tool. Find the window. Close the gap.
```

## Overview
THRESHOLD predicts impending ecological tipping points, quantifies the intervention cost window, and automatically provisions a transparent, on-chain funding pipeline when an anomaly is detected.

### Sponsor Challenge Implementations
We have integrated the core sponsor requirements natively into our pipeline:
1. **Scripps Data**: Our foundation runs entirely on Scripps datasets (Keeling + CalCOFI).
2. **Databricks**: Ingestion pipeline powered by PySpark notebooks.
3. **Snowflake**: End-to-end data lake / warehouse utilizing Snowflake APIs.
4. **AWS**: Data assets managed securely in S3; models leverage SageMaker infrastructure.
5. **Marimo & Sphinx**: High-fidelity Marimo ML notebooks paired with comprehensive Sphinx docs.

## Setup Instructions

### Prerequisites
- Docker & Docker Compose
- Node.js (v18+) for local UI dev
- Python 3.10+

### Quick Start (Full Stack)
```bash
# 1. Clone repository
git clone <url> && cd threshold

# 2. Setup Environment Variables
cp .env.example .env
# Edit .env to add keys

# 3. Startup Services
docker-compose up --build
```
> **Note**: For the demo execution without active Snowflake credentials, our database adapter gracefully falls back to synthetic data mocks generated instantly on startup.

## Architecture Highlights
- **Frontend**: React + Vite, Globe.gl (3D Visuals), TailwindCSS, D3.js timelines.
- **Backend**: FastAPI with async Python, scalable endpoints formatting ML proxy outputs.
- **Data/ML**: Scikit-Learn / Prophet tipping classifiers wrapped via AWS interfaces + Marimo analytics.
- **Blockchain**: Solana transparent impact fund registry + Stripe on-ramps.
