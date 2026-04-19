from __future__ import annotations

from pydantic import BaseModel


class FundTransaction(BaseModel):
    tx_hash: str
    round_id: str
    tranche: int
    amount_usdc: float
    timestamp: str
    status: str
    from_wallet: str
    to_wallet: str
    memo: str


class DisbursementResponse(BaseModel):
    status: str
    round_id: str
    tranche: int
    solana_tx: str
    blockchain_status: str


class TransparencyLedger(BaseModel):
    total_volume_usd: float
    total_transactions: int
    smart_contract_address: str
    recent_transactions: list[FundTransaction]
