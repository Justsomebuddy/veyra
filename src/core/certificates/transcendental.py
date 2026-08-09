"""Transcendental/limit algebra certificate helper for the main Veyra suite."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..shadows.ratio import ratio_from_ints, ratio_shadow
from ..shadows.transcendental_limit import alternating_log1p_envelope, alternating_tail_bound_card, exp_derivative_card, exp_series, log1p_derivative_card, transcendental_limit_checklist

logger = logging.getLogger(__name__)


def certify_transcendental_limit() -> Certificate:
    """Certify finite transcendental series and tail-envelope seeds."""
    logger.debug("certify_transcendental_limit entry")
    exp = exp_series(4)
    exp_card = exp_derivative_card(4)
    log_card = log1p_derivative_card(4)
    envelope = alternating_log1p_envelope(4, ratio_from_ints(1, 2))
    tail_card = alternating_tail_bound_card(4, ratio_from_ints(1, 2))
    passed = [str(ratio_shadow(c)) for c in exp.coefficients] == ["1", "1", "1/2", "1/6", "1/24"] and exp_card.relation == "coherent" and log_card.relation == "coherent" and envelope.as_dict()["radius"] == "1/160" and tail_card.relation == "bounded" and len(transcendental_limit_checklist()) == 4
    detail = f"exp_order={exp.order} log_center={envelope.as_dict()['center']} radius={envelope.as_dict()['radius']}"
    result = Certificate("transcendental_limit", "finite exp/log series and alternating tail envelope", passed, detail, 1)
    logger.debug("certify_transcendental_limit exit result=%r", result)
    return result
