import json
import shutil
import subprocess
from pathlib import Path

import pytest

from vam.src import canonical_report, encode_dense, encode_vmbc, execute, optimize, parse_vmasm
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


def run_native_optimizer(blob: bytes, tmp_path: Path, suffix: str = ".vam0", slice_name: str = "observer-alias-v1"):
    sample = tmp_path / f"sample{suffix}"
    sample.write_bytes(blob)
    result = subprocess.run(
        [
            cargo_bin(),
            "run",
            "--quiet",
            "--manifest-path",
            str(NATIVE / "Cargo.toml"),
            "--",
            "--optimize",
            slice_name,
            str(sample),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result, json.loads(result.stdout)


def native_comparable(report):
    rows = []
    for inst in report["optimized_report"]["instructions"]:
        args = []
        for arg in inst["args"]:
            if arg["t"] == "reg":
                args.append(f"%r{arg['v']}")
            else:
                args.append(arg["v"])
        rows.append((inst["op"], tuple(args)))
    return rows


def python_rows(report):
    return [
        {
            "pass_name": row.pass_name,
            "action": row.action,
            "detail": row.detail,
            "accepted": row.accepted,
        }
        for row in report.rows
        if row.pass_name == "observer-alias"
    ]


def python_core_report(program):
    report = canonical_report(program, execute(program))
    return {
        "pc": report["final_pc"],
        "registers": report["registers"],
        "trace": report["trace"],
        "certs": report["certs"],
        "obstructions": report["obstructions"],
    }


def assert_core_parity(py, rust):
    optimized = rust["optimized_report"]
    assert optimized["ok"] is True
    assert optimized["pc"] == py["pc"]
    assert optimized["trace"] == py["trace"]
    assert optimized["registers"] == py["registers"]
    assert optimized["certs"] == py["certs"]
    assert optimized["obstructions"] == py["obstructions"]


def test_native_observer_alias_slice_matches_python_rows_and_execution(tmp_path):
    program = parse_vmasm(
        '''
OBSERVER %r1, "kind"
OBSERVER %r2, "kind"
REZ %r3, "phase"
ECHO %r4, %r3, %r3, %r2
CERT %r5, "observer-alias", %r4, "native optimizer slice"
'''
    )
    py = optimize(program)
    result, native = run_native_optimizer(encode_vmbc(program), tmp_path)

    assert result.returncode == 0, result.stderr + result.stdout
    assert native["optimizer_contract"] == "native-optimizer-parity-v1"
    assert native["optimizer_slice"] == "observer-alias-v1"
    assert native["input_magic"] == "VAM0"
    assert native["optimizer_boundary"] == "decoded-ir-report-only"
    assert native["rows"] == python_rows(py)
    assert "optimized_frame" not in native
    assert "optimized_bytes" not in native
    assert "frame" not in native["optimized_report"]
    assert native_comparable(native) == [inst.comparable() for inst in py.optimized]
    assert native["optimized_instruction_count"] == len(py.optimized)
    assert_core_parity(python_core_report(py.optimized), native)


def test_native_observer_alias_slice_preserves_multiple_definition_surface(tmp_path):
    program = parse_vmasm(
        '''
OBSERVER %r1, "kind"
OBSERVER %r2, "kind"
OBSERVER %r2, "label"
REZ %r3, "phase"
ECHO %r4, %r3, %r3, %r2
'''
    )
    py = optimize(program)
    result, native = run_native_optimizer(encode_vmbc(program), tmp_path)

    assert result.returncode == 0, result.stderr + result.stdout
    assert native["rows"] == python_rows(py) == []
    assert native_comparable(native) == [inst.comparable() for inst in program]
    assert_core_parity(python_core_report(program), native)


def test_native_optimizer_slice_accepts_vamd_report_only_boundary(tmp_path):
    program = [
        Instruction("OBSERVER", ("%r1", "kind"), 1),
        Instruction("OBSERVER", ("%r2", "kind"), 2),
        Instruction("REZ", ("%r3", "phase"), 3),
        Instruction("ECHO", ("%r4", "%r3", "%r3", "%r2"), 4),
    ]
    py = optimize(program)
    result, report = run_native_optimizer(encode_dense(program), tmp_path, suffix=".vamd")

    assert result.returncode == 0, result.stderr + result.stdout
    assert report["ok"] is True
    assert report["input_magic"] == "VAMD"
    assert report["optimizer_boundary"] == "decoded-ir-report-only"
    assert report["rows"] == python_rows(py)
    assert "optimized_frame" not in report
    assert "optimized_bytes" not in report
    assert "frame" not in report["optimized_report"]
    assert native_comparable(report) == [inst.comparable() for inst in py.optimized]
    assert_core_parity(python_core_report(py.optimized), report)


def test_native_optimizer_unsupported_slice_rejects_vamd(tmp_path):
    program = [Instruction("OBSERVER", ("%r1", "kind"), 1)]
    result, report = run_native_optimizer(
        encode_dense(program),
        tmp_path,
        suffix=".vamd",
        slice_name="not-a-slice",
    )

    assert result.returncode != 0
    assert report["ok"] is False
    assert report["error"]["kind"] == "unsupported-profile"
