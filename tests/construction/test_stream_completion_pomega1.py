"""Positive surface, exact mathematics, resource order, and bounded shadows."""

from dataclasses import replace
from pathlib import Path

import pytest

from src.core.stream_completion import (
    AXIOM_CLOSURE, THEOREM_IDS, StreamCompletionValidationError,
    bounded_stream_shadow, stream_alphabet_source, stream_completion_judgment,
    stream_completion_package, stream_completion_policy,
    validate_stream_completion_result,
)
from src.core.stream_completion_formal import capture_generic_source
from src.core.stream_completion_types import (
    CompletedCarrierStatus, CompletionFailedBound, ObligationStatus,
    POMEGA1_NONCLAIMS, StreamCompletionJudgment, StreamCompletionResourceLimit,
)
from stream_completion_fixture import exact_package

pytestmark = pytest.mark.requires_lean


def test_positive_exact_15_theorems_11_obligations_and_relative_status():
    package = exact_package()
    result = stream_completion_judgment(package)
    assert type(result) is StreamCompletionJudgment
    assert result.theorem_ids == THEOREM_IDS and len(result.theorem_ids) == 15
    assert result.theorem_axiom_closure == AXIOM_CLOSURE == ("Quot.sound",)
    assert len(result.obligations.__dict__) == 11
    assert set(result.obligations.__dict__.values()) == {ObligationStatus.ESTABLISHED}
    assert result.completed_carrier is CompletedCarrierStatus.ESTABLISHED_RELATIVE_TO_LEDGER
    assert result.nonclaims == POMEGA1_NONCLAIMS
    assert validate_stream_completion_result(package, result) == result


def test_utf8_order_inverse_inhabitant_and_generated_roundtrips_are_bound():
    package = exact_package(("\n", "한", "𐍈", "\\\""))
    presentation = package.alphabet_presentation
    assert presentation.index_to_symbol == ("\n", "한", "𐍈", "\\\"")
    assert presentation.symbol_to_index == (("\n", 0), ("한", 1), ("𐍈", 2), ("\\\"", 3))
    assert presentation.inhabitant_index == 0 and presentation.inhabitant_symbol == "\n"
    assert stream_completion_judgment(package).completed_carrier is CompletedCarrierStatus.ESTABLISHED_RELATIVE_TO_LEDGER


@pytest.mark.parametrize("symbols", [(), ("",), ("a", "a"), tuple(str(i) for i in range(17))])
def test_invalid_or_vacuous_alphabets_reject(symbols):
    with pytest.raises(StreamCompletionValidationError):
        stream_alphabet_source(symbols)


def test_boolean_surrogate_mutable_and_subclass_alphabets_reject():
    class Text(str):
        pass

    for symbols in (["a"], (Text("a"),), (True,)):
        with pytest.raises(StreamCompletionValidationError):
            stream_alphabet_source(symbols)  # type: ignore[arg-type]


def test_bounded_shadow_is_pressure_only_and_sees_finite_nonseparation():
    alphabet = stream_alphabet_source(("a", "b"))
    shadow = bounded_stream_shadow(alphabet, 12)
    assert shadow.finite_stream == shadow.diagonal == ("a",) * 12
    assert shadow.scope == "finite-pressure-not-completed-carrier-evidence"
    left, right = ("a",) * 8 + ("a",), ("a",) * 8 + ("b",)
    assert left[:8] == right[:8] and left != right
    with pytest.raises(StreamCompletionValidationError):
        stream_completion_judgment(shadow)  # type: ignore[arg-type]


def test_policy_refusal_is_first_bound_and_compile_is_not_called(monkeypatch):
    base = exact_package()
    generic = capture_generic_source(base.theorem_source)
    required = len(generic) + len(base.alphabet_presentation.generated_instance_bytes)
    policy = stream_completion_policy(max_captured_bytes=required - 1, max_static_cost=1)
    package = stream_completion_package(
        base.doctrine, base.alphabet, base.theorem_source, base.ledger, policy,
    )
    monkeypatch.setattr(
        "src.core.stream_completion_runtime.compile_captured_sources",
        lambda *args: (_ for _ in ()).throw(AssertionError("compile-before-preflight")),
    )
    result = stream_completion_judgment(package)
    assert type(result) is StreamCompletionResourceLimit
    assert result.failed_bound is CompletionFailedBound.CAPTURED_BYTES
    assert result.required_value == required and result.allowed_value == required - 1
    assert not hasattr(result, "theorem_ids") and not hasattr(result, "obligations")


def test_reordered_theorems_foreign_presentation_and_package_digest_reject():
    package = exact_package()
    theorem = replace(package.theorem_source, theorem_ids=tuple(reversed(THEOREM_IDS)))
    foreign = exact_package(("x", "y", "z"))
    bad = (
        replace(package, theorem_source=theorem),
        replace(package, alphabet_presentation=foreign.alphabet_presentation),
        replace(package, package_digest="0" * 64),
    )
    for value in bad:
        with pytest.raises(StreamCompletionValidationError):
            stream_completion_judgment(value)


def test_artifact_comment_change_is_not_semantically_ignored(monkeypatch):
    package = exact_package()
    original = Path(package.theorem_source.artifact_path_id).read_bytes()
    monkeypatch.setattr(
        "src.core.stream_completion_formal._read_bounded_source",
        lambda path: original + b"\n-- comment drift\n",
    )
    with pytest.raises(StreamCompletionValidationError, match="stream-artifact-drift"):
        stream_completion_judgment(package)
