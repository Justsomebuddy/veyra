"""Direct level-1 certificate for P3-C1 generated finite confluence."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..confluence.generated.core import (
    GeneratedConfluenceStatus,
    GeneratedFiniteConfluence,
    StateRank,
    carry_normalization_probe,
    continuation_edge,
    continuation_state,
    generated_finite_confluence,
    generated_local_peaks,
    generated_reachable,
    local_join_cell,
    local_nonterminating_countermodel,
    ranked_continuation_system,
    validate_generated_confluence_result,
)
from ..confluence.generated.counterpressure import ATTACK_IDS, required_counterpressure

logger = logging.getLogger(__name__)


def _positive_package():
    logger.debug("_positive_package entry")
    states = tuple(continuation_state(name, "node", name.encode()) for name in ("v", "w", "x", "y", "z"))
    edges = (
        continuation_edge("wv", "w", "v", "step", b"wv"),
        continuation_edge("xy", "x", "y", "step", b"xy"),
        continuation_edge("xz", "x", "z", "step", b"xz"),
        continuation_edge("yw", "y", "w", "step", b"yw"),
        continuation_edge("zw", "z", "w", "step", b"zw"),
    )
    ranks = tuple(StateRank(name, rank) for name, rank in (("v", 0), ("w", 1), ("x", 3), ("y", 2), ("z", 2)))
    system = ranked_continuation_system("p3c1-doctrine", "cert-system", "v1", states, edges, ("x",), ranks)
    reachable, _ = generated_reachable(system)
    peaks = generated_local_peaks(system)
    edge_paths = {("xy", "xz"): (("yw",), ("zw",)), ("xz", "xy"): (("zw",), ("yw",))}
    cells = tuple(
        local_join_cell(
            system,
            peak.peak_id,
            *edge_paths[(peak.left_edge_id, peak.right_edge_id)],
            "w",
        )
        for peak in peaks
    )
    logger.debug("_positive_package exit peaks=%d", len(peaks))
    return system, cells


def certify_generated_confluence_p3c1() -> Certificate:
    """Certify exact generated coverage, structural Lean TLGC, and boundaries."""
    logger.debug("certify_generated_confluence_p3c1 entry")
    system, cells = _positive_package()
    first = generated_finite_confluence(system, cells)
    second = validate_generated_confluence_result(system, cells, first)
    counter = local_nonterminating_countermodel()
    probes = carry_normalization_probe()
    attacks = required_counterpressure(system, cells, first)
    passed = (
        type(first) is GeneratedFiniteConfluence
        and type(second) is GeneratedFiniteConfluence
        and first is not second
        and first == second
        and first.status is GeneratedConfluenceStatus.GENERATED_FINITE_CONFLUENT_RELATIVE_TO_SYSTEM
        and first.first_counterexample_peak_id is None
        and len(first.reachable_state_ids) == 5
        and len(first.reachable_edge_ids) == 5
        and tuple(row.attack_id for row in attacks) == ATTACK_IDS
        and all(row.passed for row in attacks)
        and counter.local_peaks_joinable
        and not counter.globally_confluent
        and len(probes) == 6
        and all(row.scope == "experiment-only-no-general-rule-source" for row in probes)
        and all(row.generated_peak_count > 0 and row.value_preserved for row in probes)
        and all(row.status == "generated-ranked-confluent" for row in probes)
    )
    result = Certificate(
        "generated_confluence_p3c1",
        "exact ranked finite source, complete generated ordered peaks, same-source local joins, structural no-axiom Lean TLGC",
        passed,
        "states=5 edges=5 peaks=2 lean=1 countermodels=10 carry_systems=6 promotions=0",
        1,
    )
    logger.debug("certify_generated_confluence_p3c1 exit passed=%s", passed)
    return result
