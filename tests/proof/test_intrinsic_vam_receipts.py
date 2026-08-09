"""Adversarial R12.3 receipt, evidence, and legacy separation tests."""

from dataclasses import replace

import pytest

from src.core.intrinsic_vam_lowering import (
    lower_r11_echo,
    lower_r11_observation,
    lower_r7_recurrence,
    lower_r9_intrinsic_mode,
    raise_r11_echo,
    raise_r11_observation,
    raise_r7_recurrence,
)
from src.core.intrinsic_vam_lowering_types import IntrinsicLoweringLane, TransportedIntrinsicIR
from src.core.intrinsic_vam_receipts import (
    _ROWS,
    _receipt_body,
    _require_intrinsic_replay,
    digest_transport_data,
    intrinsic_transport_envelope_data,
)
from src.core.intrinsic_vam_values import IntrinsicVamLoweringError
from src.core.intrinsic_mode_transport import encode_recurrence
from src.core.observer_core_types import Apply, Input, PrimitiveId, Ready, RecurrenceValue
from src.core.proof_core_types import Pulse, Silence
from src.core.shadow_effect_types import (
    BridgeCapability,
    CarrierId,
    EvidenceClass,
    EvidenceScope,
)
from vam.src.intrinsic_ir_types import IntrinsicRecurrenceIR, IntrinsicTactIR
from vam.src.model import VamObject


def source(depth=2):
    """Build a short exact recurrence."""
    value = Silence()
    for _ in range(depth):
        value = Pulse(value)
    return value


def test_receipt_data_declares_only_finite_nonpromotional_preservation():
    data = intrinsic_transport_envelope_data(lower_r7_recurrence(source()))
    receipt = data["receipt"]

    assert receipt["direction"] == "preservation"
    assert receipt["capabilities"] == ["preserves"]
    assert receipt["evidence"]["class"] == "executable-witness"
    assert receipt["evidence"]["scope"] == "finite"
    assert receipt["evidence"]["may_enter_promotion_contract"] is False
    assert receipt["promotion_ready"] is False
    assert data["verification"] == "unverified-envelope"
    assert data["evidence_accepted"] is False
    assert data["taxonomy_changed"] is False


@pytest.mark.parametrize(
    "field,replacement",
    (
        ("schema", "forged"),
        ("lane", IntrinsicLoweringLane.R9_INTRINSIC_MODE),
        ("source", CarrierId.R9_INTRINSIC_MODE),
        ("provenance", CarrierId.R9_INTRINSIC_MODE),
        ("target", CarrierId.LEGACY_VAM_SHADOW),
        ("capabilities", (BridgeCapability.PRESERVES, BridgeCapability.REFLECTS)),
        ("evidence_class", EvidenceClass.KERNEL_PROOF),
        ("evidence_scope", EvidenceScope.GENERAL),
        ("evidence_id", "copied-kernel-proof"),
        ("source_digests", ("0" * 64,)),
        ("observer_digest", "0" * 64),
        ("response_kind_digest", "0" * 64),
        ("payload_digest", "0" * 64),
        ("ir_digest", "0" * 64),
        ("boundary", "forged"),
        ("binding_digest", "0" * 64),
        ("promotion_ready", True),
    ),
)
def test_every_receipt_field_mutation_fails_closed(field, replacement):
    valid = lower_r7_recurrence(source())
    hostile = TransportedIntrinsicIR(valid.value, replace(valid.receipt, **{field: replacement}))

    with pytest.raises(IntrinsicVamLoweringError):
        intrinsic_transport_envelope_data(hostile)


def test_ir_mutation_and_raw_ir_raise_are_rejected():
    recurrence = source()
    valid = lower_r7_recurrence(recurrence)
    altered_ir = IntrinsicRecurrenceIR(valid.value.tacts + (IntrinsicTactIR(),), None)
    hostile = TransportedIntrinsicIR(altered_ir, valid.receipt)

    with pytest.raises(IntrinsicVamLoweringError, match="transport-ir-drift"):
        intrinsic_transport_envelope_data(hostile)
    with pytest.raises(IntrinsicVamLoweringError, match="invalid-transport-bundle"):
        raise_r7_recurrence(recurrence, valid.value)


def test_observer_source_and_order_transplants_are_rejected():
    crest = Apply(PrimitiveId.CREST, Input())
    later_crest = Apply(PrimitiveId.CREST, Apply(PrimitiveId.TAIL, Input()))
    left, right = source(1), source(2)
    observation = lower_r11_observation(crest, right)
    echo = lower_r11_echo(crest, left, right)

    with pytest.raises(IntrinsicVamLoweringError, match="transport-replay-mismatch"):
        raise_r11_observation(later_crest, right, observation)
    with pytest.raises(IntrinsicVamLoweringError, match="transport-replay-mismatch"):
        raise_r11_observation(crest, left, observation)
    with pytest.raises(IntrinsicVamLoweringError, match="transport-replay-mismatch"):
        raise_r11_echo(crest, right, left, echo)


