from __future__ import annotations
from typing import Optional

import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from config import settings


class StripeService:
    def create_payment_intent(
        self,
        db: Session,
        *,
        round_id: str,
        amount_usd: float,
        donor_email: Optional[str],
    ) -> dict:
        payment_intent_id = f"pi_{uuid.uuid4().hex[:24]}"
        donor_hash = (
            hashlib.sha256(donor_email.lower().encode("utf-8")).hexdigest()
            if donor_email
            else None
        )
        created_at = datetime.now(timezone.utc).isoformat()
        status = "requires_confirmation" if settings.stripe_secret_key else "succeeded"
        db.execute(
            text(
                """
                INSERT INTO stripe_transactions (
                    payment_intent_id, amount_usd, donor_email_hash, round_id, status, created_at
                ) VALUES (
                    :payment_intent_id, :amount_usd, :donor_email_hash, :round_id, :status, :created_at
                )
                """
            ),
            {
                "payment_intent_id": payment_intent_id,
                "amount_usd": amount_usd,
                "donor_email_hash": donor_hash,
                "round_id": round_id,
                "status": status,
                "created_at": created_at,
            },
        )
        return {
            "id": payment_intent_id,
            "status": status,
            "amount_usd": amount_usd,
        }


stripe_service = StripeService()
