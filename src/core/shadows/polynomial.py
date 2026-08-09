"""Polynomial ratio forms for Veyra school-algebra shadows."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .ratio import RatioMode, add_ratios, multiply_ratios, ratio_from_ints, ratio_shadow

logger = logging.getLogger(__name__)


def zero_ratio() -> RatioMode:
    """Return zero ratio."""
    logger.debug("zero_ratio entry")
    result = ratio_from_ints(0)
    logger.debug("zero_ratio exit result=%s", result.word)
    return result


@dataclass(frozen=True)
class Polynomial:
    """Polynomial with ratio coefficients, low degree first."""

    coefficients: tuple[RatioMode, ...]

    @property
    def degree(self) -> int:
        """Return degree after ignoring trailing zero coefficients."""
        logger.debug("Polynomial.degree entry coeffs=%d", len(self.coefficients))
        for index in range(len(self.coefficients) - 1, -1, -1):
            if ratio_shadow(self.coefficients[index]) != 0:
                logger.debug("Polynomial.degree exit result=%d", index)
                return index
        logger.debug("Polynomial.degree exit zero=-1")
        return -1


def normalize_polynomial(poly: Polynomial) -> Polynomial:
    """Remove trailing zero coefficients while keeping at least one term."""
    logger.debug("normalize_polynomial entry coeffs=%d", len(poly.coefficients))
    coeffs = list(poly.coefficients)
    while len(coeffs) > 1 and ratio_shadow(coeffs[-1]) == 0:
        coeffs.pop()
    result = Polynomial(tuple(coeffs or [zero_ratio()]))
    logger.debug("normalize_polynomial exit coeffs=%d", len(result.coefficients))
    return result


def polynomial_from_ints(values: list[int]) -> Polynomial:
    """Build polynomial from integer coefficients."""
    logger.debug("polynomial_from_ints entry values=%r", values)
    result = normalize_polynomial(Polynomial(tuple(ratio_from_ints(value) for value in values)))
    logger.debug("polynomial_from_ints exit degree=%d", result.degree)
    return result


def add_polynomials(left: Polynomial, right: Polynomial) -> Polynomial:
    """Add two polynomials."""
    logger.debug("add_polynomials entry left_degree=%d right_degree=%d", left.degree, right.degree)
    size = max(len(left.coefficients), len(right.coefficients))
    rows: list[RatioMode] = []
    for index in range(size):
        a = left.coefficients[index] if index < len(left.coefficients) else zero_ratio()
        b = right.coefficients[index] if index < len(right.coefficients) else zero_ratio()
        rows.append(add_ratios(a, b))
    result = normalize_polynomial(Polynomial(tuple(rows)))
    logger.debug("add_polynomials exit degree=%d", result.degree)
    return result


def multiply_polynomials(left: Polynomial, right: Polynomial) -> Polynomial:
    """Multiply two polynomials by convolution."""
    logger.debug("multiply_polynomials entry left_degree=%d right_degree=%d", left.degree, right.degree)
    rows = [zero_ratio() for _ in range(len(left.coefficients) + len(right.coefficients) - 1)]
    for i, a in enumerate(left.coefficients):
        for j, b in enumerate(right.coefficients):
            rows[i + j] = add_ratios(rows[i + j], multiply_ratios(a, b))
    result = normalize_polynomial(Polynomial(tuple(rows)))
    logger.debug("multiply_polynomials exit degree=%d", result.degree)
    return result


def eval_polynomial(poly: Polynomial, value: RatioMode) -> RatioMode:
    """Evaluate polynomial at a ratio value using Horner form."""
    logger.debug("eval_polynomial entry degree=%d value=%s", poly.degree, value.word)
    result = zero_ratio()
    for coeff in reversed(poly.coefficients):
        result = add_ratios(multiply_ratios(result, value), coeff)
    logger.debug("eval_polynomial exit result=%s", result.word)
    return result


def derivative_polynomial(poly: Polynomial) -> Polynomial:
    """Return formal derivative in the ratio shadow layer."""
    logger.debug("derivative_polynomial entry degree=%d", poly.degree)
    if len(poly.coefficients) <= 1:
        result = Polynomial((zero_ratio(),))
    else:
        result = normalize_polynomial(Polynomial(tuple(
            multiply_ratios(coeff, ratio_from_ints(index))
            for index, coeff in enumerate(poly.coefficients[1:], start=1)
        )))
    logger.debug("derivative_polynomial exit degree=%d", result.degree)
    return result
