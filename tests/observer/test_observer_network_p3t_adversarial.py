"""Independent literal attack oracle and hostile P3-T regressions."""

from dataclasses import replace
import inspect

import pytest

from observer_network_fixture import network_source
from src.core.observer_network import (
    LawStatus,
    NetworkResourcePolicy,
    ObserverNetworkError,
    RefinementStatus,
    observer_network_judgment,
    observer_network_source,
    observation_row,
    silent,
    snapshot_network_source,
    translation_row,
    translation_source,
    typed_value,
    validate_observer_network_result,
)
from src.core.observer_network_coherence import strict_cycle_check
from src.core.observer_network_attack_certificate import observer_network_attack_results
from src.core.observer_network_maps import compose_path, operational_edge_map
from src.core.observer_network_relations import isomorphism_judgment

ATTACK_ORACLE = (
    "incompatible-response-grammars",
    "composition-outside-pullback-domain",
    "preservation-relabeled-equivalence",
    "reverse-missing-round-trip",
    "strict-without-reachable-separator",
    "a2-passes-but-map-does-not-commute",
    "triangle-semantic-disagreement",
    "intersection-agreement-relabeled-coherence",
    "open-relabeled-incomparable",
    "strict-cycle-hidden-by-alias",
    "empty-map-vacuous-promotion",
    "caller-supplied-composite-or-a2",
    "cross-source-transplant",
    "mutable-response-grammar",
    "resource-refusal-relabeled-semantic",
    "inverse-permutation-noncommuting",
    "empty-node-identity-promotion",
    "off-scope-separator-promoted-all-carrier",
)


def _rebuild(source, *, edges=None, observers=None, raw_pairs=None):
    """Reconstruct one source while retaining every raw P1 root explicitly."""
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
        source.raw_pairs if raw_pairs is None else raw_pairs,
    )


def _replace_edge(source, edge_id, replacement):
    """Replace one edge through a fresh network commitment."""
    edges = tuple(replacement if item.edge_id == edge_id else item for item in source.translations)
    return _rebuild(source, edges=edges)


def _edge(source, old, rows, *, domain=None, dependencies=None):
    """Build one exact hostile/positive replacement edge."""
    selected_domain = tuple(item.source_value.value_digest for item in rows) if domain is None else domain
    return translation_source(
        old.edge_id,
        old.source_observer_id,
        old.target_observer_id,
        selected_domain,
        rows,
        old.dependency_ids if dependencies is None else dependencies,
    )


def test_independent_literal_oracle_has_exact_eighteen_unique_attacks():
    assert len(ATTACK_ORACLE) == len(set(ATTACK_ORACLE)) == 18
    assert ATTACK_ORACLE[0] == "incompatible-response-grammars"
    assert ATTACK_ORACLE[-1] == "off-scope-separator-promoted-all-carrier"
    actual = observer_network_attack_results()
    assert tuple(item_id for item_id, _ in actual) == ATTACK_ORACLE
    assert all(status for _, status in actual)


def test_semantic_map_attack_cannot_inherit_actual_p1a2_preservation():
    source = network_source()
    old = next(item for item in source.translations if item.edge_id == "total-crest")
    target_values = tuple(item.target_value for item in old.rows)
    bad_rows = tuple(
        translation_row(item.source_value, target_values[(index + 1) % len(target_values)])
        for index, item in enumerate(old.rows)
    )
    changed = _replace_edge(source, old.edge_id, _edge(source, old, bad_rows))
    edge = next(item for item in observer_network_judgment(changed).edges if item.edge_id == old.edge_id)
    assert edge.relation_preserving is LawStatus.ESTABLISHED
    assert edge.translation_preserving is LawStatus.REFUTED
    assert edge.refinement is RefinementStatus.OPEN


def test_pullback_and_triangle_attacks_are_exercised_semantically():
    source = network_source()
    partial = operational_edge_map(source, "triply-total-partial")
    composed = compose_path(source, ("triply-total-partial", "total-nested"))
    assert composed.domain == partial.domain
    assert "composite" not in inspect.signature(observer_network_judgment).parameters
    old = next(item for item in source.translations if item.edge_id == "triply-total")
    targets = tuple(item.target_value for item in old.rows)
    bad_rows = tuple(
        translation_row(item.source_value, targets[(index + 1) % len(targets)])
        for index, item in enumerate(old.rows)
    )
    changed = _replace_edge(source, old.edge_id, _edge(source, old, bad_rows))
    triangle = next(
        item for item in observer_network_judgment(changed).triangles if item.demand_id == "triangle-exact"
    )
    assert triangle.status.value == "refuted"


def test_grammar_foreign_output_missing_domain_and_dependency_attacks_fail():
    source = network_source()
    old = source.translations[0]
    alien = typed_value("alien", "observation", b"foreign")
    rows = (translation_row(old.rows[0].source_value, alien),) + old.rows[1:]
    with pytest.raises(ObserverNetworkError, match="translation-grammar-kind-mismatch"):
        _replace_edge(source, old.edge_id, _edge(source, old, rows))
    with pytest.raises(ObserverNetworkError, match="translation-declared-domain-row-mismatch"):
        _replace_edge(source, old.edge_id, replace(old, declared_domain=old.declared_domain + ("0" * 64,)))
    with pytest.raises(ObserverNetworkError, match="translation-dependency-closure-invalid"):
        _replace_edge(source, old.edge_id, _edge(source, old, old.rows, dependencies=old.dependency_ids[::-1]))


