Architecture
============

THRESHOLD is split into four major runtime domains:

Frontend
--------

- React + Vite
- Globe, triage, funding, and regional intelligence interfaces

Backend
-------

- FastAPI application
- Serves region, funding, charity, counterfactual, and fund APIs
- Uses SQLite for local development today

Data
----

- Ingestion scripts and synthetic data generation
- Separate container profile for long-running or on-demand data refresh jobs

Blockchain
----------

- Solana devnet-oriented funding ledger scaffold
- Anchor-compatible on-chain account model
- Node client scripts that can run in ``mock`` mode when credentials are absent
