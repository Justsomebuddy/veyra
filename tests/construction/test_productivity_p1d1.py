"""Positive laws and permanent boundaries for provisional P1-D1."""

import inspect

import src.core.productivity_runtime as runtime
from src.core.finite_builder_types import TargetIndependence
from src.core.infinity_prefix import prefix_alphabet
from src.core.productivity import (
    OUTPUT_ENCODING_ID, RESTRICTION_LAW_ID, TOTALITY_BASIS_ID,
    construct_at_depth, execution_policy, periodic_program,
    productive_process_source, restriction_judgment,
    validate_construction_result, validate_restriction_result,
)
from src.core.productivity_digest import encode_stage, required_output_bytes
from src.core.productivity_types import (
    AllDepthEvidenceStatus, AllDepthProvenance, CompletedCarrierStatus,
    ConstructionArtifact, OperationKind, OperationStatus, PointwiseSchemaStatus,
    PointwiseStatus, ProductivityStatus, ResourceBound, ResourceLimitResult,
    RestrictionArtifact, StructuralGuardedness,
)


def make_source(*, max_depth=32, max_output_bytes=100_000, period=("a", "b", "a")):
    program = periodic_program(prefix_alphabet(("a", "b")), period)
    policy = execution_policy(max_depth, max_output_bytes)
    source = productive_process_source(
        program, TOTALITY_BASIS_ID, RESTRICTION_LAW_ID, OUTPUT_ENCODING_ID, policy
    )
    return program, policy, source


def test_zero_and_positive_depth_formula_are_one_row_only():
    _, _, source = make_source()
    zero = construct_at_depth(source, 0)
    row = construct_at_depth(source, 8)
    assert isinstance(zero, ConstructionArtifact) and isinstance(row, ConstructionArtifact)
    assert zero.depth == zero.stage.depth == 0 and zero.stage.symbols == ()
    assert row.depth == row.stage.depth == len(row.stage.symbols) == 8
    assert row.stage.symbols == ("a", "b", "a", "a", "b", "a", "a", "b")
    assert not hasattr(row, "stages") and not hasattr(row, "window")


def test_deterministic_commitments_have_fresh_result_stage_and_symbols():
    _, _, source = make_source()
    first = construct_at_depth(source, 7)
    second = construct_at_depth(source, 7)
    assert isinstance(first, ConstructionArtifact) and isinstance(second, ConstructionArtifact)
    assert first == second and first is not second
    assert first.stage is not second.stage
    assert first.stage.symbols is not second.stage.symbols
    fresh = validate_construction_result(source, 7, first)
    assert isinstance(fresh, ConstructionArtifact)
    assert fresh == first and fresh is not first and fresh.stage is not first.stage


def test_restriction_identity_composition_freshness_and_determinism():
    _, _, source = make_source()
    identity = restriction_judgment(source, 6, 6)
    lower_mid = restriction_judgment(source, 2, 4)
    mid_upper = restriction_judgment(source, 4, 7)
    lower_upper = restriction_judgment(source, 2, 7)
    again = restriction_judgment(source, 2, 7)
    assert all(isinstance(item, RestrictionArtifact) for item in (
        identity, lower_mid, mid_upper, lower_upper, again
    ))
    assert identity.lower_stage == identity.upper_stage == identity.restricted_stage
    assert identity.lower_stage is not identity.upper_stage
    assert identity.upper_stage is not identity.restricted_stage
    assert identity.restricted_stage.symbols is not identity.upper_stage.symbols
    assert lower_upper.restricted_output_digest == lower_mid.restricted_output_digest
    assert mid_upper.restricted_output_digest == mid_upper.lower_output_digest
    assert lower_upper == again and lower_upper is not again
    fresh = validate_restriction_result(source, 2, 7, lower_upper)
    assert fresh == lower_upper and fresh is not lower_upper


def test_same_generator_different_policy_keeps_math_identity_not_provenance():
    program, _, first_source = make_source(max_depth=8)
    second_policy = execution_policy(16, 200_000)
    second_source = productive_process_source(
        program, TOTALITY_BASIS_ID, RESTRICTION_LAW_ID, OUTPUT_ENCODING_ID, second_policy
    )
    first = construct_at_depth(first_source, 6)
    second = construct_at_depth(second_source, 6)
    assert isinstance(first, ConstructionArtifact) and isinstance(second, ConstructionArtifact)
    assert first.program_digest == second.program_digest
    assert first.generator_digest == second.generator_digest
    assert first.output_digest == second.output_digest
    assert first.policy_digest != second.policy_digest
    assert first.source_digest != second.source_digest
    assert first.run_digest != second.run_digest


def test_matching_samples_do_not_identify_different_programs():
    first_program, _, first_source = make_source(period=("a",))
    second_program, _, second_source = make_source(period=("a", "a"))
    first = construct_at_depth(first_source, 10)
    second = construct_at_depth(second_source, 10)
    assert isinstance(first, ConstructionArtifact) and isinstance(second, ConstructionArtifact)
    assert first.stage.symbols == second.stage.symbols
    assert first.output_digest == second.output_digest
    assert first_program.program_digest != second_program.program_digest
    assert first.generator_digest != second.generator_digest


