from fractions import Fraction

import pytest

from src.core.balance import balance_from_int
from src.core.order import (
    RatioInterval,
    balance_magnitude,
    clamp_ratio,
    compare_balances,
    compare_ratios,
    interval_contains,
    ratio_between,
    ratio_magnitude,
)
from src.core.ratio import ratio_from_ints, ratio_shadow


def test_balance_comparison_and_magnitude():
    comp = compare_balances(balance_from_int(3), balance_from_int(-2))
    assert comp.sign == 1
    assert comp.relation == ">"
    assert comp.gap.net_length == 5
    assert balance_magnitude(balance_from_int(-4)).length == 4


def test_ratio_comparison_and_magnitude():
    comp = compare_ratios(ratio_from_ints(1, 2), ratio_from_ints(2, 3))
    assert comp.sign == -1
    assert comp.relation == "<"
    assert ratio_shadow(comp.gap) == Fraction(-1, 6)
    assert ratio_shadow(ratio_magnitude(comp.gap)) == Fraction(1, 6)


def test_ratio_intervals_between_and_clamp():
    lower = ratio_from_ints(1, 4)
    upper = ratio_from_ints(1, 2)
    value = ratio_from_ints(1, 3)
    interval = RatioInterval(lower, upper)
    assert interval_contains(interval, value)
    assert ratio_between(lower, lower, upper)
    assert not ratio_between(lower, lower, upper, lower_closed=False)
    assert ratio_shadow(clamp_ratio(ratio_from_ints(3, 4), interval)) == Fraction(1, 2)


def test_invalid_interval_rejected():
    with pytest.raises(ValueError):
        RatioInterval(ratio_from_ints(2, 3), ratio_from_ints(1, 3))
