"""Luhn (MOD 10) checksum used by payment card numbers.

How it works: starting from the rightmost digit (the check digit) and moving
left, double every second digit. If doubling gives a two-digit number,
subtract 9 (same as adding its digits). The number is valid when the total
is a multiple of 10.
"""

SEPARATORS = " -"
MIN_DIGITS = 2  # one payload digit plus the check digit


def normalize_number(raw: str) -> str | None:
    """Remove spaces and dashes. Return None if anything else isn't 0-9."""
    if not isinstance(raw, str):
        raise TypeError(f"card number must be a string, got {type(raw).__name__}")
    digits = "".join(ch for ch in raw if ch not in SEPARATORS)
    if digits == "":
        return ""  # empty is its own case, not "bad characters"
    # isascii() matters: "٣".isdigit() is True, but it is not a card digit.
    if not digits.isascii() or not digits.isdigit():
        return None
    return digits


def luhn_check(number: str) -> bool:
    """Return True if `number` passes the Luhn checksum."""
    digits = normalize_number(number)
    if digits is None or len(digits) < MIN_DIGITS:
        return False

    total = 0
    for index, char in enumerate(reversed(digits)):
        value = int(char)
        if index % 2 == 1:  # every second digit from the right
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0
