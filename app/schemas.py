"""Request and response models for the API."""

from pydantic import BaseModel, Field

from app.brands import Brand
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
