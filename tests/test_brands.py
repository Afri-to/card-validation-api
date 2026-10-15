import pytest

from app.brands import Brand, detect_brand, find_rule


@pytest.mark.parametrize(
    "number, brand",
    [
        ("4111111111111111", Brand.VISA),
        ("4222222222222", Brand.VISA),  # 13-digit Visa test number
        ("5555555555554444", Brand.MASTERCARD),
        ("5105105105105100", Brand.MASTERCARD),
        ("2223003122003222", Brand.MASTERCARD),  # 2-series
        ("2720990000000007", Brand.MASTERCARD),  # top of 2-series range
        ("378282246310005", Brand.AMEX),
        ("341111111111111", Brand.AMEX),
        ("6011111111111117", Brand.DISCOVER),
        ("6500000000000002", Brand.DISCOVER),
        ("6445644564456445", Brand.DISCOVER),
        ("6221260000000000", Brand.DISCOVER),
    ],
)
def test_detects_brand(number, brand):
    assert detect_brand(number) is brand


@pytest.mark.parametrize(
    "number",
    [
        "2220990000000000",  # just below Mastercard 2-series
        "2721000000000000",  # just above it
        "5655555555554444",  # 56 is not Mastercard
        "3530111333300000",  # JCB: not supported
        "6221250000000000",  # just below Discover 622126
        "9999999999999995",
    ],
)
def test_unknown_prefix_returns_none(number):
    assert find_rule(number) is None
    assert detect_brand(number) is None


@pytest.mark.parametrize(
    "number",
    [
        "41111111111111",  # Visa prefix, 14 digits
        "55555555555544",  # Mastercard prefix, 14 digits
        "3782822463100050",  # Amex prefix, 16 digits
        "601111111111111",  # Discover prefix, 15 digits
    ],
)
def test_right_prefix_wrong_length_returns_none(number):
    assert find_rule(number) is not None
    assert detect_brand(number) is None


def test_short_input_does_not_crash():
    assert find_rule("6") is None
    assert find_rule("") is None
