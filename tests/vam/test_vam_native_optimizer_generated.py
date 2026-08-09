from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from vam.src import canonical_report, encode_dense, encode_vmbc, execute, optimize
from vam.src.model import Instruction
from src.core.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT
NATIVE = ROOT / "vam" / "native"
NATIVE_SLICE = "observer-alias-v1"
FORMATS = ("VAM0", "VAMD")


def cargo_bin() -> str:
    found = shutil.which("cargo")
    if found:
        return found
    fallback = Path.home() / ".cargo" / "bin" / "cargo"
    if fallback.exists():
        return str(fallback)
    pytest.skip("cargo/rust unavailable")


def _inst(op: str, *args: object, line: int) -> Instruction:
    return Instruction(op, args, line)


def _encode(fmt: str, program: tuple[Instruction, ...]) -> bytes:
    return encode_vmbc(program) if fmt == "VAM0" else encode_dense(program)


def _run_native_optimizer(blob: bytes, fmt: str, name: str, tmp_path: Path) -> dict:
    suffix = ".vam0" if fmt == "VAM0" else ".vamd"
    sample = tmp_path / f"{name}{suffix}"
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
            NATIVE_SLICE,
            str(sample),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    body = json.loads(result.stdout)
    assert result.returncode == 0, result.stderr + result.stdout
    return body


def _native_comparable(report: dict) -> list[tuple[str, tuple[object, ...]]]:
    rows = []
    for inst in report["optimized_report"]["instructions"]:
        args = tuple(f"%r{arg['v']}" if arg["t"] == "reg" else arg["v"] for arg in inst["args"])
        rows.append((inst["op"], args))
    return rows


def _python_rows(report) -> list[dict]:
    return [
        {
            "pass_name": row.pass_name,
            "action": row.action,
            "detail": row.detail,
            "accepted": row.accepted,
        }
        for row in report.rows
    ]


def _semantic_core(program: tuple[Instruction, ...]) -> dict:
    report = canonical_report(program, execute(program))
    return {
        "profile": report["profile"],
        "pc": report["final_pc"],
        "trace": report["trace"],
        "registers": report["registers"],
        "certs": report["certs"],
        "obstructions": report["obstructions"],
    }


def _base() -> list[Instruction]:
    return [
        _inst("REZ", "%r1", "phase", line=1),
        _inst("NOD", "%r2", "%r1", "a", line=2),
        _inst("NOD", "%r3", "%r1", "b", line=3),
        _inst("TACT", "%r4", "%r2", "%r3", "step", line=4),
        _inst("BREATH", "%r5", "%r4", line=5),
        _inst("MODE", "%r6", "%r5", line=6),
    ]


def _generated_cases() -> tuple[tuple[str, tuple[Instruction, ...]], ...]:
    cases: list[tuple[str, tuple[Instruction, ...]]] = []
    cases.append(
        (
            "observer-alias-chain",
            tuple(
                _base()
                + [
                    _inst("OBSERVER", "%r7", "kind", line=7),
                    _inst("OBSERVER", "%r8", "kind", line=8),
                    _inst("ECHO", "%r9", "%r6", "%r6", "%r8", line=9),
                    _inst("CERT", "%r10", "alias", "%r9", "duplicate observer", line=10),
                ]
            ),
        )
    )
    cases.append(
        (
            "duplicate-compress-safe",
            tuple(
                _base()
                + [
                    _inst("OBSERVER", "%r7", "length", line=7),
                    _inst("COMPRESS", "%r8", "%r6", "%r7", line=8),
                    _inst("COMPRESS", "%r9", "%r6", "%r7", line=9),
                    _inst("ECHO", "%r10", "%r8", "%r9", "%r7", line=10),
                ]
            ),
        )
    )
    cases.append(
        (
            "idempotent-compress-safe",
            tuple(
                _base()
                + [
                    _inst("OBSERVER", "%r7", "boundary", line=7),
                    _inst("COMPRESS", "%r8", "%r6", "%r7", line=8),
                    _inst("COMPRESS", "%r9", "%r8", "%r7", line=9),
                    _inst("ECHO", "%r10", "%r8", "%r9", "%r7", line=10),
                ]
            ),
        )
    )
    cases.append(
        (
            "dead-shadow-safe-unused-compress",
            tuple(
                _base()
                + [
                    _inst("OBSERVER", "%r7", "trace", line=7),
                    _inst("COMPRESS", "%r8", "%r6", "%r7", line=8),
                    _inst("ECHO", "%r9", "%r6", "%r6", "%r7", line=9),
                ]
            ),
        )
    )
    cases.append(
        (
            "dead-shadow-reject-obstruction",
            (
                _inst("REZ", "%r1", "phase", line=1),
                _inst("COMPRESS", "%r2", "%r1", "%r1", line=2),
            ),
        )
    )
    cases.append(
        (
            "combined-alias-compress-idempotent-dead",
            tuple(
                _base()
                + [
                    _inst("OBSERVER", "%r7", "kind", line=7),
                    _inst("OBSERVER", "%r8", "kind", line=8),
                    _inst("COMPRESS", "%r9", "%r6", "%r8", line=9),
                    _inst("COMPRESS", "%r10", "%r6", "%r7", line=10),
                    _inst("COMPRESS", "%r11", "%r10", "%r7", line=11),
                    _inst("COMPRESS", "%r12", "%r6", "%r7", line=12),
                    _inst("ECHO", "%r13", "%r9", "%r11", "%r7", line=13),
                    _inst("CERT", "%r14", "combined", "%r13", "generated parity", line=14),
                ]
            ),
        )
    )
    return tuple(cases)


CASES = _generated_cases()


def test_generated_corpus_boundary_is_fixed() -> None:
    assert FORMATS == ("VAM0", "VAMD")
    assert len(CASES) == 6


@pytest.mark.parametrize("fmt", FORMATS)
@pytest.mark.parametrize(("name", "program"), CASES, ids=[name for name, _ in CASES])
def test_generated_native_optimizer_matches_python_oracle(
    name: str,
    program: tuple[Instruction, ...],
    fmt: str,
    tmp_path: Path,
) -> None:
    py = optimize(program)
    native = _run_native_optimizer(_encode(fmt, program), fmt, name, tmp_path)

    assert native["optimizer_contract"] == "native-optimizer-parity-v1"
    assert native["optimizer_slice"] == NATIVE_SLICE
    assert native["input_magic"] == fmt
    assert native["optimizer_boundary"] == "decoded-ir-report-only"
    assert native["rows"] == _python_rows(py)
    assert "optimized_frame" not in native
    assert "optimized_bytes" not in native
    assert "frame" not in native["optimized_report"]
    assert _native_comparable(native) == [inst.comparable() for inst in py.optimized]
    assert native["optimized_instruction_count"] == len(py.optimized)
    expected = _semantic_core(py.optimized)
    optimized = native["optimized_report"]
    assert optimized["profile"] == expected["profile"]
    assert optimized["pc"] == expected["pc"]
    assert optimized["trace"] == expected["trace"]
    assert optimized["registers"] == expected["registers"]
    assert optimized["certs"] == expected["certs"]
    assert optimized["obstructions"] == expected["obstructions"]
