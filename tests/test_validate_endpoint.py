import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def post(number):
    return client.post("/validate", json={"number": number})


def codes(response):
    return [e["code"] for e in response.json()["errors"]]


def test_valid_visa():
    response = post("4111 1111 1111 1111")
    assert response.status_code == 200
    assert response.json() == {
        "valid": True,
        "brand": "visa",
        "luhn_valid": True,
        "masked_number": "**** 1111",
        "errors": [],
    }


@pytest.mark.parametrize(
    "number, brand",
    [
        ("5555555555554444", "mastercard"),
        ("378282246310005", "amex"),
        ("6011111111111117", "discover"),
    ],
)
def test_valid_other_brands(number, brand):
    body = post(number).json()
    assert body["valid"] is True
    assert body["brand"] == brand


def test_full_number_is_never_returned():
    number = "4111111111111111"
    assert number not in post(number).text


@pytest.mark.parametrize(
    "number, expected_codes",
    [
        ("", ["EMPTY_NUMBER"]),
        ("  - ", ["EMPTY_NUMBER"]),
        ("4111abcd11111111", ["INVALID_CHARACTERS"]),
        ("4111111111111112", ["LUHN_CHECK_FAILED"]),
        ("9999999999999995", ["UNKNOWN_BRAND"]),
        ("41111111111111", ["INVALID_LENGTH", "LUHN_CHECK_FAILED"]),
        ("9999999999999999", ["UNKNOWN_BRAND", "LUHN_CHECK_FAILED"]),
    ],
)
def test_error_codes(number, expected_codes):
    response = post(number)
    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert codes(response) == expected_codes


def test_wrong_length_still_reports_likely_brand():
    body = post("41111111111111").json()
    assert body["brand"] == "visa"


def test_missing_field_returns_422():
    assert client.post("/validate", json={}).status_code == 422


def test_non_string_number_returns_422():
    assert client.post("/validate", json={"number": 4111111111111111}).status_code == 422


def test_oversized_input_returns_422():
    assert post("4" * 65).status_code == 422
