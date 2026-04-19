from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from config import settings


class SolanaService:
    def record(
        self,
        db: Session,
        *,
        round_id: str,
        amount_usdc: float,
        tranche: int,
        memo: str,
        to_wallet: str = "verified-charity-wallet",
    ) -> dict:
        tx_hash = f"sol_{uuid.uuid4().hex}"
        timestamp = datetime.now(timezone.utc).isoformat()
        db.execute(
            text(
                """
                INSERT INTO solana_transactions (
                    tx_hash, from_wallet, to_wallet, amount_usdc, memo,
                    round_id, tranche, timestamp, status
                ) VALUES (
                    :tx_hash, :from_wallet, :to_wallet, :amount_usdc, :memo,
                    :round_id, :tranche, :timestamp, :status
                )
                """
            ),
            {
                "tx_hash": tx_hash,
                "from_wallet": settings.solana_program_id,
                "to_wallet": to_wallet,
                "amount_usdc": amount_usdc,
                "memo": memo,
                "round_id": round_id,
                "tranche": tranche,
                "timestamp": timestamp,
                "status": "confirmed",
            },
        )
        return {"tx_hash": tx_hash, "status": "confirmed"}


solana_service = SolanaService()
