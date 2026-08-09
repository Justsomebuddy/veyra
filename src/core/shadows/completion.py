"""Completion, refinement, and limit certificates for Veyra analysis seed."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import logging

from .ratio import RatioMode, ratio_from_fraction, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CompletionInterval:
    """Nested rational interval representing a completion shadow."""

    lower: RatioMode
    upper: RatioMode
    label: str = "completion"

    @property
    def width(self) -> Fraction:
        """Return rational interval width."""
        logger.debug("CompletionInterval.width entry label=%s", self.label)
        result = ratio_shadow(self.upper) - ratio_shadow(self.lower)
        logger.debug("CompletionInterval.width exit result=%s", result)
        return result


@dataclass(frozen=True)
class LimitCertificate:
    """Finite certificate that a tail is stable under a tolerance observer."""

    status: str
    value: RatioMode | None
    obstruction: str
    checked: int


def make_interval(lower: Fraction, upper: Fraction, label: str = "completion") -> CompletionInterval:
    """Create a completion interval from rational bounds."""
    logger.debug("make_interval entry lower=%s upper=%s label=%s", lower, upper, label)
    if lower > upper:
        logger.error("make_interval lower>upper")
        raise ValueError("lower must not exceed upper")
    result = CompletionInterval(ratio_from_fraction(lower), ratio_from_fraction(upper), label)
    logger.debug("make_interval exit width=%s", result.width)
    return result


def square_refinement(value: RatioMode, steps: int) -> CompletionInterval:
    """Return nested rational interval approximating sqrt(value)."""
    logger.debug("square_refinement entry value=%s steps=%d", value.word, steps)
    target = ratio_shadow(value)
    if target < 0:
        logger.error("square_refinement negative target=%s", target)
        raise ValueError("negative value has no real square refinement")
    low = Fraction(0)
    high = max(Fraction(1), target)
    while high * high < target:
        high *= 2
    for _ in range(steps):
        mid = (low + high) / 2
        if mid * mid <= target:
            low = mid
        else:
            high = mid
    result = make_interval(low, high, f"sqrt({value.word})")
    logger.debug("square_refinement exit width=%s", result.width)
    return result


def interval_refines(previous: CompletionInterval, current: CompletionInterval) -> bool:
    """Return True iff current interval is nested inside previous."""
    logger.debug("interval_refines entry previous=%s current=%s", previous.label, current.label)
    result = ratio_shadow(previous.lower) <= ratio_shadow(current.lower) and ratio_shadow(current.upper) <= ratio_shadow(previous.upper)
    logger.debug("interval_refines exit result=%s", result)
    return result


def interval_within(interval: CompletionInterval, tolerance: RatioMode) -> bool:
    """Return True iff interval width is no larger than tolerance."""
    logger.debug("interval_within entry interval=%s tolerance=%s", interval.label, tolerance.word)
    result = interval.width <= ratio_shadow(tolerance)
    logger.debug("interval_within exit result=%s", result)
    return result


def ratio_distance(left: RatioMode, right: RatioMode) -> Fraction:
    """Return absolute rational distance between two ratio shadows."""
    logger.debug("ratio_distance entry left=%s right=%s", left.word, right.word)
    result = abs(ratio_shadow(subtract_ratios(left, right)))
    logger.debug("ratio_distance exit result=%s", result)
    return result


def tail_limit_certificate(samples: tuple[RatioMode, ...], candidate: RatioMode, tolerance: RatioMode, tail: int) -> LimitCertificate:
    """Certify that a finite tail remains within tolerance of candidate."""
    logger.debug("tail_limit_certificate entry samples=%d tail=%d", len(samples), tail)
    if tail <= 0 or tail > len(samples):
        logger.error("tail_limit_certificate invalid tail=%d", tail)
        raise ValueError("tail must be between 1 and len(samples)")
    eps = ratio_shadow(tolerance)
    checked = 0
    for item in samples[-tail:]:
        checked += 1
        if ratio_distance(item, candidate) > eps:
            result = LimitCertificate("none", None, "tail-jump", checked)
            logger.debug("tail_limit_certificate exit obstruction")
            return result
    result = LimitCertificate("stable", candidate, "none", checked)
    logger.debug("tail_limit_certificate exit stable")
    return result
