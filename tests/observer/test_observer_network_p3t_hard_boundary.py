"""Final exact-shape, cycle, and hard-before-work P3-T regressions."""

from dataclasses import replace
from time import perf_counter

import pytest

from observer_network_fixture import network_source
from src.core.observer_network import (
    ObserverNetworkError,
    LawStatus,
    RefinementStatus,
    observer_network_judgment,
    observer_network_source,
    snapshot_network_source,
    translation_source,
    validate_observer_network_result,
)
from src.core.observer_network_coherence import strict_cycle_check
from src.core.observer_network_common import exact_text
from src.core.observer_network_preflight import hard_preflight, network_resource_policy


class BombDict(dict):
    """A mapping subclass whose virtual operations must never run."""

    calls = 0

    def keys(self):
        type(self).calls += 1
        raise AssertionError("hostile keys")

    def __iter__(self):
        type(self).calls += 1
        raise AssertionError("hostile iteration")

    def __contains__(self, key):
        type(self).calls += 1
        raise AssertionError("hostile contains")


class Bomb:
    """A member that must remain wholly unexamined after aggregate refusal."""

    calls = 0

    def __getattribute__(self, name):
        type(self).calls += 1
        raise AssertionError("hostile member read")


def test_source_root_requires_exact_real_dict_required_fields_and_no_extras():
    source = network_source()
    deleted = replace(source)
    object.__delattr__(deleted, "inputs")
    with pytest.raises(ObserverNetworkError, match="preflight-root-shape-invalid"):
        hard_preflight(deleted, network_resource_policy())

    extra = replace(source)
    object.__setattr__(extra, "unexpected", "metadata")
    with pytest.raises(ObserverNetworkError, match="preflight-root-shape-invalid"):
        hard_preflight(extra, network_resource_policy())

    BombDict.calls = 0
    hostile = replace(source)
    object.__setattr__(hostile, "__dict__", BombDict(object.__getattribute__(hostile, "__dict__")))
    with pytest.raises(ObserverNetworkError, match="preflight-root-shape-invalid"):
        hard_preflight(hostile, network_resource_policy())
    assert BombDict.calls == 0


def test_cyclic_response_value_is_a_typed_iterative_source_refusal():
    source = network_source()
    observer = source.observers[0]
    row = observer.rows[0]
    cyclic = replace(row.response)
    object.__setattr__(cyclic, "value", cyclic)
    bad_row = replace(row, response=cyclic)
    bad_observer = replace(observer, rows=(bad_row,) + observer.rows[1:])
    bad = replace(source, observers=(bad_observer,) + source.observers[1:])
    with pytest.raises(ObserverNetworkError, match="source-byte-cycle"):
        snapshot_network_source(bad)


def test_huge_source_text_is_rejected_by_codepoint_bound_before_utf8_work():
    with pytest.raises(ObserverNetworkError, match="huge-invalid"):
        exact_text("x" * 1_000_000, "huge")
    source = replace(network_source(), source_id="x" * 2_000_000)
    with pytest.raises(ObserverNetworkError, match="canonical-byte-hard-limit"):
        hard_preflight(source, network_resource_policy())


def test_aggregate_row_limit_precedes_member_traversal_and_byte_charging():
    source = network_source()
    Bomb.calls = 0
    observer = replace(source.observers[0], rows=(Bomb(),) * 4097)
    bad = replace(source, observers=(observer,) + source.observers[1:])
    with pytest.raises(ObserverNetworkError, match="network-hard-work-limit"):
        hard_preflight(bad, network_resource_policy())
    assert Bomb.calls == 0


def test_p1_container_limit_precedes_member_traversal_and_byte_charging():
    source = network_source()
    Bomb.calls = 0
    doctrine = replace(source.p1a_doctrine, metadata=(Bomb(),) * 4097)
    bad = replace(source, p1a_doctrine=doctrine)
    with pytest.raises(ObserverNetworkError, match="p1-raw-count-limit"):
        hard_preflight(bad, network_resource_policy())
    assert Bomb.calls == 0


def test_result_requires_exact_real_dict_required_fields_and_no_extras():
    source = network_source()
    result = observer_network_judgment(source)
    deleted = replace(result)
    object.__delattr__(deleted, "nonclaims")
    with pytest.raises(ObserverNetworkError, match="result-instance-shape-invalid"):
        validate_observer_network_result(source, deleted)

    extra = replace(result)
    object.__setattr__(extra, "unexpected", "metadata")
    with pytest.raises(ObserverNetworkError, match="result-instance-shape-invalid"):
        validate_observer_network_result(source, extra)

    BombDict.calls = 0
    hostile = replace(result)
    object.__setattr__(hostile, "__dict__", BombDict(object.__getattribute__(hostile, "__dict__")))
    with pytest.raises(ObserverNetworkError, match="result-instance-shape-invalid"):
        validate_observer_network_result(source, hostile)
    assert BombDict.calls == 0


def test_huge_result_string_is_refused_by_remaining_codepoint_budget():
    source = network_source()
    result = observer_network_judgment(source)
    forged = replace(result, nonclaims=("x" * 5_000_000,))
    with pytest.raises(ObserverNetworkError, match="result-byte-hard-limit"):
        validate_observer_network_result(source, forged)


def test_parallel_reverse_edges_do_not_create_factorial_strict_cycle_search():
    source = network_source()
    judgment = observer_network_judgment(source)
    raw_by_id = {item.edge_id: item for item in source.translations}
    judged_by_id = {item.edge_id: item for item in judgment.edges}
    forward_raw = raw_by_id["nested-total"]
    reverse_raw = raw_by_id["total-nested"]
    forward_judged = judged_by_id["nested-total"]
    reverse_judged = judged_by_id["total-nested"]

    def committed(template, edge_id):
        return translation_source(
            edge_id,
            template.source_observer_id,
            template.target_observer_id,
            template.declared_domain,
            template.rows,
            template.dependency_ids,
        )

    forwards = tuple(committed(forward_raw, f"parallel-forward-{index}") for index in range(7))
    reverses = tuple(committed(reverse_raw, f"parallel-reverse-{index}") for index in range(7))
    synthetic = observer_network_source(
        source.doctrine_id,
        f"{source.source_id}-parallel-cycle",
        source.source_version,
        source.inputs,
        source.observers,
        forwards + reverses,
        (),
        source.p1a_doctrine,
        source.p1a_binding,
        source.p1a_stage_source,
        source.raw_pairs,
    )
    nonstrict_forwards = tuple(
        replace(forward_judged, edge_id=item.edge_id, refinement=RefinementStatus.NONSTRICT)
        for item in forwards[:-1]
    )
    nonstrict_reverses = tuple(
        replace(reverse_judged, edge_id=item.edge_id, refinement=RefinementStatus.NONSTRICT)
        for item in reverses
    )
    strict_last = replace(
        forward_judged, edge_id=forwards[-1].edge_id, refinement=RefinementStatus.STRICT
    )
    started = perf_counter()
    status, cycle = strict_cycle_check(
        synthetic, nonstrict_forwards + nonstrict_reverses + (strict_last,), 4096
    )
    elapsed = perf_counter() - started
    assert status is LawStatus.REFUTED
    assert cycle == (forwards[-1].edge_id, reverses[0].edge_id)
    assert elapsed < 1.0
