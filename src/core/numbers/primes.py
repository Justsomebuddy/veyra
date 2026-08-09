"""Prime and primitive variants for Veyra mode shadows."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .modes import Mode, cyclic_observer, is_ordered_primitive, natural_shadow, primitive_root

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PrimeProfile:
    """Small classification of prime-like properties for a mode."""

    mode: Mode
    numeric_prime: bool
    ordered_primitive: bool
    cyclic_primitive: bool
    ordered_resonance_prime: bool


def is_prime_int(value: int) -> bool:
    """Return True iff value is an ordinary prime integer."""
    logger.debug("is_prime_int entry value=%d", value)
    if value < 2:
        logger.debug("is_prime_int exit result=False small")
        return False
    if value == 2:
        logger.debug("is_prime_int exit result=True two")
        return True
    if value % 2 == 0:
        logger.debug("is_prime_int exit result=False even")
        return False
    factor = 3
    while factor * factor <= value:
        if value % factor == 0:
            logger.debug("is_prime_int exit result=False factor=%d", factor)
            return False
        factor += 2
    logger.debug("is_prime_int exit result=True")
    return True


def is_one_tact_numeric_prime(mode: Mode, tact: str = "τ") -> bool:
    """Return True iff mode is tau^p for an ordinary prime p."""
    logger.debug("is_one_tact_numeric_prime entry mode=%s tact=%r", mode.word, tact)
    if any(item != tact for item in mode.tacts):
        logger.debug("is_one_tact_numeric_prime exit result=False non_shadow")
        return False
    result = is_prime_int(natural_shadow(mode, tact))
    logger.debug("is_one_tact_numeric_prime exit result=%s", result)
    return result


def cyclic_root(mode: Mode) -> tuple[Mode, int]:
    """Return primitive root/exponent of the canonical cyclic rotation."""
    logger.debug("cyclic_root entry mode=%s", mode.word)
    canonical = Mode(cyclic_observer(mode))
    result = primitive_root(canonical)
    logger.debug("cyclic_root exit root=%s exponent=%d", result[0].word, result[1])
    return result


def is_cyclic_primitive(mode: Mode) -> bool:
    """Return True iff the cyclic class is not a power of a shorter cycle."""
    logger.debug("is_cyclic_primitive entry mode=%s", mode.word)
    if mode.length == 0:
        logger.debug("is_cyclic_primitive exit result=False silent")
        return False
    root, exponent = cyclic_root(mode)
    result = root.length == mode.length and exponent == 1
    logger.debug("is_cyclic_primitive exit result=%s", result)
    return result


def is_ordered_resonance_prime(mode: Mode) -> bool:
    """First resonance-prime proxy: length>1 and ordered-primitive."""
    logger.debug("is_ordered_resonance_prime entry mode=%s", mode.word)
    result = mode.length > 1 and is_ordered_primitive(mode)
    logger.debug("is_ordered_resonance_prime exit result=%s", result)
    return result


def prime_profile(mode: Mode, tact: str = "τ") -> PrimeProfile:
    """Return all currently defined prime-like classifications."""
    logger.debug("prime_profile entry mode=%s tact=%r", mode.word, tact)
    result = PrimeProfile(
        mode=mode,
        numeric_prime=is_one_tact_numeric_prime(mode, tact),
        ordered_primitive=is_ordered_primitive(mode),
        cyclic_primitive=is_cyclic_primitive(mode),
        ordered_resonance_prime=is_ordered_resonance_prime(mode),
    )
    logger.debug("prime_profile exit result=%r", result)
    return result
