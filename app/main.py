"""Card Validation API: entry point."""

from fastapi import FastAPI

from app.schemas import ErrorDetail, ValidateRequest, ValidateResponse
from app.validation import MESSAGES, validate_card

app = FastAPI(
    title="Card Validation API",
    description=(
        "Validates test payment card numbers and records mock transactions. "
        "Use public test card numbers only."
    ),
    version="0.1.0",
)


@app.get("/health")
def health() -> dict:
    """Liveness check used by CI, Docker and the uptime monitor."""
    return {"status": "ok"}


@app.post("/validate", response_model=ValidateResponse)
def validate(request: ValidateRequest) -> ValidateResponse:
    """Check a card number's characters, brand, length and Luhn checksum.

    A number that fails validation still returns 200: the request worked,
    and the answer is "not valid", with a code for each problem found.
    A malformed request body returns 422.
    """
    result = validate_card(request.number)
    return ValidateResponse(
        valid=result.valid,
        brand=result.brand,
        luhn_valid=result.luhn_valid,
        masked_number=result.masked_number,
        errors=[ErrorDetail(code=c, message=MESSAGES[c]) for c in result.errors],
    )
