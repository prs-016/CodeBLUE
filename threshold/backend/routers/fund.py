from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
from ..database import get_db

router = APIRouter()

@router.post("/rounds")
def create_funding_round(db: Session = Depends(get_db)):
    """Admin: creates new funding round when threshold triggered"""
    return {"status": "success", "message": "Manual creation is locked in demo mode."}
    
@router.get("/transactions", response_model=List[Dict[str, Any]])
def get_transactions(db: Session = Depends(get_db)):
    """Returns all on-chain transactions with Solana hashes"""
    # Mocking Solana transactions
    return [
        {"hash": "5dJqXp...", "round_id": "FR_001", "amount_usd": 500, "timestamp": "2025-01-01T12:00:00Z"},
        {"hash": "8pLvZm...", "round_id": "FR_002", "amount_usd": 1500, "timestamp": "2025-01-02T14:30:00Z"}
    ]
    
@router.post("/disburse/{round_id}/{tranche}")
def trigger_disbursement(round_id: str, tranche: int, db: Session = Depends(get_db)):
    """Admin: triggers disbursement, calls Solana service"""
    return {"status": "success", "round_id": round_id, "tranche": tranche, "solana_tx": "mock_tx_hash"}
    
@router.get("/transparency", response_model=Dict[str, Any])
def get_transparency_ledger(db: Session = Depends(get_db)):
    """Returns full transaction ledger for public transparency page"""
    return {
        "total_volume_usd": 15000000,
        "total_transactions": 24501,
        "smart_contract_address": "ThResH1...9zQ2",
        "recent_blocks": []
    }
