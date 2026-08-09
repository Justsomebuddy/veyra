"""Hostile exact-type, ledger, execution, continuity, and result pressure."""

from dataclasses import replace
from pathlib import Path

import pytest

from src.core.all_depth_family_types import AllDepthFamilyJudgment
from src.core.stream_completion import (
    StreamCompletionValidationError, stream_completion_judgment,
    validate_stream_completion_result,
)
from src.core.stream_completion_formal import CompileOutcome
from src.core.stream_completion_types import (
    CompletionFailedBound, FormalExecutionFailure, FormalExecutionFailureKind, LedgerRowClass,
    StreamCompletionJudgment, StreamCompletionResourceLimit,
)
from stream_completion_fixture import exact_package

pytestmark = pytest.mark.requires_lean


def test_toolchain_tcb_ledger_dag_and_axiom_closure_drift_reject():
    package = exact_package()
    theorem = package.theorem_source
    ledger = package.ledger
    row = ledger.rows[4]
    cases = (
        replace(package, theorem_source=replace(theorem, toolchain_id="leanprover/lean4:latest")),
        replace(package, theorem_source=replace(theorem, tcb_digest="0" * 64)),
        replace(package, ledger=replace(ledger, theorem_axiom_closure=())),
        replace(package, ledger=replace(ledger, rows=ledger.rows[:4] + (
            replace(row, direct_dependencies=(row.row_id,)),
        ) + ledger.rows[5:])),
        replace(package, ledger=replace(ledger, rows=ledger.rows[:3] + (
            replace(ledger.rows[3], row_class=LedgerRowClass.NOT_USED),
        ) + ledger.rows[4:])),
    )
    for value in cases:
        with pytest.raises(StreamCompletionValidationError):
            stream_completion_judgment(value)


def test_finite_family_generator_prior_judgment_and_callable_are_not_packages():
    alien = object.__new__(AllDepthFamilyJudgment)
    for value in (("a",), lambda n: n, alien, stream_completion_judgment(exact_package())):
        with pytest.raises(StreamCompletionValidationError):
            stream_completion_judgment(value)  # type: ignore[arg-type]


@pytest.mark.parametrize("kind", [
    FormalExecutionFailureKind.TIMEOUT,
    FormalExecutionFailureKind.OUTPUT_LIMIT,
    FormalExecutionFailureKind.COMPILE_ERROR,
])
def test_typed_operational_failures_have_no_proof_payload(monkeypatch, kind):
    package = exact_package()
    monkeypatch.setattr(
        "src.core.stream_completion_runtime.compile_captured_sources",
        lambda *args: CompileOutcome(kind, b"hostile /private/path secret", (-1,)),
    )
    result = stream_completion_judgment(package)
    assert type(result) is FormalExecutionFailure and result.kind is kind
    assert "/private" not in result.diagnostic
    assert not hasattr(result, "obligations") and not hasattr(result, "completed_carrier")
    assert validate_stream_completion_result(package, result) == result


def test_post_compile_source_swap_is_typed_continuity_drift(monkeypatch):
    package = exact_package()
    path = Path(package.theorem_source.artifact_path_id)
    original = path.read_bytes()
    calls = 0

    def swapping_read(self):
        nonlocal calls
        if self == path:
            calls += 1
            return original if calls == 1 else original + b"\n-- swapped\n"
        return Path.open(self, "rb").read(2 * 1024 * 1024 + 1)

    monkeypatch.setattr("src.core.stream_completion_formal._read_bounded_source", swapping_read)
    result = stream_completion_judgment(package)
    assert type(result) is FormalExecutionFailure
    assert result.kind is FormalExecutionFailureKind.CONTINUITY_DRIFT


def test_unexpected_internal_exception_propagates(monkeypatch):
    package = exact_package()
    monkeypatch.setattr(
        "src.core.stream_completion_runtime.compile_captured_sources",
        lambda *args: (_ for _ in ()).throw(RuntimeError("unexpected-sentinel")),
    )
    with pytest.raises(RuntimeError, match="unexpected-sentinel"):
        stream_completion_judgment(package)


def test_hollow_extra_field_subclass_and_huge_outer_results_fail_fast():
    package = exact_package()
    positive = stream_completion_judgment(package)
    hollow = object.__new__(StreamCompletionJudgment)
    object.__setattr__(positive, "partial_proof", "forbidden")
    huge = replace(positive, theorem_ids=("x",) * 100_000)

    class Forged(StreamCompletionJudgment):
        pass

    forged = Forged(**{name: getattr(positive, name) for name in positive.__dataclass_fields__})
    for value in (hollow, positive, huge, forged):
        with pytest.raises(StreamCompletionValidationError):
            validate_stream_completion_result(package, value)


def test_refusal_with_partial_positive_payload_is_rejected_before_replay():
    base = exact_package()
    required = (
        len(Path(base.theorem_source.artifact_path_id).read_bytes())
        + len(base.alphabet_presentation.generated_instance_bytes)
    )
    package = exact_package(max_captured_bytes=required - 1)
    refusal = stream_completion_judgment(package)
    assert type(refusal) is StreamCompletionResourceLimit
    object.__setattr__(refusal, "obligations", ("forged",) * 11)
    with pytest.raises(StreamCompletionValidationError, match="field-shape"):
        validate_stream_completion_result(package, refusal)


