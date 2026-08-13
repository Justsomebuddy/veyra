from __future__ import annotations

import json
import shutil
import struct
import subprocess
import zlib
from collections.abc import Callable
from pathlib import Path

import pytest

from vam.src import encode_dense
from vam.src.model import Instruction

ROOT = Path(__file__).resolve().parents[1]
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


@pytest.fixture(scope="session")
def native_cli() -> str:
    """Build the vam0-inspect CLI once and return its executable path.

    Compiler warnings are emitted while the binary is built; invoking the
    built binary directly keeps every test's stderr assertion clean and
    avoids one cargo invocation per test.
    """
    build = subprocess.run(
        [cargo_bin(), "build", "--manifest-path", str(NATIVE / "Cargo.toml"), "--bin", "vam0-inspect"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert build.returncode == 0, build.stderr
    cli = NATIVE / "target" / "debug" / "vam0-inspect"
    assert cli.exists(), f"expected CLI binary at {cli}"
    return str(cli)


def run_native(blob: bytes, tmp_path: Path, cli: str) -> subprocess.CompletedProcess[str]:
    sample = tmp_path / "bad-frame.vamd"
    sample.write_bytes(blob)
    return subprocess.run(
        [cli, str(sample)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def assert_cli_error(
    result: subprocess.CompletedProcess[str],
    *,
    kind: str,
    message_contains: str | None = None,
) -> dict:
    assert result.returncode != 0, result.stdout + result.stderr
    assert result.stderr == ""
    body = json.loads(result.stdout)
    assert body["ok"] is False
    assert body["profile"] == "vam0-ref-v1"
    assert set(body["error"]) == {"kind", "message"}
    assert body["error"]["kind"] == kind
    if message_contains is not None:
        assert message_contains in body["error"]["message"]
    return body


def seed_frame() -> bytes:
    return encode_dense([Instruction("REZ", ("%r1", "phase"), 1)])


def with_header(blob: bytes, *, magic: bytes | None = None, version: int | None = None, length: int | None = None, crc: int | None = None) -> bytes:
    old_magic, old_version, old_length, old_crc = HEADER.unpack_from(blob, 0)
    payload = blob[HEADER.size :]
    return HEADER.pack(
        old_magic if magic is None else magic,
        old_version if version is None else version,
        old_length if length is None else length,
        old_crc if crc is None else crc,
    ) + payload


def with_payload(blob: bytes, mutate: Callable[[bytearray], None]) -> bytes:
    _, version, _, _ = HEADER.unpack_from(blob, 0)
    payload = bytearray(blob[HEADER.size :])
    mutate(payload)
    return HEADER.pack(b"VAMD", version, len(payload), zlib.crc32(payload) & 0xFFFFFFFF) + bytes(payload)


def unknown_opcode(blob: bytes) -> bytes:
    return with_payload(blob, lambda payload: payload.__setitem__(2, 0xFF))


def bad_argument_tag(blob: bytes) -> bytes:
    return with_payload(blob, lambda payload: payload.__setitem__(8, 0xEE))


def invalid_utf8_string(blob: bytes) -> bytes:
    return with_payload(blob, lambda payload: payload.__setitem__(14, 0xFF))


@pytest.mark.parametrize(
    ("name", "blob_factory", "kind", "message_marker"),
    [
        ("short_vamd_header", lambda blob: b"VAMD", "short_frame", "short VAMD frame"),
        ("bad_version", lambda blob: with_header(blob, version=2), "version", "unsupported VAMD version"),
        ("length_mismatch", lambda blob: with_header(blob, length=999), "length", "length mismatch"),
        ("crc_mismatch", lambda blob: with_header(blob, crc=0), "crc32", "checksum mismatch"),
        ("unknown_opcode", unknown_opcode, "opcode", "unknown VAMD opcode"),
        ("bad_argument_tag", bad_argument_tag, "payload", "bad VAMD payload"),
        ("invalid_utf8", invalid_utf8_string, "payload", "bad VAMD payload"),
        ("unknown_magic", lambda blob: with_header(blob, magic=b"NOPE"), "magic", "unsupported VAM frame magic"),
    ],
)
def test_native_vamd_cli_rejects_malformed_frames(name, blob_factory, kind, message_marker, tmp_path, native_cli):
    result = run_native(blob_factory(seed_frame()), tmp_path, native_cli)

    body = assert_cli_error(result, kind=kind, message_contains=message_marker)
    assert body["error"]["message"], name
