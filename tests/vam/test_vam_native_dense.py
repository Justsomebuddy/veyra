import os
import shutil
import struct
import subprocess
import zlib
from pathlib import Path

import pytest
from src.core.paths import PROJECT_ROOT


ROOT = PROJECT_ROOT
NATIVE = ROOT / "vam" / "native"
HEADER = struct.Struct(">4sHII")


def cargo_bin() -> str:
    found = shutil.which("cargo")
    if found:
        return found
    fallback = Path.home() / ".cargo" / "bin" / "cargo"
    if fallback.exists():
        return str(fallback)
    pytest.skip("cargo/rust unavailable")


def dense_arg(tag: int, value) -> bytes:
    if tag == 1:
        return struct.pack(">BH", tag, value)
    if tag == 2:
        return struct.pack(">Bq", tag, value)
    if tag == 3:
        raw = value.encode("utf-8")
        return struct.pack(">BH", tag, len(raw)) + raw
    raise ValueError(tag)


def dense_row(opcode: int, line: int, args: list[tuple[int, object]]) -> bytes:
    body = bytearray(struct.pack(">BI", opcode, line))
    body.append(len(args))
    for tag, value in args:
        body.extend(dense_arg(tag, value))
    return bytes(body)


def build_vamdense() -> bytes:
    payload = bytearray(struct.pack(">H", 3))
    payload.extend(dense_row(0x01, 12, [(1, 7), (3, "root")]))
    payload.extend(dense_row(0x03, 18, [(1, 7), (2, -5), (3, "edge")]))
    payload.extend(dense_row(0x0B, 21, [(3, "claim"), (1, 7), (3, "dense-boundary")]))
    payload = bytes(payload)
    checksum = zlib.crc32(payload) & 0xFFFFFFFF
    return HEADER.pack(b"VAMD", 1, len(payload), checksum) + payload


def run_dense_rust_test(blob: bytes, tmp_path: Path):
    sample = tmp_path / "sample.vamd"
    sample.write_bytes(blob)
    return subprocess.run(
        [
            cargo_bin(),
            "test",
            "--quiet",
            "--manifest-path",
            str(NATIVE / "Cargo.toml"),
            "inspect_vamdense_from_env_blob",
            "--",
            "--exact",
        ],
        env={**os.environ, "VAMD_BLOB_PATH": str(sample)},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_native_dense_scaffold_parses_python_built_vamdense(tmp_path):
    result = run_dense_rust_test(build_vamdense(), tmp_path)
    assert result.returncode == 0, result.stderr + result.stdout
