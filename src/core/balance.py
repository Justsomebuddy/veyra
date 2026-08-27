"""Opposite and balance modes: Veyra shadow for signed arithmetic."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import logging

from .modes import Mode, cyclic_observer, natural_mode

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BalanceMode:
    """A mode pair: arising recurrence opposed by fading recurrence."""

    arising: Mode
    fading: Mode

    @property
    def net_length(self) -> int:
        """Return length-observer signed shadow (host `int` subtraction; external shadow per docs/06 §3)."""
        logger.debug("BalanceMode.net_length entry arising=%s fading=%s", self.arising.word, self.fading.word)
        result = self.arising.length - self.fading.length
        logger.debug("BalanceMode.net_length exit result=%d", result)
        return result

    @property
    def word(self) -> str:
        """Return compact balance display."""
        logger.debug("BalanceMode.word entry")
        result = f"{self.arising.word}⇅{self.fading.word}"
        logger.debug("BalanceMode.word exit result=%s", result)
        return result


def balance_from_int(value: int, tact: str = "τ") -> BalanceMode:
    """Create one-tact balance with integer shadow value."""
    logger.debug("balance_from_int entry value=%d tact=%r", value, tact)
    if value >= 0:
        result = BalanceMode(natural_mode(value, tact), Mode(()))
    else:
        result = BalanceMode(Mode(()), natural_mode(-value, tact))
    logger.debug("balance_from_int exit result=%s", result.word)
    return result


def opposite_balance(balance: BalanceMode) -> BalanceMode:
    """Swap arising and fading modes."""
    logger.debug("opposite_balance entry balance=%s", balance.word)
    result = BalanceMode(balance.fading, balance.arising)
    logger.debug("opposite_balance exit result=%s", result.word)
    return result


def stitch_balance(left: BalanceMode, right: BalanceMode) -> BalanceMode:
    """Add balances by stitching same-polarity components."""
    logger.debug("stitch_balance entry left=%s right=%s", left.word, right.word)
    result = BalanceMode(left.arising.stitch(right.arising), left.fading.stitch(right.fading))
    logger.debug("stitch_balance exit result=%s", result.word)
    return result


def subtract_balance(left: BalanceMode, right: BalanceMode) -> BalanceMode:
    """Subtract by stitching with the opposite balance."""
    logger.debug("subtract_balance entry left=%s right=%s", left.word, right.word)
    result = stitch_balance(left, opposite_balance(right))
    logger.debug("subtract_balance exit result=%s", result.word)
    return result


def canonical_length_balance(balance: BalanceMode, tact: str = "τ") -> BalanceMode:
    """Cancel by length-observer and return one-tact canonical balance.

    The pair construction (`stitch_balance`, `opposite_balance`) is native;
    this quotient is not: cancellation is performed by the host integer shadow
    round-trip, not by tact-level rewriting.
    """
    logger.debug("canonical_length_balance entry balance=%s tact=%r", balance.word, tact)
    result = balance_from_int(balance.net_length, tact)
    logger.debug("canonical_length_balance exit result=%s", result.word)
    return result


def balance_echo_key(balance: BalanceMode, test_name: str = "length") -> object:
    """Return balance observer key under length, bag, ordered, or cycle test."""
    logger.debug("balance_echo_key entry balance=%s test=%s", balance.word, test_name)
    if test_name == "length":
        result: object = balance.net_length
    elif test_name == "ordered":
        result = (balance.arising.tacts, balance.fading.tacts)
    elif test_name == "cycle":
        result = (cyclic_observer(balance.arising), cyclic_observer(balance.fading))
    elif test_name == "bag":
        diff = Counter(balance.arising.tacts)
        diff.subtract(Counter(balance.fading.tacts))
        result = tuple(sorted((tact, count) for tact, count in diff.items() if count))
    else:
        logger.error("balance_echo_key unknown test=%s", test_name)
        raise ValueError(f"unknown balance test: {test_name}")
    logger.debug("balance_echo_key exit result=%r", result)
    return result


def balance_echo_equivalent(left: BalanceMode, right: BalanceMode, test_name: str = "length") -> bool:
    """Return True iff two balances echo under a balance observer."""
    logger.debug("balance_echo_equivalent entry left=%s right=%s test=%s", left.word, right.word, test_name)
    result = balance_echo_key(left, test_name) == balance_echo_key(right, test_name)
    logger.debug("balance_echo_equivalent exit result=%s", result)
    return result


def multiply_balance_by_natural(balance: BalanceMode, times: int) -> BalanceMode:
    """Repeat both polar components by a nonnegative natural multiplier."""
    logger.debug("multiply_balance_by_natural entry balance=%s times=%d", balance.word, times)
    if times < 0:
        logger.error("multiply_balance_by_natural invalid times=%d", times)
        raise ValueError("times must be non-negative")
    result = BalanceMode(Mode(balance.arising.tacts * times), Mode(balance.fading.tacts * times))
    logger.debug("multiply_balance_by_natural exit result=%s", result.word)
    return result
