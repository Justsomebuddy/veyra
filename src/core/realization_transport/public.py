"""Narrow public surface for realization transport research evidence."""

from __future__ import annotations

import logging

from .runtime import (
    compose_realization_context_morphisms,
    identity_realization_context_morphism,
    realization_context_morphism,
    verify_realization_transport,
)

logger = logging.getLogger(__name__)


def realization_transport_scope_boundary() -> tuple[str, ...]:
    """Return fixed limitations of the first transport contract."""
    logger.debug("realization_transport_scope_boundary entry")
    result = (
        "finite-relative-replayed-single-arrow-no-category-or-functor-claim",
        "no-cross-doctrine-transport",
        "no-p1a-response-transport",
        "no-natural-quotient-section",
        "same-exact-p1-doctrine-only",
        "exact-recurrence-preserving-total-finite-index-map-only",
        "closure-action-is-contravariant-partition-pullback",
        "endpoint-witnesses-are-authoritatively-replayed",
        "costs-are-nonincreasing-not-generally-exact",
        "local-names-ordinals-generators-and-representatives-do-not-transport",
        "no-p1a-cross-doctrine-or-covariant-pushforward-claim",
        "single-arrow-identity-and-composition-evidence-not-category-or-functor-proof",
        "digests-bind-integrity-not-authentication",
        "finite-relative-executable-evidence-not-theorem-or-promotion",
    )
    logger.debug("realization_transport_scope_boundary exit items=%d", len(result))
    return result


__all__ = [
    "compose_realization_context_morphisms",
    "identity_realization_context_morphism",
    "realization_context_morphism",
    "realization_transport_scope_boundary",
    "verify_realization_transport",
]
