"""Direct level-1 certificate for exact raw-P1-backed P3-T1--T4."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..observer.network.attack_certificate import observer_network_attack_results
from ..observer.network.core import (
    LawStatus,
    RefinementStatus,
    TriangleStatus,
    example_observer_network,
    observer_network_judgment,
    validate_observer_network_result,
)

logger = logging.getLogger(__name__)


def certify_observer_network_p3t() -> Certificate:
    """Certify actual P1 rows, arbitrary finite closure, laws, and boundaries."""
    logger.debug("certify_observer_network_p3t entry")
    source = example_observer_network()
    first = observer_network_judgment(source)
    second = validate_observer_network_result(source, first)
    edge = {item.edge_id: item for item in first.edges}
    triangle = {item.demand_id: item for item in first.triangles}
    pair = {(item.source_observer_id, item.target_observer_id): item for item in first.observer_pairs}
    raw_rows = sum(len(item.relation_rows) for item in first.edges)
    attacks = observer_network_attack_results()
    attack_count = len(attacks)
    passed = (
        first == second
        and first is not second
        and len(first.identities) == 5
        and len(first.evaluation_domains) == 5
        and len(first.edges) == 7
        and raw_rows == 112
        and all(len(item.relation_rows) == 16 for item in first.edges)
        and edge["total-crest"].refinement is RefinementStatus.STRICT
        and edge["hole-crest"].relation_preserving is LawStatus.OPEN
        and edge["hole-crest"].translation_preserving is LawStatus.ESTABLISHED
        and edge["triply-total-partial"].translation_preserving is LawStatus.REFUTED
        and len(first.isomorphisms) == 1
        and first.isomorphisms[0].status is LawStatus.ESTABLISHED
        and first.isomorphisms[0].forward_round_trip is LawStatus.ESTABLISHED
        and first.isomorphisms[0].reverse_round_trip is LawStatus.ESTABLISHED
        and first.isomorphisms[0].forward_evaluation_commutes is LawStatus.ESTABLISHED
        and first.isomorphisms[0].reverse_evaluation_commutes is LawStatus.ESTABLISHED
        and pair[("fine-triply-nested", "coarse-crest")].path_edge_ids
        == ("triply-nested", "nested-total", "total-crest")
        and pair[("fine-triply-nested", "coarse-crest")].status is RefinementStatus.STRICT
        and all(item.status is LawStatus.ESTABLISHED for item in first.associativity)
        and triangle["triangle-exact"].status is TriangleStatus.ESTABLISHED
        and triangle["triangle-partial"].status is TriangleStatus.AGREES_ON_DOMAIN_INTERSECTION
        and first.strict_cycle_status is LawStatus.ESTABLISHED
        and attack_count == 18
        and all(status for _, status in attacks)
        and first.promotions == 0
    )
    detail = (
        f"observers=5 edges=7 raw_a2_rows={raw_rows} pairs={len(first.compositions)} "
        f"triples={len(first.associativity)} triangles=2 isomorphisms=1 attacks={attack_count} promotions=0"
    )
    result = Certificate(
        "observer_network_p3t",
        "one exact P1-bound finite translation network with nonvacuous maps, raw A2 rows, units, composition, arbitrary finite path closure, and demanded triangles",
        passed,
        detail,
        1,
    )
    logger.debug("certify_observer_network_p3t exit passed=%s", passed)
    return result