def test_actual_p1_ready_or_blocked_row_cannot_be_rewritten_as_silent():
    source = network_source()
    observer = source.observers[0]
    hostile_row = observation_row(source.inputs[0], silent("not-observed"))
    changed_observer = replace(observer, rows=(hostile_row,) + observer.rows[1:])
    with pytest.raises(ObserverNetworkError, match="observer-ready-row-not-p1-replay"):
        _rebuild(source, observers=(changed_observer,) + source.observers[1:])


def test_cross_source_raw_pair_transplant_and_incomplete_catalog_fail():
    source = network_source()
    with pytest.raises(ObserverNetworkError, match="network-digest-mismatch"):
        snapshot_network_source(replace(source, source_id="transplant"))
    with pytest.raises(ObserverNetworkError, match="raw-p1a2-pair-catalog-not-complete-ordered"):
        _rebuild(source, raw_pairs=source.raw_pairs[:-1])


def test_hard_preflight_rejects_subclass_containers_without_invocation():
    source = network_source()

    class BombTuple(tuple):
        calls = 0

        def __len__(self):
            type(self).calls += 1
            raise AssertionError("hostile len")

    with pytest.raises(ObserverNetworkError, match="network-container-invalid"):
        snapshot_network_source(replace(source, inputs=BombTuple(source.inputs)))
    assert BombTuple.calls == 0


def test_result_exact_node_cap_and_hostile_tuple_subclass_fail_before_replay():
    source = network_source()
    result = observer_network_judgment(source)
    tiny = NetworkResourcePolicy(64, 64, 256, 4096, 32768, 4096, 1_048_576, 10, 128, 4_194_304)
    with pytest.raises(ObserverNetworkError, match="result-node-hard-limit"):
        validate_observer_network_result(source, result, tiny)

    class BombTuple(tuple):
        calls = 0

        def __iter__(self):
            type(self).calls += 1
            raise AssertionError("hostile iteration")

    forged = replace(result, identities=BombTuple(result.identities))
    with pytest.raises(ObserverNetworkError, match="result-nested-shape-invalid"):
        validate_observer_network_result(source, forged)
    assert BombTuple.calls == 0


def test_strict_cycle_attack_is_semantically_refuted_not_only_cataloged():
    source = network_source()
    result = observer_network_judgment(source)
    forward = result.edges[0]
    raw_forward = source.translations[0]
    reverse_source = replace(
        source.translations[1],
        edge_id="hostile-return",
        source_observer_id=raw_forward.target_observer_id,
        target_observer_id=raw_forward.source_observer_id,
    )
    semantic_source = replace(source, translations=source.translations + (reverse_source,))
    strict = replace(forward, refinement=RefinementStatus.STRICT)
    return_edge = replace(result.edges[1], edge_id="hostile-return", refinement=RefinementStatus.NONSTRICT)
    status, cycle = strict_cycle_check(semantic_source, (strict, return_edge))
    assert status is LawStatus.REFUTED
    assert cycle == (strict.edge_id, return_edge.edge_id)


def test_empty_forward_reverse_maps_establish_no_isomorphism_law():
    source = network_source()
    result = observer_network_judgment(source)
    forward = result.edges[0]
    raw_forward = source.translations[0]
    raw_reverse = replace(
        source.translations[1],
        edge_id="empty-return",
        source_observer_id=raw_forward.target_observer_id,
        target_observer_id=raw_forward.source_observer_id,
    )
    semantic_source = replace(source, translations=source.translations + (raw_reverse,))
    empty_forward_map = replace(forward.operational_map, domain=(), rows=())
    empty_reverse_map = replace(
        result.edges[1].operational_map,
        path_edge_ids=("empty-return",),
        source_observer_id=raw_forward.target_observer_id,
        target_observer_id=raw_forward.source_observer_id,
        domain=(),
        rows=(),
    )
    empty_forward = replace(forward, operational_map=empty_forward_map)
    empty_reverse = replace(result.edges[1], edge_id="empty-return", operational_map=empty_reverse_map)
    iso = isomorphism_judgment(semantic_source, empty_forward, empty_reverse)
    assert iso.status is LawStatus.NOT_ESTABLISHED
    assert iso.evaluation_domains_agree is LawStatus.NOT_ESTABLISHED
    assert iso.forward_round_trip is iso.reverse_round_trip is LawStatus.NOT_ESTABLISHED
    assert iso.forward_evaluation_commutes is iso.reverse_evaluation_commutes is LawStatus.NOT_ESTABLISHED


def test_inverse_permutation_has_no_commuting_or_unit_respecting_isomorphism():
    source = network_source()
    reverse = next(item for item in source.translations if item.edge_id == "total-nested")
    targets = tuple(item.target_value for item in reverse.rows)
    bad_rows = tuple(
        translation_row(item.source_value, targets[(index + 1) % len(targets)])
        for index, item in enumerate(reverse.rows)
    )
    changed = _replace_edge(source, reverse.edge_id, _edge(source, reverse, bad_rows))
    result = observer_network_judgment(changed)
    iso = result.isomorphisms[0]
    assert iso.status is LawStatus.REFUTED
    assert iso.reverse_evaluation_commutes is LawStatus.REFUTED
    assert LawStatus.REFUTED in (iso.forward_round_trip, iso.reverse_round_trip)


def test_forged_equivalence_separator_and_resource_status_never_validate():
    source = network_source()
    result = observer_network_judgment(source)
    edge = result.edges[0]
    forged_edge = replace(
        edge,
        refinement=RefinementStatus.ISOMORPHIC,
        separator_input_ids=("outside", "scope"),
    )
    forged = replace(result, edges=(forged_edge,) + result.edges[1:], promotions=1)
    with pytest.raises(ObserverNetworkError, match="observer-network-result-mismatch"):
        validate_observer_network_result(source, forged)
