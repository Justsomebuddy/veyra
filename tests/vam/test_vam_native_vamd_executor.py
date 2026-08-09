import json
import shutil
import subprocess
from pathlib import Path

import pytest

from vam.src import canonical_report, decode_dense, encode_dense, encode_vmbc, execute
from vam.src.fixtures import iter_valid_vam0_fixture_report_programs
from vam.src.model import Instruction
from src.core.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT
NATIVE = ROOT / "vam" / "native"


def cargo_bin():
    found = shutil.which("cargo")
    if found:
        return found
    fallback = Path.home() / ".cargo" / "bin" / "cargo"
    if fallback.exists():
        return str(fallback)
    pytest.skip("cargo/rust unavailable")


def run_native(blob: bytes, tmp_path: Path, suffix: str = ".vamd"):
    sample = tmp_path / f"sample{suffix}"
    sample.write_bytes(blob)
    return subprocess.run(
        [cargo_bin(), "run", "--quiet", "--manifest-path", str(NATIVE / "Cargo.toml"), "--", str(sample)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def native_json(blob: bytes, tmp_path: Path, suffix: str = ".vamd"):
    result = run_native(blob, tmp_path, suffix=suffix)
    assert result.returncode == 0, result.stderr + result.stdout
    return json.loads(result.stdout)


def python_dense_report(blob: bytes):
    program = decode_dense(blob)
    report = canonical_report(program, execute(program))
    return {
        "pc": report["final_pc"],
        "registers": report["registers"],
        "trace": report["trace"],
        "certs": report["certs"],
        "obstructions": report["obstructions"],
    }


def assert_core_parity(py, rust):
    assert rust["ok"] is True
    assert rust["pc"] == py["pc"]
    assert rust["trace"] == py["trace"]
    assert rust["registers"] == py["registers"]
    assert rust["certs"] == py["certs"]
    assert rust["obstructions"] == py["obstructions"]


def test_native_vamd_executor_minimal_echo_matches_python_oracle(tmp_path):
    program = [
        Instruction("REZ", ("%r1", "root"), 1),
        Instruction("NOD", ("%r2", "%r1", "a"), 2),
        Instruction("NOD", ("%r3", "%r1", "b"), 3),
        Instruction("TACT", ("%r4", "%r2", "%r3", "edge"), 4),
        Instruction("BREATH", ("%r5", "%r4"), 5),
        Instruction("MODE", ("%r6", "%r5"), 6),
        Instruction("OBSERVER", ("%r7", "length"), 7),
        Instruction("ECHO", ("%r8", "%r6", "%r6", "%r7"), 8),
        Instruction("CERT", ("%r9", "dense-self-length", "%r8", "native dense executor parity"), 9),
    ]
    blob = encode_dense(program)
    rust = native_json(blob, tmp_path)

    assert rust["frame"]["magic"] == "VAMD"
    assert_core_parity(python_dense_report(blob), rust)


@pytest.mark.parametrize(("name", "program"), tuple(iter_valid_vam0_fixture_report_programs()))
def test_native_vamd_executor_golden_fixture_reports_match_python_oracle(name, program, tmp_path):
    blob = encode_dense(program)
    rust = native_json(blob, tmp_path)

    assert rust["profile"] == "vam0-ref-v1"
    assert rust["frame"]["magic"] == "VAMD"
    assert rust["instruction_count"] == len(program), name
    assert_core_parity(python_dense_report(blob), rust)


def test_native_cli_preserves_vam0_magic_after_autodetect(tmp_path):
    program = [Instruction("REZ", ("%r1", "phase"), 1)]
    rust = native_json(encode_vmbc(program), tmp_path, suffix=".vam0")

    assert rust["frame"]["magic"] == "VAM0"
    assert rust["pc"] == 1


def test_native_cli_rejects_unknown_frame_magic(tmp_path):
    result = run_native(b"NOPE" + b"\x00" * 10, tmp_path, suffix=".bin")

    assert result.returncode != 0
    body = json.loads(result.stdout)
    assert body["ok"] is False
    assert body["error"]["kind"] == "magic"
