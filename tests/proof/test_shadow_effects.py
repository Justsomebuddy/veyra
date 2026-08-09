"""R12.1 tests for bridge effects, evidence boundaries, and response brands."""

from dataclasses import replace

import pytest

from src.core.observer_core_semantics import observe
from src.core.observer_core_types import (
    Apply,
    Input,
    PairKind,
    PrimitiveId,
    Ready,
    RecurrenceValue,
)
from src.core.proof_core_types import Pulse, Silence
from src.core.shadow_effect_types import (
    BridgeCapability,
    BridgeClaim,
    BridgeDirection,
    CarrierId,
    EvidenceClass,
    EvidenceRef,
    EvidenceScope,
)
from src.core.shadow_effect_branding import (
    ShadowEffectError,
    brand_observation,
    branded_observation_data,
    response_kind_data,
    verify_branded_observation,
)
from src.core.shadow_effects import (
    bridge_claim_data,
    bridge_direction,
    default_shadow_bridge_registry,
    shadow_effect_registry_data,
    shadow_effect_registry_digest,
    shadow_effect_summary,
    validate_bridge_claim,
)


def test_exact_capability_rows_derive_all_five_directions():
    rows = {
        (BridgeCapability.PRESERVES,): BridgeDirection.PRESERVATION,
        (BridgeCapability.PRESERVES, BridgeCapability.COLLAPSE_WITNESS): BridgeDirection.QUOTIENT,
        (BridgeCapability.REFLECTS,): BridgeDirection.REFLECTION,
        (BridgeCapability.PRESERVES, BridgeCapability.REFLECTS): BridgeDirection.FAITHFUL,
        (
            BridgeCapability.PRESERVES,
            BridgeCapability.REFLECTS,
            BridgeCapability.LEFT_ROUND_TRIP,
            BridgeCapability.RIGHT_ROUND_TRIP,
        ): BridgeDirection.EQUIVALENCE,
    }
    assert {bridge_direction(row) for row in rows} == set(BridgeDirection)
    assert all(bridge_direction(row) is direction for row, direction in rows.items())


@pytest.mark.parametrize(
    "row, reason",
    (
        ((), "invalid-capability-row"),
        ((BridgeCapability.REFLECTS, BridgeCapability.PRESERVES), "noncanonical-capability-row"),
        ((BridgeCapability.PRESERVES, BridgeCapability.PRESERVES), "noncanonical-capability-row"),
        ((BridgeCapability.PRESERVES, BridgeCapability.LEFT_ROUND_TRIP), "unsupported-capability-combination"),
        ((BridgeCapability.PRESERVES, "reflects"), "invalid-capability-row"),
    ),
)
def test_direction_derivation_rejects_inconsistent_or_laundered_rows(row, reason):
    with pytest.raises(ShadowEffectError, match=reason):
        bridge_direction(row)


def test_ready_and_blocked_observations_are_bound_to_exact_observer_and_kind():
    crest = Apply(PrimitiveId.CREST, Input())
    tail = Apply(PrimitiveId.TAIL, Input())
    recurrence = Pulse(Pulse(Silence()))
    ready = brand_observation(crest, observe(crest, recurrence), CarrierId.R7_RECURRENCE)
    blocked = brand_observation(tail, observe(tail, Silence()), CarrierId.R7_RECURRENCE)

    assert verify_branded_observation(crest, ready, CarrierId.R7_RECURRENCE)
    assert verify_branded_observation(tail, blocked, CarrierId.R7_RECURRENCE)
    assert branded_observation_data(ready)["payload"]["tag"] == "ready"
    assert branded_observation_data(blocked)["payload"]["tag"] == "blocked"
    with pytest.raises(ShadowEffectError, match="observation-brand-transplant"):
        verify_branded_observation(tail, ready, CarrierId.R7_RECURRENCE)


