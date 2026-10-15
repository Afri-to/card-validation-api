"""Business rules that decide a mock transaction's status.

Kept free of HTTP and database code so each rule can be unit tested alone.
"""

import hashlib
import hmac
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from app.models import TransactionStatus


class Reason(str, Enum):
    OVER_LIMIT = "OVER_LIMIT"
    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"


@dataclass(frozen=True)
class Decision:
    status: TransactionStatus
    reason: Reason | None = None


def card_fingerprint(digits: str, key: str) -> str:
    """HMAC-SHA256 of the card number. Same card -> same fingerprint, not reversible."""
    return hmac.new(key.encode(), digits.encode(), hashlib.sha256).hexdigest()


def decide(amount: Decimal, max_approved: Decimal, is_duplicate: bool) -> Decision:
    """Over the limit is declined; a repeat is flagged for review; otherwise approved.

    Decline wins over flag: a payment we would refuse anyway needs no review.
    """
    if amount > max_approved:
        return Decision(TransactionStatus.DECLINED, Reason.OVER_LIMIT)
    if is_duplicate:
        return Decision(TransactionStatus.FLAGGED, Reason.POSSIBLE_DUPLICATE)
    return Decision(TransactionStatus.APPROVED)
