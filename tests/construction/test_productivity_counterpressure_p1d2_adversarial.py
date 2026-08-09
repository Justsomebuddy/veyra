"""Hostile exactness, source, resource, and revalidation pressure for P1-D2."""

from dataclasses import replace
from pathlib import Path

import pytest

import src.core.productivity_counterpressure_basis as basis_module
import src.core.productivity_counterpressure_runtime as runtime
from src.core.productivity_counterpressure import (
    ARTIFACT_NAME, check_basis_source, counterpressure_alphabet,
    counterpressure_basis_source, counterpressure_policy, counterpressure_result,
    CounterpressureValidationError,
    decreasing_tree_request, ledger_request, long_run_request,
    shrinking_stage_request, target_chooser_request, validate_counterpressure_result,
)
from src.core.productivity_counterpressure_common import MAX_NATURAL
from src.core.productivity_counterpressure_digest import (
    alphabet_digest, symbol_tuple_digest,
)
from src.core.productivity_counterpressure_types import (
    CounterpressureCertificate, CounterpressurePolicy, CounterpressureRequestKind,
    CounterpressureResourceLimit,
    CounterpressureStatus, DecreasingTreeRequest, LedgerInsufficiencyEvidence,
    LedgerRow, LongRunRequest, NonuniformLedgerRequest, ShrinkingStageRequest,
)
from src.core.productivity_counterpressure_validation import DEFAULT_POLICY, REQUEST_VERSION

pytestmark = pytest.mark.requires_lean


def _ledger():
    return ledger_request((LedgerRow(1, "w1", "s1"), LedgerRow(2, "w2", "s2")))


class LedgerSubclass(NonuniformLedgerRequest):
    pass


class DuckRequest:
    version = REQUEST_VERSION
    rows = ()


class TupleSubclass(tuple):
    pass


class Trap:
    def __len__(self):
        raise AssertionError("nested-evidence-touched-too-early")

    def __iter__(self):
        raise AssertionError("nested-evidence-touched-too-early")


def test_subclass_duck_callable_mapping_and_injected_shape_reject():
    request = _ledger()
    subclass = LedgerSubclass(request.version, request.rows)
    for alien in (subclass, DuckRequest(), lambda: request, {"rows": request.rows}):
        with pytest.raises(CounterpressureValidationError, match="request|exact"):
            counterpressure_result(alien)  # type: ignore[arg-type]
    injected = _ledger()
    object.__setattr__(injected, "oracle", lambda: True)
    with pytest.raises(CounterpressureValidationError, match="shape-drift"):
        counterpressure_result(injected)


@pytest.mark.parametrize("value", [0, True, -1, MAX_NATURAL + 1, 1.5, "5"])
def test_boolean_negative_hard_overflow_and_noninteger_naturals_reject(value):
    with pytest.raises(CounterpressureValidationError):
        long_run_request(value)  # type: ignore[arg-type]


def test_one_row_duplicate_out_of_order_and_repeated_selector_ledgers_reject():
    invalid = (
        (LedgerRow(1, "w", "s"),),
        (LedgerRow(1, "w1", "s1"), LedgerRow(1, "w2", "s2")),
        (LedgerRow(2, "w2", "s2"), LedgerRow(1, "w1", "s1")),
        (LedgerRow(1, "w1", "same"), LedgerRow(2, "w2", "same")),
    )
    for rows in invalid:
        with pytest.raises(CounterpressureValidationError):
            ledger_request(rows)
    with pytest.raises(CounterpressureValidationError):
        ledger_request([LedgerRow(1, "w1", "s1"), LedgerRow(2, "w2", "s2")])  # type: ignore[arg-type]


def test_alphabet_and_target_exactness_boundaries():
    for symbols in (
        (), ("a", "a"), ("",), ("x" * 65,), ("\ud800",), tuple(str(i) for i in range(17)),
    ):
        with pytest.raises(CounterpressureValidationError):
            counterpressure_alphabet(symbols)
    alphabet = counterpressure_alphabet(("a", "b"))
    for target in ((), ("c",), ("a",) * 257, ["a"]):
        with pytest.raises(CounterpressureValidationError):
            target_chooser_request(alphabet, target)  # type: ignore[arg-type]