def test_exact_depth_and_output_caps_refuse_without_partial_artifact():
    program, _, _ = make_source()
    exact_bytes = required_output_bytes(5, program.period, OUTPUT_ENCODING_ID)
    exact_source = productive_process_source(
        program, TOTALITY_BASIS_ID, RESTRICTION_LAW_ID, OUTPUT_ENCODING_ID,
        execution_policy(5, exact_bytes),
    )
    exact_row = construct_at_depth(exact_source, 5)
    assert isinstance(exact_row, ConstructionArtifact)
    assert len(encode_stage(exact_row.stage)) == exact_bytes
    depth_refusal = construct_at_depth(exact_source, 6)
    byte_source = productive_process_source(
        program, TOTALITY_BASIS_ID, RESTRICTION_LAW_ID, OUTPUT_ENCODING_ID,
        execution_policy(5, exact_bytes - 1),
    )
    byte_refusal = construct_at_depth(byte_source, 5)
    assert isinstance(depth_refusal, ResourceLimitResult)
    assert isinstance(byte_refusal, ResourceLimitResult)
    assert depth_refusal.failed_bound is ResourceBound.DEPTH
    assert byte_refusal.failed_bound is ResourceBound.OUTPUT_BYTES
    for refusal in (depth_refusal, byte_refusal):
        assert refusal.operation_status is OperationStatus.RESOURCE_LIMIT
        assert not hasattr(refusal, "stage") and not hasattr(refusal, "output_digest")
        assert not hasattr(refusal, "trace_digest")


def test_restriction_cap_charges_all_three_finite_outputs():
    program, _, _ = make_source()
    lower = required_output_bytes(2, program.period, OUTPUT_ENCODING_ID)
    upper = required_output_bytes(6, program.period, OUTPUT_ENCODING_ID)
    total = lower + upper + lower
    exact = productive_process_source(
        program, TOTALITY_BASIS_ID, RESTRICTION_LAW_ID, OUTPUT_ENCODING_ID,
        execution_policy(6, total),
    )
    tight = productive_process_source(
        program, TOTALITY_BASIS_ID, RESTRICTION_LAW_ID, OUTPUT_ENCODING_ID,
        execution_policy(6, total - 1),
    )
    assert isinstance(restriction_judgment(exact, 2, 6), RestrictionArtifact)
    refusal = restriction_judgment(tight, 2, 6)
    assert isinstance(refusal, ResourceLimitResult)
    assert refusal.failed_bound is ResourceBound.OUTPUT_BYTES
    assert (refusal.required_value, refusal.allowed_value) == (total, total - 1)


def test_closed_statuses_and_target_free_surface_never_promote():
    _, _, source = make_source(max_depth=1)
    positive = construct_at_depth(source, 1)
    refusal = construct_at_depth(source, 2)
    assert isinstance(positive, ConstructionArtifact) and isinstance(refusal, ResourceLimitResult)
    for row in (positive, refusal):
        assert row.guardedness is StructuralGuardedness.STRUCTURALLY_GUARDED
        assert row.pointwise_schema is PointwiseSchemaStatus.ESTABLISHED
        assert row.productivity is ProductivityStatus.PRODUCTIVE
        assert row.all_depth_family is AllDepthEvidenceStatus.OPEN
        assert row.all_depth_provenance is AllDepthProvenance.OPEN
        assert row.completed_carrier is CompletedCarrierStatus.NOT_ESTABLISHED
        assert row.target_independence is TargetIndependence.NOT_ESTABLISHED
    assert positive.pointwise_status is PointwiseStatus.POINTWISE_CONSTRUCTIBLE
    assert not hasattr(refusal, "pointwise_status")
    assert set(inspect.signature(construct_at_depth).parameters) == {"source", "n"}
    assert set(inspect.signature(restriction_judgment).parameters) == {"source", "m", "n"}
    assert tuple(AllDepthEvidenceStatus) == (AllDepthEvidenceStatus.OPEN,)
    assert tuple(AllDepthProvenance) == (AllDepthProvenance.OPEN,)
    assert refusal.operation is OperationKind.CONSTRUCT


def test_instrumentation_confirms_no_prefix_tower_build(monkeypatch):
    _, _, source = make_source()
    calls: list[int] = []
    original = runtime._build_stage

    def counted(item, depth):
        calls.append(depth)
        return original(item, depth)

    monkeypatch.setattr(runtime, "_build_stage", counted)
    assert isinstance(construct_at_depth(source, 9), ConstructionArtifact)
    assert calls == [9]
    calls.clear()
    assert isinstance(restriction_judgment(source, 3, 9), RestrictionArtifact)
    assert calls == [3, 9]
