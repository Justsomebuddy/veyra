"""Hostile exactness, resource, mutation, and nonpromotion pressure for P1-D1."""

from dataclasses import replace

import pytest

import src.core.productivity_runtime as runtime
from src.core.finite_builder_types import TargetIndependence
from src.core.infinity_prefix_types import PrefixAlphabet
from src.core.productivity import (
    OUTPUT_ENCODING_ID, RESTRICTION_LAW_ID, TOTALITY_BASIS_ID,
    construct_at_depth, execution_policy, periodic_program,
    productive_process_source, restriction_judgment,
    validate_construction_result, validate_restriction_result,
)
from src.core.productivity_types import (
    AllDepthEvidenceStatus, CompletedCarrierStatus, ConstructionArtifact,
    OperationStatus, PeriodicProgram, ProductivityStatus, ResourceLimitResult,
    RestrictionArtifact,
)
from src.core.productivity_validation import (
    MAX_PERIOD_SYMBOLS, MAX_POLICY_DEPTH, MAX_POLICY_OUTPUT_BYTES,
    ProductivityValidationError,
)


def source(*, period=("a", "b"), depth=16, output=100_000):
    program = periodic_program(PrefixAlphabet(("a", "b")), period)
    policy = execution_policy(depth, output)
    return productive_process_source(
        program, TOTALITY_BASIS_ID, RESTRICTION_LAW_ID, OUTPUT_ENCODING_ID, policy
    )


class ProgramSubclass(PeriodicProgram):
    pass


class DuckSource:
    def program(self):
        return None


def test_empty_oversized_foreign_nonexact_and_table_periods_reject():
    alphabet = PrefixAlphabet(("a", "b"))
    with pytest.raises(ProductivityValidationError, match="invalid-period"):
        periodic_program(alphabet, ())
    with pytest.raises(ProductivityValidationError, match="invalid-period"):
        periodic_program(alphabet, ("a",) * (MAX_PERIOD_SYMBOLS + 1))
    with pytest.raises(ProductivityValidationError, match="foreign-or-nonexact"):
        periodic_program(alphabet, ("foreign",))
    with pytest.raises(ProductivityValidationError, match="foreign-or-nonexact"):
        periodic_program(alphabet, (lambda: "a",))  # type: ignore[arg-type]
    with pytest.raises(ProductivityValidationError, match="invalid-period"):
        periodic_program(alphabet, ["a", "b"])  # type: ignore[arg-type]
    with pytest.raises(ProductivityValidationError, match="invalid-period"):
        periodic_program(alphabet, {0: "a"})  # type: ignore[arg-type]


def test_callable_subclass_duck_source_and_raw_target_reject():
    valid = source()
    subclass = ProgramSubclass(
        valid.program.version, valid.program.alphabet,
        valid.program.period, valid.program.program_digest,
    )
    with pytest.raises(ProductivityValidationError, match="program-must-be-exact"):
        productive_process_source(
            subclass, TOTALITY_BASIS_ID, RESTRICTION_LAW_ID,
            OUTPUT_ENCODING_ID, valid.policy,
        )
    for alien in (DuckSource(), lambda: valid, ("a", "b")):
        with pytest.raises(ProductivityValidationError, match="source-must-be-exact"):
            construct_at_depth(alien, 2)  # type: ignore[arg-type]


def test_duplicate_surrogate_and_nonexact_alphabet_reject_as_named_validation():
    for alphabet in (
        PrefixAlphabet(("a", "a")), PrefixAlphabet(("\ud800",)),
        PrefixAlphabet(("a", 1)),
    ):
        with pytest.raises(ProductivityValidationError, match="alphabet"):
            periodic_program(alphabet, ("a",))  # type: ignore[arg-type]


