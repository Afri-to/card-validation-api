"""/transactions endpoints: record and list mock transactions."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Transaction, TransactionStatus
from app.schemas import TransactionCreate, TransactionOut
from app.validation import MESSAGES, validate_card

router = APIRouter(prefix="/transactions", tags=["transactions"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(payload: TransactionCreate, db: DbSession) -> Transaction:
    """Validate the card, then record a mock transaction with the card masked."""
    check = validate_card(payload.card_number)
    if not check.valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "errors": [{"code": c, "message": MESSAGES[c]} for c in check.errors]
            },
        )

    transaction = Transaction(
        masked_card=check.masked_number,
        brand=check.brand,
        amount=payload.amount,
        currency=payload.currency,
        status=TransactionStatus.APPROVED,
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
