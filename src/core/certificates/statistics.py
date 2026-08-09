"""Statistics inference certificate helper for the main Veyra suite."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..shadows.ratio import ratio_from_ints, ratio_shadow
from ..shadows.statistics_inference import bernoulli_family, hypothesis_mean_card, interval_contains_shadow, mean_interval, sample_echo_from_ints, standard_error_shadow, statistics_inference_checklist

logger = logging.getLogger(__name__)


def certify_statistics_inference() -> Certificate:
    """Certify finite statistics inference shadows."""
    logger.debug("certify_statistics_inference entry")
    sample = sample_echo_from_ints([1, 2, 3])
    interval = mean_interval(sample, ratio_from_ints(1, 2))
    family = bernoulli_family(3, 4)
    accepted = hypothesis_mean_card(sample, ratio_from_ints(2), ratio_from_ints(0))
    rejected = hypothesis_mean_card(sample, ratio_from_ints(5), ratio_from_ints(1))
    uncertainty = standard_error_shadow(ratio_from_ints(3, 16), 4)
    passed = ratio_shadow(interval.center) == 2 and interval_contains_shadow(interval, ratio_from_ints(2)) and family.parameter_shadow("p") == "3/4" and accepted.relation == "accepted" and rejected.relation == "rejected" and ratio_shadow(uncertainty) == ratio_shadow(ratio_from_ints(3, 64)) and len(statistics_inference_checklist()) == 4
    result = Certificate("statistics_inference", "distribution family, interval, hypothesis, uncertainty seed", passed, f"center={ratio_shadow(interval.center)} p={family.parameter_shadow('p')}", 1)
    logger.debug("certify_statistics_inference exit result=%r", result)
    return result
