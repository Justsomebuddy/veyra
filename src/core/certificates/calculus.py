"""Calculus-depth certificate helper for the main Veyra suite."""

from __future__ import annotations

import logging

from ..shadows.calculus_depth import calculus_depth_checklist, chain_rule_card, integral_coherence_card, local_linearization, product_rule_card
from ..certify_types import Certificate
from ..shadows.polynomial import polynomial_from_ints
from ..shadows.ratio import ratio_from_ints, ratio_shadow

logger = logging.getLogger(__name__)


def certify_calculus_depth() -> Certificate:
    """Certify polynomial calculus-depth shadows."""
    logger.debug("certify_calculus_depth entry")
    square = polynomial_from_ints([0, 0, 1])
    shift = polynomial_from_ints([1, 1])
    linear = polynomial_from_ints([0, 2])
    tangent = local_linearization(square, ratio_from_ints(3))
    product = product_rule_card(square, shift)
    chain = chain_rule_card(square, shift)
    integral = integral_coherence_card(linear, ratio_from_ints(0), ratio_from_ints(3), ratio_from_ints(9))
    passed = ratio_shadow(tangent.slope) == 6 and product.relation == "coherent" and chain.relation == "coherent" and integral.relation == "coherent" and len(calculus_depth_checklist()) == 4
    result = Certificate("calculus_depth", "local linearization, derivative rules, integral coherence", passed, f"slope={ratio_shadow(tangent.slope)} integral={integral.relation}", 1)
    logger.debug("certify_calculus_depth exit result=%r", result)
    return result
