"""/transactions endpoints: record and list mock transactions."""

import uuid
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.luhn import normalize_number
from app.models import Transaction, TransactionStatus
from app.rules import card_fingerprint, decide
from app.schemas import TransactionCreate, TransactionOut
from app.validation import MESSAGES, validate_card

router = APIRouter(prefix="/transactions", tags=["transactions"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(payload: TransactionCreate, db: DbSession) -> Transaction:
    """Validate the card, apply the business rules, and record the transaction.

    Declined and flagged transactions are still recorded (201): the request
    succeeded, and the status says what happened to the payment.
    """
    check = validate_card(payload.card_number)
    if not check.valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "errors": [{"code": c, "message": MESSAGES[c]} for c in check.errors]
            },
        )

    settings = get_settings()
    fingerprint = card_fingerprint(
        normalize_number(payload.card_number), settings.card_fingerprint_key
    )
    window_start = func.now() - timedelta(seconds=settings.duplicate_window_seconds)
    is_duplicate = db.scalar(
        select(
            select(Transaction.id)
            .where(
                Transaction.card_fingerprint == fingerprint,
                Transaction.amount == payload.amount,
                Transaction.currency == payload.currency,
                Transaction.created_at >= window_start,
            )
            .exists()
        )
    )
    decision = decide(payload.amount, settings.max_approved_amount, is_duplicate)

    transaction = Transaction(
        masked_card=check.masked_number,
        card_fingerprint=fingerprint,
        brand=check.brand,
        amount=payload.amount,
        currency=payload.currency,
        status=decision.status,
        reason=decision.reason.value if decision.reason else None,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    db: DbSession,
    status_filter: Annotated[TransactionStatus | None, Query(alias="status")] = None,
    created_from: Annotated[datetime | None, Query(alias="from")] = None,
    created_to: Annotated[datetime | None, Query(alias="to")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Transaction]:
    """List transactions, newest first, filtered by status and/or date range."""
    if created_from and created_to and created_from > created_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="'from' must be before 'to'.",
        )

    query = select(Transaction).order_by(Transaction.created_at.desc())
    if status_filter:
        query = query.where(Transaction.status == status_filter)
    if created_from:
        query = query.where(Transaction.created_at >= created_from)
    if created_to:
        query = query.where(Transaction.created_at <= created_to)
    return list(db.scalars(query.limit(limit).offset(offset)))


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(transaction_id: uuid.UUID, db: DbSession) -> Transaction:
    transaction = db.get(Transaction, transaction_id)
    if transaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found.")
    return transaction
