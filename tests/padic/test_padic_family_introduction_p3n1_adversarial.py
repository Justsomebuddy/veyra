"""Hostile envelope and forbidden-cast pressure for P3-N1."""

from dataclasses import replace

import pytest

from src.core.certify_types import Certificate
from src.core.padic_family_introduction import (
    N1ExecutionFailureKind, N1FamilyJudgment, N1FormalFailure,
    PadicFamilyIntroductionValidationError, introduce_integer_residue_family,
    validate_n1_result,
)
from src.core.padic_family_introduction_runtime import _positive
from padic_family_introduction_fixture import exact_n1_package

pytestmark = pytest.mark.requires_lean


class FamilyJudgmentSubclass(N1FamilyJudgment):
    pass


class Hostile:
    def __getattribute__(self, name):
        raise AssertionError(f"hostile attribute touched: {name}")

    def __eq__(self, other):
        raise AssertionError("hostile equality touched")


def test_hostile_or_subclass_result_is_rejected_before_semantic_replay():
    package = exact_n1_package(max_captured_bytes=1)
    with pytest.raises(PadicFamilyIntroductionValidationError):
        validate_n1_result(package, Hostile())
    positive = _positive(package, "0" * 64)
    subclass = FamilyJudgmentSubclass(**positive.__dict__)
    with pytest.raises(PadicFamilyIntroductionValidationError):
        validate_n1_result(package, subclass)


def test_certificate_and_prior_evidence_have_no_raw_source_lane():
    package = exact_n1_package()
    forbidden = (
        Certificate("old", "not raw", True, "finite-prefix", 1),
        introduce_integer_residue_family(package),
        {"depth": 1000, "compatible": True},
        lambda requested_depth: 0,
    )
    for value in forbidden:
        with pytest.raises(PadicFamilyIntroductionValidationError):
            introduce_integer_residue_family(value)


def test_mutated_status_provenance_and_digest_distinctness_are_rejected():
    package = exact_n1_package()
    value = introduce_integer_residue_family(package)
    mutants = (
        replace(value, status="established"),
        replace(value, provenance="formally-derived"),
        replace(value, introduction_evidence_digest=value.family_term_digest),
        replace(value, nonclaims=value.nonclaims[:-1]),
    )
    for mutant in mutants:
        with pytest.raises(PadicFamilyIntroductionValidationError):
            validate_n1_result(package, mutant)


def test_continuity_drift_is_typed_and_has_no_family_payload(monkeypatch):
    import src.core.padic_family_introduction_runtime as runtime

    monkeypatch.setattr(runtime, "continuity_holds", lambda package, captured: False)
    value = runtime.introduce_integer_residue_family(exact_n1_package())
    assert type(value) is N1FormalFailure
    assert value.kind is N1ExecutionFailureKind.CONTINUITY_DRIFT
    assert not hasattr(value, "family_term_digest")
