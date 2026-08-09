"""Weave schemas for Veyra mode shadows."""

from __future__ import annotations

import logging

from .modes import Mode, cyclic_observer, substitute_mode

logger = logging.getLogger(__name__)


def cyclic_representative(mode: Mode) -> Mode:
    """Return the canonical rotation representative of a closed mode."""
    logger.debug("cyclic_representative entry mode=%s", mode.word)
    result = Mode(cyclic_observer(mode))
    logger.debug("cyclic_representative exit result=%s", result.word)
    return result


def ordered_weave(driver: Mode, mapping: dict[str, Mode]) -> Mode:
    """Linear substitution weave that preserves the chosen word cut."""
    logger.debug("ordered_weave entry driver=%s keys=%r", driver.word, sorted(mapping))
    result = substitute_mode(driver, mapping)
    logger.debug("ordered_weave exit result=%s", result.word)
    return result


def cyclic_weave(driver: Mode, mapping: dict[str, Mode]) -> Mode:
    """Cyclic weave via canonical driver cut and canonical output rotation."""
    logger.debug("cyclic_weave entry driver=%s keys=%r", driver.word, sorted(mapping))
    canonical_driver = cyclic_representative(driver)
    substituted = substitute_mode(canonical_driver, mapping)
    result = cyclic_representative(substituted)
    logger.debug(
        "cyclic_weave exit canonical_driver=%s substituted=%s result=%s",
        canonical_driver.word,
        substituted.word,
        result.word,
    )
    return result


def compare_ordered_cyclic(driver: Mode, mapping: dict[str, Mode]) -> tuple[Mode, Mode]:
    """Return ordered and cyclic weave outputs for the same driver."""
    logger.debug("compare_ordered_cyclic entry driver=%s", driver.word)
    result = (ordered_weave(driver, mapping), cyclic_weave(driver, mapping))
    logger.debug("compare_ordered_cyclic exit ordered=%s cyclic=%s", result[0].word, result[1].word)
    return result
