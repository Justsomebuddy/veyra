"""Scale-memory logarithm certificate helper."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..shadows.ratio import ratio_from_ints, ratio_shadow
from ..shadows.scale_memory_log import finite_field_log_fixture, recover_transition_depth, scale_memory_log_checklist, scale_memory_obstruction_card

logger = logging.getLogger(__name__)


def certify_scale_memory_log() -> Certificate:
    """Certify transition-depth recovery, residual log, cyclic unwrap, and obstruction rows."""
    logger.debug("certify_scale_memory_log entry")
    exact = recover_transition_depth("doubling-exact", ratio_from_ints(2), ratio_from_ints(32), 10)
    approximate = recover_transition_depth("doubling-residual", ratio_from_ints(2), ratio_from_ints(20), 6, ratio_from_ints(4))
    cyclic = finite_field_log_fixture()
    obstruction = scale_memory_obstruction_card()
    passed = exact.status == "exact" and exact.candidate.depth == 5 and approximate.status == "approximate" and approximate.candidate.depth == 4 and ratio_shadow(approximate.candidate.residual) == 4 and cyclic.status == "exact" and cyclic.candidate_depth == 17 and obstruction.obstruction == "cycle-collapse" and len(scale_memory_log_checklist()) == 4
    detail = f"exact={exact.candidate.depth} residual={ratio_shadow(approximate.candidate.residual)} cyclic={cyclic.candidate_depth} obstruction={obstruction.obstruction}"
    result = Certificate("scale_memory_log", "transition-depth recovery, residual log, cyclic unwrap, obstruction certificates", passed, detail, 1)
    logger.debug("certify_scale_memory_log exit result=%r", result)
    return result
