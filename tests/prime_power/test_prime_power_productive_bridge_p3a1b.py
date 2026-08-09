"""Positive, projection, identity, and nonclaim tests for P3-A1b."""

from dataclasses import replace

import pytest

from src.core.prime_power_productive_bridge import (
    BoundaryStatus, BridgeEvidenceKind, BridgeResourceLimit, BridgeStatus,
    FamilyKind, ProductiveBridgeJudgment, ProductiveBridgeValidationError,
    ProjectionArtifact, ResultStatus, establish_productive_family_bridge,
    project_residue, refute_offset_program, report_missing_bridge_evidence,
    validate_offset_refutation_result, validate_open_result,
    validate_productive_bridge_result, validate_projection_result,
)
from src.core.padic_completion import prime_source
from src.core.padic_family_introduction import integer_source
from src.core.prime_power_productive_bridge import residue_program_source
from prime_power_productive_bridge_fixture import exact_a1b_package, exact_offset_pressure

pytestmark = pytest.mark.requires_lean


def test_exact_formal_bridge_and_fresh_replay():
    package = exact_a1b_package()
    value = establish_productive_family_bridge(package)
    replay = validate_productive_bridge_result(package, value)
    assert type(value) is ProductiveBridgeJudgment
    assert type(replay) is ProductiveBridgeJudgment and replay is not value
    assert value.family_kind is FamilyKind.ALL_DEPTH_FAMILY
    assert value.bridge_evidence_kind is BridgeEvidenceKind.PRODUCTIVE_FAMILY_BRIDGE
    assert value.bridge_status is BridgeStatus.ESTABLISHED_RELATIVE_TO_LEDGER


def test_six_identities_are_distinct_and_projection_run_is_absent():
    value = establish_productive_family_bridge(exact_a1b_package())
    identities = (value.program_digest, value.family_term_digest,
                  value.productivity_evidence_digest, value.family_introduction_digest,
                  value.bridge_evidence_digest, value.judgment_digest)
    assert len(set(identities)) == 6
    assert not hasattr(value, "projection_run_digest") and not hasattr(value, "run_digest")


def test_nonpromotion_and_infinity_boundaries_are_literal():
    value = establish_productive_family_bridge(exact_a1b_package())
    assert value.promotions == 0
    assert value.completed_carrier is BoundaryStatus.NOT_ESTABLISHED
    assert value.universal_completion is BoundaryStatus.OPEN
    assert value.physical_or_foundation_independent_infinity is BoundaryStatus.NOT_CLAIMED


@pytest.mark.parametrize("p,z,n", [(2, 19, 0), (2, -19, 4), (3, 71, 3), (3, -71, 5), (5, 0, 7)])
def test_fresh_bounded_qa_projection(p, z, n):
    package = exact_a1b_package(p, z)
    value = project_residue(package, n)
    assert type(value) is ProjectionArtifact
    assert value.qa_scope == "QA_BOUNDED"
    assert value.residue == z % (p ** (n + 1))
    assert validate_projection_result(package, n, value) == value


def test_runtime_policy_changes_run_not_program_or_family_identity():
    a = exact_a1b_package(max_depth=7)
    b = exact_a1b_package(max_depth=8)
    pa, pb = project_residue(a, 2), project_residue(b, 2)
    ja, jb = establish_productive_family_bridge(a), establish_productive_family_bridge(b)
    assert pa.projection_run_digest != pb.projection_run_digest
    assert ja.program_digest == jb.program_digest
    assert ja.family_term_digest == jb.family_term_digest


def test_closed_program_identity_binds_exact_prime_and_integer():
    base = exact_a1b_package(p=5, z=7).program.program_digest
    other_p = exact_a1b_package(p=3, z=7).program.program_digest
    other_z = exact_a1b_package(p=5, z=8).program.program_digest
    assert len({base, other_p, other_z}) == 3


def test_projection_resource_refusal_is_not_nonproductivity():
    value = project_residue(exact_a1b_package(max_depth=2), 3)
    assert type(value) is BridgeResourceLimit
    assert value.status is ResultStatus.RESOURCE_LIMIT


def test_negative_only_coherent_offset_is_refuted():
    package = exact_a1b_package()
    pressure = exact_offset_pressure(package)
    value = refute_offset_program(package, pressure, 0)
    assert value.status is ResultStatus.REFUTED
    assert value.expected_residue != value.observed_residue
    assert validate_offset_refutation_result(package, pressure, 0, value) == value


def test_missing_admissible_bridge_evidence_is_typed_open():
    prime, integer = prime_source(5), integer_source(7)
    value = report_missing_bridge_evidence(
        prime, integer, residue_program_source(prime, integer),
    )
    assert value.status is ResultStatus.OPEN
    assert value.reason == "missing-admissible-bridge-evidence"
    assert validate_open_result(prime, integer, residue_program_source(prime, integer), value) == value


@pytest.mark.parametrize("offset", [0, True])
def test_pressure_grammar_rejects_nonnegative_lane(offset):
    package = exact_a1b_package()
    with pytest.raises(ProductiveBridgeValidationError):
        from src.core.prime_power_productive_bridge import offset_residue_program_source
        offset_residue_program_source(package.prime, package.integer, offset)


def test_pressure_negative_depth_is_rejected():
    package = exact_a1b_package()
    with pytest.raises(ProductiveBridgeValidationError):
        refute_offset_program(package, exact_offset_pressure(package), -1)


def test_result_transplant_across_integer_is_rejected():
    value = establish_productive_family_bridge(exact_a1b_package(z=7))
    with pytest.raises(ProductiveBridgeValidationError):
        validate_productive_bridge_result(exact_a1b_package(z=8), value)


def test_result_transplant_across_prime_is_rejected():
    value = establish_productive_family_bridge(exact_a1b_package(p=3))
    with pytest.raises(ProductiveBridgeValidationError):
        validate_productive_bridge_result(exact_a1b_package(p=5), value)


def test_forged_completion_and_promotion_are_rejected_before_replay():
    package = exact_a1b_package()
    value = establish_productive_family_bridge(package)
    with pytest.raises(ProductiveBridgeValidationError):
        validate_productive_bridge_result(package, replace(value, promotions=1))
    with pytest.raises(ProductiveBridgeValidationError):
        validate_productive_bridge_result(
            package, replace(value, completed_carrier=BoundaryStatus.OPEN),
        )
