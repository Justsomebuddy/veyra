"""Executable independent attack results consumed by the P3-T certificate."""

from __future__ import annotations

from dataclasses import replace
import inspect
import logging

from .coherence import strict_cycle_check
from .common import ObserverNetworkError
from .examples import example_observer_network
from .maps import compose_path, operational_edge_map
from .preflight import network_resource_policy
from .relations import isomorphism_judgment
from .result_validation import validate_observer_network_result
from .runtime import observer_network_judgment
from .source import (
    observer_network_source,
    translation_row,
    translation_source,
    typed_value,
)
from .types import LawStatus, RefinementStatus, TriangleStatus
from .validation import snapshot_network_source
from .work import network_evaluation_charge

logger = logging.getLogger(__name__)


def _rejected(operation) -> bool:
    """Return true only for one typed P3-T refusal."""
    logger.debug("attack rejected check entry")
    try:
        operation()
    except ObserverNetworkError:
        logger.debug("attack rejected check exit rejected=True")
        return True
    logger.debug("attack rejected check exit rejected=False")
    return False


def _rebuild(source, *, edges=None, observers=None):
    """Rebuild one exact network while retaining every raw P1 root."""
    logger.debug("attack rebuild entry")
    result = observer_network_source(
        source.doctrine_id,
        source.source_id,
        source.source_version,
        source.inputs,
        source.observers if observers is None else observers,
        source.translations if edges is None else edges,
        source.triangles,
        source.p1a_doctrine,
        source.p1a_binding,
        source.p1a_stage_source,
        source.raw_pairs,
    )
    logger.debug("attack rebuild exit")
    return result


def _replace_edge(source, old, rows):
    """Replace one exact edge with a freshly committed row table."""
    logger.debug("attack replace edge entry edge=%s", old.edge_id)
    domain = tuple(item.source_value.value_digest for item in rows)
    changed = translation_source(
        old.edge_id,
        old.source_observer_id,
        old.target_observer_id,
        domain,
        rows,
        old.dependency_ids,
    )
    edges = tuple(changed if item.edge_id == old.edge_id else item for item in source.translations)
    result = _rebuild(source, edges=edges)
    logger.debug("attack replace edge exit edge=%s", old.edge_id)
    return result


def _permuted_rows(edge):
    """Construct one reachable but concretely noncommuting permutation."""
    logger.debug("attack permuted rows entry edge=%s", edge.edge_id)
    targets = tuple(item.target_value for item in edge.rows)
    result = tuple(
        translation_row(item.source_value, targets[(index + 1) % len(targets)])
        for index, item in enumerate(edge.rows)
    )
    logger.debug("attack permuted rows exit edge=%s", edge.edge_id)
    return result


