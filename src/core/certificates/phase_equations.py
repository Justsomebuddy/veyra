"""Phase-equation normal-form certificate helper for the main Veyra suite."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..numbers.phase_equations import default_phase_basis, inverse_phase_obstruction_card, phase_coordinate_row, phase_equation_checklist, phase_equation_normal_form_card, phase_pair_row
from ..shadows.ratio import ratio_from_ints

logger = logging.getLogger(__name__)


def certify_phase_equation_normal_forms() -> Certificate:
    """Certify finite rational phase-equation rows and obstruction cards."""
    logger.debug("certify_phase_equation_normal_forms entry")
    basis = default_phase_basis()
    cos_row = phase_coordinate_row("cos", ratio_from_ints(3, 5), basis)
    pair_row = phase_pair_row(ratio_from_ints(3, 5), ratio_from_ints(4, 5), basis)
    normal_card = phase_equation_normal_form_card(ratio_from_ints(3, 5), ratio_from_ints(4, 5), basis)
    unit_card = inverse_phase_obstruction_card(ratio_from_ints(2), ratio_from_ints(0), basis)
    basis_card = inverse_phase_obstruction_card(ratio_from_ints(0), ratio_from_ints(1), basis)
    passed = cos_row.matches == ("a", "-a") and pair_row.matches == ("a",) and normal_card.relation == "resolved" and unit_card.obstruction == "unit-gap" and basis_card.obstruction == "basis-gap" and len(phase_equation_checklist()) == 4
    detail = f"basis={len(basis)} cos_matches={cos_row.matches} rejected={unit_card.obstruction}/{basis_card.obstruction}"
    result = Certificate("phase_equation_normal_forms", "rational phase equation normal forms and inverse obstruction cards", passed, detail, 1)
    logger.debug("certify_phase_equation_normal_forms exit result=%r", result)
    return result
