"""Card brand detection from the number's prefix (IIN range) and length.

Ranges follow the networks' public documentation:
  Visa        starts with 4                     13, 16 or 19 digits
  Mastercard  51-55 or 2221-2720                16 digits
  Amex        34 or 37                          15 digits
  Discover    6011, 622126-622925, 644-649, 65  16-19 digits
"""

from dataclasses import dataclass
from enum import Enum


class Brand(str, Enum):
    VISA = "visa"
    MASTERCARD = "mastercard"
    AMEX = "amex"
    DISCOVER = "discover"


@dataclass(frozen=True)
class BrandRule:
    brand: Brand
    ranges: tuple[tuple[int, int], ...]  # inclusive (low, high) prefix ranges
    lengths: frozenset[int]


RULES: tuple[BrandRule, ...] = (
    BrandRule(Brand.VISA, ((4, 4),), frozenset({13, 16, 19})),
    BrandRule(Brand.MASTERCARD, ((51, 55), (2221, 2720)), frozenset({16})),
    BrandRule(Brand.AMEX, ((34, 34), (37, 37)), frozenset({15})),
    BrandRule(
        Brand.DISCOVER,
        ((6011, 6011), (622126, 622925), (644, 649), (65, 65)),
        frozenset(range(16, 20)),
    ),
)


def _matches(digits: str, low: int, high: int) -> bool:
    width = len(str(low))
    if len(digits) < width:
        return False
    return low <= int(digits[:width]) <= high


def find_rule(digits: str) -> BrandRule | None:
    """Return the rule whose prefix matches, ignoring length. Expects digits only."""
    for rule in RULES:
        if any(_matches(digits, low, high) for low, high in rule.ranges):
            return rule
    return None


def detect_brand(digits: str) -> Brand | None:
    """Return the brand only if both prefix and length match."""
    rule = find_rule(digits)
    if rule is None or len(digits) not in rule.lengths:
        return None
    return rule.brand
