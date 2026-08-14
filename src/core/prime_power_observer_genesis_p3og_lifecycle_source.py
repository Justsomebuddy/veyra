"""Outcome-free source binding for bounded P3-OG lifecycle replay."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest
import logging

from .prime_power_observer_genesis_p3og_codec import canonical_bytes
from .prime_power_observer_genesis_p3og_lifecycle_codec import lifecycle_digest
from .prime_power_observer_genesis_p3og_lifecycle_types import P3OGFormationSource
from .prime_power_observer_genesis_p3og_source import (
    _deterministic_select_validated,
    validate_source,
)
from .prime_power_observer_genesis_p3og_types import (
    DeterministicSelectionReceipt,
    P3OGSource,
)

logger = logging.getLogger(__name__)
FORMATION_SOURCE_VERSION = "p3og-formation-source-v1"
CLOSURE_RULE_ID = "least-nontrivial-return-v1"


def p3og_formation_source(source: P3OGSource) -> P3OGFormationSource:
    """Bind the selected committed cycle as an outcome-free formation word."""
    logger.debug("p3og.lifecycle.source entry")
    try:
        source = validate_source(source)
        selection = _deterministic_select_validated(source)
        selected = source.seeds[selection.selected_index]
        fields = (
            FORMATION_SOURCE_VERSION,
            source.source_digest,
            selection,
            selected.seed_digest,
            selected.cycle,
            CLOSURE_RULE_ID,
        )
        result = P3OGFormationSource(
            *fields,
            lifecycle_digest("formation-source", *fields),
        )
    except (AttributeError, IndexError, TypeError, UnicodeError, ValueError) as exc:
        logger.error("p3og.lifecycle.source error type=%s", type(exc).__name__)
        raise
    logger.debug(
        "p3og.lifecycle.source exit source=%s",
        result.source_digest[:12],
    )
    return result


def validate_formation_source(
    source: P3OGSource,
    formation_source: P3OGFormationSource,
) -> tuple[P3OGSource, P3OGFormationSource]:
    """Freshly rebuild an exact lifecycle source without trusting its digests."""
    logger.debug("p3og.lifecycle.validate_source entry")
    source = validate_source(source)
    if type(formation_source) is not P3OGFormationSource:
        logger.error("p3og.lifecycle.validate_source wrong outer type")
        raise ValueError("p3og-formation-source-type")
    try:
        if type(formation_source.selection) is not DeterministicSelectionReceipt:
            logger.error("p3og.lifecycle.validate_source wrong selection type")
            raise ValueError("p3og-formation-source-selection")
        if type(formation_source.formation_word) is not tuple or not 2 <= len(formation_source.formation_word) <= 64:
            logger.error("p3og.lifecycle.validate_source invalid word envelope")
            raise ValueError("p3og-formation-source-word")
        expected = p3og_formation_source(source)
        equal = compare_digest(
            canonical_bytes(formation_source),
            canonical_bytes(expected),
        )
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        logger.error(
            "p3og.lifecycle.validate_source malformed type=%s",
            type(exc).__name__,
        )
        raise ValueError("p3og-formation-source-malformed") from exc
    if not equal:
        logger.error("p3og.lifecycle.validate_source source drift")
        raise ValueError("p3og-formation-source-drift")
    result = (source, replace(expected))
    logger.debug(
        "p3og.lifecycle.validate_source exit source=%s",
        result[1].source_digest[:12],
    )
    return result
