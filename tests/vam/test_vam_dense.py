from __future__ import annotations

from pathlib import Path
import struct
import zlib

import pytest

from vam.src import compile_source, parse_vmasm
from vam.src.bytecode import encode_vmbc
from vam.src.dense import DENSE_MAGIC, DENSE_VERSION, DenseBytecodeError, decode_dense, dense_round_trip, encode_dense
from vam.src.model import Instruction
from src.core.paths import PROJECT_ROOT


ROOT = PROJECT_ROOT


def _read_example(name: str):
    return parse_vmasm((ROOT / "vam" / "examples" / name).read_text())


def _core_echo_source() -> str:
    return "echo(mode(breath(tact(nod:a,nod:b),tact(nod:b,nod:a))),mode(breath(tact(nod:b,nod:a),tact(nod:a,nod:b))),observer:length)"


def _retag_opcode(blob: bytes, opcode_code: int) -> bytes:
    header = struct.Struct(">4sHII")
    data = bytearray(blob)
    payload = bytearray(data[header.size :])
    payload[2] = opcode_code
    data[header.size :] = payload
    data[10:14] = struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)
    return bytes(data)


def test_dense_round_trip_minimal_echo_and_compactness() -> None:
    program = _read_example("minimal_echo.vmasm")
    dense_blob = encode_dense(program)

    assert dense_blob.startswith(DENSE_MAGIC)
    assert int.from_bytes(dense_blob[4:6], "big") == DENSE_VERSION
    assert len(dense_blob) < len(encode_vmbc(program))
    assert decode_dense(dense_blob) == program
    assert dense_round_trip(program) == program


def test_dense_round_trip_compiled_core_echo() -> None:
    program = compile_source(_core_echo_source()).program

    assert dense_round_trip(program) == list(program)


@pytest.mark.parametrize(
    ("program", "marker"),
    [
        ([Instruction("REZ", ("not-a-register", "phase"), 1)], "register"),
        ([Instruction("REZ", ("%r1", "%r2"), 1)], "string"),
        ([Instruction("BREATH", ("%r1",), 2)], "arity"),
    ],
)
def test_dense_encode_validation_rejects_bad_operands(program, marker: str) -> None:
    with pytest.raises(DenseBytecodeError, match=marker):
        encode_dense(program)


@pytest.mark.parametrize(
    ("mutator", "marker"),
    [
        (lambda blob: b"NOPE" + blob[4:], "magic"),
        (lambda blob: blob[:-1], "truncated"),
        (lambda blob: blob[:-1] + bytes([blob[-1] ^ 0x01]), "checksum"),
        (lambda blob: _retag_opcode(blob, 0xFF), "opcode"),
    ],
)
def test_dense_decode_rejects_frame_corruption(mutator, marker: str) -> None:
    blob = encode_dense([Instruction("REZ", ("%r1", "phase"), 1)])

    with pytest.raises(DenseBytecodeError, match=marker):
        decode_dense(mutator(blob))
