"""Positive, local, global, and C2.2-derived reconciliation tests."""

from dataclasses import replace
import pytest
from src.core.transport_coherence import (
    GeneratedTransportCoherence,
    HigherCellStructureStatus,
    TransportCoherenceError,
    TransportCoherenceStatus,
    TransportFailedBound,
    TransportResourceLimit,
    apply_path,
    cofinal_boundary_reconciliation,
    generated_transport_coherence,
    generated_transport_filler,
    paths_equivalent,
    transport_package,
    validate_transport_result,
)
from src.core.transport_coherence_examples import unequal_transport_example
from transport_coherence_fixture import exact_transport_package

pytestmark = pytest.mark.requires_lean


def test_exact_total_transport_is_edge_derived_and_typed():
    package = exact_transport_package()
    assert apply_path(package.system, package.doctrine, "x", ("xy", "yw"), "1") == ("w", "1")
    assert paths_equivalent(package.system, package.doctrine, "x", ("xy", "yw"), ("xz", "zw"))


def test_local_squares_and_global_generated_fillers_are_established():
    value = generated_transport_coherence(exact_transport_package())
    assert type(value) is GeneratedTransportCoherence
    assert value.status is TransportCoherenceStatus.GENERATED_TRANSPORT_COHERENT_RELATIVE_TO_SYSTEM
    assert value.local_square_count == 2 and value.global_boundary_count == len(value.global_fillers) == 72
    assert value.formal_phase_count == 3


def test_result_fresh_replay_and_permanent_boundaries():
    package = exact_transport_package()
    value = generated_transport_coherence(package)
    replay = validate_transport_result(package, value)
    assert replay == value and replay is not value
    assert value.higher_cell_structure is HigherCellStructureStatus.NOT_IMPLEMENTED
    assert "no-admitted-source-bound-3cell-universe" in value.nonclaims
    assert "p3t-adapter-gated-unreleased" in value.nonclaims
    assert "symbolic-natop-from-finite-tlgc" in value.nonclaims


def test_missing_ordered_local_peak_is_open_not_established():
    package = exact_transport_package()
    incomplete = transport_package(
        package.system,
        package.doctrine,
        package.local_fillers[:1],
        package.theorem_source,
        package.assumption_ledger,
        package.policy,
    )
    value = generated_transport_coherence(incomplete)
    assert value.status is TransportCoherenceStatus.OPEN and value.local_square_count == 2


def test_joinable_endpoints_can_refute_transport_coherence():
    value = generated_transport_coherence(unequal_transport_example().package)
    assert value.status is TransportCoherenceStatus.REFUTED
    assert value.global_boundary_count == 0


def test_policy_refusal_is_typed_and_has_no_coherence_payload():
    value = generated_transport_coherence(exact_transport_package(max_values=1))
    assert type(value) is TransportResourceLimit
    assert not hasattr(value, "global_fillers") and value.required_value > value.allowed_value


def test_global_boundary_work_is_bounded_before_filler_search():
    from src.core.transport_coherence_examples import positive_example

    value = generated_transport_coherence(positive_example(max_generated_paths=50).package)
    assert type(value) is TransportResourceLimit
    assert value.failed_bound is TransportFailedBound.GENERATED_PATHS and value.required_value == 72


def test_c22_derived_cofinal_boundary_reconciliation_is_not_a_3cell():
    package = exact_transport_package()
    first = generated_transport_filler(package, "x", ("xy",), ("xz",), "w", ("yw",), ("zw",))
    second = generated_transport_filler(package, "x", ("xy",), ("xz",), "v", ("yw", "wv"), ("zw", "wv"))
    value = cofinal_boundary_reconciliation(package, first, second, "v", ("wv",), ())
    assert value.first_target_state_id == "w" and value.second_target_state_id == "v"
    assert value.postjoin_state_id == "v" and value.first_postpath == ("wv",)
    assert not hasattr(value, "cell_digest")


def test_forged_filler_digest_is_rejected_before_cofinal_use():
    package = exact_transport_package()
    first = generated_transport_filler(package, "x", ("xy",), ("xz",), "w", ("yw",), ("zw",))
    with pytest.raises(TransportCoherenceError):
        cofinal_boundary_reconciliation(package, replace(first, filler_digest="0" * 64), first, "w", (), ())


def test_exact_semantic_work_cap_refuses_before_search():
    from src.core.transport_coherence_examples import positive_example

    established = generated_transport_coherence(positive_example().package)
    assert type(established) is GeneratedTransportCoherence and established.semantic_work > 0
    refused = generated_transport_coherence(
        positive_example(max_semantic_work=established.semantic_work - 1).package
    )
    assert type(refused) is TransportResourceLimit
    assert refused.failed_bound is TransportFailedBound.SEMANTIC_WORK
    assert refused.required_value == established.semantic_work
