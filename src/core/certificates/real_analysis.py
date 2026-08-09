"""Real-analysis structure certificate helper."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..shadows.ratio import ratio_from_ints, ratio_shadow
from ..shadows.real_analysis_structure import area_refinement_certificate, derivative_refinement_certificate, finite_modulus_certificate, jump_obstruction_card, real_analysis_structure_checklist, square_rule, identity_rule

logger = logging.getLogger(__name__)


def certify_real_analysis_structure() -> Certificate:
    """Certify finite real-analysis structure rows."""
    logger.debug("certify_real_analysis_structure entry")
    grid = tuple(ratio_from_ints(n, 4) for n in range(5))
    modulus = finite_modulus_certificate("square-grid-modulus", square_rule, grid, ratio_from_ints(1, 4), ratio_from_ints(1, 2))
    derivative = derivative_refinement_certificate(square_rule, ratio_from_ints(2), (ratio_from_ints(1), ratio_from_ints(1, 2), ratio_from_ints(1, 4)), ratio_from_ints(0))
    area = area_refinement_certificate(identity_rule, ratio_from_ints(0), ratio_from_ints(1), (2, 4, 8), ratio_from_ints(0))
    jump = jump_obstruction_card()
    passed = ratio_shadow(modulus.max_output_drift) == ratio_shadow(ratio_from_ints(7, 16)) and modulus.status == "stable" and derivative.values == (ratio_from_ints(4), ratio_from_ints(4), ratio_from_ints(4)) and area.values == (ratio_from_ints(1, 2), ratio_from_ints(1, 2), ratio_from_ints(1, 2)) and jump.relation == "blocked" and len(real_analysis_structure_checklist()) == 4
    detail = f"modulus={ratio_shadow(modulus.max_output_drift)} derivative={ratio_shadow(derivative.values[0])} area={ratio_shadow(area.values[0])} jump={jump.relation}"
    result = Certificate("real_analysis_structure", "finite modulus/refinement/jump-obstruction rows", passed, detail, 1)
    logger.debug("certify_real_analysis_structure exit result=%r", result)
    return result