def observer_network_attack_results() -> tuple[tuple[str, bool], ...]:
    """Execute all eighteen named classifier, map, source, and cap attacks."""
    logger.debug("observer_network_attack_results entry")
    source = example_observer_network()
    judgment = observer_network_judgment(source)
    edges = {item.edge_id: item for item in source.translations}
    judged = {item.edge_id: item for item in judgment.edges}
    pairs = {(item.source_observer_id, item.target_observer_id): item for item in judgment.observer_pairs}

    alien = typed_value("alien", "observation", b"foreign")
    first = edges["triply-nested"]
    alien_rows = (translation_row(first.rows[0].source_value, alien),) + first.rows[1:]
    incompatible = _rejected(lambda: _replace_edge(source, first, alien_rows))

    partial = operational_edge_map(source, "triply-total-partial")
    pulled = compose_path(source, ("triply-total-partial", "total-nested"))
    pullback = pulled.domain == partial.domain

    pair = pairs[("fine-triply-nested", "fine-total")]
    forged_pair = replace(pair, status=RefinementStatus.ISOMORPHIC)
    pair_rows = tuple(
        forged_pair if item.judgment_digest == pair.judgment_digest else item for item in judgment.observer_pairs
    )
    false_equivalence = _rejected(
        lambda: validate_observer_network_result(source, replace(judgment, observer_pairs=pair_rows))
    )

    iso = judgment.isomorphisms[0]
    forward, reverse = judged[iso.forward_edge_id], judged[iso.reverse_edge_id]
    empty_reverse = replace(reverse, operational_map=replace(reverse.operational_map, domain=(), rows=()))
    missing_roundtrip = isomorphism_judgment(source, forward, empty_reverse).status is LawStatus.NOT_ESTABLISHED

    strict = replace(judged["triply-nested"], refinement=RefinementStatus.STRICT, separator_input_ids=None)
    strict_rows = tuple(strict if item.edge_id == strict.edge_id else item for item in judgment.edges)
    strict_without_separator = _rejected(
        lambda: validate_observer_network_result(source, replace(judgment, edges=strict_rows))
    )

    bad_map_source = _replace_edge(source, edges["total-crest"], _permuted_rows(edges["total-crest"]))
    bad_map = next(item for item in observer_network_judgment(bad_map_source).edges if item.edge_id == "total-crest")
    noncommuting = bad_map.relation_preserving is LawStatus.ESTABLISHED and bad_map.translation_preserving is LawStatus.REFUTED

    bad_triangle_source = _replace_edge(source, edges["triply-total"], _permuted_rows(edges["triply-total"]))
    bad_triangle = next(
        item for item in observer_network_judgment(bad_triangle_source).triangles if item.demand_id == "triangle-exact"
    )
    triangle_disagreement = bad_triangle.status is TriangleStatus.REFUTED
    intersection_only = next(
        item for item in judgment.triangles if item.demand_id == "triangle-partial"
    ).status is TriangleStatus.AGREES_ON_DOMAIN_INTERSECTION

    open_pair = pairs[("coarse-crest", "fine-domain-hole")]
    open_rows = tuple(
        replace(item, status=RefinementStatus.INCOMPARABLE) if item is open_pair else item
        for item in judgment.observer_pairs
    )
    open_not_incomparable = _rejected(
        lambda: validate_observer_network_result(source, replace(judgment, observer_pairs=open_rows))
    )

    raw_forward = source.translations[0]
    raw_return = replace(
        source.translations[1],
        edge_id="hostile-return",
        source_observer_id=raw_forward.target_observer_id,
        target_observer_id=raw_forward.source_observer_id,
    )
    semantic_source = replace(source, translations=source.translations + (raw_return,))
    return_edge = replace(judgment.edges[1], edge_id="hostile-return", refinement=RefinementStatus.NONSTRICT)
    cycle_status, _ = strict_cycle_check(semantic_source, (strict, return_edge))
    strict_cycle = cycle_status is LawStatus.REFUTED

    empty_raw = edges["nested-total"]
    empty_edge = translation_source(
        empty_raw.edge_id,
        empty_raw.source_observer_id,
        empty_raw.target_observer_id,
        (),
        (),
        empty_raw.dependency_ids,
    )
    empty_source = _rebuild(
        source,
        edges=tuple(empty_edge if item.edge_id == empty_edge.edge_id else item for item in source.translations),
    )
    empty_result = observer_network_judgment(empty_source)
    empty_judged = next(item for item in empty_result.edges if item.edge_id == empty_edge.edge_id)
    empty_no_promotion = all(
        status is LawStatus.NOT_ESTABLISHED
        for status in (
            empty_judged.relation_preserving,
            empty_judged.translation_preserving,
            empty_judged.equal_evaluation_domain,
        )
    )
    no_supplied_composite = "composite" not in inspect.signature(observer_network_judgment).parameters
    transplant = _rejected(lambda: snapshot_network_source(replace(source, source_id="transplant")))

    observer = source.observers[0]
    descriptor = replace(observer.grammar_descriptor, canonical_source=b"foreign")
    grammar_mutation = _rejected(
        lambda: _rebuild(source, observers=(replace(observer, grammar_descriptor=descriptor),) + source.observers[1:])
    )
    policy = replace(network_resource_policy(), max_evaluations=network_evaluation_charge(source) - 1)
    resource_refusal = _rejected(lambda: snapshot_network_source(source, policy))

    bad_reverse_source = _replace_edge(source, edges["total-nested"], _permuted_rows(edges["total-nested"]))
    bad_iso = observer_network_judgment(bad_reverse_source).isomorphisms[0]
    inverse_permutation = (
        bad_iso.status is LawStatus.REFUTED
        and bad_iso.reverse_evaluation_commutes is LawStatus.REFUTED
    )
    empty_node = _rejected(lambda: _rebuild(source, observers=(replace(observer, rows=()),) + source.observers[1:]))
    off_scope = replace(judged["triply-nested"], separator_input_ids=("outside", "scope"))
    off_rows = tuple(off_scope if item.edge_id == off_scope.edge_id else item for item in judgment.edges)
    off_scope_separator = _rejected(
        lambda: validate_observer_network_result(source, replace(judgment, edges=off_rows))
    )

    result = (
        ("incompatible-response-grammars", incompatible),
        ("composition-outside-pullback-domain", pullback),
        ("preservation-relabeled-equivalence", false_equivalence),
        ("reverse-missing-round-trip", missing_roundtrip),
        ("strict-without-reachable-separator", strict_without_separator),
        ("a2-passes-but-map-does-not-commute", noncommuting),
        ("triangle-semantic-disagreement", triangle_disagreement),
        ("intersection-agreement-relabeled-coherence", intersection_only),
        ("open-relabeled-incomparable", open_not_incomparable),
        ("strict-cycle-hidden-by-alias", strict_cycle),
        ("empty-map-vacuous-promotion", empty_no_promotion),
        ("caller-supplied-composite-or-a2", no_supplied_composite),
        ("cross-source-transplant", transplant),
        ("mutable-response-grammar", grammar_mutation),
        ("resource-refusal-relabeled-semantic", resource_refusal),
        ("inverse-permutation-noncommuting", inverse_permutation),
        ("empty-node-identity-promotion", empty_node),
        ("off-scope-separator-promoted-all-carrier", off_scope_separator),
    )
    logger.debug("observer_network_attack_results exit passed=%d", sum(status for _, status in result))
    return result
