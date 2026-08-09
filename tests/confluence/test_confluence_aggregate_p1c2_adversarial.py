"""Hostile binding, atomicity, and anti-promotion pressure for P1-C2."""

from dataclasses import replace

import pytest

import src.core.confluence_aggregate_global as global_runtime
import src.core.confluence_aggregate_runtime as aggregate_runtime
from src.core.confluence import (
    diagram_edge, diagram_path, finite_diagram_source, fork_confluence_judgment,
    fork_join_plan,
)
from src.core.confluence_aggregate import (
    AggregateFailedBound, ConfluenceAggregateResourceLimit,
    FiniteConfluenceAggregate,
    confluence_aggregate_policy, finite_confluence_aggregate,
    finite_confluence_catalog, global_path_pair_requirement, identity_history,
    local_critical_fork_requirement, validate_finite_confluence_result,
)
from src.core.confluence_aggregate_preflight import total_catalog_charge
from src.core.confluence_preflight import ConfluenceValidationError
from src.core.confluence_types import AlignmentPoint
from src.core.positive_ontology import ontology_stage
from src.core.proof_core_types import Pulse, Silence

from confluence_aggregate_fixture import aggregate_fixture


def test_multi_edge_local_branch_is_not_a_local_critical_fork():
    doctrine, diagram, crest, _, _, _, _ = aggregate_fixture()
    q = ontology_stage("q", Pulse(Silence()), doctrine, 1)
    edges = diagram.edges + (
        diagram_edge("jq-left", "j", "q", ("crest",)),
        diagram_edge("jq-right", "j", "q", ("crest",)),
    )
    paths = diagram.paths + (
        diagram_path("jq-left-path", ("jq-left",), "j", "q"),
        diagram_path("jq-right-path", ("jq-right",), "j", "q"),
    )
    expanded = finite_diagram_source(
        doctrine, "multi-edge-source", diagram.stages + (q,), edges, paths,
    )
    plan = fork_join_plan(
        doctrine, expanded, "multi-edge-plan", "full-left", "full-right",
        "jq-left-path", "jq-right-path",
        (AlignmentPoint(0, 0), AlignmentPoint(1, 1), AlignmentPoint(2, 2),
         AlignmentPoint(3, 3)), crest,
    )
    with pytest.raises(ConfluenceValidationError, match="one-edge"):
        local_critical_fork_requirement(doctrine, expanded, "not-local", plan, crest)


def test_empty_identity_relabel_and_same_histories_fail_closed():
    doctrine, diagram, crest, _, _, globals_, _ = aggregate_fixture()
    with pytest.raises(ConfluenceValidationError, match="path-edges"):
        diagram_path("fake-empty", (), "c", "c")
    identity = globals_[1].right
    forged = replace(identity, stage_id="d")
    with pytest.raises(ConfluenceValidationError, match="identity-history-drift"):
        global_path_pair_requirement(
            doctrine, diagram, "forged-id", globals_[1].left, forged,
            globals_[1].alignment, crest,
        )
    alias = identity_history(doctrine, diagram, "identity-alias", "c")
    with pytest.raises(ConfluenceValidationError, match="identical"):
        global_path_pair_requirement(
            doctrine, diagram, "same-history", identity, alias,
            (AlignmentPoint(0, 0),), crest,
        )


def test_endpoint_only_alignment_and_duplicate_cross_catalog_id_reject():
    doctrine, diagram, crest, _, local, global_, catalog = aggregate_fixture()
    with pytest.raises(ConfluenceValidationError, match="full-monotone"):
        global_path_pair_requirement(
            doctrine, diagram, "endpoint-only", global_[0].left, global_[0].right,
            (AlignmentPoint(0, 0), AlignmentPoint(2, 2)), crest,
        )
    duplicate = replace(global_[0], requirement_id=local[0].requirement_id)
    duplicate = replace(
        duplicate,
        requirement_digest=global_path_pair_requirement(
            doctrine, diagram, local[0].requirement_id, duplicate.left,
            duplicate.right, duplicate.alignment, duplicate.transport,
        ).requirement_digest,
    )
    with pytest.raises(ConfluenceValidationError, match="duplicate-cross-catalog"):
        finite_confluence_catalog(
            doctrine, diagram, local, (duplicate, global_[1]), catalog.policy,
        )


def test_incomplete_reordered_and_omitted_expected_keys_are_invalid():
    doctrine, diagram, _, _, _, _, catalog = aggregate_fixture()
    for forged in (
        replace(catalog, expected_global_keys=catalog.expected_global_keys[:1]),
        replace(catalog, expected_local_keys=tuple(reversed(catalog.expected_local_keys))),
    ):
        with pytest.raises(ConfluenceValidationError, match="key-drift"):
            finite_confluence_aggregate(doctrine, diagram, forged)


def test_prior_judgment_or_cell_cannot_enter_raw_requirement_catalog():
    doctrine, diagram, crest, _, local, global_, catalog = aggregate_fixture()
    judgment = fork_confluence_judgment(
        doctrine, diagram, local[0].plan, local[0].transport,
    )
    with pytest.raises(ConfluenceValidationError, match="local-requirement-must-be-exact"):
        finite_confluence_catalog(
            doctrine, diagram, (judgment,), global_, catalog.policy,  # type: ignore[arg-type]
        )
    result = finite_confluence_aggregate(doctrine, diagram, catalog)
    assert type(result) is FiniteConfluenceAggregate
    with pytest.raises(ConfluenceValidationError, match="global-requirement-must-be-exact"):
        finite_confluence_catalog(
            doctrine, diagram, local, (result,), catalog.policy,  # type: ignore[arg-type]
        )