def test_scalar_subclasses_and_boolean_policy_are_rejected():
    package = exact_package()

    class EvilText(str):
        def __eq__(self, other):
            raise AssertionError("hostile equality ran")

    bad_doctrine = replace(package.doctrine, doctrine_id=EvilText(package.doctrine.doctrine_id))
    with pytest.raises(StreamCompletionValidationError, match="scalar-type"):
        stream_completion_judgment(replace(package, doctrine=bad_doctrine))
    from src.core.stream_completion import stream_completion_policy
    with pytest.raises(StreamCompletionValidationError):
        stream_completion_policy(compile_timeout_seconds=True)


def test_template_and_policy_digest_transplants_reject_before_compile(monkeypatch):
    package = exact_package()
    foreign = exact_package(max_output_bytes=2048)
    monkeypatch.setattr(
        "src.core.stream_completion_alphabet.inspect.getsource", lambda function: "drift",
    )
    with pytest.raises(StreamCompletionValidationError, match="template-drift"):
        stream_completion_judgment(package)
    monkeypatch.undo()
    transplanted = replace(package, policy=foreign.policy)
    with pytest.raises(StreamCompletionValidationError):
        stream_completion_judgment(transplanted)


def test_static_cost_refusal_is_reachable_after_captured_bytes_pass():
    from src.core.stream_completion import stream_completion_package, stream_completion_policy
    from src.core.stream_completion_formal import capture_generic_source
    from src.core.stream_completion_preflight import preflight_charge

    base = exact_package()
    generic = capture_generic_source(base.theorem_source)
    charge = preflight_charge(base, generic)
    policy = stream_completion_policy(max_static_cost=charge.static_cost - 1)
    package = stream_completion_package(
        base.doctrine, base.alphabet, base.theorem_source, base.ledger, policy,
    )
    result = stream_completion_judgment(package)
    assert type(result) is StreamCompletionResourceLimit
    assert result.failed_bound.value == "static-cost"


def test_generator_helper_drift_rejects_before_generator_runs(monkeypatch):
    from src.core import stream_completion_alphabet as module

    package = exact_package()
    calls = []
    original = module._lean_literal

    def drift(value):
        calls.append(value)
        return original(value)

    monkeypatch.setattr(module, "_lean_literal", drift)
    with pytest.raises(StreamCompletionValidationError, match="template-drift"):
        stream_completion_judgment(package)
    assert calls == []


def test_presentation_lengths_and_hard_bytes_reject_before_hash_or_member_hooks(monkeypatch):
    from src.core.stream_completion_alphabet import snapshot_presentation

    package = exact_package()

    class Evil:
        def __getattribute__(self, name):
            raise AssertionError("member hook traversed")

    bad_length = replace(package.alphabet_presentation, index_to_symbol=(Evil(),))
    with pytest.raises(StreamCompletionValidationError, match="forward-table-length"):
        snapshot_presentation(bad_length, package.alphabet, package.theorem_source.source_digest)
    huge = replace(package.alphabet_presentation, generated_instance_bytes=b"x" * (2 * 1024 * 1024 + 1))
    monkeypatch.setattr(
        "src.core.stream_completion_alphabet.sha",
        lambda payload: (_ for _ in ()).throw(AssertionError("hash ran before hard cap")),
    )
    with pytest.raises(StreamCompletionValidationError, match="hard-size"):
        snapshot_presentation(huge, package.alphabet, package.theorem_source.source_digest)


def test_refusal_bound_specific_maxima_order_and_diagnostic_utf8_reject():
    base = exact_package()
    required = len(Path(base.theorem_source.artifact_path_id).read_bytes()) + len(
        base.alphabet_presentation.generated_instance_bytes
    )
    refusal_package = exact_package(max_captured_bytes=required - 1)
    refusal = stream_completion_judgment(refusal_package)
    assert type(refusal) is StreamCompletionResourceLimit
    bad_refusals = (
        replace(refusal, required_value=refusal.allowed_value),
        replace(refusal, required_value=2 * 1024 * 1024 + 1),
        replace(refusal, failed_bound=CompletionFailedBound.STATIC_COST, required_value=9 * 1024 * 1024),
    )
    for value in bad_refusals:
        with pytest.raises(StreamCompletionValidationError, match="bound"):
            validate_stream_completion_result(refusal_package, value)
    positive = stream_completion_judgment(base)
    assert type(positive) is StreamCompletionJudgment
    failure = FormalExecutionFailure(
        FormalExecutionFailureKind.COMPILE_ERROR, base.package_digest,
        base.policy.policy_digest, "0" * 64, "1" * 64, "bad\ud800",
        positive.physical_instantiation,
        positive.observer_independent_metaphysical_totality,
        positive.nonclaims,
    )
    with pytest.raises(StreamCompletionValidationError, match="invalid-utf8"):
        validate_stream_completion_result(base, failure)


def test_attempt_digest_binds_exact_phase_provenance():
    from src.core.stream_completion_formal_process import FormalPhaseReceipt
    from src.core.stream_completion_runtime import _execution_failure

    package = exact_package()
    first = FormalPhaseReceipt(
        "elan-which", 0, 4, "2" * 64, None,
    )
    second = replace(first, phase="lean-version")
    left = _execution_failure(
        package, "0" * 64, FormalExecutionFailureKind.COMPILE_ERROR,
        b"same", (0,), (first,),
    )
    right = _execution_failure(
        package, "0" * 64, FormalExecutionFailureKind.COMPILE_ERROR,
        b"same", (0,), (second,),
    )
    assert left.attempt_digest != right.attempt_digest
