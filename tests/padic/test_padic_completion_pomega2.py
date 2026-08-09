"""Positive, bounded-shadow, refusal, and separation tests for PΩ2."""

from dataclasses import replace

import pytest

from src.core.certify_padic_completion import certify_padic_completion_pomega2
from src.core.padic_completion import (
    CANONICAL_OPS_ID, CONCRETE_INSTANCE_ID, POMEGA2_NONCLAIMS,
    PadicCompletedCarrierStatus, PadicCompletionJudgment,
    PadicCompletionResourceLimit, PadicFormalExecutionFailure,
    PadicNotClaimedStatus, PadicNotEstablishedStatus,
    PadicObligationStatus, PadicCompletionValidationError, bounded_padic_shadow,
    padic_completion_judgment, prime_source, validate_padic_completion_result,
)
from src.core.padic_completion_ledger import AXIOM_CLOSURE
from src.core.padic_completion_formal import THEOREM_IDS

from padic_completion_fixture import exact_padic_package

pytestmark = pytest.mark.requires_lean


def test_positive_ppcp_reports_exact_scoped_status_matrix():
    package = exact_padic_package()
    result = padic_completion_judgment(package)
    assert type(result) is PadicCompletionJudgment
    assert result.completed_carrier is PadicCompletedCarrierStatus.ESTABLISHED_RELATIVE_TO_LEDGER
    assert all(value is PadicObligationStatus.ESTABLISHED for value in result.obligations.__dict__.values())
    assert result.theorem_axiom_closure == AXIOM_CLOSURE
    assert result.canonical_ops_id == CANONICAL_OPS_ID
    assert result.concrete_instance_id == CONCRETE_INSTANCE_ID
    assert result.categorical_inverse_limit_universal_property is PadicNotEstablishedStatus.NOT_ESTABLISHED
    assert result.equivalent_to_mathlib_padic_int is PadicNotEstablishedStatus.NOT_ESTABLISHED
    assert result.topological_completion is PadicNotEstablishedStatus.NOT_ESTABLISHED
    assert result.physical_instantiation is PadicNotEstablishedStatus.NOT_ESTABLISHED
    assert result.foundation_independent_actuality is PadicNotClaimedStatus.NOT_CLAIMED
    assert result.nonclaims == POMEGA2_NONCLAIMS


def test_result_revalidation_is_fresh_and_rejects_mutation():
    package = exact_padic_package()
    result = padic_completion_judgment(package)
    replay = validate_padic_completion_result(package, result)
    assert replay is not result and replay == result
    with pytest.raises(PadicCompletionValidationError):
        validate_padic_completion_result(package, replace(result, run_digest="0" * 64))


def test_resource_refusal_precedes_formal_execution():
    result = padic_completion_judgment(exact_padic_package(max_captured_bytes=1))
    assert type(result) is PadicCompletionResourceLimit
    assert result.failed_bound.value == "captured-bytes"
    assert not hasattr(result, "completed_carrier")


def test_output_limit_is_typed_provenance_only_and_revalidates():
    package = exact_padic_package(max_output_bytes=1)
    result = padic_completion_judgment(package)
    assert type(result) is PadicFormalExecutionFailure
    assert result.kind.value == "output-limit"
    assert result.diagnostic == "formal execution output-limit"
    assert not hasattr(result, "completed_carrier")
    replay = validate_padic_completion_result(package, result)
    assert replay == result and replay is not result


@pytest.mark.parametrize("p", [2, 3, 5])
def test_bounded_shadows_are_arithmetic_qa_only(p):
    row = bounded_padic_shadow(p, 8)
    assert row.zero == (0,) * 8 and row.one == (1,) * 8
    assert row.minus_one == tuple(p ** (n + 1) - 1 for n in range(8))
    assert row.add_inverse_checks == (True,) * 8
    assert row.restriction_checks == 140 and row.strict_refinement_witnesses == 28
    assert row.incompatible_first_failure == (0, 1)
    assert row.scope == "bounded-arithmetic-pressure-not-family-or-completion-evidence"


@pytest.mark.parametrize("value", [True, False, -3, 0, 1, 4, 9, 65_537, 65_522])
def test_prime_source_rejects_boolean_nonpositive_composite_or_out_of_range(value):
    with pytest.raises(PadicCompletionValidationError):
        prime_source(value)


def test_package_cannot_carry_concrete_family_or_family_adapter():
    package = exact_padic_package()
    assert tuple(package.__dict__) == (
        "prime", "doctrine", "theorem_source", "ledger", "policy", "package_digest",
    )
    for name in ("family", "residues", "generator", "oracle", "callback", "adapter"):
        assert not hasattr(package, name)


def test_ledger_exposes_constructed_ring_witness_and_exact_call_dependencies():
    package = exact_padic_package()
    rows = {row.row_id: row for row in package.ledger.rows}
    assert rows["stage-ring-laws"].use == "ring-law witness interface"
    assert rows[CANONICAL_OPS_ID].use == "constructed canonical stage ring witness"
    assert rows[CONCRETE_INSTANCE_ID].use == "p-specific canonical THM017 application"
    assert rows[THEOREM_IDS[4]].direct_dependencies == (THEOREM_IDS[1], "canonical-reduction")
    assert THEOREM_IDS[8] in rows[THEOREM_IDS[13]].direct_dependencies
    assert THEOREM_IDS[8] in rows[THEOREM_IDS[15]].direct_dependencies
    assert rows["proof-irrelevance"].row_class.value == "foundation"
    assert "proof-irrelevance" in rows[THEOREM_IDS[8]].direct_dependencies
    assert rows[THEOREM_IDS[-1]].direct_dependencies == (
        *THEOREM_IDS[:16], CANONICAL_OPS_ID, "runtime-compiler-boundary",
        "lean-Std.Tactic", "lean-Init.GrindInstances.Ring.Fin",
    )
    assert rows[THEOREM_IDS[-1]].axiom_closure == AXIOM_CLOSURE
    assert rows["integers"].row_class.value == "not-used"
    assert rows["topological-completeness"].row_class.value == "not-used"


def test_direct_level_one_certificate_passes_exact_detail():
    row = certify_padic_completion_pomega2()
    assert row.passed is True and row.level == 1 and row.name == "padic_completion_pomega2"
    assert row.detail == (
        "theorems=17 obligations=17 positive=1 resource=1 shadows=3 "
        "canonical_ops=1 concrete_instance=1 categorical=0 topology=0 physical=0 adapter=0"
    )
