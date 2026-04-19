# THRESHOLD

THRESHOLD is Code Blue's three-horizon climate crisis intelligence platform for DataHacks 2026. This repo is being built in parallel, so some modules are already functional while others are still moving from scaffold to full implementation.

## Current shape

- `frontend/`: React + Vite interface for the globe, triage queue, region briefs, and fund flows.
- `backend/`: FastAPI API layer serving region, funding, news, and counterfactual endpoints.
- `data/`: ingestion and synthetic-data jobs.
- `blockchain/`: Solana devnet / Anchor-friendly funding ledger scaffold and client scripts.
- `docs/`: Sphinx docs for setup and architecture.

## Quick start

1. Copy the environment template:

```bash
cp .env.example .env
```

2. Start the local app stack:

```bash
docker compose up --build
```

3. Open:

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:8000](http://localhost:8000)
- OpenAPI: [http://localhost:8000/api/v1/openapi.json](http://localhost:8000/api/v1/openapi.json)

## Blockchain modes

The blockchain scaffold is intentionally safe for local development.

- `THRESHOLD_CHAIN_MODE=mock`
  Default. Client scripts return structured mock responses and the app can boot without Solana credentials.
- `THRESHOLD_CHAIN_MODE=devnet`
  Uses Solana devnet and Anchor-compatible account layouts. Requires `SOLANA_PROGRAM_ID` and a funded devnet keypair.

## Solana / Anchor setup

Prerequisites:

- Rust toolchain
- Solana CLI
- Anchor CLI
- Node.js 20+

Recommended local flow:

```bash
cp .env.example .env
solana-keygen new -o blockchain/keypairs/threshold-devnet.json
solana config set --url https://api.devnet.solana.com
solana airdrop 2 $(solana-keygen pubkey blockchain/keypairs/threshold-devnet.json)
```

Then set:

```bash
THRESHOLD_CHAIN_MODE=devnet
SOLANA_KEYPAIR_PATH=./blockchain/keypairs/threshold-devnet.json
ANCHOR_WALLET=./blockchain/keypairs/threshold-devnet.json
```

Useful commands:

```bash
cd blockchain
npm install
node client/interact.js health
node client/deploy.js validate-env
```

## Docker services

- `backend`: FastAPI server
- `frontend`: Vite dev server
- `data_pipeline`: optional ingestion container via `--profile data`
- `blockchain_client`: optional chain smoke test via `--profile blockchain`

Examples:

```bash
docker compose --profile data up data_pipeline
docker compose --profile blockchain up blockchain_client
```

## Notes

- The backend and frontend containers are designed for local development and live reload.
- Missing chain credentials do not block app startup.
- The Anchor program in `blockchain/` is scaffolded for devnet iteration and integration with a later backend service layer.

## Docs

Build the Sphinx docs locally:

```bash
python -m sphinx -b html docs docs/_build
```

See [docs/index.rst](/Users/divyanshkanodia/Desktop/CodeBLUE/threshold/docs/index.rst) for the table of contents.
