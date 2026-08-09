"""Exact-instance and hostile-result pressure for P1-C2."""

from dataclasses import replace

import pytest

import src.core.confluence_aggregate_result_validation as result_validation
from src.core.confluence_aggregate import (
    ConfluenceAggregateResourceLimit, FiniteConfluenceAggregate,
    confluence_aggregate_policy, finite_confluence_aggregate,
    finite_confluence_catalog, validate_finite_confluence_result,
)
from src.core.confluence_aggregate_preflight import total_catalog_charge
from src.core.confluence_preflight import ConfluenceValidationError

from confluence_aggregate_fixture import aggregate_fixture


class TupleTrap(tuple):
    def __iter__(self):
        raise AssertionError("tuple-subclass-iteration-invoked")


class EqualityTrap:
    calls = 0
    repr_calls = 0

    def __eq__(self, other):
        type(self).calls += 1
        raise AssertionError("hostile-equality-invoked")

    def __repr__(self):
        type(self).repr_calls += 1
        raise AssertionError("hostile-repr-invoked")


class PositivePropertyTrap(FiniteConfluenceAggregate):
    @property
    def rows(self):
        raise AssertionError("hostile-property-invoked")


def test_exact_instance_field_sets_hollow_rows_obstructions_and_traps_reject():
    doctrine, diagram, _, _, _, _, catalog = aggregate_fixture(global_open=True)
    result = finite_confluence_aggregate(doctrine, diagram, catalog)
    assert type(result) is FiniteConfluenceAggregate

    hollow = replace(result)
    object.__delattr__(hollow, "rows")
    with pytest.raises(ConfluenceValidationError, match="instance-fields"):
        validate_finite_confluence_result(doctrine, diagram, catalog, hollow)

    extra = replace(result)
    object.__setattr__(extra, "status", "established")
    with pytest.raises(ConfluenceValidationError, match="instance-fields"):
        validate_finite_confluence_result(doctrine, diagram, catalog, extra)

    bad_row = replace(result.rows[0])
    object.__setattr__(bad_row, "trace", ())
    with pytest.raises(ConfluenceValidationError, match="instance-fields"):
        validate_finite_confluence_result(
            doctrine, diagram, catalog, replace(result, rows=(bad_row, *result.rows[1:])),
        )

    obstruction = replace(result.first_obstruction)
    object.__delattr__(obstruction, "outcome")
    with pytest.raises(ConfluenceValidationError, match="instance-fields"):
        validate_finite_confluence_result(
            doctrine, diagram, catalog, replace(result, first_obstruction=obstruction),
        )

    with pytest.raises(ConfluenceValidationError, match="container-drift"):
        validate_finite_confluence_result(
            doctrine, diagram, catalog, replace(result, rows=TupleTrap(result.rows)),
        )
    EqualityTrap.calls = 0
    with pytest.raises(ConfluenceValidationError, match="outer-drift"):
        validate_finite_confluence_result(
            doctrine, diagram, catalog, replace(result, aggregate_digest=EqualityTrap()),
        )
    assert EqualityTrap.calls == 0
    assert EqualityTrap.repr_calls == 0
    property_trap = object.__new__(PositivePropertyTrap)
    with pytest.raises(ConfluenceValidationError, match="variant-drift"):
        validate_finite_confluence_result(doctrine, diagram, catalog, property_trap)


def test_refusal_exact_instance_rejects_hollow_and_partial_evidence_fields():
    doctrine, diagram, _, _, local, global_, baseline = aggregate_fixture()
    exact = total_catalog_charge(doctrine, diagram, baseline)
    catalog = finite_confluence_catalog(
        doctrine, diagram, local, global_, confluence_aggregate_policy(exact - 1),
    )
    refusal = finite_confluence_aggregate(doctrine, diagram, catalog)
    assert type(refusal) is ConfluenceAggregateResourceLimit
    hollow = replace(refusal)
    object.__delattr__(hollow, "failed_bound")
    with pytest.raises(ConfluenceValidationError, match="instance-fields"):
        validate_finite_confluence_result(doctrine, diagram, catalog, hollow)
    for name, value in (
        ("rows", ()), ("trace", ()), ("cell", object()),
        ("coverage", "complete"), ("local_status", "open"),
    ):
        forged = replace(refusal)
        object.__setattr__(forged, name, value)
        with pytest.raises(ConfluenceValidationError, match="instance-fields"):
            validate_finite_confluence_result(doctrine, diagram, catalog, forged)


def test_unexpected_semantic_attribute_error_propagates_from_recompute(monkeypatch):
    doctrine, diagram, _, _, _, _, catalog = aggregate_fixture()
    result = finite_confluence_aggregate(doctrine, diagram, catalog)

    def semantic_failure(*args, **kwargs):
        raise AttributeError("unexpected-semantic-attribute")

    monkeypatch.setattr(result_validation, "finite_confluence_aggregate", semantic_failure)
    with pytest.raises(AttributeError, match="unexpected-semantic-attribute"):
        validate_finite_confluence_result(doctrine, diagram, catalog, result)