def test_request_and_nested_digest_mutation_reject():
    alphabet = counterpressure_alphabet(("a", "b"))
    object.__setattr__(alphabet, "alphabet_digest", "0" * 64)
    with pytest.raises(CounterpressureValidationError, match="alphabet-drift"):
        target_chooser_request(alphabet, ("a",))
    basis = counterpressure_basis_source()
    object.__setattr__(basis, "basis_digest", "0" * 64)
    with pytest.raises(CounterpressureValidationError, match="basis-source-drift"):
        decreasing_tree_request(2, basis)


def test_cross_kind_evidence_transplant_and_mutation_fail():
    ledger_request_value = _ledger()
    ledger = counterpressure_result(ledger_request_value)
    run_request = long_run_request(4)
    run = counterpressure_result(run_request)
    assert isinstance(ledger, CounterpressureCertificate)
    assert isinstance(run, CounterpressureCertificate)
    forged = replace(ledger, evidence=run.evidence)
    with pytest.raises(CounterpressureValidationError, match="evidence"):
        validate_counterpressure_result(forged, ledger_request_value, DEFAULT_POLICY)
    assert isinstance(ledger.evidence, LedgerInsufficiencyEvidence)
    object.__setattr__(ledger.evidence, "selector_count", 99)
    with pytest.raises(CounterpressureValidationError):
        validate_counterpressure_result(ledger, ledger_request_value, DEFAULT_POLICY)


def test_raw_string_enum_bool_int_and_tuple_subclass_fail():
    request = _ledger()
    result = counterpressure_result(request)
    assert isinstance(result, CounterpressureCertificate)
    with pytest.raises(CounterpressureValidationError, match="status-drift"):
        validate_counterpressure_result(
            replace(result, status=result.status.value), request, DEFAULT_POLICY  # type: ignore[arg-type]
        )
    assert isinstance(result.evidence, LedgerInsufficiencyEvidence)
    forged_bool = replace(result.evidence, common_source_supplied=0)  # type: ignore[arg-type]
    with pytest.raises(CounterpressureValidationError):
        validate_counterpressure_result(replace(result, evidence=forged_bool), request, DEFAULT_POLICY)
    forged_tuple = replace(result.evidence, depths=TupleSubclass(result.evidence.depths))
    with pytest.raises(CounterpressureValidationError, match="depths-shape"):
        validate_counterpressure_result(replace(result, evidence=forged_tuple), request, DEFAULT_POLICY)


def test_forged_positive_fields_periodic_fit_and_target_read_removal_fail():
    request = ledger_request((LedgerRow(2, "ab", "even"), LedgerRow(4, "abab", "even2")))
    result = counterpressure_result(request)
    assert isinstance(result, CounterpressureCertificate)
    assert result.status is CounterpressureStatus.INSUFFICIENT_TO_ESTABLISH
    object.__setattr__(result, "all_depth_family", "established")
    with pytest.raises(CounterpressureValidationError, match="all-depth"):
        validate_counterpressure_result(result, request, DEFAULT_POLICY)
    chooser_request = target_chooser_request(counterpressure_alphabet(("a",)), ("a",))
    chooser = counterpressure_result(chooser_request)
    assert isinstance(chooser, CounterpressureCertificate)
    object.__setattr__(chooser.evidence, "target_read", False)
    with pytest.raises(CounterpressureValidationError, match="target-read"):
        validate_counterpressure_result(chooser, chooser_request, DEFAULT_POLICY)


def test_finite_branching_bounded_sample_theorem_tcb_and_toolchain_drift_reject():
    basis = counterpressure_basis_source()
    rows = (
        replace(basis, foundation_id="finite-branching-koenig"),
        replace(basis, theorem_ids=("bounded-sample-only",)),
        replace(basis, tcb_digest="0" * 64),
        replace(basis, toolchain_id="leanprover/lean4:latest"),
    )
    for alien in rows:
        with pytest.raises(CounterpressureValidationError, match="basis-source-drift"):
            decreasing_tree_request(3, alien)


