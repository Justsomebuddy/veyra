"""Weighted echo measure certificate helper."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..shadows.ratio import ratio_shadow
from ..shadows.weighted_measure import coverage_row, finite_additivity_row, overlap_gap_card, pushforward_by_tact, weighted_echo_measure, weighted_measure_checklist

logger = logging.getLogger(__name__)


def certify_weighted_echo_measure() -> Certificate:
    """Certify finite weighted-echo measure rows."""
    logger.debug("certify_weighted_echo_measure entry")
    measure = weighted_echo_measure()
    coverage = coverage_row(measure, "alpha-beta", frozenset({"alpha", "beta"}))
    additivity = finite_additivity_row(measure, "partition", frozenset({"alpha"}), frozenset({"beta", "gamma"}))
    push = {row.target: row for row in pushforward_by_tact(measure)}
    overlap = overlap_gap_card(measure)
    passed = measure.total_weight == 6 and ratio_shadow(coverage.mass) == ratio_shadow(coverage.complement) == ratio_shadow(additivity.union_mass) / 2 and additivity.relation == "additive" and ratio_shadow(additivity.union_mass) == 1 and ratio_shadow(push["warm"].target_mass) == ratio_shadow(coverage.complement) / 3 and ratio_shadow(push["cool"].target_mass) == ratio_shadow(additivity.union_mass) * 5 / 6 and overlap.relation == "blocked-naive" and len(weighted_measure_checklist()) == 4
    detail = f"coverage={ratio_shadow(coverage.mass)} cool={ratio_shadow(push['cool'].target_mass)} overlap={overlap.obstruction}"
    result = Certificate("weighted_echo_measure", "finite weighted echo measure, additivity, pushforward coverage", passed, detail, 1)
    logger.debug("certify_weighted_echo_measure exit result=%r", result)
    return result
