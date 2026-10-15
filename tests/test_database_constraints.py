"""The database enforces the key rules too, so a bug in the API code (or a
manual SQL insert) still can't store a bad row."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DataError, IntegrityError

from app.db import engine

INSERT = text(
    "INSERT INTO transactions "
    "(id, masked_card, card_fingerprint, brand, amount, currency, status) "
    "VALUES (gen_random_uuid(), '**** 1111', repeat('a', 64), 'VISA', :amount, :currency, 'APPROVED')"
)


@pytest.mark.usefixtures("client")
@pytest.mark.parametrize(
    "amount, currency",
    [
        ("-1.00", "USD"),  # negative amount
        ("0", "USD"),  # zero amount
        ("10.00", "usd"),  # lowercase currency
        ("10.00", "US1"),  # not letters
    ],
)
def test_database_rejects_bad_rows(amount, currency):
    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(INSERT, {"amount": amount, "currency": currency})


@pytest.mark.usefixtures("client")
def test_masked_card_column_is_too_short_for_a_full_number():
    # masked_card is VARCHAR(9): "**** 1111" fits, a 16-digit number does not.
    with engine.begin() as conn:
        conn.execute(INSERT, {"amount": "1.00", "currency": "USD"})
    with pytest.raises(DataError):
        with engine.begin() as conn:
            conn.execute(text("UPDATE transactions SET masked_card = '4111111111111111'"))