def test_comment_only_artifact_drift_fails_before_compile(monkeypatch):
    basis_module._compile_captured.cache_clear()
    original = Path.read_bytes

    def changed(path):
        payload = original(path)
        return payload + b"\n-- comment drift\n" if str(path) == ARTIFACT_NAME else payload

    monkeypatch.setattr(Path, "read_bytes", changed)
    with pytest.raises(CounterpressureValidationError, match="artifact-drift"):
        check_basis_source(counterpressure_basis_source())


def test_reused_common_point_and_digest_framing_pressure():
    request = shrinking_stage_request(7, counterpressure_basis_source())
    result = counterpressure_result(request)
    assert isinstance(result, CounterpressureCertificate)
    object.__setattr__(result.evidence, "local_witness", 100)
    with pytest.raises(CounterpressureValidationError):
        validate_counterpressure_result(result, request, DEFAULT_POLICY)
    assert alphabet_digest("p1-d2-alphabet-v1", ("ab", "c")) != alphabet_digest(
        "p1-d2-alphabet-v1", ("a", "bc")
    )
    assert symbol_tuple_digest("chooser-sequence", ("a", "b")) != symbol_tuple_digest(
        "symbolic-formula", ("a", "b")
    )


def test_refusal_rejects_partial_evidence_and_policy_is_not_reconstructed():
    request = _ledger()
    policy = counterpressure_policy(1, 1)
    refusal = counterpressure_result(request, policy)
    assert isinstance(refusal, CounterpressureResourceLimit)
    object.__setattr__(refusal, "evidence", "partial")
    with pytest.raises(CounterpressureValidationError, match="shape-drift"):
        validate_counterpressure_result(refusal, request, policy)
    forged_policy = replace(policy, policy_digest=DEFAULT_POLICY.policy_digest)
    with pytest.raises(CounterpressureValidationError, match="policy-drift"):
        validate_counterpressure_result(
            counterpressure_result(request, policy), request, forged_policy
        )


def test_huge_nested_evidence_is_not_touched_before_outer_precheck():
    request = _ledger()
    result = counterpressure_result(request)
    assert isinstance(result, CounterpressureCertificate)
    assert isinstance(result.evidence, LedgerInsufficiencyEvidence)
    object.__setattr__(result.evidence, "depths", Trap())
    object.__setattr__(result, "request_kind", CounterpressureRequestKind.LONG_RUN)
    with pytest.raises(CounterpressureValidationError, match="request-kind"):
        validate_counterpressure_result(result, request, DEFAULT_POLICY)


def test_unexpected_internal_exception_propagates(monkeypatch):
    def explode(_request):
        raise RuntimeError("unexpected-internal")

    monkeypatch.setattr(runtime, "replay_counterpressure", explode)
    with pytest.raises(RuntimeError, match="unexpected-internal"):
        counterpressure_result(_ledger())


def test_wrong_request_variants_are_never_coerced():
    basis = counterpressure_basis_source()
    for raw in (
        DecreasingTreeRequest(REQUEST_VERSION, True, basis),
        LongRunRequest(REQUEST_VERSION, -1),
        ShrinkingStageRequest(REQUEST_VERSION, MAX_NATURAL + 1, basis),
    ):
        with pytest.raises(CounterpressureValidationError):
            counterpressure_result(raw)


def test_policy_bool_overflow_subclass_and_alphabet_digest_cross_domain():
    for raw in ((True, 1), (1, True), (0, 1), (65_537, 1), (1, 100_001)):
        with pytest.raises(CounterpressureValidationError):
            counterpressure_policy(*raw)  # type: ignore[arg-type]
    policy = DEFAULT_POLICY

    class PolicySubclass(CounterpressurePolicy):
        pass

    subclass = PolicySubclass(
        policy.version, policy.max_request_bytes, policy.max_symbolic_cost, policy.policy_digest
    )
    with pytest.raises(CounterpressureValidationError, match="policy-must-be-exact"):
        counterpressure_result(_ledger(), subclass)
    assert alphabet_digest("p1-d2-alphabet-v1", ("a",)) != symbol_tuple_digest(
        "alphabet", ("a",)
    )
