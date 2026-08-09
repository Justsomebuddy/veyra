"""Powers, roots, and logarithm shadows for Veyra transformers."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import logging

from .ratio import RatioMode, inverse_ratio, multiply_ratios, ratio_from_fraction, ratio_from_ints, ratio_shadow
from .transformer import ModeTransformer, compose_transformers, identity_transformer

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LiftResult:
    """Result of root/log lift attempt."""

    status: str
    value: RatioMode | int | None
    obstruction: str


@dataclass(frozen=True)
class IterationResult:
    """Result of transformer iteration."""

    transformer: ModeTransformer
    count: int


def iterate_transformer(transformer: ModeTransformer, times: int) -> IterationResult:
    """Compose transformer with itself a nonnegative number of times."""
    logger.debug("iterate_transformer entry name=%s times=%d", transformer.name, times)
    if times < 0:
        logger.error("iterate_transformer negative times=%d", times)
        raise ValueError("times must be nonnegative")
    result = identity_transformer()
    for _ in range(times):
        result = compose_transformers(transformer, result, f"{transformer.name}^{times}")
    payload = IterationResult(result, times)
    logger.debug("iterate_transformer exit degree=%d", result.degree)
    return payload


def ratio_power(value: RatioMode, exponent: int) -> RatioMode:
    """Raise ratio shadow to an integer power by repeated transformer-weave."""
    logger.debug("ratio_power entry value=%s exponent=%d", value.word, exponent)
    if exponent == 0:
        result = ratio_from_ints(1)
    elif exponent < 0:
        result = ratio_power(inverse_ratio(value), -exponent)
    else:
        result = ratio_from_ints(1)
        for _ in range(exponent):
            result = multiply_ratios(result, value)
    logger.debug("ratio_power exit result=%s", result.word)
    return result


def exact_integer_root(value: int, degree: int) -> int | None:
    """Return exact integer degree-root when it exists."""
    logger.debug("exact_integer_root entry value=%d degree=%d", value, degree)
    if degree <= 0:
        logger.error("exact_integer_root invalid degree=%d", degree)
        raise ValueError("degree must be positive")
    if value < 0 and degree % 2 == 0:
        logger.debug("exact_integer_root exit even negative none")
        return None
    sign = -1 if value < 0 else 1
    target = abs(value)
    lo, hi = 0, max(1, target)
    while lo <= hi:
        mid = (lo + hi) // 2
        power = mid ** degree
        if power == target:
            result = sign * mid
            logger.debug("exact_integer_root exit result=%d", result)
            return result
        if power < target:
            lo = mid + 1
        else:
            hi = mid - 1
    logger.debug("exact_integer_root exit none")
    return None


def nth_root_shadow(value: RatioMode, degree: int) -> LiftResult:
    """Try exact rational degree-root lift."""
    logger.debug("nth_root_shadow entry value=%s degree=%d", value.word, degree)
    shadow = ratio_shadow(value)
    num = exact_integer_root(shadow.numerator, degree)
    den = exact_integer_root(shadow.denominator, degree)
    if num is None or den is None:
        result = LiftResult("none", None, "irrational-shadow")
    else:
        result = LiftResult("unique", ratio_from_fraction(Fraction(num, den)), "none")
    logger.debug("nth_root_shadow exit status=%s", result.status)
    return result


def discrete_log_shadow(base: RatioMode, target: RatioMode, max_steps: int = 1024) -> LiftResult:
    """Find n with base^n=target in finite rational shadow search."""
    logger.debug("discrete_log_shadow entry base=%s target=%s max=%d", base.word, target.word, max_steps)
    if max_steps < 0:
        logger.error("discrete_log_shadow invalid max_steps=%d", max_steps)
        raise ValueError("max_steps must be nonnegative")
    current = ratio_from_ints(1)
    target_shadow = ratio_shadow(target)
    for step in range(max_steps + 1):
        if ratio_shadow(current) == target_shadow:
            result = LiftResult("unique", step, "none")
            logger.debug("discrete_log_shadow exit step=%d", step)
            return result
        current = multiply_ratios(current, base)
    result = LiftResult("none", None, "outside-search-window")
    logger.debug("discrete_log_shadow exit none")
    return result
