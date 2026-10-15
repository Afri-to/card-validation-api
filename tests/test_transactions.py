"""Integration tests: real HTTP requests against a real PostgreSQL test database."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.db import engine

VISA = "4111 1111 1111 1111"
AMEX = "378282246310005"


def create(client, card=VISA, amount="25.00", currency="USD"):
    return client.post(
        "/transactions",
        json={"card_number": card, "amount": amount, "currency": currency},
    )


def test_create_transaction_returns_201_and_masked_card(client):
    response = create(client)
    assert response.status_code == 201
    body = response.json()
    assert body["masked_card"] == "**** 1111"
    assert body["brand"] == "visa"
    assert body["amount"] == "25.00"
    assert body["currency"] == "USD"
    assert body["status"] == "approved"
    assert "id" in body and "created_at" in body


def test_full_card_number_is_never_stored(client):
    create(client)
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM transactions")).all()
    assert len(rows) == 1
    assert "4111111111111111" not in str(rows)


def test_invalid_card_is_rejected_with_error_codes(client):
    response = create(client, card="4111111111111112")
    assert response.status_code == 422
    assert response.json()["detail"]["errors"][0]["code"] == "LUHN_CHECK_FAILED"
    assert client.get("/transactions").json() == []


def test_bad_currency_is_rejected(client):
    assert create(client, currency="usd").status_code == 422
    assert create(client, currency="DOLLARS").status_code == 422


def test_more_than_two_decimals_is_rejected(client):
    assert create(client, amount="10.005").status_code == 422


def test_list_returns_newest_first(client):
    first = create(client, amount="1.00").json()
    second = create(client, card=AMEX, amount="2.00").json()
    ids = [t["id"] for t in client.get("/transactions").json()]
    assert ids == [second["id"], first["id"]]


def test_filter_by_status(client):
    create(client)
    assert len(client.get("/transactions?status=approved").json()) == 1
    assert client.get("/transactions?status=declined").json() == []
    assert client.get("/transactions?status=bogus").status_code == 422


def test_filter_by_date_range(client):
    create(client)
    now = datetime.now(timezone.utc)
    hour = timedelta(hours=1)
    params = {"from": (now - hour).isoformat(), "to": (now + hour).isoformat()}
    assert len(client.get("/transactions", params=params).json()) == 1

    future = {"from": (now + hour).isoformat()}
    assert client.get("/transactions", params=future).json() == []


def test_from_after_to_is_rejected(client):
    now = datetime.now(timezone.utc)
    params = {"from": now.isoformat(), "to": (now - timedelta(days=1)).isoformat()}
    assert client.get("/transactions", params=params).status_code == 422


def test_limit_and_offset(client):
    for cents in range(5):
        create(client, amount=f"1.0{cents}")
    assert len(client.get("/transactions?limit=2").json()) == 2
    assert len(client.get("/transactions?limit=2&offset=4").json()) == 1
    assert client.get("/transactions?limit=0").status_code == 422
    assert client.get("/transactions?limit=101").status_code == 422