def test_atomic_check_refusal_happens_before_any_echo(monkeypatch):
    doctrine, diagram, _, _, local, global_, _ = aggregate_fixture()
    baseline = finite_confluence_catalog(
        doctrine, diagram, local, global_, confluence_aggregate_policy(),
    )
    exact = total_catalog_charge(doctrine, diagram, baseline)
    catalog = finite_confluence_catalog(
        doctrine, diagram, local, global_, confluence_aggregate_policy(exact - 1),
    )
    calls = 0

    def forbidden(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("observation-ran-before-whole-catalog-preflight")

    monkeypatch.setattr(aggregate_runtime, "fork_confluence_judgment", forbidden)
    monkeypatch.setattr(global_runtime, "echo", forbidden)
    result = finite_confluence_aggregate(doctrine, diagram, catalog)
    assert type(result) is ConfluenceAggregateResourceLimit
    assert result.failed_bound is AggregateFailedBound.TOTAL_CHECKS
    assert result.required_value == exact and result.allowed_value == exact - 1
    assert calls == 0


def test_canonical_bytes_have_first_refusal_priority(monkeypatch):
    doctrine, diagram, _, _, local, global_, _ = aggregate_fixture()
    catalog = finite_confluence_catalog(
        doctrine, diagram, local, global_, confluence_aggregate_policy(1, 1),
    )
    calls = 0

    def forbidden(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("observation-ran-before-byte-priority-refusal")

    monkeypatch.setattr(aggregate_runtime, "fork_confluence_judgment", forbidden)
    monkeypatch.setattr(global_runtime, "echo", forbidden)
    result = finite_confluence_aggregate(doctrine, diagram, catalog)
    assert type(result) is ConfluenceAggregateResourceLimit
    assert result.failed_bound is AggregateFailedBound.CANONICAL_BYTES
    assert not hasattr(result, "rows") and not hasattr(result, "coverage")
    assert not hasattr(result, "local_status") and not hasattr(result, "global_status")
    assert calls == 0


def test_hard_invalid_charge_precedes_policy_byte_refusal_and_observation(monkeypatch):
    doctrine, diagram, _, _, local, _, _ = aggregate_fixture()
    long_cycle = diagram_path("long-cycle", ("cd", "dc") * 64, "c", "c")
    expanded = finite_diagram_source(
        doctrine, "hard-charge-source", diagram.stages, diagram.edges,
        diagram.paths + (long_cycle,),
    )
    from src.core.confluence import direct_echo_transport
    from src.core.confluence_aggregate import declared_history

    transport = direct_echo_transport(
        doctrine, tuple(item.observer_id for item in doctrine.observers),
    )
    cycle = declared_history(doctrine, expanded, "long-history", "long-cycle")
    identity = identity_history(doctrine, expanded, "long-identity", "c")
    alignment = tuple(AlignmentPoint(index, 0) for index in range(129))
    globals_ = tuple(
        global_path_pair_requirement(
            doctrine, expanded, f"hard-global-{index}", cycle, identity,
            alignment, transport,
        ) for index in range(50)
    )
    rebound_local = []
    for item in local:
        plan = item.plan
        rebound_plan = fork_join_plan(
            doctrine, expanded, plan.plan_id, plan.left_branch_path_id,
            plan.right_branch_path_id, plan.left_join_path_id,
            plan.right_join_path_id, plan.alignment, item.transport,
        )
        rebound_local.append(local_critical_fork_requirement(
            doctrine, expanded, item.requirement_id, rebound_plan, item.transport,
        ))
    catalog = finite_confluence_catalog(
        doctrine, expanded, tuple(rebound_local), globals_,
        confluence_aggregate_policy(1, 1),
    )
    calls = 0

    def forbidden(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("observation-ran-before-hard-check")

    monkeypatch.setattr(aggregate_runtime, "fork_confluence_judgment", forbidden)
    monkeypatch.setattr(global_runtime, "echo", forbidden)
    with pytest.raises(ConfluenceValidationError, match="hard-check-limit"):
        finite_confluence_aggregate(doctrine, expanded, catalog)
    assert calls == 0


def test_foreign_diagram_and_transport_transplants_reject():
    doctrine, diagram, crest, tail, local, global_, catalog = aggregate_fixture()
    alien = replace(diagram, source_id="alien")
    with pytest.raises(ConfluenceValidationError):
        finite_confluence_aggregate(doctrine, alien, catalog)
    stale = replace(local[0], transport=tail)
    with pytest.raises(ConfluenceValidationError):
        finite_confluence_catalog(
            doctrine, diagram, (stale, local[1]), global_, catalog.policy,
        )


def test_forged_deleted_reordered_and_coercive_result_fields_reject():
    doctrine, diagram, _, _, _, _, catalog = aggregate_fixture()
    result = finite_confluence_aggregate(doctrine, diagram, catalog)
    assert type(result) is FiniteConfluenceAggregate
    attacks = (
        replace(result, rows=result.rows[:-1]),
        replace(result, rows=tuple(reversed(result.rows))),
        replace(result, global_status="global-declared-finite-confluent"),
        replace(result, total_charge=True),
        replace(result, aggregate_digest="0" * 64),
        replace(result, rows=(None,) * 10_000),
    )
    for forged in attacks:
        with pytest.raises(ConfluenceValidationError):
            validate_finite_confluence_result(doctrine, diagram, catalog, forged)


def test_unexpected_internal_error_is_not_normalized_to_open(monkeypatch):
    doctrine, diagram, _, _, _, _, catalog = aggregate_fixture()

    def explode(*args, **kwargs):
        raise RuntimeError("unexpected-c2-internal")

    monkeypatch.setattr(aggregate_runtime, "fork_confluence_judgment", explode)
    with pytest.raises(RuntimeError, match="unexpected-c2-internal"):
        finite_confluence_aggregate(doctrine, diagram, catalog)
