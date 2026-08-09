import json
import struct
import zlib

import pytest

from vam.src.bytecode import MAGIC, VERSION, VamBytecodeError, decode_vmbc, encode_vmbc
from vam.src.fixtures import (
    fixture_program,
    fixture_report,
    fixture_report_program,
    iter_fixture_programs,
    iter_fixture_report_programs,
    iter_fixture_reports,
    iter_valid_vam0_fixture_report_programs,
)
from vam.src.model import Instruction


def comparable(program):
    return [inst.comparable() for inst in program]


def test_vam_fixture_programs_are_unique_and_cover_at_least_four_cases():
    fixtures = tuple(iter_fixture_programs())
    names = [name for name, _ in fixtures]
    programs = [program for _, program in fixtures]

    assert len(fixtures) >= 4
    assert len(names) == len(set(names))
    assert len({tuple(comparable(program)) for program in programs}) == len(programs)
    assert sum(1 for op, _ in comparable(fixture_program("optimizer-duplicate-compress")) if op == "COMPRESS") == 2


def test_vam_fixture_reports_are_json_serializable():
    reports = tuple(iter_fixture_reports())

    assert len(reports) >= 4
    for name, report in reports:
        dumped = json.dumps(report, sort_keys=True)
        assert dumped.startswith("{")
        assert report["profile"] == "vam0-ref-v1"


def test_vam_fixture_reports_capture_current_semantics_spot_checks():
    minimal = fixture_report("minimal-accepted-echo-cert")
    bad = fixture_report("bad-breath-nod-obstruction")
    shell = fixture_report("shell-lowering")
    optimized = fixture_report("optimizer-duplicate-compress")

    assert minimal["certs"][0]["data"]["accepted"] is True
    assert bad["obstructions"][0]["kind"] == "Obstruction"
    assert bad["certs"] == []
    assert shell["certs"] == []
    assert shell["instructions"][0]["op"] == "REZ"
    assert len(optimized["instructions"]) == len(fixture_program("optimizer-duplicate-compress")) - 1
    assert len(fixture_report_program("optimizer-duplicate-compress")) == len(optimized["instructions"])
    assert len(tuple(iter_fixture_report_programs())) == len(tuple(iter_fixture_programs()))


def test_vam_fixture_reports_cover_current_obstruction_surfaces():
    expected = {
        "obstruction-nod-requires-rez": "nod-requires-rez",
        "obstruction-tact-left": "tact-left",
        "obstruction-tact-right": "tact-right",
        "obstruction-breath-requires-tacts": "breath-requires-tacts",
        "obstruction-mode-requires-breath": "mode-requires-breath",
        "obstruction-observe-requires-observer": "observe-requires-observer",
        "obstruction-explicit-manual": "manual-obstruction",
        "obstruction-missing-register-witness": "missing-register",
    }

    for name, claim in expected.items():
        report = fixture_report(name)
        assert report["obstructions"][0]["data"]["claim"] == claim, name

    missing = fixture_report("obstruction-missing-register-witness")
    assert missing["obstructions"][0]["data"]["witness"]["claim"] == "missing-register"

    compressed = fixture_report("obstruction-compress-nested-shadow")
    shadow = compressed["registers"]["%r2"]["data"]["shadow"]
    assert compressed["obstructions"] == []
    assert shadow["kind"] == "Obstruction"
    assert shadow["data"]["claim"] == "observe-requires-observer"

    blocked = fixture_report("shell-blocked-child-obstruction")
    unsupported = fixture_report("shell-unsupported-child-obstruction")
    assert blocked["obstructions"][0]["data"]["claim"].startswith("shell.blocked:")
    assert unsupported["obstructions"][0]["data"]["claim"] == "shell.unsupported_child"


def test_valid_vam0_fixture_report_iterator_filters_only_valid_payloads():
    valid_names = [name for name, _ in iter_valid_vam0_fixture_report_programs()]
    all_names = [name for name, _ in iter_fixture_report_programs()]

    assert valid_names == all_names


def _frame(payload: bytes, *, magic: bytes = MAGIC, version: int = VERSION, size: int | None = None) -> bytes:
    declared = len(payload) if size is None else size
    checksum = zlib.crc32(payload) & 0xFFFFFFFF
    return struct.pack(">4sHII", magic, version, declared, checksum) + payload


@pytest.mark.parametrize(
    ("blob", "message"),
    (
        (b"VAM", "short VAM0 frame"),
        (b"NOPE" + encode_vmbc([Instruction("REZ", ("%r1", "phase"))])[4:], "bad VAM0 magic"),
        (_frame(b"[]", version=VERSION + 1), "unsupported VAM0 version"),
        (_frame(b"[]", size=3), "VAM0 payload length mismatch"),
        (encode_vmbc([Instruction("REZ", ("%r1", "phase"))])[:-1] + b"x", "VAM0 checksum mismatch"),
        (_frame(b"\xff"), "bad VAM0 payload"),
        (_frame(b"{}"), "VAM0 payload must be a list"),
        (_frame(b'[{"op":"REZ"}]'), "bad instruction row"),
        (_frame(b'[{"op":"REZ","args":[{"t":"reg","v":-1}]}]'), "bad argument item"),
    ),
)
def test_malformed_vam0_frames_stop_at_python_decoder_boundary(blob, message):
    with pytest.raises(VamBytecodeError, match=message):
        decode_vmbc(blob)