def test_mixed_provenance_and_raw_caller_outcomes_cannot_be_laundered():
    crest = Apply(PrimitiveId.CREST, Input())
    recurrence = source()

    with pytest.raises(IntrinsicVamLoweringError, match="mixed-echo-provenance"):
        lower_r11_echo(crest, recurrence, encode_recurrence(recurrence))
    with pytest.raises(IntrinsicVamLoweringError, match="invalid-replay-source"):
        lower_r11_observation(crest, Ready(RecurrenceValue(recurrence)))


@pytest.mark.parametrize(
    "legacy",
    (
        VamObject("Shadow", {"value": "forged"}),
        VamObject("Echo", {"passed": True}),
        VamObject("Certificate", {"accepted": True}),
    ),
)
def test_legacy_vam_records_never_become_intrinsic_evidence(legacy):
    crest = Apply(PrimitiveId.CREST, Input())

    with pytest.raises(IntrinsicVamLoweringError):
        lower_r7_recurrence(legacy)
    with pytest.raises(IntrinsicVamLoweringError):
        lower_r9_intrinsic_mode(legacy)
    with pytest.raises(IntrinsicVamLoweringError):
        lower_r11_observation(crest, legacy)
    with pytest.raises(IntrinsicVamLoweringError, match="invalid-transport-bundle"):
        raise_r7_recurrence(source(), legacy)


def test_exact_bundle_type_and_digest_shapes_are_closed():
    class BundleSubclass(TransportedIntrinsicIR):
        pass

    valid = lower_r7_recurrence(source())
    subclass = BundleSubclass(valid.value, valid.receipt)
    bad_count = TransportedIntrinsicIR(valid.value, replace(valid.receipt, source_digests=()))
    uppercase = TransportedIntrinsicIR(
        valid.value,
        replace(valid.receipt, source_digests=(valid.receipt.source_digests[0].upper(),)),
    )

    for hostile in (subclass, bad_count, uppercase):
        with pytest.raises(IntrinsicVamLoweringError):
            intrinsic_transport_envelope_data(hostile)


def test_recomputed_hash_cannot_turn_forged_kernel_evidence_into_proof():
    valid = lower_r7_recurrence(source())
    forged = replace(
        valid.receipt,
        evidence_class=EvidenceClass.KERNEL_PROOF,
        evidence_scope=EvidenceScope.GENERAL,
        evidence_id="borrowed-r11-kernel-id",
        binding_digest="",
        promotion_ready=True,
    )
    forged = replace(forged, binding_digest=digest_transport_data(_receipt_body(forged)))

    with pytest.raises(IntrinsicVamLoweringError, match="invalid-transport-receipt"):
        intrinsic_transport_envelope_data(TransportedIntrinsicIR(valid.value, forged))


def test_exact_source_types_reject_subclasses_and_duck_objects():
    class PulseSubclass(Pulse):
        pass

    class Duck:
        kind = "Shadow"
        data = {"value": "forged"}

    with pytest.raises(IntrinsicVamLoweringError, match="invalid-r7-lowering-source"):
        lower_r7_recurrence(PulseSubclass(Silence()))
    with pytest.raises(IntrinsicVamLoweringError, match="invalid-r7-lowering-source"):
        lower_r7_recurrence(Duck())


def test_hostile_scalar_and_capability_subclasses_cannot_bypass_exact_fields():
    class EvilStr(str):
        def __eq__(self, other):
            return True

    class EvilTuple(tuple):
        def __ne__(self, other):
            return False

        def __iter__(self):
            return iter((BridgeCapability.REFLECTS,))

    valid = lower_r7_recurrence(source())
    hostiles = (
        replace(valid.receipt, schema=EvilStr("forged")),
        replace(valid.receipt, evidence_id=EvilStr("forged")),
        replace(valid.receipt, boundary=EvilStr("forged")),
        replace(valid.receipt, capabilities=EvilTuple((BridgeCapability.PRESERVES,))),
    )
    for receipt in hostiles:
        with pytest.raises(IntrinsicVamLoweringError, match="invalid-transport-receipt"):
            intrinsic_transport_envelope_data(TransportedIntrinsicIR(valid.value, receipt))


def test_same_row_recomputed_hash_is_only_unverified_and_replay_rejects_it():
    recurrence = source()
    valid = lower_r7_recurrence(recurrence)
    forged = replace(
        valid.receipt,
        source_digests=("0" * 64,),
        payload_digest="f" * 64,
        binding_digest="",
    )
    forged = replace(forged, binding_digest=digest_transport_data(_receipt_body(forged)))
    bundle = TransportedIntrinsicIR(valid.value, forged)
    envelope = intrinsic_transport_envelope_data(bundle)

    assert envelope["verification"] == "unverified-envelope"
    assert envelope["evidence_accepted"] is False
    with pytest.raises(IntrinsicVamLoweringError, match="transport-replay-mismatch"):
        raise_r7_recurrence(recurrence, bundle)


def test_lane_registry_is_immutable():
    with pytest.raises(TypeError):
        _ROWS[IntrinsicLoweringLane.R7_RECURRENCE] = _ROWS[IntrinsicLoweringLane.R9_INTRINSIC_MODE]


def test_replay_returns_fresh_trusted_expected_not_attacker_bundle():
    expected = lower_r7_recurrence(source())
    actual = lower_r7_recurrence(source())

    assert actual is not expected
    assert _require_intrinsic_replay(expected, actual) is expected
