"""Dominance, magnitude, and intervals for Veyra arithmetic shadows."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import logging

from .balance import BalanceMode, balance_from_int, canonical_length_balance, subtract_balance
from ..numbers.modes import Mode, natural_mode
from .ratio import RatioMode, ratio_from_fraction, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)


def sign_of(value: int | Fraction) -> int:
    """Return -1, 0, or 1 for an ordered shadow value."""
    logger.debug("sign_of entry value=%s", value)
    result = 1 if value > 0 else (-1 if value < 0 else 0)
    logger.debug("sign_of exit result=%d", result)
    return result


@dataclass(frozen=True)
class BalanceComparison:
    """Dominance result for two balance modes."""

    sign: int
    gap: BalanceMode

    @property
    def relation(self) -> str:
        """Return symbolic relation of left to right."""
        logger.debug("BalanceComparison.relation entry sign=%d", self.sign)
        result = ">" if self.sign > 0 else ("<" if self.sign < 0 else "=")
        logger.debug("BalanceComparison.relation exit result=%s", result)
        return result


@dataclass(frozen=True)
class RatioComparison:
    """Dominance result for two ratio modes."""

    sign: int
    gap: RatioMode

    @property
    def relation(self) -> str:
        """Return symbolic relation of left to right."""
        logger.debug("RatioComparison.relation entry sign=%d", self.sign)
        result = ">" if self.sign > 0 else ("<" if self.sign < 0 else "=")
        logger.debug("RatioComparison.relation exit result=%s", result)
        return result


@dataclass(frozen=True)
class RatioInterval:
    """Closed/open ratio interval in length-shadow order."""

    lower: RatioMode
    upper: RatioMode
    lower_closed: bool = True
    upper_closed: bool = True

    def __post_init__(self) -> None:
        """Validate lower <= upper."""
        logger.debug("RatioInterval.__post_init__ entry lower=%s upper=%s", self.lower.word, self.upper.word)
        if ratio_shadow(self.lower) > ratio_shadow(self.upper):
            logger.error("RatioInterval invalid lower>upper")
            raise ValueError("interval lower must not exceed upper")
        logger.debug("RatioInterval.__post_init__ exit")


def compare_balances(left: BalanceMode, right: BalanceMode, tact: str = "τ") -> BalanceComparison:
    """Compare balances under signed length dominance."""
    logger.debug("compare_balances entry left=%s right=%s", left.word, right.word)
    gap = canonical_length_balance(subtract_balance(left, right), tact)
    result = BalanceComparison(sign_of(gap.net_length), gap)
    logger.debug("compare_balances exit result=%r", result)
    return result


def balance_magnitude(balance: BalanceMode, tact: str = "τ") -> Mode:
    """Return magnitude mode under signed length dominance."""
    logger.debug("balance_magnitude entry balance=%s tact=%r", balance.word, tact)
    result = natural_mode(abs(balance.net_length), tact)
    logger.debug("balance_magnitude exit result=%s", result.word)
    return result


def compare_ratios(left: RatioMode, right: RatioMode, tact: str = "τ") -> RatioComparison:
    """Compare ratios under rational length dominance."""
    logger.debug("compare_ratios entry left=%s right=%s", left.word, right.word)
    gap = subtract_ratios(left, right, tact)
    result = RatioComparison(sign_of(ratio_shadow(gap)), gap)
    logger.debug("compare_ratios exit result=%r", result)
    return result


def ratio_magnitude(ratio: RatioMode, tact: str = "τ") -> RatioMode:
    """Return nonnegative ratio magnitude under length shadow."""
    logger.debug("ratio_magnitude entry ratio=%s", ratio.word)
    result = ratio_from_fraction(abs(ratio_shadow(ratio)), tact)
    logger.debug("ratio_magnitude exit result=%s", result.word)
    return result


def ratio_between(value: RatioMode, lower: RatioMode, upper: RatioMode, lower_closed: bool = True, upper_closed: bool = True) -> bool:
    """Return True iff value is inside a ratio interval."""
    logger.debug("ratio_between entry value=%s lower=%s upper=%s", value.word, lower.word, upper.word)
    item = ratio_shadow(value)
    lo = ratio_shadow(lower)
    hi = ratio_shadow(upper)
    left_ok = item >= lo if lower_closed else item > lo
    right_ok = item <= hi if upper_closed else item < hi
    result = left_ok and right_ok
    logger.debug("ratio_between exit result=%s", result)
    return result


def interval_contains(interval: RatioInterval, value: RatioMode) -> bool:
    """Return True iff interval contains value."""
    logger.debug("interval_contains entry interval=%r value=%s", interval, value.word)
    result = ratio_between(value, interval.lower, interval.upper, interval.lower_closed, interval.upper_closed)
    logger.debug("interval_contains exit result=%s", result)
    return result


def clamp_ratio(value: RatioMode, interval: RatioInterval, tact: str = "τ") -> RatioMode:
    """Clamp value into an interval under rational length order."""
    logger.debug("clamp_ratio entry value=%s interval=%r", value.word, interval)
    raw = ratio_shadow(value)
    clipped = min(max(raw, ratio_shadow(interval.lower)), ratio_shadow(interval.upper))
    result = ratio_from_fraction(clipped, tact)
    logger.debug("clamp_ratio exit result=%s", result.word)
    return result
