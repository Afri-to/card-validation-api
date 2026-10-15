"""Combine normalization, brand detection and the Luhn check into one result."""

from dataclasses import dataclass, field
from enum import Enum

from app.brands import Brand, detect_brand, find_rule
from app.luhn import luhn_check, normalize_number


class ErrorCode(str, Enum):
    EMPTY_NUMBER = "EMPTY_NUMBER"
    INVALID_CHARACTERS = "INVALID_CHARACTERS"
    UNKNOWN_BRAND = "UNKNOWN_BRAND"
    INVALID_LENGTH = "INVALID_LENGTH"
    LUHN_CHECK_FAILED = "LUHN_CHECK_FAILED"


MESSAGES = {
    ErrorCode.EMPTY_NUMBER: "No card number was provided.",
    ErrorCode.INVALID_CHARACTERS: "Only digits, spaces and dashes are allowed.",
    ErrorCode.UNKNOWN_BRAND: "The number does not match a supported card brand.",
    ErrorCode.INVALID_LENGTH: "The number has the wrong length for its brand.",
    ErrorCode.LUHN_CHECK_FAILED: "The number fails the Luhn checksum (likely a typo).",
}


@dataclass
class ValidationResult:
    valid: bool
    brand: Brand | None = None
    luhn_valid: bool = False
    masked_number: str | None = None
    errors: list[ErrorCode] = field(default_factory=list)


def mask(digits: str) -> str:
    """Show only the last 4 digits, as receipts do."""
    return "**** " + digits[-4:] if len(digits) >= 4 else "****"


def validate_card(raw: str) -> ValidationResult:
    digits = normalize_number(raw)
    if digits is None:
        return ValidationResult(valid=False, errors=[ErrorCode.INVALID_CHARACTERS])
    if not digits:
        return ValidationResult(valid=False, errors=[ErrorCode.EMPTY_NUMBER])

    errors: list[ErrorCode] = []
    rule = find_rule(digits)
    brand = detect_brand(digits)
    if rule is None:
        errors.append(ErrorCode.UNKNOWN_BRAND)
    elif brand is None:
        errors.append(ErrorCode.INVALID_LENGTH)

    passes_luhn = luhn_check(digits)
    if not passes_luhn:
        errors.append(ErrorCode.LUHN_CHECK_FAILED)

    return ValidationResult(
        valid=not errors,
        brand=brand or (rule.brand if rule else None),
        luhn_valid=passes_luhn,
        masked_number=mask(digits),
        errors=errors,
    )
