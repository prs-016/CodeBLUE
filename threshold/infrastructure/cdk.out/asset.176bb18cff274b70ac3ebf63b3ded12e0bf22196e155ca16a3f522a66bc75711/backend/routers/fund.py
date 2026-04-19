from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from models.funding import FundingRoundCreateRequest
from models.transaction import DisbursementResponse, FundTransaction, TransparencyLedger
from services.solana_service import solana_service


router = APIRouter()


@router.post(
    "/rounds",
    response_model=dict,
    summary="Create a funding round",
)
def create_funding_round(
    payload: FundingRoundCreateRequest,
    db: Session = Depends(get_db),
) -> dict:
    region = db.execute(
        text("SELECT id, primary_threat FROM regions WHERE id = :region_id"),
        {"region_id": payload.region_id},
    ).fetchone()
    if region is None:
        raise HTTPException(status_code=404, detail="Region not found")
    round_id = f"round_{uuid.uuid4().hex[:10]}"
    db.execute(
        text(
            """
            INSERT INTO funding_rounds (
                id, region_id, title, target_amount, raised_amount, status, deadline,
                cost_multiplier, partner_ein
            ) VALUES (
                :id, :region_id, :title, :target_amount, 0, 'active', :deadline, 1.0, :partner_ein
            )
            """
        ),
        {
            "id": round_id,
            "region_id": payload.region_id,
            "title": payload.title,
            "target_amount": payload.target_amount,
            "deadline": payload.deadline,
            "partner_ein": payload.partner_ein,
        },
    )
    db.commit()
    return {"status": "success", "round_id": round_id}


@router.get(
    "/transactions",
    response_model=list[FundTransaction],
    summary="List fund transactions",
)
def get_transactions(db: Session = Depends(get_db)) -> list[FundTransaction]:
    rows = db.execute(
        text(
            """
            SELECT tx_hash, round_id, tranche, amount_usdc, timestamp, status, from_wallet, to_wallet, memo
            FROM solana_transactions
            ORDER BY timestamp DESC
            """
        )
    ).fetchall()
    return [FundTransaction(**dict(row._mapping)) for row in rows]


@router.post(
    "/disburse/{round_id}/{tranche}",
    response_model=DisbursementResponse,
    summary="Trigger a tranche disbursement",
)
def trigger_disbursement(round_id: str, tranche: int, db: Session = Depends(get_db)) -> DisbursementResponse:
    funding_round = db.execute(
        text("SELECT id, title, raised_amount FROM funding_rounds WHERE id = :round_id"),
        {"round_id": round_id},
    ).fetchone()
    if funding_round is None:
        raise HTTPException(status_code=404, detail="Funding round not found")
    if tranche < 1:
        raise HTTPException(status_code=400, detail="Tranche must be >= 1")

    amount = round(float(funding_round.raised_amount) * (0.5 if tranche == 1 else 0.25), 2)
    solana_record = solana_service.record(
        db,
        round_id=round_id,
        amount_usdc=amount,
        tranche=tranche,
        memo=f"{funding_round.title.replace(' ', '_')}_tranche_{tranche}",
    )
    db.commit()
    return DisbursementResponse(
        status="success",
        round_id=round_id,
        tranche=tranche,
        solana_tx=solana_record["tx_hash"],
        blockchain_status=solana_record["status"],
    )


@router.get(
    "/transparency",
    response_model=TransparencyLedger,
    summary="Get the public transparency ledger",
)
def get_transparency_ledger(db: Session = Depends(get_db)) -> TransparencyLedger:
    summary = db.execute(
        text(
            """
            SELECT
                COALESCE(SUM(amount_usdc), 0) AS total_volume_usd,
                COUNT(*) AS total_transactions
            FROM solana_transactions
            """
        )
    ).fetchone()
    recent_rows = db.execute(
        text(
            """
            SELECT tx_hash, round_id, tranche, amount_usdc, timestamp, status, from_wallet, to_wallet, memo
            FROM solana_transactions
            ORDER BY timestamp DESC
            LIMIT 10
            """
        )
    ).fetchall()
    return TransparencyLedger(
        total_volume_usd=summary.total_volume_usd,
        total_transactions=summary.total_transactions,
        smart_contract_address="threshold-demo-program",
        recent_transactions=[FundTransaction(**dict(row._mapping)) for row in recent_rows],
    )