def test_negative_bool_noninteger_and_astronomical_depths():
    valid = source(depth=4)
    for value in (-1, True, 1.5, "2"):
        with pytest.raises(ProductivityValidationError, match="construction-depth"):
            construct_at_depth(valid, value)  # type: ignore[arg-type]
    astronomical = construct_at_depth(valid, 10**1000)
    assert isinstance(astronomical, ResourceLimitResult)
    assert astronomical.required_value == 10**1000
    assert not hasattr(astronomical, "stage")


def test_unknown_versions_basis_law_encoding_and_oracle_reject():
    alphabet = PrefixAlphabet(("a",))
    with pytest.raises(ProductivityValidationError, match="program-version"):
        periodic_program(alphabet, ("a",), "unknown")
    with pytest.raises(ProductivityValidationError, match="policy-version"):
        execution_policy(1, 100, "unknown")
    valid = source()
    rows = (
        ("oracle-total", RESTRICTION_LAW_ID, OUTPUT_ENCODING_ID),
        (TOTALITY_BASIS_ID, "unknown-law", OUTPUT_ENCODING_ID),
        (TOTALITY_BASIS_ID, RESTRICTION_LAW_ID, "unknown-encoding"),
    )
    for basis, law, encoding in rows:
        with pytest.raises(ProductivityValidationError, match="basis-law-or-encoding"):
            productive_process_source(valid.program, basis, law, encoding, valid.policy)


def test_policy_hard_bounds_bool_and_mutation_reject():
    for depth, output in (
        (True, 100), (MAX_POLICY_DEPTH + 1, 100),
        (1, 0), (1, True), (1, MAX_POLICY_OUTPUT_BYTES + 1),
    ):
        with pytest.raises(ProductivityValidationError, match="policy"):
            execution_policy(depth, output)  # type: ignore[arg-type]
    valid = source()
    object.__setattr__(valid.policy, "max_depth", valid.policy.max_depth + 1)
    with pytest.raises(ProductivityValidationError, match="policy-drift"):
        construct_at_depth(valid, 1)


def test_program_source_and_reordered_period_stale_digest_mutations_reject():
    first = source()
    object.__setattr__(first.program, "period", tuple(reversed(first.program.period)))
    with pytest.raises(ProductivityValidationError, match="program-drift"):
        construct_at_depth(first, 2)
    second = source()
    object.__setattr__(second, "generator_digest", "0" * 64)
    with pytest.raises(ProductivityValidationError, match="source-drift"):
        construct_at_depth(second, 2)
    ab = source(period=("a", "b"))
    ba = source(period=("b", "a"))
    assert ab.program.program_digest != ba.program.program_digest


def test_counted_digest_framing_separates_ambiguous_symbol_boundaries():
    left = periodic_program(PrefixAlphabet(("ab", "c")), ("ab", "c"))
    right = periodic_program(PrefixAlphabet(("a", "bc")), ("a", "bc"))
    assert "".join(left.alphabet.symbols) == "".join(right.alphabet.symbols)
    assert "".join(left.period) == "".join(right.period)
    assert left.program_digest != right.program_digest


def test_restriction_m_greater_n_rejects_before_emission(monkeypatch):
    valid = source()
    calls = 0

    def forbidden(*args):
        nonlocal calls
        calls += 1
        raise AssertionError("emission-before-order-check")

    monkeypatch.setattr(runtime, "_build_stage", forbidden)
    with pytest.raises(ProductivityValidationError, match="m-less-or-equal"):
        restriction_judgment(valid, 5, 4)
    assert calls == 0


def test_depth_and_output_refusal_happen_before_emission(monkeypatch):
    depth_source = source(depth=1)
    byte_source = source(depth=4, output=1)
    calls = 0

    def forbidden(*args):
        nonlocal calls
        calls += 1
        raise AssertionError("emission-before-resource-check")

    monkeypatch.setattr(runtime, "_build_stage", forbidden)
    assert isinstance(construct_at_depth(depth_source, 2), ResourceLimitResult)
    assert isinstance(construct_at_depth(byte_source, 1), ResourceLimitResult)
    assert calls == 0


