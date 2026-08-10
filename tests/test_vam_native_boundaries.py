import json
import os
import shutil
import struct
import subprocess
import sys
import zlib
from pathlib import Path

import pytest

from vam.src import encode_vmbc
from vam.src.model import Instruction


ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "vam" / "native"
NATIVE_BIN = NATIVE / "target" / "debug" / (
    "vam0-inspect.exe" if sys.platform == "win32" else "vam0-inspect"
)
HEADER = struct.Struct(">4sHII")


def native_command(path: Path) -> list[str]:
    if NATIVE_BIN.exists() and os.access(NATIVE_BIN, os.X_OK):
        return [str(NATIVE_BIN), str(path)]
    cargo = shutil.which("cargo")
    if cargo is None:
        fallback = Path.home() / ".cargo" / "bin" / "cargo"
        cargo = str(fallback) if fallback.exists() else None
    if cargo is None:
        pytest.skip("native executable/cargo unavailable")
    return [cargo, "run", "--quiet", "--manifest-path", str(NATIVE / "Cargo.toml"), "--", str(path)]


def run_native_blob(blob: bytes, tmp_path: Path, name: str = "sample.vam0"):
    sample = tmp_path / name
    sample.write_bytes(blob)
    result = subprocess.run(
        native_command(sample),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.stdout.strip(), result.stderr
    return result, json.loads(result.stdout)


def valid_blob() -> bytearray:
    return bytearray(encode_vmbc([Instruction("REZ", ("%r1", "root"), 1)]))


def framed_payload(payload: bytes, *, magic: bytes = b"VAM0", version: int = 1) -> bytes:
    checksum = zlib.crc32(payload) & 0xFFFFFFFF
    return HEADER.pack(magic, version, len(payload), checksum) + payload


def assert_error_shape(report: dict, kind: str) -> None:
    assert set(report) == {"ok", "profile", "error"}
    assert report["ok"] is False
    assert report["profile"] == "vam0-ref-v1"
    assert set(report["error"]) == {"kind", "message"}
    assert report["error"]["kind"] == kind
    assert isinstance(report["error"]["message"], str)
    assert report["error"]["message"]


@pytest.mark.parametrize(
    ("name", "blob", "kind"),
    [
        ("short_frame", b"VAM0\x00", "short_frame"),
        ("bad_magic", bytes(valid_blob()[:0] + b"NOPE" + valid_blob()[4:]), "magic"),
        (
            "bad_version",
            bytes(valid_blob()[:4] + (2).to_bytes(2, "big") + valid_blob()[6:]),
            "version",
        ),
        (
            "bad_length",
            bytes(valid_blob()[:6] + (999).to_bytes(4, "big") + valid_blob()[10:]),
            "length",
        ),
        ("bad_crc32", bytes(valid_blob()[:-1] + bytes([valid_blob()[-1] ^ 1])), "crc32"),
        ("bad_payload_json", framed_payload(b'{"not":"an instruction list"}'), "payload"),
    ],
)
def test_native_vam0_boundary_errors_are_json_rows(name, blob, kind, tmp_path):
    result, report = run_native_blob(blob, tmp_path, f"{name}.vam0")

    assert result.returncode != 0
    assert_error_shape(report, kind)


def test_native_success_report_exposes_stable_boundary_shape(tmp_path):
    result, report = run_native_blob(bytes(encode_vmbc([])), tmp_path, "empty.vam0")

    assert result.returncode == 0, result.stderr + result.stdout
    assert set(report) == {
        "ok",
        "profile",
        "frame",
        "instruction_count",
        "ops",
        "instructions",
        "pc",
        "registers",
        "trace",
        "certs",
        "obstructions",
    }
    assert report["ok"] is True
    assert report["profile"] == "vam0-ref-v1"
    assert report["frame"]["magic"] == "VAM0"
    assert report["frame"]["version"] == 1
    assert set(report["frame"]) == {"magic", "version", "size", "crc32"}
    assert isinstance(report["frame"]["size"], int)
    assert isinstance(report["frame"]["crc32"], str)
    assert len(report["frame"]["crc32"]) == 8
    assert report["instruction_count"] == 0
    assert report["ops"] == []
    assert report["instructions"] == []
    assert report["pc"] == 0
    assert report["registers"] == {}
    assert report["trace"] == []
    assert report["certs"] == []
    assert report["obstructions"] == []
