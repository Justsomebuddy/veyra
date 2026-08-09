"""Positive, O(1)-symbolic, resource, and nonpromotion tests for P1-D2."""

import inspect
import tracemalloc

import src.core as core_api
from src.core.productivity_counterpressure import (
    DEFAULT_POLICY, check_basis_source, counterpressure_alphabet,
    counterpressure_basis_source, counterpressure_policy, counterpressure_result,
    decreasing_tree_request, ledger_request, long_run_request,
    shrinking_stage_request, target_chooser_request, validate_counterpressure_result,
)
from src.core.productivity_counterpressure_types import (
    AllDepthFamilyStatus, BasisUse, ChooserTargetIndependence,
    CompletedCarrierStatus, CounterpressureCertificate, CounterpressureOutcomeKind,
    CounterpressureResourceBound, CounterpressureResourceLimit, CounterpressureStatus,
    DescentCountermodelEvidence, FiniteRunInsufficiencyEvidence,
    GeneratorNonexistence, HistoricalTargetIndependence,
    LedgerInsufficiencyEvidence, LedgerRow, ShrinkingTailCountermodelEvidence,
    TargetDependenceEvidence,
)
import pytest

pytestmark = pytest.mark.requires_lean


def _ledger():
    return ledger_request((LedgerRow(2, "w2", "s2"), LedgerRow(5, "w5", "s5")))


def test_two_selector_ledger_is_insufficiency_not_countermodel():
    result = counterpressure_result(_ledger())
    assert isinstance(result, CounterpressureCertificate)
    assert result.outcome_kind is CounterpressureOutcomeKind.EVIDENCE_INSUFFICIENCY
    assert result.status is CounterpressureStatus.INSUFFICIENT_TO_ESTABLISH
    assert isinstance(result.evidence, LedgerInsufficiencyEvidence)
    assert result.evidence.depths == (2, 5)
    assert result.evidence.selector_count == 2
    assert result.evidence.common_source_supplied is False
    assert result.basis_use is BasisUse.NONE and result.basis_digest is None


def test_descent_samples_zero_and_five_are_symbolic_and_lean_bound():
    basis = counterpressure_basis_source()
    zero = counterpressure_result(decreasing_tree_request(0, basis))
    five = counterpressure_result(decreasing_tree_request(5, basis))
    assert isinstance(zero, CounterpressureCertificate)
    assert isinstance(five, CounterpressureCertificate)
    assert isinstance(zero.evidence, DescentCountermodelEvidence)
    assert isinstance(five.evidence, DescentCountermodelEvidence)
    assert (zero.evidence.witness_length, zero.evidence.first_or_none, zero.evidence.last_or_none) == (
        0, None, None,
    )
    assert (five.evidence.witness_length, five.evidence.first_or_none, five.evidence.last_or_none) == (
        5, 4, 0,
    )
    assert five.basis_use is BasisUse.BOUND
    assert five.basis_digest == basis.basis_digest == five.evidence.basis_digest
    assert five.outcome_kind is CounterpressureOutcomeKind.MATHEMATICAL_COUNTERMODEL


def test_target_copy_matches_exactly_because_it_reads_target():
    alphabet = counterpressure_alphabet(("a", "b"))
    result = counterpressure_result(target_chooser_request(alphabet, ("a", "b", "a")))
    assert isinstance(result, CounterpressureCertificate)
    assert isinstance(result.evidence, TargetDependenceEvidence)
    evidence = result.evidence
    assert evidence.target_digest == evidence.output_digest
    assert evidence.exact_match is evidence.target_read is True
    assert evidence.chooser_target_independence is ChooserTargetIndependence.REFUTED
    assert result.outcome_kind is CounterpressureOutcomeKind.MATHEMATICAL_COUNTERMODEL
    assert result.basis_use is BasisUse.NONE


def test_million_step_long_run_is_constant_size_insufficiency():
    counterpressure_result(long_run_request(1))
    tracemalloc.start()
    result = counterpressure_result(long_run_request(1_000_000))
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert isinstance(result, CounterpressureCertificate)
    assert isinstance(result.evidence, FiniteRunInsufficiencyEvidence)
    assert result.evidence == FiniteRunInsufficiencyEvidence(
        0, 1_000_000, 1_000_001, False,
        CounterpressureStatus.INSUFFICIENT_TO_ESTABLISH,
    )
    assert peak < 1_000_000
    assert not hasattr(result.evidence, "stages")


def test_shrinking_tail_binds_witness_nesting_and_diagonal_exclusion():
    result = counterpressure_result(
        shrinking_stage_request(7, counterpressure_basis_source())
    )
    assert isinstance(result, CounterpressureCertificate)
    assert isinstance(result.evidence, ShrinkingTailCountermodelEvidence)
    evidence = result.evidence
    assert (
        evidence.local_witness, evidence.nested_from, evidence.nested_into,
        evidence.diagonal_candidate, evidence.excluding_stage,
    ) == (7, 8, 7, 7, 8)
    assert result.basis_use is BasisUse.BOUND


