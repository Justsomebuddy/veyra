"""Positive and exact-source tests for P3-C1."""

from src.core.generated_confluence import (
    GeneratedConfluenceStatus,
    GeneratedFiniteConfluence,
    carry_normalization_probe,
    generated_finite_confluence,
    generated_local_peaks,
    generated_reachable,
    validate_generated_confluence_result,
)
from generated_confluence_fixture import positive_package
import pytest

pytestmark = pytest.mark.requires_lean


def test_complete_ordered_peak_universe_and_positive_result():
    system, cells = positive_package()
    states, edges = generated_reachable(system)
    peaks = generated_local_peaks(system)
    assert states == ("v", "w", "x", "y", "z") and edges == ("wv", "xy", "xz", "yw", "zw")
    assert tuple((p.left_edge_id, p.right_edge_id) for p in peaks) == (("xy", "xz"), ("xz", "xy"))
    result = generated_finite_confluence(system, cells)
    assert type(result) is GeneratedFiniteConfluence
    assert result.status is GeneratedConfluenceStatus.GENERATED_FINITE_CONFLUENT_RELATIVE_TO_SYSTEM
    assert all(row.left_endpoint_id == row.right_endpoint_id == "w" for row in result.rows)
    assert result.first_counterexample_peak_id is None


def test_result_is_freshly_replayed_and_has_no_transport_claim():
    system, cells = positive_package()
    result = generated_finite_confluence(system, cells)
    fresh = validate_generated_confluence_result(system, cells, result)
    assert fresh == result and fresh is not result
    assert "no-c1-c3-transport-claim" in result.nonclaims
    assert "transport-path-independence" in result.nonclaims


def test_bounded_number_probe_is_experiment_only():
    rows = carry_normalization_probe()
    assert len(rows) == 6
    assert {(r.prime_base, r.precision) for r in rows} == {
        (2, 1),
        (2, 2),
        (2, 3),
        (3, 1),
        (3, 2),
        (3, 3),
    }
    assert all(r.scope == "experiment-only-no-general-rule-source" for r in rows)
    assert all(r.generated_peak_count > 0 and r.value_preserved for r in rows)
    assert all(r.status == "generated-ranked-confluent" for r in rows)


def test_parallel_edge_occurrences_remain_distinct_ordered_peaks():
    from src.core.generated_confluence import (
        StateRank,
        continuation_edge,
        continuation_state,
        ranked_continuation_system,
    )

    states = (continuation_state("root", "node", b"r"), continuation_state("sink", "node", b"s"))
    edges = (
        continuation_edge("parallel-a", "root", "sink", "rule-a", b"same-target"),
        continuation_edge("parallel-b", "root", "sink", "rule-b", b"same-target"),
    )
    system = ranked_continuation_system(
        "p3c1-doctrine",
        "parallel-system",
        "v1",
        states,
        edges,
        ("root",),
        (StateRank("root", 1), StateRank("sink", 0)),
    )
    reachable, _ = generated_reachable(system)
    peaks = generated_local_peaks(system)
    assert tuple((row.left_edge_id, row.right_edge_id) for row in peaks) == (
        ("parallel-a", "parallel-b"),
        ("parallel-b", "parallel-a"),
    )
