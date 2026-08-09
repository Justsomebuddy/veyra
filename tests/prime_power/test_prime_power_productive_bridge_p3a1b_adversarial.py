"""Twenty-design-attack fail-closed pressure for P3-A1b."""

from dataclasses import replace

import pytest

from src.core.prime_power_productive_bridge import (
    BridgeOpen, BridgeRefutation, ProductiveBridgeJudgment, ProductiveBridgeValidationError,
    ProjectionArtifact, establish_productive_family_bridge, productive_bridge_package,
    project_residue, refute_offset_program, report_missing_bridge_evidence,
    residue_program_source, validate_offset_refutation_result, validate_open_result,
    validate_productive_bridge_result, validate_projection_result,
)
from src.core.prime_power_productive_bridge_sources import PROGRAM_CONSTRUCTOR
from prime_power_productive_bridge_fixture import exact_a1b_package, exact_offset_pressure

pytestmark = pytest.mark.requires_lean


class HostileTuple(tuple):
    def __eq__(self, other):
        raise AssertionError("hostile equality reached")


class HostileResult(ProductiveBridgeJudgment):
    pass


class HostileStr(str):
    def encode(self, *args, **kwargs):
        raise AssertionError("hostile encode reached")


@pytest.mark.parametrize("field", [
    "constructor", "grammar_id", "program_digest",
])
def test_attacks_1_6_target_or_alternate_program_source(field):
    package = exact_a1b_package()
    program = residue_program_source(package.prime, package.integer)
    replacement = "EXPECTED_RESIDUE_OR_CALLBACK" if field != "program_digest" else "0" * 64
    bad = replace(program, **{field: replacement})
    with pytest.raises(ProductiveBridgeValidationError):
        productive_bridge_package(package.prime, package.integer, package.doctrine, bad,
                                  package.n1_theorem, package.theorem, package.ledger, package.policy)


def test_hostile_program_scalar_is_rejected_before_callback():
    package = exact_a1b_package()
    bad = replace(package.program, constructor=HostileStr(package.program.constructor))
    with pytest.raises(ProductiveBridgeValidationError):
        productive_bridge_package(package.prime, package.integer, package.doctrine, bad,
                                  package.n1_theorem, package.theorem, package.ledger, package.policy)


@pytest.mark.parametrize("field", [
    "artifact_sha256", "n1_artifact_sha256", "pomega2_artifact_sha256",
    "source_digest", "toolchain_id",
])
def test_attacks_2_5_12_15_theorem_or_typed_source_transplant(field):
    package = exact_a1b_package()
    value = "0" * 64 if field != "toolchain_id" else "foreign-toolchain"
    theorem = replace(package.theorem, **{field: value})
    with pytest.raises(ProductiveBridgeValidationError):
        productive_bridge_package(package.prime, package.integer, package.doctrine,
                                  package.program, package.n1_theorem, theorem,
                                  package.ledger, package.policy)


def test_attacks_7_8_10_11_prior_or_bounded_evidence_has_no_raw_lane():
    package = exact_a1b_package()
    judgment = establish_productive_family_bridge(package)
    with pytest.raises(TypeError):
        productive_bridge_package(package.prime, package.integer, package.doctrine,
                                  package.program, package.n1_theorem, package.theorem,
                                  package.ledger, package.policy, judgment)


def test_attack_13_circular_ledger_is_rejected():
    package = exact_a1b_package()
    edges = package.ledger.direct_edges + (("natural-numbers", "THM_P3A1B_004_commutes"),)
    ledger = replace(package.ledger, direct_edges=edges)
    with pytest.raises(ProductiveBridgeValidationError):
        productive_bridge_package(package.prime, package.integer, package.doctrine,
                                  package.program, package.n1_theorem, package.theorem,
                                  ledger, package.policy)


def test_attacks_16_hostile_union_subclass_rejected_before_equality():
    package = exact_a1b_package()
    value = establish_productive_family_bridge(package)
    hostile = HostileResult(**value.__dict__)
    with pytest.raises(ProductiveBridgeValidationError):
        validate_productive_bridge_result(package, hostile)


def test_attacks_16_hostile_nested_tuple_rejected_before_equality():
    package = exact_a1b_package()
    value = establish_productive_family_bridge(package)
    hostile = replace(value, theorem_ids=HostileTuple(value.theorem_ids))
    with pytest.raises(ProductiveBridgeValidationError):
        validate_productive_bridge_result(package, hostile)


def test_attacks_17_run_digest_cannot_be_inserted_in_program_identity():
    package = exact_a1b_package()
    program = replace(package.program, constructor=PROGRAM_CONSTRUCTOR + "@run=deadbeef")
    with pytest.raises(ProductiveBridgeValidationError):
        productive_bridge_package(package.prime, package.integer, package.doctrine,
                                  program, package.n1_theorem, package.theorem,
                                  package.ledger, package.policy)


def test_attacks_18_19_completion_or_p2s_fields_cannot_be_added():
    value = establish_productive_family_bridge(exact_a1b_package())
    assert value.promotions == 0
    assert not hasattr(value, "p2s_premise_kind")
    assert not hasattr(value, "completed_carrier_witness")


def test_attack_20_lean_source_does_not_invoke_n1_coherence_theorem():
    text = open("proofs/lean/VeyraPrimePowerProductiveBridge.lean", encoding="utf-8").read()
    body = text.split("THM_P3A1B_003_process_coherent", 1)[1].split("THM_P3A1B_004_commutes", 1)[0]
    assert "THM_P3N1_002_integer_residue_reduction" not in body
    assert "veyraIntegerFamily" not in body and "veyraIntegerResidue" not in body


def test_all_emitted_artifact_subclasses_are_rejected_before_replay():
    package = exact_a1b_package()
    projection = project_residue(package, 1)
    pressure = exact_offset_pressure(package)
    refutation = refute_offset_program(package, pressure, 0)
    opened = report_missing_bridge_evidence(package.prime, package.integer, package.program)
    hostile_projection = type("HostileProjection", (ProjectionArtifact,), {})(**projection.__dict__)
    hostile_refutation = type("HostileRefutation", (BridgeRefutation,), {})(**refutation.__dict__)
    hostile_open = type("HostileOpen", (BridgeOpen,), {})(**opened.__dict__)
    with pytest.raises(ProductiveBridgeValidationError):
        validate_projection_result(package, 1, hostile_projection)
    with pytest.raises(ProductiveBridgeValidationError):
        validate_offset_refutation_result(package, pressure, 0, hostile_refutation)
    with pytest.raises(ProductiveBridgeValidationError):
        validate_open_result(package.prime, package.integer, package.program, hostile_open)


def test_deleted_result_field_is_rejected_as_shape_not_attribute_fault():
    package = exact_a1b_package()
    value = project_residue(package, 1)
    object.__getattribute__(value, "__dict__").pop("residue")
    with pytest.raises(ProductiveBridgeValidationError):
        validate_projection_result(package, 1, value)
