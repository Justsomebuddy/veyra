"""Trigonometry identity certificate helper for the main Veyra suite."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..shadows.trigonometry_identities import double_angle_identity_card, inverse_phase_identity_card, pythagorean_identity_card, sum_angle_identity_card, trig_vector_from_ints, trigonometry_identity_checklist

logger = logging.getLogger(__name__)


def certify_trigonometry_identities() -> Certificate:
    """Certify rational trigonometry identity theorem cards."""
    logger.debug("certify_trigonometry_identities entry")
    first = trig_vector_from_ints(3, 4, 5, "a")
    second = trig_vector_from_ints(5, 12, 13, "b")
    cards = (pythagorean_identity_card(first), sum_angle_identity_card(first, second), double_angle_identity_card(first), inverse_phase_identity_card(first))
    passed = all(card.relation == "coherent" for card in cards) and len(trigonometry_identity_checklist()) == 4
    result = Certificate("trigonometry_identities", "rational unit phase, sum/double/inverse identity cards", passed, f"cards={','.join(card.name for card in cards)}", 1)
    logger.debug("certify_trigonometry_identities exit result=%r", result)
    return result
