"""Statistics concentration and likelihood certificate helper."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..shadows.ratio import ratio_from_ints, ratio_shadow
from ..shadows.statistics_concentration import bernoulli_likelihood_row, chebyshev_mean_bound, concentration_bound_card, decision_error_row, hoeffding_exponent_guard, likelihood_ratio_card, statistics_concentration_checklist

logger = logging.getLogger(__name__)


def certify_statistics_concentration_likelihood() -> Certificate:
    """Certify finite concentration, likelihood, and decision-error rows."""
    logger.debug("certify_statistics_concentration_likelihood entry")
    cheb = chebyshev_mean_bound(ratio_from_ints(3, 16), 4, ratio_from_ints(1, 2))
    hoeffding = hoeffding_exponent_guard(4, ratio_from_ints(1, 2), ratio_from_ints(1))
    likely = bernoulli_likelihood_row(3, 4, ratio_from_ints(3, 4))
    baseline = bernoulli_likelihood_row(3, 4, ratio_from_ints(1, 2))
    fp = decision_error_row(ratio_from_ints(3, 4), ratio_from_ints(1, 2), False)
    fn = decision_error_row(ratio_from_ints(1, 4), ratio_from_ints(1, 2), True)
    card = likelihood_ratio_card(likely, baseline)
    passed = ratio_shadow(cheb.evidence) == ratio_shadow(ratio_from_ints(3, 16)) and concentration_bound_card(cheb).relation == "informative" and ratio_shadow(hoeffding.evidence) == 2 and ratio_shadow(likely.likelihood) == ratio_shadow(ratio_from_ints(27, 256)) and card.relation == "left-preferred" and fp.outcome == "false-positive" and fn.outcome == "false-negative" and len(statistics_concentration_checklist()) == 5
    result = Certificate("statistics_concentration_likelihood", "finite concentration, Bernoulli likelihood geometry, false-positive/false-negative rows", passed, f"cheb={ratio_shadow(cheb.evidence)} like={ratio_shadow(likely.likelihood)} fp/fn", 1)
    logger.debug("certify_statistics_concentration_likelihood exit result=%r", result)
    return result
