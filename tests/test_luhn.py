"""Unit tests for the Luhn (MOD 10) check.

All card numbers here are public test numbers published by card networks and
payment processors for testing. None of them belong to a real account.
"""

import pytest

from app.luhn import luhn_check, normalize_number

# --- Valid numbers ---------------------------------------------------------

VALID_TEST_NUMBERS = [
    "4111111111111111",  # Visa
    "4242424242424242",  # Visa
    "4012888888881881",  # Visa
    "5555555555554444",  # Mastercard
    "5105105105105100",  # Mastercard
    "2223003122003222",  # Mastercard (2-series)
    "378282246310005",  # American Express (15 digits)
    "371449635398431",  # American Express
    "6011111111111117",  # Discover
    "6011000990139424",  # Discover
]


@pytest.mark.parametrize("number", VALID_TEST_NUMBERS)
def test_valid_test_numbers_pass(number):
    assert luhn_check(number) is True


# --- Invalid numbers -------------------------------------------------------


@pytest.mark.parametrize(
    "number",
    [
        "4111111111111112",  # last digit changed
        "4111111111111121",  # two digits swapped
        "5555555555554445",
        "378282246310006",
        "1234567812345678",
    ],
)
def test_invalid_numbers_fail(number):
    assert luhn_check(number) is False


def test_single_wrong_digit_is_always_caught():
    # Luhn's main guarantee: changing any one digit breaks the checksum.
    original = "4111111111111111"
    for position in range(len(original)):
        for digit in "0123456789":
            if digit == original[position]:
                continue
            mutated = original[:position] + digit + original[position + 1 :]
            assert luhn_check(mutated) is False, mutated


# --- Formatting ------------------------------------------------------------


@pytest.mark.parametrize(
    "number",
    [
        "4111 1111 1111 1111",
        "4111-1111-1111-1111",
        " 4111111111111111 ",
        "3782 822463 10005",  # Amex grouping
    ],
)
def test_spaces_and_dashes_are_ignored(number):
    assert luhn_check(number) is True


# --- Bad input -------------------------------------------------------------


@pytest.mark.parametrize("number", ["", "   ", "--", "7"])
def test_empty_or_too_short_input_fails(number):
    assert luhn_check(number) is False


@pytest.mark.parametrize(
    "number",
    [
        "4111a11111111111",
        "4111.1111.1111.1111",
        "4111_1111_1111_1111",
        "+4111111111111111",
        "٤١١١١١١١١١١١١١١١",  # Arabic-Indic digits: isdigit() is True, but not ASCII
    ],
)
def test_non_digit_characters_fail(number):
    assert luhn_check(number) is False


def test_non_string_input_raises_type_error():
    with pytest.raises(TypeError):
        luhn_check(4111111111111111)


# --- normalize_number ------------------------------------------------------


def test_normalize_strips_spaces_and_dashes():
    assert normalize_number(" 4111-1111 1111-1111 ") == "4111111111111111"


def test_normalize_returns_none_for_non_digits():
    assert normalize_number("4111x") is None


def test_normalize_returns_empty_string_for_blank_input():
    assert normalize_number(" - ") == ""
