from __future__ import annotations

import json
import logging
import os
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
CARGO_TOOLCHAIN = "1.95.0"
COMMAND_TIMEOUT_SECONDS = 300

logger = logging.getLogger(__name__)


def cargo_bin() -> str:
    logger.debug("vamd_boundaries.cargo_bin entry")
    found = shutil.which("cargo")
    if found:
        logger.debug("vamd_boundaries.cargo_bin exit path=%s", found)
        return found
    fallback = Path.home() / ".cargo" / "bin" / "cargo"
    if fallback.exists():
        logger.debug("vamd_boundaries.cargo_bin exit fallback=%s", fallback)
        return str(fallback)
    logger.warning("vamd_boundaries.cargo_bin unavailable")
    pytest.skip("cargo/rust unavailable")


def cargo_command() -> tuple[str, str]:
    """Return the repository-pinned Cargo invocation."""
    logger.debug("vamd_boundaries.cargo_command entry")
    result = (cargo_bin(), f"+{CARGO_TOOLCHAIN}")
    logger.debug("vamd_boundaries.cargo_command exit toolchain=%s", CARGO_TOOLCHAIN)
    return result


def cargo_target_directory(
    command: tuple[str, str],
    *,
    environment: dict[str, str] | None = None,
) -> Path:
    """Ask Cargo for its effective absolute target directory."""
    logger.debug("vamd_boundaries.cargo_target_directory entry")
    try:
        metadata = subprocess.run(
            [
                *command,
                "metadata",
                "--locked",
                "--format-version",
                "1",
                "--no-deps",
                "--manifest-path",
                str(NATIVE / "Cargo.toml"),
            ],
            cwd=ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        logger.exception("vamd_boundaries.cargo_target_directory invocation failed")
        raise
    if metadata.returncode != 0:
        logger.error(
            "vamd_boundaries.cargo_target_directory metadata failed returncode=%d stderr=%s",
            metadata.returncode,
            metadata.stderr[-2000:],
        )
        raise AssertionError(metadata.stderr)
    try:
        payload = json.loads(metadata.stdout)
        raw_target = payload["target_directory"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        logger.error("vamd_boundaries.cargo_target_directory invalid metadata")
        raise AssertionError("cargo metadata omitted target_directory") from exc
    if type(raw_target) is not str or not raw_target:
        logger.error("vamd_boundaries.cargo_target_directory invalid target type")
        raise AssertionError("cargo metadata target_directory is invalid")
    candidate = Path(raw_target)
    if not candidate.is_absolute():
        logger.error("vamd_boundaries.cargo_target_directory target is relative path=%s", candidate)
        raise AssertionError("cargo metadata target_directory must be absolute")
    result = candidate.resolve()
    logger.debug("vamd_boundaries.cargo_target_directory exit path=%s", result)
    return result


def build_native_cli() -> Path:
    """Build vam0-inspect once and return Cargo's exact executable artifact."""
    logger.debug("vamd_boundaries.build_native_cli entry")
    command = cargo_command()
    target_directory = cargo_target_directory(command)
    try:
        build = subprocess.run(
            [
                *command,
                "build",
                "--locked",
                "--manifest-path",
                str(NATIVE / "Cargo.toml"),
                "--bin",
                "vam0-inspect",
                "--message-format=json-render-diagnostics",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        logger.exception("vamd_boundaries.build_native_cli invocation failed")
        raise
    if build.returncode != 0:
        logger.error(
            "vamd_boundaries.build_native_cli build failed returncode=%d stderr=%s",
            build.returncode,
            build.stderr[-4000:],
        )
        raise AssertionError(build.stderr)
    executable: Path | None = None
    for line in build.stdout.splitlines():
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            logger.error("vamd_boundaries.build_native_cli non-json Cargo output")
            raise AssertionError("Cargo emitted non-JSON build output") from exc
        if type(message) is not dict:
            logger.error("vamd_boundaries.build_native_cli non-object Cargo message")
            raise AssertionError("Cargo emitted a non-object build message")
        target = message.get("target")
        artifact = message.get("executable")
        if (
            message.get("reason") == "compiler-artifact"
            and type(target) is dict
            and target.get("name") == "vam0-inspect"
            and type(artifact) is str
        ):
            executable = Path(artifact).resolve()
    if executable is None or not executable.is_file():
        logger.error("vamd_boundaries.build_native_cli executable artifact missing")
        raise AssertionError("Cargo did not report a vam0-inspect executable artifact")
    try:
        executable.relative_to(target_directory)
    except ValueError as exc:
        logger.error(
            "vamd_boundaries.build_native_cli artifact escaped target directory artifact=%s target=%s",
            executable,
            target_directory,
        )
        raise AssertionError("Cargo executable escaped target_directory") from exc
    logger.debug("vamd_boundaries.build_native_cli exit path=%s", executable)
    return executable


@pytest.fixture(scope="session")
def native_cli() -> Path:
    logger.debug("vamd_boundaries.native_cli fixture entry")
    result = build_native_cli()
    logger.debug("vamd_boundaries.native_cli fixture exit path=%s", result)
    return result


def run_native(blob: bytes, tmp_path: Path, executable: Path) -> subprocess.CompletedProcess[str]:
    logger.debug("vamd_boundaries.run_native entry bytes=%d", len(blob))
    sample = tmp_path / "bad-frame.vamd"
    sample.write_bytes(blob)
    try:
        result = subprocess.run(
            [str(executable), str(sample)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        logger.exception("vamd_boundaries.run_native invocation failed")
        raise
    logger.debug("vamd_boundaries.run_native exit returncode=%d", result.returncode)
    return result


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


def test_cargo_metadata_honors_relative_external_target_directory(tmp_path):
    logger.debug("test_cargo_metadata_honors_relative_external_target_directory entry")
    external_target = tmp_path / "external-cargo-target"
    relative_target = os.path.relpath(external_target, ROOT)
    environment = os.environ.copy()
    environment["CARGO_TARGET_DIR"] = relative_target

    result = cargo_target_directory(cargo_command(), environment=environment)

    assert result == external_target.resolve()
    logger.debug("test_cargo_metadata_honors_relative_external_target_directory exit")


def test_build_native_cli_selects_locked_external_cargo_artifact(tmp_path, monkeypatch):
    logger.debug("test_build_native_cli_selects_locked_external_cargo_artifact entry")
    target_directory = (tmp_path / "external-target").resolve()
    executable = target_directory / "debug" / "vam0-inspect"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"test executable")
    calls: list[tuple[str, ...]] = []

    def fake_run(arguments, **_kwargs):
        logger.debug("fake Cargo run entry arguments=%r", arguments)
        call = tuple(arguments)
        calls.append(call)
        if "metadata" in call:
            stdout = json.dumps({"target_directory": str(target_directory)})
        elif "build" in call:
            stdout = json.dumps(
                {
                    "reason": "compiler-artifact",
                    "target": {"name": "vam0-inspect"},
                    "executable": str(executable),
                }
            )
        else:
            logger.error("fake Cargo run unexpected arguments=%r", arguments)
            raise AssertionError("unexpected Cargo command")
        result = subprocess.CompletedProcess(arguments, 0, stdout, "")
        logger.debug("fake Cargo run exit")
        return result

    monkeypatch.setattr(shutil, "which", lambda name: "/mock/cargo" if name == "cargo" else None)
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = build_native_cli()

    assert result == executable
    assert len(calls) == 2
    assert all(call[:2] == ("/mock/cargo", "+1.95.0") for call in calls)
    assert all("--locked" in call for call in calls)
    assert "--message-format=json-render-diagnostics" in calls[1]
    assert str(NATIVE / "target") not in " ".join(calls[1])
    logger.debug("test_build_native_cli_selects_locked_external_cargo_artifact exit")


@pytest.mark.parametrize("failure", ("escaped", "missing"))
def test_build_native_cli_rejects_untrusted_cargo_artifact(
    failure, tmp_path, monkeypatch,
):
    logger.debug("test_build_native_cli_rejects_untrusted_cargo_artifact entry failure=%s", failure)
    target_directory = (tmp_path / "external-target").resolve()
    target_directory.mkdir()
    executable = (
        (tmp_path / "escaped" / "vam0-inspect").resolve()
        if failure == "escaped"
        else target_directory / "debug" / "vam0-inspect"
    )
    if failure == "escaped":
        executable.parent.mkdir()
        executable.write_bytes(b"escaped executable")

    def fake_run(arguments, **_kwargs):
        logger.debug("hostile fake Cargo run entry arguments=%r", arguments)
        call = tuple(arguments)
        if "metadata" in call:
            stdout = json.dumps({"target_directory": str(target_directory)})
        elif "build" in call:
            stdout = json.dumps(
                {
                    "reason": "compiler-artifact",
                    "target": {"name": "vam0-inspect"},
                    "executable": str(executable),
                }
            )
        else:
            logger.error("hostile fake Cargo run unexpected arguments=%r", arguments)
            raise AssertionError("unexpected Cargo command")
        result = subprocess.CompletedProcess(arguments, 0, stdout, "")
        logger.debug("hostile fake Cargo run exit")
        return result

    monkeypatch.setattr(shutil, "which", lambda name: "/mock/cargo" if name == "cargo" else None)
    monkeypatch.setattr(subprocess, "run", fake_run)

    expected = (
        "Cargo executable escaped target_directory"
        if failure == "escaped"
        else "Cargo did not report a vam0-inspect executable artifact"
    )
    with pytest.raises(AssertionError, match=f"^{expected}$"):
        build_native_cli()
    logger.debug("test_build_native_cli_rejects_untrusted_cargo_artifact exit failure=%s", failure)


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
def test_native_vamd_cli_rejects_malformed_frames(
    name, blob_factory, kind, message_marker, tmp_path, native_cli,
):
    logger.debug("test_native_vamd_cli_rejects_malformed_frames entry case=%s", name)
    result = run_native(blob_factory(seed_frame()), tmp_path, native_cli)

    body = assert_cli_error(result, kind=kind, message_contains=message_marker)
    assert body["error"]["message"], name
    logger.debug("test_native_vamd_cli_rejects_malformed_frames exit case=%s", name)
