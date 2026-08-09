"""Focused finite-evidence and isolated-effect regressions for R13."""
from dataclasses import replace
from types import MappingProxyType

import pytest

import src.core.intrinsic_observer_echo_effects as effects
from src.core.intrinsic_observer_echo_evidence import (
    BOUNDARY,
    EXPECTED_EVIDENCE_DIGEST,
    IntrinsicObserverEchoEvidence,
    intrinsic_observer_echo_evidence,
    verify_intrinsic_observer_echo_evidence,
)
from src.core.intrinsic_observer_echo_effects import (
    BRIDGE_ID,
    EFFECT_BOUNDARY,
    EXPECTED_REGISTRY_DIGEST,
    intrinsic_observer_echo_effect_data,
    intrinsic_observer_echo_effect_digest,
)
from src.core.shadow_effect_types import BridgeCapability
from src.core.shadow_effects import shadow_effect_registry_digest

pytestmark = pytest.mark.requires_lean


@pytest.fixture(scope="module")
def evidence() -> IntrinsicObserverEchoEvidence:
    """Build the exact evidence once for focused mutation checks."""
    return intrinsic_observer_echo_evidence()


def test_three_rows_preserve_ready_blockage_and_nonreflection(
    evidence: IntrinsicObserverEchoEvidence,
) -> None:
    assert evidence.digest == EXPECTED_EVIDENCE_DIGEST
    assert evidence.boundary == BOUNDARY
    ready, blocked, collapse = evidence.rows
    assert ready.row_id == "R13-EVIDENCE-READY"
    assert '"mark":"pulse"' in ready.observation
    assert '"tag":"echo"' in ready.outcome
    assert ready.sources_equal and ready.lowered_equal
    assert blocked.row_id == "R13-EVIDENCE-TAIL-BLOCKED"
    assert blocked.outcome.count("tail-of-silence") == 2
    assert blocked.outcome.count("apply-tail") == 2
    assert collapse.row_id == "R13-EVIDENCE-CREST-NONREFLECTION"
    assert '"tag":"echo"' in collapse.outcome
    assert not collapse.sources_equal and not collapse.lowered_equal
    assert collapse.left_ir_digest != collapse.right_ir_digest
    assert verify_intrinsic_observer_echo_evidence(evidence)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("source_artifact_digest", "0" * 64),
        ("boundary", "broader"),
        ("digest", "0" * 64),
        ("rows", ()),
    ),
)
def test_evidence_envelope_mutation_fails_closed(
    evidence: IntrinsicObserverEchoEvidence,
    field: str,
    value: object,
) -> None:
    assert not verify_intrinsic_observer_echo_evidence(
        replace(evidence, **{field: value}),
    )


def test_row_transplant_and_subclasses_fail_closed(
    evidence: IntrinsicObserverEchoEvidence,
) -> None:
    transplanted = replace(evidence.rows[0], row_id=evidence.rows[1].row_id)
    assert not verify_intrinsic_observer_echo_evidence(
        replace(evidence, rows=(transplanted, *evidence.rows[1:])),
    )

    class EvidenceSubclass(IntrinsicObserverEchoEvidence):
        pass

    hostile = EvidenceSubclass(
        *(getattr(evidence, name) for name in evidence.__dataclass_fields__),
    )
    assert not verify_intrinsic_observer_echo_evidence(hostile)

    class TextSubclass(str):
        pass

    hostile_row = replace(
        evidence.rows[0],
        row_id=TextSubclass(evidence.rows[0].row_id),
    )
    assert not verify_intrinsic_observer_echo_evidence(
        replace(evidence, rows=(hostile_row, *evidence.rows[1:])),
    )


def test_effect_is_isolated_preservation_and_never_self_promotes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = shadow_effect_registry_digest()
    data = intrinsic_observer_echo_effect_data()
    assert before == EXPECTED_REGISTRY_DIGEST == shadow_effect_registry_digest()
    assert data["capabilities"] == [BridgeCapability.PRESERVES.value]
    assert data["evidence"] == [
        {"class": "kernel-proof", "scope": "general", "id": "THM-R13-003"},
        {"class": "formal-bridge", "scope": "general", "id": BRIDGE_ID},
    ]
    assert data["executable_evidence"]["digest"] == EXPECTED_EVIDENCE_DIGEST
    assert data["boundary"] == EFFECT_BOUNDARY
    assert data["promotion_ready"] is False
    assert data["taxonomy_changed"] is False
    assert len(intrinsic_observer_echo_effect_digest()) == 64

    forged = dict(effects._EFFECT_ROW)
    forged["capabilities"] = (BridgeCapability.PRESERVES, BridgeCapability.REFLECTS)
    forged["promotion_ready"] = True
    monkeypatch.setattr(effects, "_EFFECT_ROW", MappingProxyType(forged))
    with pytest.raises(ValueError, match="r13-effect-row-or-r12.1-registry-invalid"):
        intrinsic_observer_echo_effect_data()
