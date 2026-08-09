"""R13.2 phase-one canonical source replay and fail-closed binding tests."""
from __future__ import annotations

from dataclasses import replace
from typing import Any, cast

import pytest

import src.core.intrinsic_observer_echo_source as source_module
from src.core.intrinsic_observer_echo_source import (
    BOUNDARY,
    CANONICAL_SOURCE,
    EXPECTED_ARTIFACT_DIGEST,
    EXPECTED_PROOF_DIGEST,
    EXPECTED_R10_BINDING_DIGEST,
    EXPECTED_SEMANTIC_DIGEST,
    EXPECTED_SOURCE_DIGEST,
    EXPECTED_SYNTAX_DIGEST,
    EXPECTED_THEOREM_DIGEST,
    PHASE,
    SCHEMA,
    THEOREM_LABEL,
    IntrinsicObserverEchoSourceArtifact,
    intrinsic_observer_echo_source_artifact,
    verify_intrinsic_observer_echo_source_artifact,
)
from src.core.proof_core_types import (
    Bound,
    Equal,
    Forall,
    ForallIntro,
    NativeLaw,
    NativeLawId,
    Pulse,
    Silence,
    Weave,
)
from src.core.proof_surface_elaborator import compile_surface_program

pytestmark = pytest.mark.requires_lean


@pytest.fixture(scope="module")
def artifact() -> IntrinsicObserverEchoSourceArtifact:
    """Build the guarded source artifact once for focused phase-one tests."""
    return intrinsic_observer_echo_source_artifact()


def test_exact_doc139_source_replays_through_parser_and_kernel(
    artifact: IntrinsicObserverEchoSourceArtifact,
) -> None:
    expected = b"""(veyra-proof 1
  (claim (forall item recurrence
    (equal (weave (var item) (pulse (silence))) (var item))))
  (proof (forall-intro item recurrence
    (native-law weave-unit-right (var item)))))"""
    assert CANONICAL_SOURCE == expected
    elaborated = compile_surface_program(expected.decode("ascii"))
    assert elaborated.claim == Forall(
        elaborated.claim.binder_type,
        Equal(Weave(Bound(0), Pulse(Silence())), Bound(0)),
    )
    assert elaborated.proof == ForallIntro(
        elaborated.proof.binder_type,
        NativeLaw(NativeLawId.WEAVE_UNIT_RIGHT, (Bound(0),)),
    )
    assert artifact.source == expected.decode("ascii")


def test_artifact_is_distinct_pinned_and_explicitly_phase_one(
    artifact: IntrinsicObserverEchoSourceArtifact,
) -> None:
    assert artifact.schema == SCHEMA
    assert artifact.phase == PHASE
    assert artifact.theorem_label == THEOREM_LABEL
    assert not artifact.theorem_label.startswith("THM-R13-")
    assert artifact.rule_closure == ("forall-intro", "native-law")
    assert artifact.native_law_closure == ("weave-unit-right",)
    assert artifact.boundary == BOUNDARY
    assert "no R13 observer-echo theorem" in artifact.boundary


def test_every_reviewed_digest_and_exact_replay_are_stable(
    artifact: IntrinsicObserverEchoSourceArtifact,
) -> None:
    assert artifact.source_digest == EXPECTED_SOURCE_DIGEST
    assert artifact.theorem_digest == EXPECTED_THEOREM_DIGEST
    assert artifact.syntax_digest == EXPECTED_SYNTAX_DIGEST
    assert artifact.semantic_digest == EXPECTED_SEMANTIC_DIGEST
    assert artifact.proof_digest == EXPECTED_PROOF_DIGEST
    assert artifact.r10_binding_digest == EXPECTED_R10_BINDING_DIGEST
    assert artifact.artifact_digest == EXPECTED_ARTIFACT_DIGEST
    assert artifact == intrinsic_observer_echo_source_artifact()
    assert verify_intrinsic_observer_echo_source_artifact(artifact).ok


@pytest.mark.parametrize(
    ("field", "value", "error"),
    (
        ("theorem_label", "THM-R13-003", "r13-source-theorem-label-mismatch"),
        ("source", "forged", "r13-source-source-mismatch"),
        ("source_digest", "0" * 64, "r13-source-source-digest-mismatch"),
        ("theorem_digest", "0" * 64, "r13-source-theorem-digest-mismatch"),
        ("syntax_digest", "0" * 64, "r13-source-syntax-digest-mismatch"),
        ("semantic_digest", "0" * 64, "r13-source-semantic-digest-mismatch"),
        ("proof_digest", "0" * 64, "r13-source-proof-digest-mismatch"),
        ("r10_binding_digest", "0" * 64, "r13-source-r10-binding-mismatch"),
        ("artifact_digest", "0" * 64, "r13-source-artifact-digest-mismatch"),
    ),
)
def test_source_theorem_and_digest_mutations_fail_closed(
    artifact: IntrinsicObserverEchoSourceArtifact,
    field: str,
    value: str,
    error: str,
) -> None:
    check = verify_intrinsic_observer_echo_source_artifact(
        replace(artifact, **cast(Any, {field: value})),
    )
    assert not check.ok
    assert error in check.errors


def test_captured_source_drift_is_recompiled_then_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        source_module,
        "CANONICAL_SOURCE",
        CANONICAL_SOURCE.replace(b"item", b"term"),
    )
    with pytest.raises(ValueError, match="r13-source-source-digest-mismatch"):
        intrinsic_observer_echo_source_artifact()


def test_artifact_subclass_is_rejected_before_field_replay(
    artifact: IntrinsicObserverEchoSourceArtifact,
) -> None:
    class ForgedArtifact(IntrinsicObserverEchoSourceArtifact):
        pass

    forged = ForgedArtifact(**artifact.__dict__)
    check = verify_intrinsic_observer_echo_source_artifact(forged)
    assert not check.ok
    assert check.errors == ("invalid-r13-source-artifact-type",)


def test_field_subclass_and_attribute_trap_are_rejected(
    artifact: IntrinsicObserverEchoSourceArtifact,
) -> None:
    class ForgedText(str):
        pass

    class AttributeTrap:
        def __getattribute__(self, name: str) -> object:
            raise RuntimeError(name)

    forged = replace(artifact, theorem_label=ForgedText(artifact.theorem_label))
    assert verify_intrinsic_observer_echo_source_artifact(forged).errors == (
        "invalid-r13-source-scalar-types",
    )
    assert verify_intrinsic_observer_echo_source_artifact(AttributeTrap()).errors == (
        "invalid-r13-source-artifact-type",
    )


def test_uninitialized_exact_artifact_fails_closed_without_raising() -> None:
    forged = object.__new__(IntrinsicObserverEchoSourceArtifact)
    check = verify_intrinsic_observer_echo_source_artifact(forged)
    assert not check.ok
    assert check.errors == ("invalid-r13-source-artifact-shape",)
