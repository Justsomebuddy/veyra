"""Polynomial calculus-depth shadows for Veyra analysis."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .change import ratio_divide
from ..geometry.theorems import TheoremCard
from .polynomial import Polynomial, add_polynomials, derivative_polynomial, eval_polynomial, multiply_polynomials, normalize_polynomial, zero_ratio
from .ratio import RatioMode, add_ratios, multiply_ratios, ratio_from_ints, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LocalLinearization:
    """First-order polynomial shadow at one observer anchor."""

    anchor: RatioMode
    value: RatioMode
    slope: RatioMode
    tangent: Polynomial
    obstruction: str


@dataclass(frozen=True)
class IntegralCoherence:
    """Exact antiderivative interval certificate for a polynomial shadow."""

    lower: RatioMode
    upper: RatioMode
    value: RatioMode
    antiderivative: Polynomial
    obstruction: str


def scale_polynomial(poly: Polynomial, factor: RatioMode) -> Polynomial:
    """Multiply every polynomial coefficient by a ratio factor."""
    logger.debug("scale_polynomial entry degree=%d factor=%s", poly.degree, factor.word)
    result = normalize_polynomial(Polynomial(tuple(multiply_ratios(coeff, factor) for coeff in poly.coefficients)))
    logger.debug("scale_polynomial exit degree=%d", result.degree)
    return result


def polynomial_power(poly: Polynomial, exponent: int) -> Polynomial:
    """Return nonnegative integer polynomial power."""
    logger.debug("polynomial_power entry degree=%d exponent=%d", poly.degree, exponent)
    if exponent < 0:
        logger.error("polynomial_power negative exponent=%d", exponent)
        raise ValueError("exponent must be nonnegative")
    result = Polynomial((ratio_from_ints(1),))
    for _ in range(exponent):
        result = multiply_polynomials(result, poly)
    logger.debug("polynomial_power exit degree=%d", result.degree)
    return result


def compose_polynomials(outer: Polynomial, inner: Polynomial) -> Polynomial:
    """Return polynomial composition `outer(inner(x))`."""
    logger.debug("compose_polynomials entry outer_degree=%d inner_degree=%d", outer.degree, inner.degree)
    result = Polynomial((zero_ratio(),))
    for exponent, coeff in enumerate(outer.coefficients):
        term = scale_polynomial(polynomial_power(inner, exponent), coeff)
        result = add_polynomials(result, term)
    result = normalize_polynomial(result)
    logger.debug("compose_polynomials exit degree=%d", result.degree)
    return result


def antiderivative_polynomial(poly: Polynomial) -> Polynomial:
    """Return exact zero-constant antiderivative polynomial shadow."""
    logger.debug("antiderivative_polynomial entry degree=%d", poly.degree)
    coeffs = [zero_ratio()]
    for index, coeff in enumerate(poly.coefficients):
        coeffs.append(ratio_divide(coeff, ratio_from_ints(index + 1)))
    result = normalize_polynomial(Polynomial(tuple(coeffs)))
    logger.debug("antiderivative_polynomial exit degree=%d", result.degree)
    return result


def local_linearization(poly: Polynomial, anchor: RatioMode) -> LocalLinearization:
    """Return tangent polynomial `f(a)+f'(a)(x-a)` at an anchor."""
    logger.debug("local_linearization entry degree=%d anchor=%s", poly.degree, anchor.word)
    value = eval_polynomial(poly, anchor)
    slope = eval_polynomial(derivative_polynomial(poly), anchor)
    intercept = subtract_ratios(value, multiply_ratios(slope, anchor))
    result = LocalLinearization(anchor, value, slope, Polynomial((intercept, slope)), "none")
    logger.debug("local_linearization exit value=%s slope=%s", value.word, slope.word)
    return result


def linearization_error(poly: Polynomial, anchor: RatioMode, point: RatioMode) -> RatioMode:
    """Return exact error between polynomial and its local linearization."""
    logger.debug("linearization_error entry anchor=%s point=%s", anchor.word, point.word)
    linear = local_linearization(poly, anchor)
    result = subtract_ratios(eval_polynomial(poly, point), eval_polynomial(linear.tangent, point))
    logger.debug("linearization_error exit result=%s", result.word)
    return result


def product_rule_card(left: Polynomial, right: Polynomial) -> TheoremCard:
    """Return exact product-rule theorem card for polynomial shadows."""
    logger.debug("product_rule_card entry")
    observed = derivative_polynomial(multiply_polynomials(left, right))
    expected = add_polynomials(multiply_polynomials(derivative_polynomial(left), right), multiply_polynomials(left, derivative_polynomial(right)))
    ok = tuple(map(ratio_shadow, observed.coefficients)) == tuple(map(ratio_shadow, expected.coefficients))
    relation = "coherent" if ok else "broken"
    obstruction = "none" if ok else "product-derivative-gap"
    result = TheoremCard("calculus-product-rule", "exact", relation, obstruction, (("degree", str(observed.degree)),))
    logger.debug("product_rule_card exit relation=%s", relation)
    return result


def chain_rule_card(outer: Polynomial, inner: Polynomial) -> TheoremCard:
    """Return exact chain-rule theorem card for polynomial shadows."""
    logger.debug("chain_rule_card entry")
    observed = derivative_polynomial(compose_polynomials(outer, inner))
    expected = multiply_polynomials(compose_polynomials(derivative_polynomial(outer), inner), derivative_polynomial(inner))
    ok = tuple(map(ratio_shadow, observed.coefficients)) == tuple(map(ratio_shadow, expected.coefficients))
    relation = "coherent" if ok else "broken"
    obstruction = "none" if ok else "chain-derivative-gap"
    result = TheoremCard("calculus-chain-rule", "exact", relation, obstruction, (("degree", str(observed.degree)),))
    logger.debug("chain_rule_card exit relation=%s", relation)
    return result


def integral_coherence(poly: Polynomial, lower: RatioMode, upper: RatioMode) -> IntegralCoherence:
    """Return antiderivative interval coherence certificate."""
    logger.debug("integral_coherence entry lower=%s upper=%s degree=%d", lower.word, upper.word, poly.degree)
    anti = antiderivative_polynomial(poly)
    value = subtract_ratios(eval_polynomial(anti, upper), eval_polynomial(anti, lower))
    result = IntegralCoherence(lower, upper, value, anti, "none")
    logger.debug("integral_coherence exit value=%s", value.word)
    return result


def integral_coherence_card(poly: Polynomial, lower: RatioMode, upper: RatioMode, expected: RatioMode) -> TheoremCard:
    """Return exact antiderivative-vs-expected theorem card."""
    logger.debug("integral_coherence_card entry")
    cert = integral_coherence(poly, lower, upper)
    ok = ratio_shadow(cert.value) == ratio_shadow(expected)
    relation = "coherent" if ok else "broken"
    obstruction = "none" if ok else "integral-gap"
    result = TheoremCard("calculus-integral-coherence", "exact", relation, obstruction, (("value", str(ratio_shadow(cert.value))), ("expected", str(ratio_shadow(expected)))))
    logger.debug("integral_coherence_card exit relation=%s", relation)
    return result


def calculus_depth_checklist() -> tuple[str, ...]:
    """Return calculus-depth acceptance checklist."""
    logger.debug("calculus_depth_checklist entry")
    result = ("local linearization", "product-rule card", "chain-rule card", "integral coherence card")
    logger.debug("calculus_depth_checklist exit count=%d", len(result))
    return result
