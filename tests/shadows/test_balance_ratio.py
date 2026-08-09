from fractions import Fraction

import pytest

from src.core.balance import (
    balance_echo_equivalent,
    balance_echo_key,
    balance_from_int,
    canonical_length_balance,
    multiply_balance_by_natural,
    opposite_balance,
    stitch_balance,
    subtract_balance,
)
from src.core.ratio import (
    add_ratios,
    add_ratios_raw,
    inverse_ratio,
    multiply_ratios,
    multiply_ratios_raw,
    ratio_from_ints,
    ratio_shadow,
    subtract_ratios,
    subtract_ratios_raw,
)


def test_balance_one_tact_signed_shadow():
    left = balance_from_int(3)
    right = balance_from_int(-2)
    total = stitch_balance(left, right)
    assert total.net_length == 1
    assert canonical_length_balance(total).net_length == 1
    assert opposite_balance(total).net_length == -1


def test_balance_subtract_and_echo_scales():
    raw = subtract_balance(balance_from_int(2), balance_from_int(5))
    assert raw.net_length == -3
    assert balance_echo_equivalent(raw, balance_from_int(-3), "length")
    assert balance_echo_key(raw, "bag") == (("τ", -3),)


def test_balance_natural_multiplication_and_validation():
    doubled = multiply_balance_by_natural(balance_from_int(-2), 3)
    assert doubled.net_length == -6
    with pytest.raises(ValueError):
        multiply_balance_by_natural(balance_from_int(1), -1)


def test_ratio_basic_shadows_and_canonical_addition():
    half = ratio_from_ints(1, 2)
    third = ratio_from_ints(1, 3)
    assert ratio_shadow(half) == Fraction(1, 2)
    assert ratio_shadow(add_ratios(half, third)) == Fraction(5, 6)
    assert ratio_shadow(subtract_ratios(half, third)) == Fraction(1, 6)


def test_ratio_raw_operations_preserve_uncollapsed_scale():
    half = ratio_from_ints(1, 2)
    third = ratio_from_ints(1, 3)
    raw_sum = add_ratios_raw(half, third)
    raw_diff = subtract_ratios_raw(half, third)
    assert raw_sum.scale.length == 6
    assert raw_sum.numerator.net_length == 5
    assert ratio_shadow(raw_sum) == Fraction(5, 6)
    assert raw_diff.scale.length == 6
    assert raw_diff.numerator.net_length == 1


def test_ratio_multiplication_inverse_and_errors():
    left = ratio_from_ints(-2, 3)
    right = ratio_from_ints(9, 4)
    raw_product = multiply_ratios_raw(left, right)
    assert raw_product.scale.length == 12
    assert raw_product.numerator.net_length == -18
    assert ratio_shadow(multiply_ratios(left, right)) == Fraction(-3, 2)
    assert ratio_shadow(inverse_ratio(left)) == Fraction(-3, 2)
    with pytest.raises(ValueError):
        ratio_from_ints(1, 0)
    with pytest.raises(ValueError):
        inverse_ratio(ratio_from_ints(0, 5))
