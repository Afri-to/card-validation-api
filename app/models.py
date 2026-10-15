"""Database tables."""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import CheckConstraint, DateTime, Index, Numeric, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.brands import Brand
from app.db import Base


class TransactionStatus(str, Enum):
    APPROVED = "approved"
    DECLINED = "declined"
    FLAGGED = "flagged"


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("currency ~ '^[A-Z]{3}$'", name="currency_iso_format"),
        Index("ix_duplicate_lookup", "card_fingerprint", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Only the masked number is stored ("**** 1111"). The full number never is.
    masked_card: Mapped[str] = mapped_column(String(9))
    # Keyed hash (HMAC-SHA256) of the full number: lets us spot repeats of the
    # same card without being able to recover the number from the database.
    card_fingerprint: Mapped[str] = mapped_column(String(64))
    brand: Mapped[Brand] = mapped_column(SAEnum(Brand, name="card_brand"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[TransactionStatus] = mapped_column(
        SAEnum(TransactionStatus, name="transaction_status"), index=True
    )
    reason: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