def test_equal_payload_under_different_observers_has_different_brand():
    crest = Apply(PrimitiveId.CREST, Input())
    crest_after_tail = Apply(PrimitiveId.CREST, Apply(PrimitiveId.TAIL, Input()))
    recurrence = Pulse(Pulse(Silence()))
    first = brand_observation(crest, observe(crest, recurrence), CarrierId.R7_RECURRENCE)
    second = brand_observation(crest_after_tail, observe(crest_after_tail, recurrence), CarrierId.R7_RECURRENCE)

    assert first.payload_digest == second.payload_digest
    assert first.brand.observer_digest != second.brand.observer_digest
    with pytest.raises(ShadowEffectError, match="observation-brand-transplant"):
        verify_branded_observation(crest_after_tail, first, CarrierId.R7_RECURRENCE)


def test_brand_rejects_wrong_ready_kind_and_nonexistent_obstruction_site():
    crest = Apply(PrimitiveId.CREST, Input())
    tail = Apply(PrimitiveId.TAIL, Input())
    wrong_ready = Ready(RecurrenceValue(Silence()))
    impossible_blocked = observe(tail, Silence())

    with pytest.raises(ShadowEffectError, match="observation-kind-mismatch"):
        brand_observation(crest, wrong_ready, CarrierId.R7_RECURRENCE)
    with pytest.raises(ShadowEffectError, match="observation-obstruction-mismatch"):
        brand_observation(crest, impossible_blocked, CarrierId.R7_RECURRENCE)


def test_source_carrier_is_closed_and_verified():
    crest = Apply(PrimitiveId.CREST, Input())
    branded = brand_observation(crest, observe(crest, Silence()), CarrierId.R7_RECURRENCE)
    r9_branded = brand_observation(crest, observe(crest, Silence()), CarrierId.R9_INTRINSIC_MODE)

    with pytest.raises(ShadowEffectError, match="observation-source-transplant"):
        verify_branded_observation(crest, r9_branded, CarrierId.R7_RECURRENCE)
    transplanted = replace(branded, brand=replace(branded.brand, source=CarrierId.R9_INTRINSIC_MODE))
    with pytest.raises(ShadowEffectError, match="observation-brand-drift"):
        branded_observation_data(transplanted)
    forbidden = replace(branded, brand=replace(branded.brand, source=CarrierId.LEGACY_CORE))
    with pytest.raises(ShadowEffectError, match="invalid-observation-brand"):
        branded_observation_data(forbidden)
    with pytest.raises(ShadowEffectError, match="invalid-observation-source"):
        verify_branded_observation(crest, branded, CarrierId.LEGACY_CORE)


def test_payload_mutation_and_hostile_type_confusion_fail_closed():
    crest = Apply(PrimitiveId.CREST, Input())
    branded = brand_observation(crest, observe(crest, Pulse(Silence())), CarrierId.R7_RECURRENCE)
    object.__setattr__(branded, "observation", observe(crest, Silence()))
    with pytest.raises(ShadowEffectError, match="observation-payload-drift"):
        branded_observation_data(branded)

    class ClaimSubclass(BridgeClaim):
        pass

    claim = default_shadow_bridge_registry()[0]
    hostile = ClaimSubclass(**claim.__dict__)
    with pytest.raises(ShadowEffectError, match="invalid-bridge-claim"):
        validate_bridge_claim(hostile)
    with pytest.raises(ShadowEffectError, match="invalid-effect-registry"):
        shadow_effect_registry_data(list(default_shadow_bridge_registry()))


def test_response_kind_serializer_rejects_cycle_and_unknown_kind():
    pair = PairKind(PairKind.__new__(PairKind), PairKind.__new__(PairKind))
    object.__setattr__(pair, "left", pair)
    object.__setattr__(pair, "right", pair)
    with pytest.raises(ShadowEffectError, match="circular-response-kind"):
        response_kind_data(pair)
    with pytest.raises(ShadowEffectError, match="invalid-response-kind"):
        response_kind_data("mark")


