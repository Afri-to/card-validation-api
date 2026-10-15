"""A full user journey through the API, in order."""


def test_validate_then_pay_then_review(client):
    card = "5555 5555 5555 4444"

    check = client.post("/validate", json={"number": card}).json()
    assert check["valid"] and check["brand"] == "mastercard"

    first = client.post(
        "/transactions",
        json={"card_number": card, "amount": "49.99", "currency": "USD"},
    )
    assert first.status_code == 201 and first.json()["status"] == "approved"

    # Customer double-clicks "Pay".
    repeat = client.post(
        "/transactions",
        json={"card_number": card, "amount": "49.99", "currency": "USD"},
    )
    assert repeat.json()["status"] == "flagged"

    # A reviewer pulls up the flagged queue and opens the transaction.
    queue = client.get("/transactions", params={"status": "flagged"}).json()
    assert [t["id"] for t in queue] == [repeat.json()["id"]]
    detail = client.get(f"/transactions/{queue[0]['id']}").json()
    assert detail["masked_card"] == "**** 4444"
    assert detail["reason"] == "POSSIBLE_DUPLICATE"
