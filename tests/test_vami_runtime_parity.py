"""R12.4 structural-runtime parity and legacy noninterference pins."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zlib

import pytest

import vam.src as legacy_vam
from vam.intrinsic import (
    INTRINSIC_PROFILE,
    IntrinsicCodecError,
    canonical_intrinsic_report_json,
    encode_intrinsic_frame,
    inspect_intrinsic_frame,
    intrinsic_error_data,
)
from vam.src.assembly import parse_vmasm
from vam.src.bytecode import MAGIC, VERSION, VamBytecodeError, encode_vmbc
from vam.src.dense import DENSE_MAGIC, DENSE_VERSION, encode_dense
from vam.src.interpreter import execute
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
from vam.src.model import Instruction
from vam.src.opcodes import opcode_rows
from vam.src.report import PROFILE, canonical_report

ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / "vam/native/Cargo.toml"
HEADER = struct.Struct(">4sHII")


def _obstruction() -> IntrinsicObstructionIR:
    return IntrinsicObstructionIR(
        IntrinsicObstructionCodeIR.TAIL_OF_SILENCE,
        (IntrinsicPathStepIR.APPLY_TAIL,),
    )


def _corpus() -> tuple[object, ...]:
    recurrence = IntrinsicRecurrenceIR((IntrinsicTactIR(),), None)
    recurrence_value = IntrinsicRecurrenceValueIR(recurrence)
    silent = IntrinsicMarkValueIR(IntrinsicMarkIR.SILENT)
    pulse = IntrinsicMarkValueIR(IntrinsicMarkIR.PULSE)
    pair = IntrinsicPairValueIR(recurrence_value, pulse)
    obstruction = _obstruction()
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


def _frame(payload: bytes) -> bytes:
    return HEADER.pack(b"VAMI", 1, len(payload), zlib.crc32(payload) & 0xFFFFFFFF) + payload


@pytest.fixture(scope="module")
def vami_inspect() -> Path:
    cargo = shutil.which("cargo") or str(Path.home() / ".cargo/bin/cargo")
    if not Path(cargo).is_file():
        pytest.fail("cargo is required for Python/Rust VAMI parity")
    completed = subprocess.run(
        (cargo, "build", "--quiet", "--manifest-path", str(MANIFEST), "--bin", "vami-inspect"),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    binary = MANIFEST.parent / "target" / "debug" / (
        "vami-inspect.exe" if sys.platform == "win32" else "vami-inspect"
    )
    assert binary.is_file()
    return binary


def _rust_report(binary: Path, frame: bytes, tmp_path: Path) -> dict[str, object]:
    path = tmp_path / f"{sha256(frame).hexdigest()}.vami"
    path.write_bytes(frame)
    completed = subprocess.run(
        (str(binary), str(path)),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.count("\n") == 1
    return json.loads(completed.stdout)


@pytest.mark.parametrize("value", _corpus(), ids=lambda value: type(value).__name__)
def test_python_and_rust_parsed_json_are_equal_for_all_tags(
    vami_inspect: Path, tmp_path: Path, value: object
):
    frame = encode_intrinsic_frame(value)
    python_report = inspect_intrinsic_frame(frame)
    rust_report = _rust_report(vami_inspect, frame, tmp_path)
    assert rust_report == python_report
    execution = python_report["execution"]
    assert type(execution) is dict
    assert execution["evidence_accepted"] is False
    assert execution["promotion_ready"] is False
    assert execution["taxonomy_changed"] is False


def test_runtime_statuses_are_structural_and_canonical_json_is_deterministic():
    frames = [encode_intrinsic_frame(value) for value in _corpus()]
    reports = [inspect_intrinsic_frame(frame) for frame in frames]
    assert [report["execution"]["status"] for report in reports] == [
        "decoded",
        "decoded",
        "decoded",
        "decoded",
        "decoded",
        "decoded",
        "decoded",
        "decoded",
        "ready",
        "blocked",
        "ready",
        "mismatch",
        "blocked",
    ]
    for frame, report in zip(frames, reports, strict=True):
        encoded = canonical_intrinsic_report_json(frame)
        assert encoded == canonical_intrinsic_report_json(frame)
        assert json.loads(encoded) == report
        assert '"evidence_accepted":false' in encoded
        assert '"promotion_ready":false' in encoded
        assert '"taxonomy_changed":false' in encoded


@pytest.mark.parametrize(
    "frame",
    (
        b"VAMI",
        HEADER.pack(b"NOPE", 1, 1, zlib.crc32(b"\x01") & 0xFFFFFFFF) + b"\x01",
        HEADER.pack(b"VAMI", 2, 1, zlib.crc32(b"\x01") & 0xFFFFFFFF) + b"\x01",
        HEADER.pack(b"VAMI", 1, 1, zlib.crc32(b"\x63") & 0xFFFFFFFF) + b"\x63",
        _frame(b"\x0a\x00\x01\x08\x00\x00\x02\x00\x02\x00"),
        _frame(b"\x0c\x06\x00\x06\x00\x00"),
        _frame(b"\x09\x08\x00\x00\x02\x00\x02"),
        _frame(b"\x09\x0c\x06\x00\x06\x00"),
    ),
)
def test_python_and_rust_error_json_are_equal(
    vami_inspect: Path, tmp_path: Path, frame: bytes
):
    with pytest.raises(IntrinsicCodecError) as caught:
        inspect_intrinsic_frame(frame)
    python_report = intrinsic_error_data(caught.value)
    assert _rust_report(vami_inspect, frame, tmp_path) == python_report
    assert json.loads(canonical_intrinsic_report_json(caught.value)) == python_report


def test_canonical_serializer_recomputes_and_rejects_report_dict_forgery():
    frame = encode_intrinsic_frame(IntrinsicAnchorIR())
    report = inspect_intrinsic_frame(frame)
    report["execution"]["evidence_accepted"] = True
    with pytest.raises(TypeError, match="exact VAMI bytes or IntrinsicCodecError"):
        canonical_intrinsic_report_json(report)
    assert json.loads(canonical_intrinsic_report_json(frame))["execution"]["evidence_accepted"] is False


def test_python_and_rust_exact_resource_boundaries(vami_inspect: Path, tmp_path: Path):
    tail = IntrinsicPathStepIR.APPLY_TAIL
    left_step = IntrinsicPathStepIR.PAIR_LEFT
    longest = IntrinsicObstructionIR(
        IntrinsicObstructionCodeIR.TAIL_OF_SILENCE,
        (left_step,) * 127 + (tail,),
    )
    left = IntrinsicRecurrenceValueIR(IntrinsicRecurrenceIR((IntrinsicTactIR(),) * 2047, None))
    right = IntrinsicRecurrenceValueIR(IntrinsicRecurrenceIR((IntrinsicTactIR(),) * 2044, None))
    paths = tuple(
        IntrinsicObstructionIR(
            IntrinsicObstructionCodeIR.TAIL_OF_SILENCE,
            tuple(IntrinsicPathStepIR.PAIR_RIGHT if index >> bit & 1 else left_step for bit in range(11)) + (tail,),
        )
        for index in range(2048)
    )
    for value in (longest, IntrinsicPairValueIR(left, right), IntrinsicBlockedIR(paths)):
        frame = encode_intrinsic_frame(value)
        assert _rust_report(vami_inspect, frame, tmp_path) == inspect_intrinsic_frame(frame)
    for payload in (
        b"\x07\x05\x03\x07\xff\x00\x05\x03\x07\xfd\x00",
        b"\x08\x00\x00\x81" + b"\x02" * 128 + b"\x00",
        b"\x0a\x08\x01",
    ):
        frame = _frame(payload)
        with pytest.raises(IntrinsicCodecError) as caught:
            inspect_intrinsic_frame(frame)
        assert _rust_report(vami_inspect, frame, tmp_path) == intrinsic_error_data(caught.value)


def test_native_cli_reads_at_most_one_bounded_frame(vami_inspect: Path, tmp_path: Path):
    oversized = b"VAMI" + b"\x00" * (14 + 1024 * 1024)
    report = _rust_report(vami_inspect, oversized, tmp_path)
    assert report["error"] == {
        "kind": "resource",
        "message": "VAMI file exceeds bounded frame size",
    }


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def test_vami_import_leaves_legacy_wire_and_report_digests_byte_exact():
    program = parse_vmasm((ROOT / "vam/examples/minimal_echo.vmasm").read_text())
    vam0 = encode_vmbc(program)
    vamd = encode_dense(program)
    report = _canonical_bytes(canonical_report(program, execute(program)))
    opcodes = _canonical_bytes(opcode_rows())
    assert (MAGIC, VERSION, DENSE_MAGIC, DENSE_VERSION, PROFILE) == (
        b"VAM0",
        1,
        b"VAMD",
        1,
        "vam0-ref-v1",
    )
    assert (len(vam0), sha256(vam0).hexdigest()) == (
        1128,
        "8b641b5eb56899653f5548d8a0d5ec9f6c9b7015c4691fedc19b79e51d597143",
    )
    assert (len(vamd), sha256(vamd).hexdigest()) == (
        255,
        "a93930bb32ef8b3af293a3fded78944b96025858c483b66bc66719171dbdf923",
    )
    assert sha256(report).hexdigest() == "0039f902437451fc65b27b34876265d251ce10067b3af57c8bfdfe2115f76e89"
    assert sha256(opcodes).hexdigest() == "ba43dc501b704d6435b5945d7f8ede6e5d419a52e537d2f71d5f11e6255da470"


def test_vami_types_and_profile_do_not_leak_into_legacy_protocol():
    assert INTRINSIC_PROFILE == "veyra.vami.intrinsic-r12.4.v1"
    assert MAGIC == b"VAM0"
    assert encode_intrinsic_frame(IntrinsicAnchorIR())[:4] == b"VAMI"
    assert "IntrinsicAnchorIR" not in legacy_vam.__all__
    with pytest.raises(VamBytecodeError, match="unsupported argument type"):
        encode_vmbc([Instruction("REZ", ("%r0", IntrinsicAnchorIR()), 1)])
