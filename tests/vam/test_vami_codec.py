"""R12.4 conformance tests for the bounded canonical VAMI codec."""

from __future__ import annotations

import struct
import zlib

import pytest

from src.core.intrinsic_vam_lowering import lower_r7_recurrence
from src.core.proof_core_types import Silence
from vam.intrinsic import IntrinsicCodecError, decode_intrinsic_frame, encode_intrinsic_frame
from vam.src.intrinsic_ir import silence_ir
from vam.src.intrinsic_ir_types import (
    IntrinsicAnchorIR,
    IntrinsicBlockedIR,
    IntrinsicDomainBlockedIR,
    IntrinsicEchoIR,
    IntrinsicMarkIR,
    IntrinsicMarkValueIR,
    IntrinsicMismatchIR,
    IntrinsicObstructionCodeIR,
    IntrinsicObstructionIR,
    IntrinsicPairValueIR,
    IntrinsicPathStepIR,
    IntrinsicReadyIR,
    IntrinsicRecurrenceIR,
    IntrinsicRecurrenceValueIR,
    IntrinsicTactIR,
)
from vam.src.model import VamObject

HEADER = struct.Struct(">4sHII")
TAIL = IntrinsicPathStepIR.APPLY_TAIL
LEFT = IntrinsicPathStepIR.PAIR_LEFT
RIGHT = IntrinsicPathStepIR.PAIR_RIGHT


def _obstruction(*path: IntrinsicPathStepIR) -> IntrinsicObstructionIR:
    return IntrinsicObstructionIR(IntrinsicObstructionCodeIR.TAIL_OF_SILENCE, path)


def _corpus() -> tuple[object, ...]:
    recurrence = IntrinsicRecurrenceIR((IntrinsicTactIR(),), None)
    recurrence_value = IntrinsicRecurrenceValueIR(recurrence)
    silent = IntrinsicMarkValueIR(IntrinsicMarkIR.SILENT)
    pulse = IntrinsicMarkValueIR(IntrinsicMarkIR.PULSE)
    pair = IntrinsicPairValueIR(recurrence_value, pulse)
    obstruction = _obstruction(TAIL)
    return (
        IntrinsicAnchorIR(),
        IntrinsicTactIR(),
        silence_ir(),
        IntrinsicMarkIR.PULSE,
        recurrence_value,
        pulse,
        pair,
        obstruction,
        IntrinsicReadyIR(pair),
        IntrinsicBlockedIR((obstruction,)),
        IntrinsicEchoIR(pair),
        IntrinsicMismatchIR(silent, pulse),
        IntrinsicDomainBlockedIR((obstruction,), ()),
    )


def _frame(
    payload: bytes,
    *,
    magic: bytes = b"VAMI",
    version: int = 1,
    size: int | None = None,
    checksum: int | None = None,
) -> bytes:
    declared = len(payload) if size is None else size
    crc = zlib.crc32(payload) & 0xFFFFFFFF if checksum is None else checksum
    return HEADER.pack(magic, version, declared, crc) + payload


def _assert_error(blob: object, kind: str, message: str) -> None:
    with pytest.raises(IntrinsicCodecError) as caught:
        decode_intrinsic_frame(blob)
    assert caught.value.kind == kind
    assert str(caught.value) == message


@pytest.mark.parametrize(("tag", "value"), tuple(enumerate(_corpus(), start=1)))
def test_all_thirteen_tags_have_deterministic_canonical_roundtrips(tag: int, value: object):
    first = encode_intrinsic_frame(value)
    second = encode_intrinsic_frame(value)
    magic, version, size, checksum = HEADER.unpack(first[: HEADER.size])
    assert first == second
    assert (magic, version, size) == (b"VAMI", 1, len(first) - HEADER.size)
    assert checksum == zlib.crc32(first[HEADER.size :]) & 0xFFFFFFFF
    assert first[HEADER.size] == tag
    decoded = decode_intrinsic_frame(first)
    assert decoded == value
    assert encode_intrinsic_frame(decoded) == first


def test_compact_recurrence_has_exact_2047_boundary_and_rejects_2048():
    maximum = IntrinsicRecurrenceIR((IntrinsicTactIR(),) * 2047, None)
    encoded = encode_intrinsic_frame(maximum)
    assert encoded[HEADER.size :] == b"\x03\x07\xff\x00"
    assert len(decode_intrinsic_frame(encoded).tacts) == 2047
    _assert_error(_frame(b"\x03\x08\x00\x00"), "payload", "invalid intrinsic recurrence")


