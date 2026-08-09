"""Focused semantic tests for P1-C2 declared finite aggregation."""

from src.core.confluence_aggregate import (
    AggregateCoverageStatus, C2_NONCLAIMS, FiniteConfluenceAggregate,
    GlobalDeclaredFiniteStatus, LocalFiniteStatus, RequirementKind,
    confluence_aggregate_policy, finite_confluence_aggregate,
    finite_confluence_catalog, validate_finite_confluence_result,
)
from src.core.confluence_aggregate_preflight import total_catalog_charge
from src.core.confluence_types import ConfluenceStatus

from confluence_aggregate_fixture import aggregate_fixture


def test_two_local_and_two_global_requirements_establish_independently():
    doctrine, diagram, _, _, _, _, catalog = aggregate_fixture()
    result = finite_confluence_aggregate(doctrine, diagram, catalog)
    assert type(result) is FiniteConfluenceAggregate
    assert result.local_status is LocalFiniteStatus.CONFLUENT
    assert result.global_status is GlobalDeclaredFiniteStatus.CONFLUENT
    assert result.coverage is AggregateCoverageStatus.COMPLETE
    assert len(result.rows) == 4
    assert tuple(row.key for row in result.rows) == (
        *catalog.expected_local_keys, *catalog.expected_global_keys,
    )
    assert all(row.status is ConfluenceStatus.ESTABLISHED for row in result.rows)
    assert tuple(row.key[0] for row in result.rows) == (
        RequirementKind.LOCAL, RequirementKind.LOCAL,
        RequirementKind.GLOBAL, RequirementKind.GLOBAL,
    )
    assert result.total_charge == total_catalog_charge(doctrine, diagram, catalog)


def test_cycle_against_zero_edge_identity_is_a_real_global_cell_digest():
    doctrine, diagram, _, _, _, globals_, catalog = aggregate_fixture()
    cycle, identity = globals_[1].left, globals_[1].right
    assert cycle.start_stage_id == cycle.end_stage_id == identity.stage_id
    result = finite_confluence_aggregate(doctrine, diagram, catalog)
    assert type(result) is FiniteConfluenceAggregate
    row = result.rows[-1]
    assert row.left_history_digest == cycle.history_digest
    assert row.right_history_digest == identity.history_digest
    assert row.global_history_cell_digest is not None
    assert row.local_judgment_digest is None and row.plan_digest is None
    assert row.charged_checks == 5  # two cycle edges + three aligned responses


def test_local_establishment_does_not_promote_an_open_global_catalog():
    doctrine, diagram, _, _, _, _, catalog = aggregate_fixture(global_open=True)
    result = finite_confluence_aggregate(doctrine, diagram, catalog)
    assert type(result) is FiniteConfluenceAggregate
    assert result.local_status is LocalFiniteStatus.CONFLUENT
    assert result.global_status is GlobalDeclaredFiniteStatus.OPEN
    assert tuple(row.status for row in result.rows[:2]) == (
        ConfluenceStatus.ESTABLISHED, ConfluenceStatus.ESTABLISHED,
    )
    assert result.rows[2].status is ConfluenceStatus.OPEN
    assert result.first_obstruction is result.rows[2].first_obstruction


def test_any_refuted_row_has_precedence_in_each_independent_catalog():
    doctrine, diagram, _, _, _, _, catalog = aggregate_fixture(mismatch=True)
    result = finite_confluence_aggregate(doctrine, diagram, catalog)
    assert type(result) is FiniteConfluenceAggregate
    assert result.local_status is LocalFiniteStatus.REFUTED
    assert result.global_status is GlobalDeclaredFiniteStatus.REFUTED
    assert result.rows[0].status is ConfluenceStatus.REFUTED
    assert result.rows[2].status is ConfluenceStatus.REFUTED


def test_catalog_order_and_policy_are_semantic_commitments():
    doctrine, diagram, _, _, local, global_, first = aggregate_fixture()
    reordered = finite_confluence_catalog(
        doctrine, diagram, tuple(reversed(local)), global_, first.policy,
    )
    changed_policy = finite_confluence_catalog(
        doctrine, diagram, local, global_, confluence_aggregate_policy(4095),
    )
    assert reordered.catalog_digest != first.catalog_digest
    assert reordered.expected_local_keys == tuple(reversed(first.expected_local_keys))
    assert changed_policy.catalog_digest != first.catalog_digest


def test_result_revalidation_replays_and_returns_a_fresh_expected_value():
    doctrine, diagram, _, _, _, _, catalog = aggregate_fixture()
    first = finite_confluence_aggregate(doctrine, diagram, catalog)
    second = validate_finite_confluence_result(doctrine, diagram, catalog, first)
    assert type(first) is type(second) is FiniteConfluenceAggregate
    assert first is not second and first.rows is not second.rows
    assert first.aggregate_digest == second.aggregate_digest
    object.__setattr__(first.rows[0], "row_digest", "0" * 64)
    third = finite_confluence_aggregate(doctrine, diagram, catalog)
    assert third.rows[0].row_digest != "0" * 64


def test_scope_is_catalog_relative_and_permanent_nonclaims_remain_explicit():
    doctrine, diagram, _, _, local, global_, catalog = aggregate_fixture()
    omitted_cycle = finite_confluence_catalog(
        doctrine, diagram, local, global_[:1], catalog.policy,
    )
    result = finite_confluence_aggregate(doctrine, diagram, omitted_cycle)
    assert type(result) is FiniteConfluenceAggregate
    assert result.global_status is GlobalDeclaredFiniteStatus.CONFLUENT
    assert result.catalog_digest != catalog.catalog_digest
    assert result.nonclaims == C2_NONCLAIMS
    assert "exhaustive-generated-path-coverage" in result.nonclaims
