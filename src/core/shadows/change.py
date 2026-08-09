"""Refinement-stable change and area shadows for Veyra analysis."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction
import logging

from .completion import ratio_distance
from .ratio import RatioMode, add_ratios, inverse_ratio, multiply_ratios, ratio_from_fraction, ratio_from_ints, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)
Rule = Callable[[RatioMode], RatioMode]


@dataclass(frozen=True)
class ContinuityCertificate:
    """Certificate that a sampled input tremor produces no output jump."""

    status: str
    obstruction: str
    anchor: RatioMode
    checked: int
    max_drift: Fraction


@dataclass(frozen=True)
class DriftQuotient:
    """Local change shadow: output drift divided by input drift."""

    anchor: RatioMode
    step: RatioMode
    value: RatioMode
    scheme: str


@dataclass(frozen=True)
class AreaCertificate:
    """Finite area shadow assembled from equal-width strips."""

    status: str
    value: RatioMode | None
    slices: int
    obstruction: str


def ratio_divide(numerator: RatioMode, denominator: RatioMode) -> RatioMode:
    """Divide ratio shadows by multiplying by inverse denominator."""
    logger.debug("ratio_divide entry numerator=%s denominator=%s", numerator.word, denominator.word)
    result = multiply_ratios(numerator, inverse_ratio(denominator))
    logger.debug("ratio_divide exit result=%s", result.word)
    return result


def ratio_midpoint(left: RatioMode, right: RatioMode) -> RatioMode:
    """Return midpoint of two ratio shadows."""
    logger.debug("ratio_midpoint entry left=%s right=%s", left.word, right.word)
    result = multiply_ratios(add_ratios(left, right), ratio_from_ints(1, 2))
    logger.debug("ratio_midpoint exit result=%s", result.word)
    return result


def tremor_points(anchor: RatioMode, radius: RatioMode, samples: int) -> tuple[RatioMode, ...]:
    """Return symmetric rational sample points around an anchor."""
    logger.debug("tremor_points entry anchor=%s radius=%s samples=%d", anchor.word, radius.word, samples)
    if samples <= 0:
        logger.error("tremor_points invalid samples=%d", samples)
        raise ValueError("samples must be positive")
    points = []
    for index in range(-samples, samples + 1):
        scale = ratio_from_fraction(Fraction(index, samples))
        points.append(add_ratios(anchor, multiply_ratios(radius, scale)))
    result = tuple(points)
    logger.debug("tremor_points exit count=%d", len(result))
    return result


def sampled_continuity(rule: Rule, anchor: RatioMode, radius: RatioMode, tolerance: RatioMode, samples: int = 4) -> ContinuityCertificate:
    """Certify sampled no-jump behavior near an anchor."""
    logger.debug("sampled_continuity entry anchor=%s radius=%s samples=%d", anchor.word, radius.word, samples)
    center = rule(anchor)
    eps = ratio_shadow(tolerance)
    checked = 0
    max_drift = Fraction(0)
    for point in tremor_points(anchor, radius, samples):
        checked += 1
        drift = ratio_distance(rule(point), center)
        max_drift = max(max_drift, drift)
        if drift > eps:
            result = ContinuityCertificate("none", "echo-jump", anchor, checked, max_drift)
            logger.debug("sampled_continuity exit obstruction drift=%s", drift)
            return result
    result = ContinuityCertificate("stable", "none", anchor, checked, max_drift)
    logger.debug("sampled_continuity exit stable max_drift=%s", max_drift)
    return result


def difference_quotient(rule: Rule, anchor: RatioMode, step: RatioMode) -> DriftQuotient:
    """Return one-sided local change shadow `(F(a+h)-F(a))/h`."""
    logger.debug("difference_quotient entry anchor=%s step=%s", anchor.word, step.word)
    if ratio_shadow(step) == 0:
        logger.error("difference_quotient zero step")
        raise ValueError("step must be nonzero")
    drift = subtract_ratios(rule(add_ratios(anchor, step)), rule(anchor))
    result = DriftQuotient(anchor, step, ratio_divide(drift, step), "forward")
    logger.debug("difference_quotient exit value=%s", result.value.word)
    return result


def symmetric_difference_quotient(rule: Rule, anchor: RatioMode, step: RatioMode) -> DriftQuotient:
    """Return symmetric local change shadow `(F(a+h)-F(a-h))/(2h)`."""
    logger.debug("symmetric_difference_quotient entry anchor=%s step=%s", anchor.word, step.word)
    if ratio_shadow(step) == 0:
        logger.error("symmetric_difference_quotient zero step")
        raise ValueError("step must be nonzero")
    high = rule(add_ratios(anchor, step))
    low = rule(subtract_ratios(anchor, step))
    span = multiply_ratios(step, ratio_from_ints(2))
    result = DriftQuotient(anchor, step, ratio_divide(subtract_ratios(high, low), span), "symmetric")
    logger.debug("symmetric_difference_quotient exit value=%s", result.value.word)
    return result


def riemann_area(rule: Rule, lower: RatioMode, upper: RatioMode, slices: int, sample: str = "mid") -> AreaCertificate:
    """Return finite equal-strip area shadow for a rule on an interval."""
    logger.debug("riemann_area entry lower=%s upper=%s slices=%d sample=%s", lower.word, upper.word, slices, sample)
    if slices <= 0:
        logger.error("riemann_area invalid slices=%d", slices)
        raise ValueError("slices must be positive")
    if sample not in {"left", "right", "mid"}:
        logger.error("riemann_area invalid sample=%s", sample)
        raise ValueError("sample must be left, right, or mid")
    width = ratio_divide(subtract_ratios(upper, lower), ratio_from_ints(slices))
    total = ratio_from_ints(0)
    for index in range(slices):
        left = add_ratios(lower, multiply_ratios(width, ratio_from_ints(index)))
        right = add_ratios(left, width)
        point = {"left": left, "right": right, "mid": ratio_midpoint(left, right)}[sample]
        total = add_ratios(total, multiply_ratios(rule(point), width))
    result = AreaCertificate("finite", total, slices, "none")
    logger.debug("riemann_area exit value=%s", total.word)
    return result