@pytest.mark.parametrize(
    ("blob", "kind", "message"),
    (
        (b"VAMI", "short_frame", "short VAMI frame"),
        (_frame(b"\x01", magic=b"NOPE"), "magic", "bad VAMI magic"),
        (_frame(b"\x01", version=2), "version", "unsupported VAMI version: 2"),
        (_frame(b"\x01", size=2), "length", "VAMI payload length mismatch"),
        (_frame(b"\x01", checksum=0), "crc32", "VAMI checksum mismatch"),
        (_frame(b"\x63"), "tag", "unknown VAMI tag: 99"),
        (_frame(b"\x03\x00"), "payload", "bad VAMI payload"),
        (_frame(b"\x01\x00"), "payload", "trailing VAMI payload data"),
        (_frame(b"\x04\x02"), "payload", "unknown intrinsic mark"),
        (_frame(b"\x08\x01\x00\x01\x00"), "payload", "unknown obstruction code"),
        (_frame(b"\x08\x00\x00\x01\x04"), "payload", "unknown obstruction path step"),
        (_frame(b"\x0c\x06\x00\x06\x00"), "payload", "mismatch responses are equal"),
        (
            _frame(b"\x0c\x06\x00\x05\x03\x00\x00\x01"),
            "payload",
            "mismatch response kinds differ",
        ),
    ),
)
def test_malformed_frames_fail_closed_with_stable_kind_and_message(
    blob: bytes, kind: str, message: str
):
    _assert_error(blob, kind, message)


def test_exact_bytes_and_declared_payload_cap_fail_closed():
    class BytesSubclass(bytes):
        pass

    _assert_error(BytesSubclass(encode_intrinsic_frame(IntrinsicAnchorIR())), "payload", "VAMI frame must be exact bytes")
    _assert_error(
        HEADER.pack(b"VAMI", 1, 1024 * 1024 + 1, 0),
        "resource",
        "VAMI payload exceeds 1 MiB",
    )


def test_path_depth_and_node_boundaries_are_enforced():
    longest = _obstruction(*((LEFT,) * 127), TAIL)
    assert decode_intrinsic_frame(encode_intrinsic_frame(longest)) == longest
    _assert_error(
        _frame(b"\x08\x00\x00\x81" + bytes((2,)) * 128 + b"\x00"),
        "payload",
        "invalid obstruction path length",
    )

    mark = IntrinsicMarkValueIR(IntrinsicMarkIR.PULSE)
    depth_128 = mark
    for _ in range(128):
        depth_128 = IntrinsicPairValueIR(depth_128, mark)
    assert decode_intrinsic_frame(encode_intrinsic_frame(depth_128)) == depth_128
    depth_129 = IntrinsicPairValueIR(depth_128, mark)
    with pytest.raises(IntrinsicCodecError, match="intrinsic-resource-limit"):
        encode_intrinsic_frame(depth_129)
    forged_depth_129 = b"\x07" * 129 + b"\x06\x00" + b"\x06\x01" * 129
    _assert_error(_frame(forged_depth_129), "resource", "VAMI depth exceeds 128")

    left = IntrinsicRecurrenceValueIR(IntrinsicRecurrenceIR((IntrinsicTactIR(),) * 2047, None))
    right = IntrinsicRecurrenceValueIR(IntrinsicRecurrenceIR((IntrinsicTactIR(),) * 2044, None))
    exact_4096 = IntrinsicPairValueIR(left, right)
    assert decode_intrinsic_frame(encode_intrinsic_frame(exact_4096)) == exact_4096
    broad = IntrinsicPairValueIR(left, IntrinsicRecurrenceValueIR(IntrinsicRecurrenceIR((IntrinsicTactIR(),) * 2045, None)))
    with pytest.raises(IntrinsicCodecError, match="intrinsic-resource-limit"):
        encode_intrinsic_frame(broad)
    _assert_error(_frame(b"\x07\x05\x03\x07\xff\x00\x05\x03\x07\xfd\x00"), "resource", "VAMI node count exceeds 4096")


def _paths(count: int, bits: int) -> tuple[IntrinsicObstructionIR, ...]:
    return tuple(
        _obstruction(
            *(RIGHT if index >> bit & 1 else LEFT for bit in range(bits)),
            TAIL,
        )
        for index in range(count)
    )


def test_obstruction_count_boundary_is_exact():
    maximum = IntrinsicBlockedIR(_paths(2048, 11))
    assert len(decode_intrinsic_frame(encode_intrinsic_frame(maximum)).obstructions) == 2048
    with pytest.raises(IntrinsicCodecError, match="invalid-obstruction-set"):
        encode_intrinsic_frame(IntrinsicBlockedIR(_paths(2049, 12)))


def test_hostile_subclasses_receipts_envelopes_and_legacy_objects_are_rejected():
    class AnchorSubclass(IntrinsicAnchorIR):
        pass

    transported = lower_r7_recurrence(Silence())
    hostile = (
        AnchorSubclass(),
        transported,
        transported.receipt,
        VamObject("IntrinsicAnchorIR", {"tag": "anchor"}),
        {"tag": "anchor"},
    )
    for value in hostile:
        with pytest.raises(IntrinsicCodecError) as caught:
            encode_intrinsic_frame(value)
        assert caught.value.kind == "payload"