def test_deterministic_commitments_and_fresh_nested_identities():
    request = _ledger()
    first = counterpressure_result(request)
    second = counterpressure_result(request)
    assert isinstance(first, CounterpressureCertificate)
    assert isinstance(second, CounterpressureCertificate)
    assert first == second and first is not second
    assert first.evidence is not second.evidence
    assert isinstance(first.evidence, LedgerInsufficiencyEvidence)
    assert isinstance(second.evidence, LedgerInsufficiencyEvidence)
    assert first.evidence.depths is not second.evidence.depths
    fresh = validate_counterpressure_result(first, request, DEFAULT_POLICY)
    assert fresh == first and fresh is not first
    assert isinstance(fresh, CounterpressureCertificate)
    assert fresh.evidence is not first.evidence


def test_default_request_byte_refusal_is_reachable_and_has_no_evidence():
    symbols = tuple(f"{index:02d}" + "x" * 62 for index in range(16))
    alphabet = counterpressure_alphabet(symbols)
    request = target_chooser_request(alphabet, tuple(symbols[index % 16] for index in range(256)))
    refusal = counterpressure_result(request)
    assert isinstance(refusal, CounterpressureResourceLimit)
    assert refusal.failed_bound is CounterpressureResourceBound.REQUEST_BYTES
    assert refusal.required_value > refusal.allowed_value == 4096
    assert not hasattr(refusal, "evidence") and not hasattr(refusal, "status")
    fresh = validate_counterpressure_result(refusal, request, DEFAULT_POLICY)
    assert fresh == refusal and fresh is not refusal


def test_symbolic_cost_refusal_follows_request_byte_priority():
    request = _ledger()
    broad_bytes = counterpressure_policy(4096, 1)
    refusal = counterpressure_result(request, broad_bytes)
    assert isinstance(refusal, CounterpressureResourceLimit)
    assert refusal.failed_bound is CounterpressureResourceBound.SYMBOLIC_COST


def test_allowed_mathematical_evidence_is_policy_independent():
    request = _ledger()
    first = counterpressure_result(request, DEFAULT_POLICY)
    second_policy = counterpressure_policy(8192, 8192)
    second = counterpressure_result(request, second_policy)
    assert isinstance(first, CounterpressureCertificate)
    assert isinstance(second, CounterpressureCertificate)
    assert first.evidence == second.evidence
    assert first.evidence_digest == second.evidence_digest
    assert first.policy_digest != second.policy_digest
    assert first.certificate_digest != second.certificate_digest


def test_basis_captured_compile_and_fresh_identity():
    basis = counterpressure_basis_source()
    checked = check_basis_source(basis)
    assert checked == basis and checked is not basis
    assert checked.theorem_ids is not basis.theorem_ids


def test_root_api_uses_noncolliding_d2_nominal_status_aliases():
    from src.core import observer_genesis_types as e1_types
    from src.core import productivity_counterpressure_types as d2_types
    from src.core import productivity_types as d1_types

    result = counterpressure_result(_ledger())
    assert core_api.CompletedCarrierStatus is d1_types.CompletedCarrierStatus
    assert core_api.HistoricalTargetIndependence is e1_types.HistoricalTargetIndependence
    assert core_api.CounterpressureCompletedCarrierStatus is d2_types.CompletedCarrierStatus
    assert (
        core_api.CounterpressureHistoricalTargetIndependence
        is d2_types.HistoricalTargetIndependence
    )
    assert type(result.completed_carrier) is core_api.CounterpressureCompletedCarrierStatus
    assert (
        type(result.historical_target_independence)
        is core_api.CounterpressureHistoricalTargetIndependence
    )


def test_all_results_keep_permanent_nonclaims():
    certificate = counterpressure_result(_ledger())
    refusal = counterpressure_result(_ledger(), counterpressure_policy(1, 1))
    for result in (certificate, refusal):
        assert result.generator_nonexistence is GeneratorNonexistence.NOT_PROVED
        assert result.all_depth_family is AllDepthFamilyStatus.OPEN
        assert result.completed_carrier is CompletedCarrierStatus.NOT_ESTABLISHED
        assert (
            result.historical_target_independence
            is HistoricalTargetIndependence.NOT_ESTABLISHED
        )
        assert result.scope == "counterpressure-only"


def test_public_api_threads_exact_policy():
    assert set(inspect.signature(counterpressure_result).parameters) == {"request", "policy"}
    assert set(inspect.signature(validate_counterpressure_result).parameters) == {
        "value", "request", "policy",
    }
