from __future__ import annotations

import struct
import zlib

import pytest

from vam.src.model import Instruction
from vam.src.opcodes import Arity, OpcodeSpec, OPCODES_BY_CODE, get_opcode as real_get_opcode

_dense = pytest.importorskip("vam.src.dense")
DenseBytecodeError = _dense.DenseBytecodeError
DENSE_MAGIC = _dense.DENSE_MAGIC
encode_dense = _dense.encode_dense
decode_dense = _dense.decode_dense


HEADER = struct.Struct(">4sHII")
VERSION = 1


def comparable(program):
    return [inst.comparable() for inst in program]


def reg(n: int) -> str:
    return f"%r{n}"


def wire_arg(arg):
    if isinstance(arg, int):
        return 2, struct.pack(">q", arg)
    if isinstance(arg, str) and arg.startswith("%r") and arg[2:].isdigit():
        return 1, struct.pack(">H", int(arg[2:]))
    if isinstance(arg, str):
        data = arg.encode("utf-8")
        return 3, struct.pack(">H", len(data)) + data
    raise TypeError(f"unsupported test argument: {arg!r}")


def pack_instruction(opcode: int, line: int, args: tuple[object, ...]) -> bytes:
    payload = bytearray(struct.pack(">BI", opcode, line))
    payload += struct.pack(">B", len(args))
    for arg in args:
        tag, body = wire_arg(arg)
        payload += struct.pack(">B", tag) + body
    return bytes(payload)


def pack_payload(rows: list[tuple[int, int, tuple[object, ...]]], *, count: int | None = None, suffix: bytes = b"") -> bytes:
    payload = bytearray(struct.pack(">H", len(rows) if count is None else count))
    for opcode, line, args in rows:
        payload += pack_instruction(opcode, line, args)
    payload += suffix
    return bytes(payload)


def pack_frame(payload: bytes, *, magic: bytes = DENSE_MAGIC, version: int = VERSION) -> bytes:
    checksum = zlib.crc32(payload) & 0xFFFFFFFF
    return HEADER.pack(magic, version, len(payload), checksum) + payload


def dense_frame(rows: list[tuple[int, int, tuple[object, ...]]], *, count: int | None = None, suffix: bytes = b"") -> bytes:
    return pack_frame(pack_payload(rows, count=count, suffix=suffix))


def literal_opcode() -> OpcodeSpec:
    return OpcodeSpec("LIT", 0x42, Arity(3, 3), ("dest_reg", "literal", "label"))


def small_programs():
    return (
        (
            Instruction("REZ", (reg(1), "λ-phase"), 1),
            Instruction("OBSERVER", (reg(2), "length"), 2),
            Instruction("CERT", (reg(3), "finite-claim", reg(1), "⊢"), 3),
        ),
        (
            Instruction("REZ", (reg(1), "phase"), 1),
            Instruction("NOD", (reg(2), reg(1), "left"), 2),
            Instruction("TACT", (reg(3), reg(1), reg(2), "right"), 3),
            Instruction("BREATH", (reg(4), reg(3)), 4),
            Instruction("MODE", (reg(5), reg(4)), 5),
            Instruction("OBSERVE", (reg(6), reg(5), reg(2)), 6),
        ),
        (
            Instruction("REZ", (reg(1), "phase"), 1),
            Instruction("NOD", (reg(2), reg(1), "a"), 2),
            Instruction("TACT", (reg(3), reg(1), reg(2), "b"), 3),
            Instruction("BREATH", (reg(4), reg(3)), 4),
            Instruction("MODE", (reg(5), reg(4)), 5),
            Instruction("OBSERVER", (reg(6), "trace"), 6),
            Instruction("OBSERVE", (reg(7), reg(6), reg(5)), 7),
            Instruction("COMPRESS", (reg(8), reg(7), reg(5)), 8),
            Instruction("OBSTRUCT", (reg(9), "manual-obstruction", reg(8)), 9),
            Instruction("ECHO", (reg(10), reg(5), reg(8), reg(7)), 10),
        ),
    )


