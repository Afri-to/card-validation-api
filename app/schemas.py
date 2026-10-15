"""Request and response models for the API."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.brands import Brand
from app.models import TransactionStatus
from app.validation import ErrorCode


class ValidateRequest(BaseModel):
    # max_length stops someone posting megabytes of text at the endpoint.
    number: str = Field(..., max_length=64, examples=["4111 1111 1111 1111"])


class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str


class ValidateResponse(BaseModel):
    valid: bool
    brand: Brand | None
    luhn_valid: bool
    masked_number: str | None = Field(
        None, description="Last 4 digits only. The full number is never returned."
    )
    errors: list[ErrorDetail]


class TransactionCreate(BaseModel):
    card_number: str = Field(..., max_length=64, examples=["4111 1111 1111 1111"])
    amount: Decimal = Field(..., max_digits=12, decimal_places=2, examples=["25.00"])
    currency: str = Field(..., pattern=r"^[A-Z]{3}$", examples=["USD"])


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    masked_card: str
    brand: Brand
    amount: Decimal
    currency: str
    status: TransactionStatus
    created_at: datetime