def test_matching_prefixes_different_programs_are_incomparable():
    one = source(period=("a",))
    two = source(period=("a", "a"))
    left, right = construct_at_depth(one, 8), construct_at_depth(two, 8)
    assert isinstance(left, ConstructionArtifact) and isinstance(right, ConstructionArtifact)
    assert left.stage.symbols == right.stage.symbols
    assert left.program_digest != right.program_digest
    with pytest.raises(ProductivityValidationError, match="outer-precheck"):
        validate_construction_result(two, 8, left)


def test_construction_and_restriction_nested_alias_mutation_revalidation():
    valid = source()
    construction = construct_at_depth(valid, 5)
    restriction = restriction_judgment(valid, 2, 5)
    assert isinstance(construction, ConstructionArtifact)
    assert isinstance(restriction, RestrictionArtifact)
    object.__setattr__(construction.stage, "symbols", ("b",) * 5)
    with pytest.raises(ProductivityValidationError):
        validate_construction_result(valid, 5, construction)
    object.__setattr__(restriction.restricted_stage, "symbols", ("b", "b"))
    with pytest.raises(ProductivityValidationError):
        validate_restriction_result(valid, 2, 5, restriction)
    fresh = construct_at_depth(valid, 5)
    assert isinstance(fresh, ConstructionArtifact)
    assert fresh.stage.symbols == ("a", "b", "a", "b", "a")


def test_forged_output_status_and_resource_digests_fail_revalidation():
    valid = source(depth=1)
    row = construct_at_depth(valid, 1)
    refusal = construct_at_depth(valid, 2)
    assert isinstance(row, ConstructionArtifact) and isinstance(refusal, ResourceLimitResult)
    forged_output = replace(row, output_digest="0" * 64)
    with pytest.raises(ProductivityValidationError, match="outer-precheck"):
        validate_construction_result(valid, 1, forged_output)
    object.__setattr__(row, "all_depth_family", "established")
    with pytest.raises(ProductivityValidationError, match="permanent-status"):
        validate_construction_result(valid, 1, row)
    forged_refusal = replace(refusal, refusal_digest="0" * 64)
    with pytest.raises(ProductivityValidationError, match="outer-precheck"):
        validate_construction_result(valid, 2, forged_refusal)


def test_unexpected_internal_exception_is_never_resource_or_open(monkeypatch):
    valid = source()

    def explode(*args):
        raise RuntimeError("unexpected-internal")

    monkeypatch.setattr(runtime, "_build_stage", explode)
    with pytest.raises(RuntimeError, match="unexpected-internal"):
        construct_at_depth(valid, 1)


def test_target_inspected_before_source_selection_still_not_independent():
    target = ("a", "b", "a")
    selected = source(period=target)
    row = construct_at_depth(selected, len(target))
    assert isinstance(row, ConstructionArtifact)
    assert row.stage.symbols == target
    assert row.target_independence is TargetIndependence.NOT_ESTABLISHED
    assert row.all_depth_family is AllDepthEvidenceStatus.OPEN
    assert row.completed_carrier is CompletedCarrierStatus.NOT_ESTABLISHED


def test_refusal_preserves_productive_nonclaims_and_has_no_partial_fields():
    valid = source(depth=0)
    refusal = construct_at_depth(valid, 1)
    assert isinstance(refusal, ResourceLimitResult)
    assert refusal.operation_status is OperationStatus.RESOURCE_LIMIT
    assert refusal.productivity is ProductivityStatus.PRODUCTIVE
    assert refusal.all_depth_family is AllDepthEvidenceStatus.OPEN
    assert refusal.completed_carrier is CompletedCarrierStatus.NOT_ESTABLISHED
    assert refusal.target_independence is TargetIndependence.NOT_ESTABLISHED
    assert not ({"stage", "output_digest", "trace_digest"} & set(refusal.__dataclass_fields__))
