from decimal import Decimal

from app.models import TransactionStatus
from app.rules import Reason, card_fingerprint, decide

LIMIT = Decimal("10000.00")


def test_normal_amount_is_approved():
    decision = decide(Decimal("25.00"), LIMIT, is_duplicate=False)
    assert decision.status is TransactionStatus.APPROVED
    assert decision.reason is None


def test_amount_at_limit_is_approved():
    assert decide(LIMIT, LIMIT, False).status is TransactionStatus.APPROVED


def test_amount_over_limit_is_declined():
    decision = decide(Decimal("10000.01"), LIMIT, is_duplicate=False)
    assert decision.status is TransactionStatus.DECLINED
    assert decision.reason is Reason.OVER_LIMIT


def test_duplicate_is_flagged():
    decision = decide(Decimal("25.00"), LIMIT, is_duplicate=True)
    assert decision.status is TransactionStatus.FLAGGED
    assert decision.reason is Reason.POSSIBLE_DUPLICATE


def test_decline_wins_over_flag():
    decision = decide(Decimal("50000.00"), LIMIT, is_duplicate=True)
    assert decision.status is TransactionStatus.DECLINED


def test_fingerprint_is_stable_and_keyed():
    a = card_fingerprint("4111111111111111", "key-1")
    assert a == card_fingerprint("4111111111111111", "key-1")
    assert a != card_fingerprint("4111111111111111", "key-2")
    assert a != card_fingerprint("4242424242424242", "key-1")
    assert len(a) == 64 and "4111" not in a
