"""Narrow non-root public facade for P1-A transport v2."""

from __future__ import annotations
import logging
from .composition import compose_p1a_realization_transport_v2, identity_p1a_realization_transport_v2
from .runtime import p1a_realization_transport_v2, verify_p1a_realization_transport_v2

logger = logging.getLogger(__name__)


def p1a_realization_transport_v2_scope_boundary() -> tuple[str, ...]:
    logger.debug("p1a v2 scope boundary entry")
    result = (
        "finite-same-doctrine-strong-all-status-replayed-no-category-or-lifecycle-claim",
        "v1-remains-byte-and-api-exact",
        "nonempty-projection-with-empty-blocker-filter-is-undefined",
        "no-cross-doctrine-transport",
        "no-vertical-closure-or-cost-law",
        "no-category-functor-naturality-theorem",
        "no-formation-role-history-token-efficacy-or-promotion",
    )
    logger.debug("p1a v2 scope boundary exit items=%d", len(result))
    return result


__all__ = [
    "compose_p1a_realization_transport_v2",
    "identity_p1a_realization_transport_v2",
    "p1a_realization_transport_v2",
    "p1a_realization_transport_v2_scope_boundary",
    "verify_p1a_realization_transport_v2",
]
