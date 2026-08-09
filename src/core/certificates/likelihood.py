"""Likelihood geometry certificate hook for Veyra."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..shadows.likelihood_geometry import finite_likelihood_segments, likelihood_geometry_checklist, likelihood_geometry_summary, likelihood_grid, likelihood_peak_card, residual_family_certificates
from ..shadows.ratio import ratio_from_ints, ratio_shadow

logger = logging.getLogger(__name__)


def certify_likelihood_geometry_x5() -> Certificate:
    """Certify Sprint X5 finite likelihood geometry and residual families."""
    logger.debug("certify_likelihood_geometry_x5 entry")
    points = likelihood_grid()
    segments = finite_likelihood_segments(points)
    peak = likelihood_peak_card(points)
    certs = residual_family_certificates()
    summary = likelihood_geometry_summary()
    expected = {"likelihood_points": 3, "segments": 2, "rising_segments": 2, "residual_certificates": 2, "fit_domains": 1, "blocked_domains": 1, "checklist": 4}
    passed = summary == expected and ratio_shadow(peak.parameter) == ratio_shadow(ratio_from_ints(3, 4)) and ratio_shadow(peak.likelihood) == ratio_shadow(ratio_from_ints(27, 256)) and [item.relation for item in segments] == ["rising", "rising"] and [item.status for item in certs] == ["certified", "blocked"] and len(likelihood_geometry_checklist()) == 4
    result = Certificate("likelihood_geometry_x5", "finite likelihood geometry and residual family certificates", passed, f"points={summary['likelihood_points']} blocked={summary['blocked_domains']}", 1)
    logger.debug("certify_likelihood_geometry_x5 exit result=%r", result)
    return result
