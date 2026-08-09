"""Functional R12.3 lowering/raising parity over exact reviewed carriers."""

import pytest

from src.core.intrinsic_mode_transport import encode_recurrence, recurrence_equal, verify_intrinsic_mode
from src.core.intrinsic_vam_lowering import (
    lower_r11_echo,
    lower_r11_observation,
    lower_r7_recurrence,
    lower_r9_intrinsic_mode,
    raise_r11_echo,
    raise_r11_observation,
    raise_r7_recurrence,
    raise_r9_intrinsic_mode,
)
from src.core.intrinsic_vam_lowering_types import TransportedIntrinsicIR
from src.core.intrinsic_vam_receipts import intrinsic_transport_envelope_data
from src.core.intrinsic_vam_values import IntrinsicVamLoweringError
from src.core.observer_core_support import outcome_data
from src.core.observer_core_types import Apply, Input, Pair, PrimitiveId
from src.core.proof_core_types import Bound, Pulse, Silence
from src.core.shadow_effect_branding import verify_branded_observation
from src.core.shadow_effect_types import CarrierId
from vam.src.intrinsic_ir_types import IntrinsicAnchorIR, IntrinsicRecurrenceIR, IntrinsicTactIR


def recurrence(depth: int):
    """Build one exact recurrence without integer conversion in product code."""
    value = Silence()
    for _ in range(depth):
        value = Pulse(value)
    return value


@pytest.mark.parametrize("depth", (0, 1, 2, 7, 127, 2047))
def test_r7_exact_round_trip_and_image_shape(depth):
    source = recurrence(depth)
    lowered = lower_r7_recurrence(source)
    raised = raise_r7_recurrence(recurrence(depth), lowered)

    assert recurrence_equal(source, raised)
    assert len(lowered.value.tacts) == depth
    assert (type(lowered.value.anchor) is IntrinsicAnchorIR) == (depth == 0)
    assert intrinsic_transport_envelope_data(lowered)["receipt"]["lane"] == "r7-recurrence"


@pytest.mark.parametrize("depth", (0, 1, 7, 127, 2047))
def test_r9_wrapper_round_trip_is_exact_and_lane_separated(depth):
    source = recurrence(depth)
    wrapper = encode_recurrence(source)
    r7 = lower_r7_recurrence(source)
    r9 = lower_r9_intrinsic_mode(wrapper)
    raised = raise_r9_intrinsic_mode(encode_recurrence(recurrence(depth)), r9)

    assert verify_intrinsic_mode(raised)
    assert raised.native == wrapper.native
    assert raised.digest == wrapper.digest
    assert r7.value == r9.value
    assert r7.receipt.binding_digest != r9.receipt.binding_digest
    with pytest.raises(IntrinsicVamLoweringError, match="transport-replay-mismatch"):
        raise_r7_recurrence(source, r9)


@pytest.mark.parametrize(
    "observer,source",
    (
        (Input(), recurrence(2)),
        (Apply(PrimitiveId.CREST, Input()), recurrence(2)),
        (Apply(PrimitiveId.TAIL, Input()), Silence()),
        (
            Pair(Apply(PrimitiveId.CREST, Input()), Apply(PrimitiveId.TAIL, Input())),
            recurrence(2),
        ),
    ),
)
def test_r11_observation_is_evaluated_branded_and_replayed(observer, source):
    lowered = lower_r11_observation(observer, source)
    raised = raise_r11_observation(observer, recurrence_depth_copy(source), lowered)

    assert verify_branded_observation(observer, raised, CarrierId.R7_RECURRENCE)
    assert intrinsic_transport_envelope_data(lowered)["receipt"]["lane"] == "r11-branded-observation"
    assert outcome_data(raised.observation)["tag"] in {"ready", "blocked"}


def recurrence_depth_copy(value):
    """Copy a recurrence structurally to prove content rather than identity binding."""
    depth, cursor = 0, value
    while type(cursor) is Pulse:
        depth += 1
        cursor = cursor.tail
    assert type(cursor) is Silence
    return recurrence(depth)


def test_r11_observation_accepts_only_exact_r7_or_verified_r9_provenance():
    observer = Apply(PrimitiveId.CREST, Input())
    wrapper = encode_recurrence(recurrence(3))
    lowered = lower_r11_observation(observer, wrapper)
    raised = raise_r11_observation(observer, encode_recurrence(recurrence(3)), lowered)

    assert lowered.receipt.provenance is CarrierId.R9_INTRINSIC_MODE
    assert verify_branded_observation(observer, raised, CarrierId.R9_INTRINSIC_MODE)
    with pytest.raises(IntrinsicVamLoweringError, match="invalid-replay-source"):
        lower_r11_observation(observer, Bound(0))


@pytest.mark.parametrize(
    "observer,left,right,tag",
    (
        (Input(), recurrence(2), recurrence(2), "echo"),
        (Input(), recurrence(1), recurrence(2), "mismatch"),
        (Apply(PrimitiveId.CREST, Input()), recurrence(1), recurrence(2), "echo"),
        (Apply(PrimitiveId.TAIL, Input()), Silence(), recurrence(1), "domain-blocked"),
        (Apply(PrimitiveId.TAIL, Input()), Silence(), Silence(), "domain-blocked"),
    ),
)
def test_r11_echo_three_way_outcomes_replay_exactly(observer, left, right, tag):
    lowered = lower_r11_echo(observer, left, right)
    raised = raise_r11_echo(observer, recurrence_depth_copy(left), recurrence_depth_copy(right), lowered)

    assert outcome_data(raised)["tag"] == tag
    assert intrinsic_transport_envelope_data(lowered)["receipt"]["lane"] == "r11-echo-outcome"


def test_same_crest_payload_binds_distinct_sources_and_observers():
    crest = Apply(PrimitiveId.CREST, Input())
    later_crest = Apply(PrimitiveId.CREST, Apply(PrimitiveId.TAIL, Input()))
    first = lower_r11_observation(crest, recurrence(1))
    second = lower_r11_observation(crest, recurrence(2))
    third = lower_r11_observation(later_crest, recurrence(2))

    assert first.receipt.payload_digest == second.receipt.payload_digest == third.receipt.payload_digest
    assert first.receipt.source_digests != second.receipt.source_digests
    assert second.receipt.observer_digest != third.receipt.observer_digest
    with pytest.raises(IntrinsicVamLoweringError, match="transport-replay-mismatch"):
        raise_r11_observation(crest, recurrence(2), first)


def test_recurrence_resource_boundary_rejects_without_partial_receipt():
    with pytest.raises(IntrinsicVamLoweringError, match="recurrence-lowering-resource-limit"):
        lower_r7_recurrence(recurrence(2048))
    malformed = IntrinsicRecurrenceIR((IntrinsicTactIR(),) * 2048, None)
    valid = lower_r7_recurrence(Silence())
    with pytest.raises(ValueError, match="invalid-recurrence-ir"):
        intrinsic_transport_envelope_data(TransportedIntrinsicIR(malformed, valid.receipt))
