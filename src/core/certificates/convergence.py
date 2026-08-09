"""Convergence algebra certificate helper for the main Veyra suite."""

from __future__ import annotations

from fractions import Fraction
import logging

from ..certify_types import Certificate
from ..shadows.completion import make_interval
from ..shadows.convergence_algebra import cauchy_tail_card, convergence_algebra_checklist, majorant_bound_card, nested_interval_card, radius_guard_card
from ..shadows.ratio import ratio_from_ints

logger = logging.getLogger(__name__)


def certify_convergence_algebra() -> Certificate:
    """Certify finite Cauchy/majorant/nested/radius convergence seed."""
    logger.debug("certify_convergence_algebra entry")
    samples = tuple(ratio_from_ints(n, d) for n, d in ((1, 1), (3, 2), (7, 4), (15, 8), (31, 16)))
    intervals = (
        make_interval(Fraction(1), Fraction(2), "i0"),
        make_interval(Fraction(5, 4), Fraction(7, 4), "i1"),
        make_interval(Fraction(11, 8), Fraction(13, 8), "i2"),
    )
    cauchy = cauchy_tail_card(samples, ratio_from_ints(1, 2), 3)
    majorant = majorant_bound_card("tail-majorant", ratio_from_ints(3, 16), ratio_from_ints(1, 4))
    nested = nested_interval_card("nested-shrink", intervals)
    radius = radius_guard_card("log1p-radius", ratio_from_ints(1, 2), ratio_from_ints(1))
    passed = cauchy.relation == "stable" and majorant.relation == "bounded" and nested.relation == "nested" and radius.relation == "inside" and len(convergence_algebra_checklist()) == 4
    detail = f"cauchy={cauchy.evidence[0][1]} nested={nested.evidence[1][1]} radius={radius.relation}"
    result = Certificate("convergence_algebra", "Cauchy tails, majorants, nested intervals, radius guards", passed, detail, 1)
    logger.debug("certify_convergence_algebra exit result=%r", result)
    return result