@pytest.mark.parametrize("program", small_programs())
def test_dense_round_trip_preserves_current_instruction_ir(program):
    encoded = encode_dense(program)
    decoded = decode_dense(encoded)

    assert encoded.startswith(DENSE_MAGIC)
    assert comparable(decoded) == comparable(program)
    assert decoded is not program


@pytest.mark.parametrize(
    ("rows", "expected"),
    (
        (
            [(0x01, 1, (reg(0), "zero"))],
            [("REZ", (reg(0), "zero"))],
        ),
        (
            [(0x01, 1, (reg(65535), "max"))],
            [("REZ", (reg(65535), "max"))],
        ),
    ),
)
def test_dense_register_tag_boundaries_round_trip(rows, expected):
    decoded = decode_dense(dense_frame(rows))

    assert comparable(decoded) == expected


def test_dense_rejects_registers_outside_u16_boundary():
    with pytest.raises(DenseBytecodeError, match="out of range"):
        encode_dense([Instruction("REZ", (reg(65536), "phase"), 1)])


@pytest.mark.parametrize("value", (-(2**63), (2**63) - 1))
def test_dense_int_tag_boundaries_round_trip(monkeypatch, value):
    spec = literal_opcode()
    monkeypatch.setattr(_dense, "get_opcode", lambda op: spec if op == spec.name else real_get_opcode(op))
    monkeypatch.setattr(_dense, "OPCODES_BY_CODE", {**OPCODES_BY_CODE, spec.code: spec})

    encoded = encode_dense([Instruction(spec.name, (reg(1), value, "phase"), 1)])
    decoded = decode_dense(encoded)

    assert comparable(decoded) == [(spec.name, (reg(1), value, "phase"))]


@pytest.mark.parametrize("text", ("", "λ", "🧪 unicode boundary"))
def test_dense_string_tag_handles_unicode(text):
    decoded = decode_dense(dense_frame([(0x01, 1, (reg(1), text))]))

    assert comparable(decoded) == [("REZ", (reg(1), text))]


@pytest.mark.parametrize(
    ("blob", "message"),
    (
        (
            dense_frame([(0xFF, 1, ())]),
            "unknown opcode",
        ),
        (
            pack_frame(
                b"\x00\x01"
                + struct.pack(">BI", 0x01, 1)
                + b"\x01\x63",
            ),
            "invalid argument tag",
        ),
    ),
)
def test_dense_rejects_known_bad_frames(blob, message):
    with pytest.raises(DenseBytecodeError, match=message):
        decode_dense(blob)


@pytest.mark.parametrize(
    ("blob", "message"),
    (
        (
            pack_frame(pack_payload([(0x01, 1, (reg(1), "phase"))], suffix=b"\x63")),
            "length mismatch",
        ),
        (
            pack_frame(pack_payload([(0x01, 1, (reg(1), "phase"))], count=2)),
            "truncated",
        ),
        (
            pack_frame(pack_payload([(0x01, 1, (reg(1), "phase"))], suffix=b"\x00\x01")),
            "length mismatch",
        ),
    ),
)
def test_dense_rejects_tag_count_and_trailing_byte_errors(blob, message):
    with pytest.raises(DenseBytecodeError, match=message):
        decode_dense(blob)


@pytest.mark.parametrize(
    ("blob", "message"),
    (
        (
            pack_frame(
                b"\x00\x01"
                + struct.pack(">BI", 0x01, 1)
                + b"\x02"
                + b"\x01\x00\x01"
                + b"\x03\x00\x05he",
            ),
            "truncated string",
        ),
    ),
)
def test_dense_rejects_truncated_string(blob, message):
    with pytest.raises(DenseBytecodeError, match=message):
        decode_dense(blob)
