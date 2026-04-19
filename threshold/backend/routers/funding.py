from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from models.funding import (
    ContributionRequest,
    ContributionResponse,
    FundingGapItem,
    FundingImpactItem,
    FundingRoundDetail,
    FundingRoundSummary,
)
from services.solana_service import solana_service
from services.stripe_service import stripe_service


router = APIRouter()


@router.get(
    "/gap",
    response_model=list[FundingGapItem],
    summary="Get funding gap radar data",
)
def get_funding_gap_radar(db: Session = Depends(get_db)) -> list[FundingGapItem]:
    rows = db.execute(
        text(
            """
            SELECT
                r.id AS region_id,
                r.name,
                r.current_score AS threshold_score,
                r.funding_gap,
                r.primary_threat AS threat_type,
                r.population_affected,
                ma.attention_gap,
                ROUND(
                    COALESCE(fr.raised_amount / NULLIF(fr.target_amount, 0), 0.0),
                    4
                ) AS coverage_ratio
            FROM regions r
            LEFT JOIN media_attention ma ON ma.region_id = r.id
            LEFT JOIN funding_rounds fr ON fr.region_id = r.id AND fr.status = 'active'
            ORDER BY r.current_score DESC
            """
        )
    ).fetchall()
    return [FundingGapItem(**dict(row._mapping)) for row in rows]


@router.get(
    "/rounds",
    response_model=list[FundingRoundSummary],
    summary="List funding rounds",
)
def get_funding_rounds(db: Session = Depends(get_db)) -> list[FundingRoundSummary]:
    rows = db.execute(
        text(
            """
            SELECT
                fr.id, fr.region_id, r.name AS region_name, fr.title, fr.target_amount,
                fr.raised_amount, fr.status, fr.deadline, fr.cost_multiplier,
                r.primary_threat AS threat_type
            FROM funding_rounds fr
            JOIN regions r ON r.id = fr.region_id
            ORDER BY fr.status ASC, fr.deadline ASC
            """
        )
    ).fetchall()
    return [FundingRoundSummary(**dict(row._mapping)) for row in rows]


@router.get(
    "/rounds/{round_id}",
    response_model=FundingRoundDetail,
    summary="Get funding round details",
)
def get_funding_round(round_id: str, db: Session = Depends(get_db)) -> FundingRoundDetail:
    row = db.execute(
        text(
            """
            SELECT
                fr.id, fr.region_id, r.name AS region_name, fr.title, fr.target_amount,
                fr.raised_amount, fr.status, fr.deadline, fr.cost_multiplier,
                r.primary_threat AS threat_type, fr.partner_ein, c.name AS partner_name
            FROM funding_rounds fr
            JOIN regions r ON r.id = fr.region_id
            LEFT JOIN charity_registry c ON c.ein = fr.partner_ein
            WHERE fr.id = :round_id
            """
        ),
        {"round_id": round_id},
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Funding round not found")
    data = dict(row._mapping)
    data["remaining_gap"] = round(data["target_amount"] - data["raised_amount"], 2)
    return FundingRoundDetail(**data)


@router.post(
    "/rounds/{round_id}/contribute",
    response_model=ContributionResponse,
    summary="Create a contribution",
)
def post_contribute(
    round_id: str,
    payload: ContributionRequest = Body(...),
    db: Session = Depends(get_db),
) -> ContributionResponse:
    funding_round = db.execute(
        text("SELECT id, raised_amount, title FROM funding_rounds WHERE id = :round_id"),
        {"round_id": round_id},
    ).fetchone()
    if funding_round is None:
        raise HTTPException(status_code=404, detail="Funding round not found")

    payment_intent = stripe_service.create_payment_intent(
        db,
        round_id=round_id,
        amount_usd=payload.amount_usd,
        donor_email=payload.donor_email,
    )
    solana_record = solana_service.record(
        db,
        round_id=round_id,
        amount_usdc=payload.amount_usd,
        tranche=0,
        memo=f"{funding_round.title.replace(' ', '_')}_contribution",
    )
    db.execute(
        text(
            """
            UPDATE funding_rounds
            SET raised_amount = raised_amount + :amount
            WHERE id = :round_id
            """
        ),
        {"amount": payload.amount_usd, "round_id": round_id},
    )
    db.commit()
    return ContributionResponse(
        status="success",
        round_id=round_id,
        amount_usd=payload.amount_usd,
        stripe_payment_intent=payment_intent["id"],
        stripe_status=payment_intent["status"],
        blockchain_hash=solana_record["tx_hash"],
        blockchain_status=solana_record["status"],
    )


@router.get(
    "/impact",
    response_model=list[FundingImpactItem],
    summary="Get impact registry records",
)
def get_impact_registry(db: Session = Depends(get_db)) -> list[FundingImpactItem]:
    rows = db.execute(
        text(
            """
            SELECT case_id, region_id, event_name, prevention_cost, recovery_cost, cost_multiplier
            FROM counterfactual_cases
            ORDER BY cost_multiplier DESC
            """
        )
    ).fetchall()
    return [FundingImpactItem(**dict(row._mapping)) for row in rows]
