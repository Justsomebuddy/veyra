"""Certificate for the bounded S7 topological observer separation."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..observer.gap_topology import (
    finite_topological_separation_theorem,
    observer_class_definitions,
    observer_gap_topology_summary,
)

logger = logging.getLogger(__name__)


def certify_observer_gap_topology_s7() -> Certificate:
    """Certify the declared five-row factor-class separation only."""
    logger.debug("certify_observer_gap_topology_s7 entry")
    card = finite_topological_separation_theorem()
    baseline, extended = observer_class_definitions()
    summary = observer_gap_topology_summary()
    passed = (
        card.theorem_id == "THM-S7-001"
        and card.status == "finite-checked"
        and baseline.class_id == card.baseline_class_id
        and extended.class_id == card.observer_class_id
        and summary["rows"] == 5
        and summary["baseline_equal"] == 5
        and summary["observer_separates"] == 5
        and summary["bounded"] is True
    )
    detail = (
        "rows=5 degree-factor-equal=5 topological-order-separated=5 "
        "scope=declared-finite-corpus nonclaims=minimality,all-DAG,superiority"
    )
    result = Certificate(
        "observer_gap_topology_s7",
        "finite topological-order separation from the declared degree-factor observer class",
        passed,
        detail,
        1,
    )
    if not passed:
        logger.error("certify_observer_gap_topology_s7 failed detail=%s", detail)
    logger.debug("certify_observer_gap_topology_s7 exit result=%r", result)
    return result
