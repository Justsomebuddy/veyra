"""Fail-fast source/demand-bound downstream revalidation for P1-D1."""

from dataclasses import replace

import pytest

import src.core.productivity_result_validation as validation
from src.core.infinity_prefix_types import PrefixAlphabet
from src.core.productivity import (
    OUTPUT_ENCODING_ID, RESTRICTION_LAW_ID, TOTALITY_BASIS_ID,
    construct_at_depth, execution_policy, periodic_program,
    productive_process_source, restriction_judgment,
    validate_construction_result, validate_restriction_result,
)
from src.core.productivity_types import (
    ConstructionArtifact, PeriodicPrefixStage, ResourceLimitResult,
    RestrictionArtifact,
)
from src.core.productivity_validation import ProductivityValidationError


def source(*, depth=8, output=100_000):
    program = periodic_program(PrefixAlphabet(("a", "b")), ("a", "b"))
    policy = execution_policy(depth, output)
    return productive_process_source(
        program, TOTALITY_BASIS_ID, RESTRICTION_LAW_ID, OUTPUT_ENCODING_ID, policy,
    )


def forbid_stage_snapshot(monkeypatch):
    calls = []

    def forbidden(*args):
        calls.append(args)
        raise AssertionError("stage traversal occurred before outer precheck")

    monkeypatch.setattr(validation, "snapshot_periodic_prefix_stage", forbidden)
    return calls


def test_construction_variant_outer_digest_and_huge_stage_fail_before_traversal(monkeypatch):
    valid = source()
    row = construct_at_depth(valid, 1)
    refusal = construct_at_depth(source(depth=0), 1)
    assert isinstance(row, ConstructionArtifact)
    assert isinstance(refusal, ResourceLimitResult)
    calls = forbid_stage_snapshot(monkeypatch)
    with pytest.raises(ProductivityValidationError, match="union-variant"):
        validate_construction_result(valid, 1, refusal)
    with pytest.raises(ProductivityValidationError, match="outer-precheck"):
        validate_construction_result(valid, 1, replace(row, run_digest="0" * 64))
    huge = PeriodicPrefixStage(1, ("a",) * 100_000, OUTPUT_ENCODING_ID)
    with pytest.raises(ProductivityValidationError, match="outer-precheck"):
        validate_construction_result(valid, 1, replace(row, stage=huge))
    assert calls == []


def test_restriction_all_three_depths_fail_before_any_stage_traversal(monkeypatch):
    valid = source()
    row = restriction_judgment(valid, 1, 3)
    assert isinstance(row, RestrictionArtifact)
    calls = forbid_stage_snapshot(monkeypatch)
    huge = PeriodicPrefixStage(10**1000, ("a",), OUTPUT_ENCODING_ID)
    for field in ("lower_stage", "upper_stage", "restricted_stage"):
        with pytest.raises(ProductivityValidationError, match="outer-precheck"):
            validate_restriction_result(valid, 1, 3, replace(row, **{field: huge}))
    assert calls == []


def test_restriction_and_refusal_transplants_are_source_and_demand_bound():
    first = source(depth=8, output=100_000)
    second = source(depth=9, output=100_001)
    restriction = restriction_judgment(first, 1, 3)
    assert isinstance(restriction, RestrictionArtifact)
    with pytest.raises(ProductivityValidationError, match="outer-precheck"):
        validate_restriction_result(second, 1, 3, restriction)
    capped = source(depth=1, output=100_000)
    refusal = construct_at_depth(capped, 2)
    assert isinstance(refusal, ResourceLimitResult)
    with pytest.raises(ProductivityValidationError, match="outer-precheck"):
        validate_construction_result(capped, 3, refusal)
    other = source(depth=1, output=100_001)
    with pytest.raises(ProductivityValidationError, match="outer-precheck"):
        validate_construction_result(other, 2, refusal)
    astronomical = 10**100_000
    for forged in (
        replace(refusal, requested_depths=(astronomical,)),
        replace(refusal, required_value=astronomical),
        replace(refusal, allowed_value=astronomical),
    ):
        with pytest.raises(ProductivityValidationError, match="outer-precheck"):
            validate_construction_result(capped, 2, forged)
    assert not hasattr(validation, "run_digest")
    assert not hasattr(validation, "refusal_digest")


def test_forged_trace_restriction_outputs_and_evidence_fail_before_stage_snapshot(monkeypatch):
    valid = source()
    construction = construct_at_depth(valid, 2)
    restriction = restriction_judgment(valid, 1, 3)
    assert isinstance(construction, ConstructionArtifact)
    assert isinstance(restriction, RestrictionArtifact)
    calls = forbid_stage_snapshot(monkeypatch)
    with pytest.raises(ProductivityValidationError, match="outer-precheck"):
        validate_construction_result(
            valid, 2, replace(construction, trace_digest="0" * 64),
        )
    for field in (
        "lower_output_digest", "upper_output_digest",
        "restricted_output_digest", "evidence_digest",
    ):
        with pytest.raises(ProductivityValidationError, match="outer-precheck"):
            validate_restriction_result(
                valid, 1, 3, replace(restriction, **{field: "0" * 64}),
            )
    assert calls == []
