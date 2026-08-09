"""Positive raw-P1-backed finite laws for P3-T1--T4."""

from dataclasses import replace

import pytest

from observer_network_fixture import network_source
from src.core.observer_network import (
    LawStatus,
    ObserverNetworkError,
    RefinementStatus,
    TriangleStatus,
    observer_network_judgment,
    observer_network_source,
    translation_source,
    validate_observer_network_result,
)
from src.core.observer_network_p1_replay import replay_raw_pair


def _rebuild(source, *, edges=None, observers=None):
    """Reconstruct one exact source through the public hard-first constructor."""
    return observer_network_source(
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


def _replace_edge(source, edge_id, replacement):
    """Replace one edge and rebuild the network commitment."""
    return _rebuild(
        source,
        edges=tuple(replacement if item.edge_id == edge_id else item for item in source.translations),
    )


def test_each_edge_copies_actual_ordered_raw_p1a2_rows_without_digest_synthesis():
    source = network_source()
    result = observer_network_judgment(source)
    by_id = {item.edge_id: item for item in source.translations}
    for edge in result.edges:
        raw_edge = by_id[edge.edge_id]
        raw = replay_raw_pair(source, raw_edge.source_observer_id, raw_edge.target_observer_id)
        assert len(edge.relation_rows) == len(raw.pairs) == 16
        assert tuple(item.row_digest for item in edge.relation_rows) == tuple(item.row_digest for item in raw.pairs)
        assert tuple(item.source_outcome for item in edge.relation_rows) == tuple(item.fine_outcome for item in raw.pairs)
        assert tuple(item.target_outcome for item in edge.relation_rows) == tuple(item.coarse_outcome for item in raw.pairs)
    assert sum(len(item.relation_rows) for item in result.edges) == 112


def test_actual_blockage_keeps_a2_and_translation_positive_laws_open():
    result = observer_network_judgment(network_source())
    edge = next(item for item in result.edges if item.edge_id == "hole-crest")
    assert edge.translatable is LawStatus.ESTABLISHED
    assert edge.relation_preserving is LawStatus.OPEN
    assert edge.translation_preserving is LawStatus.ESTABLISHED
    assert edge.refinement is RefinementStatus.OPEN
    assert any(
        item.source_outcome.value == "blocked" or item.target_outcome.value == "blocked"
        for item in edge.relation_rows
    )


def test_arbitrary_finite_positive_closure_reaches_exact_three_edge_chain():
    result = observer_network_judgment(network_source())
    pairs = {(item.source_observer_id, item.target_observer_id): item for item in result.observer_pairs}
    path = pairs[("fine-triply-nested", "coarse-crest")]
    assert path.path_edge_ids == ("triply-nested", "nested-total", "total-crest")
    assert path.status is RefinementStatus.STRICT
    assert path.forward_counterexample is None
    assert path.reverse_counterexample is not None


def test_nonvacuous_two_map_isomorphism_has_units_and_both_commuting_laws():
    source = network_source()
    result = observer_network_judgment(source)
    assert len(result.isomorphisms) == 1
    iso = result.isomorphisms[0]
    assert (iso.forward_edge_id, iso.reverse_edge_id) == ("nested-total", "total-nested")
    assert iso.status is LawStatus.ESTABLISHED
    assert iso.evaluation_domains_agree is LawStatus.ESTABLISHED
    assert iso.forward_round_trip is iso.reverse_round_trip is LawStatus.ESTABLISHED
    assert iso.forward_evaluation_commutes is iso.reverse_evaluation_commutes is LawStatus.ESTABLISHED
    edges = {item.edge_id: item for item in result.edges}
    assert edges["nested-total"].operational_map.domain
    assert edges["total-nested"].operational_map.domain
    raw_pairs = {
        (item.source_observer_id, item.target_observer_id): item for item in source.raw_pairs
    }
    assert raw_pairs[("fine-nested", "fine-total")].projection is not None
    assert raw_pairs[("fine-total", "fine-nested")].projection is None


def test_empty_operational_domain_never_establishes_relation_unit_or_composition():
    source = network_source()
    old = next(item for item in source.translations if item.edge_id == "nested-total")
    empty = translation_source(
        old.edge_id,
        old.source_observer_id,
        old.target_observer_id,
        (),
        (),
        old.dependency_ids,
    )
    changed = _replace_edge(source, old.edge_id, empty)
    result = observer_network_judgment(changed)
    edge = next(item for item in result.edges if item.edge_id == old.edge_id)
    unit = next(item for item in result.identity_laws if item.edge_id == old.edge_id)
    assert edge.translatable is LawStatus.VACUOUS_TYPED
    assert edge.relation_preserving is LawStatus.NOT_ESTABLISHED
    assert edge.translation_preserving is LawStatus.NOT_ESTABLISHED
    assert edge.equal_evaluation_domain is LawStatus.NOT_ESTABLISHED
    assert unit.left_status is unit.right_status is LawStatus.NOT_ESTABLISHED
    assert all(
        item.relation_composed is LawStatus.NOT_ESTABLISHED
        and item.translation_composed is LawStatus.NOT_ESTABLISHED
        for item in result.compositions
        if old.edge_id in item.edge_ids
    )


def test_three_edge_associativity_and_triangle_domains_are_semantic():
    result = observer_network_judgment(network_source())
    assert len(result.associativity) == 7
    law = next(
        item
        for item in result.associativity
        if item.edge_ids == ("triply-nested", "nested-total", "total-crest")
    )
    assert law.edge_ids == ("triply-nested", "nested-total", "total-crest")
    assert law.status is LawStatus.ESTABLISHED and law.exact_domain_equal
    assert law.left_map_digest == law.right_map_digest
    assert all(item.status is LawStatus.ESTABLISHED for item in result.associativity)
    triangles = {item.demand_id: item for item in result.triangles}
    assert triangles["triangle-exact"].status is TriangleStatus.ESTABLISHED
    assert triangles["triangle-partial"].status is TriangleStatus.AGREES_ON_DOMAIN_INTERSECTION
    assert triangles["triangle-partial"].direct_domain != triangles["triangle-partial"].indirect_domain


def test_fresh_result_replay_and_1500_level_hostile_shape_are_iterative():
    source = network_source()
    first = observer_network_judgment(source)
    second = validate_observer_network_result(source, first)
    assert first == second and first is not second
    nested = "leaf"
    for _ in range(1500):
        nested = (nested,)
    forged = replace(first, nonclaims=nested)
    with pytest.raises(ObserverNetworkError, match="result-depth-hard-limit"):
        validate_observer_network_result(source, forged)


def test_exact_grammar_source_declared_domain_and_dependencies_are_committed():
    source = network_source()
    observer = source.observers[0]
    descriptor = replace(observer.grammar_descriptor, canonical_source=b"foreign")
    with pytest.raises(ObserverNetworkError, match="grammar-canonical-source-mismatch"):
        _rebuild(source, observers=(replace(observer, grammar_descriptor=descriptor),) + source.observers[1:])
    edge = source.translations[0]
    with pytest.raises(ObserverNetworkError, match="translation-declared-domain-row-mismatch"):
        _replace_edge(source, edge.edge_id, replace(edge, declared_domain=edge.declared_domain[:-1]))
    with pytest.raises(ObserverNetworkError, match="translation-dependency-closure-invalid"):
        _replace_edge(source, edge.edge_id, replace(edge, dependency_ids=edge.dependency_ids[:1]))


def test_result_nonclaims_and_digest_roles_stay_separate_and_nonpromoting():
    result = observer_network_judgment(network_source())
    assert result.promotions == 0
    assert "observer-independent-equivalence" in result.nonclaims
    assert "productive-to-all-depth-family" in result.nonclaims
    assert "foundation-independent-infinity" in result.nonclaims
    digests = (
        result.source_digest,
        result.identities[0].map_digest,
        result.evaluation_domains[0].judgment_digest,
        result.edges[0].relation_rows[0].row_digest,
        result.edges[0].judgment_digest,
        result.judgment_digest,
    )
    assert len(set(digests)) == len(digests)
