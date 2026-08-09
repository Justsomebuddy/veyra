import json
import struct
import zlib

import pytest

from vam.src.bytecode import MAGIC, VERSION, VamBytecodeError, decode_vmbc, encode_vmbc
from vam.src.errors import ERROR_PROFILE, TAXONOMY, boundary_error_row, error_row, obstruction_error_row
from vam.src.interpreter import execute
from vam.src.model import Instruction, VamExecutionError


def _frame(payload: bytes, *, magic: bytes = MAGIC, version: int = VERSION, size: int | None = None) -> bytes:
    declared = len(payload) if size is None else size
    checksum = zlib.crc32(payload) & 0xFFFFFFFF
    return struct.pack(">4sHII", magic, version, declared, checksum) + payload


def _assert_json_row(row: dict, category: str, kind: str) -> None:
    assert set(row) == {"profile", "category", "kind", "code", "source", "message"}
    assert row["profile"] == ERROR_PROFILE
    assert row["category"] == category
    assert row["kind"] == kind
    assert row["code"] == f"{category}.{kind}"
    assert isinstance(row["source"], str)
    assert isinstance(row["message"], str)
    assert json.loads(json.dumps(row, sort_keys=True, separators=(",", ":"))) == row


@pytest.mark.parametrize(
    ("blob", "category", "kind"),
    (
        (b"VAM", "frame", "short_frame"),
        (b"NOPE" + encode_vmbc([Instruction("REZ", ("%r1", "phase"), 1)])[4:], "frame", "magic"),
        (_frame(b"[]", version=VERSION + 1), "frame", "version"),
        (_frame(b"[]", size=3), "frame", "length"),
        (encode_vmbc([Instruction("REZ", ("%r1", "phase"), 1)])[:-1] + b"x", "frame", "crc32"),
        (_frame(b"\xff"), "decode", "payload"),
        (_frame(b"{}"), "decode", "payload_shape"),
        (_frame(b'[{"op":"REZ"}]'), "decode", "instruction_row"),
        (_frame(b'[{"op":"REZ","args":[{"t":"reg","v":-1}]}]'), "decode", "argument_item"),
    ),
)
def test_bytecode_exception_messages_map_to_stable_rows(blob, category, kind):
    with pytest.raises(VamBytecodeError) as caught:
        decode_vmbc(blob)

    row = error_row(caught.value, source="bytecode")

    _assert_json_row(row, category, kind)
    assert row["source"] == "bytecode"


def test_bytecode_encode_argument_type_boundary_maps_to_stable_row():
    with pytest.raises(VamBytecodeError) as caught:
        encode_vmbc([Instruction("REZ", ("%r1", 1.5), 1)])

    row = error_row(caught.value, source="bytecode")

    _assert_json_row(row, "boundary", "argument_type")


@pytest.mark.parametrize(
    ("program", "kind"),
    (
        ([Instruction("REZ", ("not-a-register", "phase"), 7)], "destination_register"),
        ([Instruction("BOGUS", ("%r1",), 8)], "unsupported_instruction"),
        ([Instruction("REZ", ("%r1", "phase", "extra"), 9)], "unsupported_instruction"),
    ),
)
def test_interpreter_execution_exceptions_map_without_changing_semantics(program, kind):
    with pytest.raises(VamExecutionError) as caught:
        execute(program)

    row = error_row(caught.value, source="interpreter")

    _assert_json_row(row, "execution", kind)
    assert row["source"] == "interpreter"


def test_boundary_helpers_and_taxonomy_are_json_serializable():
    assert set(TAXONOMY) == {"frame", "decode", "execution", "boundary"}
    assert json.loads(json.dumps(TAXONOMY, sort_keys=True)) == TAXONOMY
    assert "native_boundary" in TAXONOMY["boundary"]
    native = boundary_error_row("native-boundary", "native process rejected VAM0", source="native")
    obstruction = obstruction_error_row("observe-requires-observer")
    unknown = error_row("unrecognized host boundary failure", source="host")

    _assert_json_row(native, "boundary", "native_boundary")
    _assert_json_row(obstruction, "boundary", "obstruction")
    _assert_json_row(unknown, "boundary", "unknown")
