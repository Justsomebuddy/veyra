from fractions import Fraction

from src.core.polynomial import (
    add_polynomials,
    derivative_polynomial,
    eval_polynomial,
    multiply_polynomials,
    polynomial_from_ints,
)
from src.core.ratio import ratio_from_ints, ratio_shadow


def coeff_shadows(poly):
    return [ratio_shadow(item) for item in poly.coefficients]


def test_polynomial_add_and_normalize():
    total = add_polynomials(polynomial_from_ints([1, 2]), polynomial_from_ints([-1, 3, 0]))
    assert coeff_shadows(total) == [0, 5]
    assert total.degree == 1


def test_polynomial_multiply_difference_of_squares():
    left = polynomial_from_ints([1, 1])
    right = polynomial_from_ints([-1, 1])
    product = multiply_polynomials(left, right)
    assert coeff_shadows(product) == [-1, 0, 1]
    assert ratio_shadow(eval_polynomial(product, ratio_from_ints(3))) == 8


def test_polynomial_derivative_shadow():
    poly = polynomial_from_ints([-1, 0, 1])
    deriv = derivative_polynomial(poly)
    assert coeff_shadows(deriv) == [0, 2]
    assert ratio_shadow(eval_polynomial(deriv, ratio_from_ints(3, 2))) == 3


def test_fraction_coefficients_via_operations():
    half_x = multiply_polynomials(polynomial_from_ints([0, 1]), polynomial_from_ints([1]))
    value = eval_polynomial(half_x, ratio_from_ints(1, 2))
    assert ratio_shadow(value) == Fraction(1, 2)
