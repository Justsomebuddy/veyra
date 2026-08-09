"""Public P1-C4 finite scoped-object formation surface."""

from __future__ import annotations

import logging

from .codec import ScopedFormationValidationError
from .result_validation import validate_scoped_formation_result
from .runtime import finite_scoped_formation_rule, scoped_formation_judgment
from .scope import (
    formation_scope, snapshot_formation_scope,
)
from .refinement import formation_refinement_requirement
from .sources import (
    bound_g4_bridge_source, bound_patch_requirement,
    finite_scoped_formation_rule_source, formation_persistence_requirement,
    formation_policy, g4_bridge_mappings, stage_map_row,
)
from .types import *  # noqa: F403

logger = logging.getLogger(__name__)


def scoped_formation_scope_boundary() -> tuple[str, ...]:
    """Expose permanent C4 nonclaims without promoting a presentation."""
    logger.debug("scoped_formation_scope_boundary entry")
    from .types import SCOPED_FORMATION_NONCLAIMS
    result = SCOPED_FORMATION_NONCLAIMS
    logger.debug("scoped_formation_scope_boundary exit rows=%d", len(result))
    return result


__all__ = [
    "ScopedFormationValidationError", "bound_g4_bridge_source",
    "bound_patch_requirement", "finite_scoped_formation_rule",
    "finite_scoped_formation_rule_source", "formation_persistence_requirement",
    "formation_policy", "formation_refinement_requirement", "formation_scope",
    "g4_bridge_mappings", "scoped_formation_judgment",
    "scoped_formation_scope_boundary", "snapshot_formation_scope",
    "stage_map_row", "validate_scoped_formation_result",
]