def test_default_registry_is_exact_canonical_and_nonpromotional():
    registry = default_shadow_bridge_registry()
    data = shadow_effect_registry_data(registry)
    assert [row["direction"] for row in data["rows"]] == [
        "equivalence",
        "preservation",
        "quotient",
        "preservation",
    ]
    assert data["rows"][2]["capabilities"] == ["preserves", "collapse-witness"]
    assert all(row["promotion_ready"] is False for row in data["rows"])
    assert shadow_effect_registry_digest(registry) == shadow_effect_registry_digest()
    summary = shadow_effect_summary()
    assert summary["rows"] == 4
    assert summary["general"] == 3
    assert summary["finite"] == 1
    assert summary["promotion_ready"] == 0
    assert summary["r12_complete"] is False
    assert summary["taxonomy_changed"] is False


def test_finite_evidence_cannot_escalate_to_general_or_kernel_proof():
    finite = EvidenceRef(EvidenceClass.VAM_CERT, "CERT:r1", EvidenceScope.FINITE, "finite echo only")
    assert finite.may_enter_promotion_contract is False
    escalated = replace(finite, scope=EvidenceScope.GENERAL)
    claim = BridgeClaim(
        "forged-general",
        CarrierId.LEGACY_CORE,
        CarrierId.LEGACY_VAM_SHADOW,
        (BridgeCapability.PRESERVES,),
        (escalated,),
        EvidenceScope.GENERAL,
        "must reject",
    )
    with pytest.raises(ShadowEffectError, match="finite-evidence-scope-escalation"):
        validate_bridge_claim(claim)


def test_general_formal_bridge_without_kernel_proof_is_not_enough():
    formal = EvidenceRef(
        EvidenceClass.FORMAL_BRIDGE,
        "lean-compiled-only",
        EvidenceScope.GENERAL,
        "compilation is not kernel evidence",
    )
    claim = BridgeClaim(
        "formal-only",
        CarrierId.R7_RECURRENCE,
        CarrierId.R11_RESPONSE,
        (BridgeCapability.PRESERVES,),
        (formal,),
        EvidenceScope.GENERAL,
        "must reject",
    )
    with pytest.raises(ShadowEffectError, match="general-bridge-without-kernel-proof"):
        bridge_claim_data(claim)


def test_registry_rejects_mutated_claim_and_forged_kernel_evidence():
    rows = default_shadow_bridge_registry()
    mutated = (replace(rows[0], boundary="mutated-boundary"),) + rows[1:]
    with pytest.raises(ShadowEffectError, match="unaudited-bridge-claim"):
        shadow_effect_registry_digest(mutated)

    forged = BridgeClaim(
        "forged-kernel-equivalence",
        CarrierId.LEGACY_CORE,
        CarrierId.LEGACY_VAM_SHADOW,
        (
            BridgeCapability.PRESERVES,
            BridgeCapability.REFLECTS,
            BridgeCapability.LEFT_ROUND_TRIP,
            BridgeCapability.RIGHT_ROUND_TRIP,
        ),
        (
            EvidenceRef(
                EvidenceClass.KERNEL_PROOF,
                "nonexistent-proof",
                EvidenceScope.GENERAL,
                "self-asserted evidence must not enter the audited registry",
            ),
        ),
        EvidenceScope.GENERAL,
        "forged",
    )
    with pytest.raises(ShadowEffectError, match="unaudited-bridge-claim"):
        bridge_claim_data(forged)


def test_registry_and_evidence_counts_are_bounded():
    rows = default_shadow_bridge_registry()
    oversized_registry = rows * 5
    with pytest.raises(ShadowEffectError, match="invalid-effect-registry"):
        shadow_effect_registry_data(oversized_registry)

    oversized_evidence = replace(rows[0], evidence=rows[0].evidence * 5)
    with pytest.raises(ShadowEffectError, match="invalid-bridge-evidence"):
        validate_bridge_claim(oversized_evidence)
