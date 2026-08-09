import json
import shutil
import subprocess
from pathlib import Path

import pytest

from vam.src import canonical_report, decode_vmbc, encode_vmbc, execute
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


def run_native(blob: bytes, tmp_path: Path):
    sample = tmp_path / "sample.vam0"
    sample.write_bytes(blob)
    result = subprocess.run(
        [cargo_bin(), "run", "--quiet", "--manifest-path", str(NATIVE / "Cargo.toml"), "--", str(sample)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    return json.loads(result.stdout)


def python_report(blob: bytes):
    program = decode_vmbc(blob)
    state = execute(program)
    report = canonical_report(program, state)
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


def test_native_executor_minimal_echo_matches_python_oracle(tmp_path):
    program = [
        Instruction("REZ", ("%r1", "root"), 1),
        Instruction("NOD", ("%r2", "%r1", "a"), 2),
        Instruction("NOD", ("%r3", "%r1", "b"), 3),
        Instruction("TACT", ("%r4", "%r2", "%r3", "edge"), 4),
        Instruction("BREATH", ("%r5", "%r4"), 5),
        Instruction("MODE", ("%r6", "%r5"), 6),
        Instruction("OBSERVER", ("%r7", "length"), 7),
        Instruction("OBSERVE", ("%r8", "%r6", "%r7"), 8),
        Instruction("COMPRESS", ("%r9", "%r6", "%r7"), 9),
        Instruction("ECHO", ("%r10", "%r6", "%r6", "%r7"), 10),
        Instruction("CERT", ("%r11", "self-length", "%r10", "native executor parity"), 11),
    ]
    blob = encode_vmbc(program)
    assert_core_parity(python_report(blob), run_native(blob, tmp_path))


def test_native_executor_obstruction_matches_python_oracle(tmp_path):
    program = [
        Instruction("REZ", ("%r1", "root"), 1),
        Instruction("NOD", ("%r2", "%r404", "bad"), 2),
        Instruction("OBSTRUCT", ("%r3", "manual-stop", "%r2"), 3),
        Instruction("CERT", ("%r4", "must-not-accept", "%r3", "obstruction fixture"), 4),
    ]
    blob = encode_vmbc(program)
    py = python_report(blob)
    rust = run_native(blob, tmp_path)
    assert_core_parity(py, rust)
    assert rust["registers"]["%r2"]["kind"] == "Obstruction"
    assert rust["registers"]["%r4"]["data"]["accepted"] is False


@pytest.mark.parametrize(("name", "program"), tuple(iter_valid_vam0_fixture_report_programs()))
def test_native_executor_golden_fixture_reports_match_python_oracle(name, program, tmp_path):
    blob = encode_vmbc(program)
    rust = run_native(blob, tmp_path)

    assert_core_parity(python_report(blob), rust)
    assert rust["profile"] == "vam0-ref-v1"
    assert rust["instruction_count"] == len(program), name
