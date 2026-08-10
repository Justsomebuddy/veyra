import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from vam.src import encode_vmbc
from vam.src.model import Instruction


ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "vam" / "native"
NATIVE_BIN = NATIVE / "target" / "debug" / (
    "vam0-inspect.exe" if sys.platform == "win32" else "vam0-inspect"
)


def native_command(*args: str) -> list[str]:
    cargo = shutil.which("cargo")
    if cargo is None:
        fallback = Path.home() / ".cargo" / "bin" / "cargo"
        cargo = str(fallback) if fallback.exists() else None
    if cargo is not None:
        return [cargo, "run", "--quiet", "--manifest-path", str(NATIVE / "Cargo.toml"), "--", *args]
    if NATIVE_BIN.exists() and os.access(NATIVE_BIN, os.X_OK):
        return [str(NATIVE_BIN), *args]
    pytest.skip("native executable/cargo unavailable")


def run_native_blob(blob: bytes, tmp_path: Path, name: str = "sample.vam0", *cli_args: str):
    sample = tmp_path / name
    sample.write_bytes(blob)
    result = subprocess.run(
        native_command(*cli_args, str(sample)),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.stdout.strip(), result.stderr
    return result, json.loads(result.stdout)


def assert_top_level_error_shape(report: dict, *, kind: str, message: str) -> None:
    assert set(report) == {"ok", "profile", "error"}
    assert report["ok"] is False
    assert report["profile"] == "vam0-ref-v1"
    assert set(report["error"]) == {"kind", "message"}
    assert report["error"] == {"kind": kind, "message": message}


def assert_ok_true_execution_error_shape(
    report: dict,
    *,
    kind: str = "execution",
    message: str,
) -> None:
    assert set(report) == {
        "ok",
        "profile",
        "frame",
        "instruction_count",
        "ops",
        "instructions",
        "execution_error",
    }
    assert report["ok"] is True
    assert report["profile"] == "vam0-ref-v1"
    assert set(report["frame"]) == {"magic", "version", "size", "crc32"}
    assert report["frame"]["magic"] == "VAM0"
    assert report["frame"]["version"] == 1
    assert isinstance(report["frame"]["size"], int)
    assert isinstance(report["frame"]["crc32"], str)
    assert len(report["frame"]["crc32"]) == 8
    assert set(report["execution_error"]) == {"kind", "message"}
    assert report["execution_error"] == {"kind": kind, "message": message}
    assert "error" not in report
    assert "pc" not in report
    assert "registers" not in report
    assert "trace" not in report
    assert "certs" not in report
    assert "obstructions" not in report


def test_native_unsupported_profile_is_top_level_ok_false_profile_error_with_fixed_profile_field(tmp_path):
    blob = encode_vmbc([])

    result, report = run_native_blob(blob, tmp_path, "empty.vam0", "--profile", "not-a-profile")

    assert result.returncode != 0
    assert_top_level_error_shape(
        report,
        kind="profile",
        message="unsupported profile: not-a-profile",
    )


def test_native_decoded_unsupported_op_is_ok_true_with_execution_error_not_top_level_error(tmp_path):
    blob = encode_vmbc([Instruction("NOPE", ("%r1",), line=41)])

    result, report = run_native_blob(blob, tmp_path, "unsupported-op.vam0")

    assert result.returncode == 0, result.stderr + result.stdout
    assert report["instruction_count"] == 1
    assert report["ops"] == ["NOPE"]
    assert report["instructions"][0]["op"] == "NOPE"
    assert report["instructions"][0]["argc"] == 1
    assert_ok_true_execution_error_shape(
        report,
        message="unsupported or malformed instruction: NOPE/1",
    )


def test_native_decoded_non_register_destination_is_ok_true_with_execution_error_not_top_level_error(tmp_path):
    blob = encode_vmbc([Instruction("REZ", ("not-a-register", "root"), line=7)])

    result, report = run_native_blob(blob, tmp_path, "bad-dst.vam0")

    assert result.returncode == 0, result.stderr + result.stdout
    assert report["instruction_count"] == 1
    assert report["ops"] == ["REZ"]
    assert report["instructions"][0]["args"][0] == {"t": "str", "v": "not-a-register"}
    assert_ok_true_execution_error_shape(
        report,
        message="line 7: first operand must be destination register",
    )


def test_native_decoded_bad_arity_is_ok_true_with_execution_error_not_top_level_error(tmp_path):
    blob = encode_vmbc([Instruction("REZ", ("%r1", "root", "extra"), line=13)])

    result, report = run_native_blob(blob, tmp_path, "bad-arity.vam0")

    assert result.returncode == 0, result.stderr + result.stdout
    assert report["instruction_count"] == 1
    assert report["ops"] == ["REZ"]
    assert report["instructions"][0]["argc"] == 3
    assert_ok_true_execution_error_shape(
        report,
        message="unsupported or malformed instruction: REZ/3",
    )
