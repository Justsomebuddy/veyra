"""Ratio modes: Veyra shadow for fractions and rational arithmetic."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import logging

from .balance import BalanceMode, balance_from_int, stitch_balance
from .modes import Mode, natural_mode

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RatioMode:
    """A balance measured against a non-silent scale mode."""

    numerator: BalanceMode
    scale: Mode

    def __post_init__(self) -> None:
        """Validate non-silent scale."""
        logger.debug("RatioMode.__post_init__ entry scale=%s", self.scale.word)
        if self.scale.length == 0:
            logger.error("RatioMode invalid silent scale")
            raise ValueError("ratio scale must be non-silent")
        logger.debug("RatioMode.__post_init__ exit")

    @property
    def word(self) -> str:
        """Return compact ratio display."""
        logger.debug("RatioMode.word entry")
        result = f"({self.numerator.word})/{self.scale.word}"
        logger.debug("RatioMode.word exit result=%s", result)
        return result


def ratio_from_ints(numerator: int, denominator: int = 1, tact: str = "τ") -> RatioMode:
    """Create a one-tact ratio with rational shadow numerator/denominator."""
    logger.debug("ratio_from_ints entry numerator=%d denominator=%d", numerator, denominator)
    if denominator == 0:
        logger.error("ratio_from_ints zero denominator")
        raise ValueError("denominator must be nonzero")
    if denominator < 0:
        numerator, denominator = -numerator, -denominator
    result = RatioMode(balance_from_int(numerator, tact), natural_mode(denominator, tact))
    logger.debug("ratio_from_ints exit result=%s", result.word)
    return result


def ratio_from_fraction(value: Fraction, tact: str = "τ") -> RatioMode:
    """Create canonical one-tact ratio from Fraction."""
    logger.debug("ratio_from_fraction entry value=%s", value)
    result = ratio_from_ints(value.numerator, value.denominator, tact)
    logger.debug("ratio_from_fraction exit result=%s", result.word)
    return result


def ratio_shadow(ratio: RatioMode) -> Fraction:
    """Return exact rational shadow under length observer (host `Fraction`; external shadow layer)."""
    logger.debug("ratio_shadow entry ratio=%s", ratio.word)
    result = Fraction(ratio.numerator.net_length, ratio.scale.length)
    logger.debug("ratio_shadow exit result=%s", result)
    return result


def canonical_ratio(ratio: RatioMode, tact: str = "τ") -> RatioMode:
    """Reduce ratio by length observer into canonical one-tact form.

    Reduction — why 2/4 echoes 1/2 — is performed by host `Fraction` GCD, not
    by a mode-theoretic account; the `*_raw` operations preserve the native
    unreduced structure for callers that need it.
    """
    logger.debug("canonical_ratio entry ratio=%s tact=%r", ratio.word, tact)
    result = ratio_from_fraction(ratio_shadow(ratio), tact)
    logger.debug("canonical_ratio exit result=%s", result.word)
    return result


def negate_ratio(ratio: RatioMode) -> RatioMode:
    """Return additive opposite of ratio."""
    logger.debug("negate_ratio entry ratio=%s", ratio.word)
    result = RatioMode(BalanceMode(ratio.numerator.fading, ratio.numerator.arising), ratio.scale)
    logger.debug("negate_ratio exit result=%s", result.word)
    return result


def scale_mode_product(left: Mode, right: Mode) -> Mode:
    """Compose scale modes by length-weaving left across right."""
    logger.debug("scale_mode_product entry left=%s right=%s", left.word, right.word)
    result = Mode(left.tacts * right.length)
    logger.debug("scale_mode_product exit result=%s", result.word)
    return result


def scale_balance_by_mode(balance: BalanceMode, scale: Mode) -> BalanceMode:
    """Scale both balance poles by a scale-mode length without canonical collapse."""
    logger.debug("scale_balance_by_mode entry balance=%s scale=%s", balance.word, scale.word)
    result = BalanceMode(Mode(balance.arising.tacts * scale.length), Mode(balance.fading.tacts * scale.length))
    logger.debug("scale_balance_by_mode exit result=%s", result.word)
    return result


def multiply_balances_native(left: BalanceMode, right: BalanceMode) -> BalanceMode:
    """Multiply balances by polarity distribution without reducing to integers."""
    logger.debug("multiply_balances_native entry left=%s right=%s", left.word, right.word)
    positive = left.arising.tacts * right.arising.length + left.fading.tacts * right.fading.length
    negative = left.arising.tacts * right.fading.length + left.fading.tacts * right.arising.length
    result = BalanceMode(Mode(positive), Mode(negative))
    logger.debug("multiply_balances_native exit result=%s", result.word)
    return result


def add_ratios_raw(left: RatioMode, right: RatioMode) -> RatioMode:
    """Add ratios by native cross-scaling, preserving raw balance/scale structure."""
    logger.debug("add_ratios_raw entry left=%s right=%s", left.word, right.word)
    left_scaled = scale_balance_by_mode(left.numerator, right.scale)
    right_scaled = scale_balance_by_mode(right.numerator, left.scale)
    result = RatioMode(stitch_balance(left_scaled, right_scaled), scale_mode_product(left.scale, right.scale))
    logger.debug("add_ratios_raw exit result=%s", result.word)
    return result


def add_ratios(left: RatioMode, right: RatioMode, tact: str = "τ") -> RatioMode:
    """Add ratios by cross-scaling balances."""
    logger.debug("add_ratios entry left=%s right=%s", left.word, right.word)
    raw = add_ratios_raw(left, right)
    result = canonical_ratio(raw, tact)
    logger.debug("add_ratios exit result=%s", result.word)
    return result


def subtract_ratios_raw(left: RatioMode, right: RatioMode) -> RatioMode:
    """Subtract ratios by native raw addition with opposite."""
    logger.debug("subtract_ratios_raw entry left=%s right=%s", left.word, right.word)
    result = add_ratios_raw(left, negate_ratio(right))
    logger.debug("subtract_ratios_raw exit result=%s", result.word)
    return result


def subtract_ratios(left: RatioMode, right: RatioMode, tact: str = "τ") -> RatioMode:
    """Subtract ratios."""
    logger.debug("subtract_ratios entry left=%s right=%s", left.word, right.word)
    result = add_ratios(left, negate_ratio(right), tact)
    logger.debug("subtract_ratios exit result=%s", result.word)
    return result


def multiply_ratios_raw(left: RatioMode, right: RatioMode) -> RatioMode:
    """Multiply ratios natively without canonical length collapse."""
    logger.debug("multiply_ratios_raw entry left=%s right=%s", left.word, right.word)
    result = RatioMode(multiply_balances_native(left.numerator, right.numerator), scale_mode_product(left.scale, right.scale))
    logger.debug("multiply_ratios_raw exit result=%s", result.word)
    return result


def multiply_ratios(left: RatioMode, right: RatioMode, tact: str = "τ") -> RatioMode:
    """Multiply ratios in the length-shadow arithmetic layer."""
    logger.debug("multiply_ratios entry left=%s right=%s", left.word, right.word)
    result = canonical_ratio(multiply_ratios_raw(left, right), tact)
    logger.debug("multiply_ratios exit result=%s", result.word)
    return result


def inverse_ratio(ratio: RatioMode, tact: str = "τ") -> RatioMode:
    """Return multiplicative inverse in length-shadow layer (computed entirely in the host `Fraction` shadow)."""
    logger.debug("inverse_ratio entry ratio=%s", ratio.word)
    value = ratio_shadow(ratio)
    if value == 0:
        logger.error("inverse_ratio zero ratio")
        raise ValueError("zero ratio has no inverse")
    result = ratio_from_fraction(1 / value, tact)
    logger.debug("inverse_ratio exit result=%s", result.word)
    return result
