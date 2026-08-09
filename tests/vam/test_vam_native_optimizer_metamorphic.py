from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from vam.src import encode_dense, encode_vmbc, parse_vmasm
from vam.src.model import Instruction
from src.core.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT
NATIVE = ROOT / "vam" / "native"
NATIVE_SLICE = "observer-alias-v1"


def _cargo() -> str:
    found = shutil.which("cargo")
    if found:
        return found
    fallback = Path.home() / ".cargo" / "bin" / "cargo"
    if fallback.exists():
        return str(fallback)
    pytest.skip("cargo/rust unavailable")


def _run_native(blob: bytes, suffix: str, tmp_path: Path, name: str = "sample") -> tuple[bytes, dict]:
    sample = tmp_path / f"{name}{suffix}"
    sample.write_bytes(blob)
    result = subprocess.run(
        [
            _cargo(),
            "run",
            "--quiet",
            "--manifest-path",
            str(NATIVE / "Cargo.toml"),
            "--bin",
            "vam0-inspect",
            "--",
            "--optimize",
            NATIVE_SLICE,
            str(sample),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode() + result.stdout.decode()
    return result.stdout, json.loads(result.stdout)


def _encoded(fmt: str, program: tuple[Instruction, ...]) -> tuple[bytes, str]:
    if fmt == "VAM0":
        return encode_vmbc(program), ".vam0"
    if fmt == "VAMD":
        return encode_dense(program), ".vamd"
    raise AssertionError(fmt)


def _run_format(fmt: str, program: tuple[Instruction, ...], tmp_path: Path, name: str = "sample") -> dict:
    blob, suffix = _encoded(fmt, program)
    return _run_native(blob, suffix, tmp_path, name)[1]


def _comparable_ir(report: dict) -> list[tuple[str, tuple[object, ...]]]:
    rows = []
    for inst in report["optimized_report"]["instructions"]:
        args = tuple(f"%r{arg['v']}" if arg["t"] == "reg" else arg["v"] for arg in inst["args"])
        rows.append((inst["op"], args))
    return rows


def _semantic_core(report: dict) -> dict:
    optimized = report["optimized_report"]
    return {
        "profile": optimized["profile"],
        "pc": optimized["pc"],
        "trace": optimized["trace"],
        "registers": optimized["registers"],
        "certs": optimized["certs"],
        "obstructions": optimized["obstructions"],
    }


def _line_insensitive_core(report: dict) -> dict:
    optimized = report["optimized_report"]
    return {
        "pc": optimized["pc"],
        "trace": optimized["trace"],
        "registers": optimized["registers"],
        "certs": optimized["certs"],
        "obstructions": optimized["obstructions"],
    }


def _program() -> tuple[Instruction, ...]:
    return tuple(
        parse_vmasm(
            """
OBSERVER %r1, "kind"
OBSERVER %r2, "kind"
REZ %r3, "phase"
COMPRESS %r4, %r3, %r2
COMPRESS %r5, %r3, %r1
ECHO %r6, %r4, %r5, %r2
CERT %r7, "metamorphic", %r6, "native optimizer parity"
"""
        )
    )


def _perturbed_lines() -> tuple[Instruction, ...]:
    return tuple(Instruction(inst.op, inst.args, inst.line + 100) for inst in _program())


def _contains_obstruction(value: object) -> bool:
    if isinstance(value, dict):
        return value.get("kind") == "Obstruction" or any(_contains_obstruction(v) for v in value.values())
    if isinstance(value, list):
        return any(_contains_obstruction(v) for v in value)
    return False


def test_vam0_and_vamd_have_same_native_optimized_semantics(tmp_path: Path) -> None:
    vam0 = _run_format("VAM0", _program(), tmp_path, "same_program_vam0")
    vamd = _run_format("VAMD", _program(), tmp_path, "same_program_vamd")

    assert vam0["input_magic"] == "VAM0"
    assert vamd["input_magic"] == "VAMD"
    assert vam0["rows"] == vamd["rows"]
    assert _comparable_ir(vam0) == _comparable_ir(vamd)
    assert _semantic_core(vam0) == _semantic_core(vamd)


def test_repeated_native_runs_are_byte_and_json_stable(tmp_path: Path) -> None:
    blob, suffix = _encoded("VAM0", _program())
    first_bytes, first_json = _run_native(blob, suffix, tmp_path, "stable")
    second_bytes, second_json = _run_native(blob, suffix, tmp_path, "stable")

    assert first_bytes == second_bytes
    assert first_json == second_json


def test_line_number_perturbation_preserves_semantic_core(tmp_path: Path) -> None:
    base = _run_format("VAM0", _program(), tmp_path, "base_lines")
    perturbed = _run_format("VAM0", _perturbed_lines(), tmp_path, "shifted_lines")

    assert base["rows"] == perturbed["rows"]
    assert _comparable_ir(base) == _comparable_ir(perturbed)
    assert [inst["line"] for inst in base["optimized_report"]["instructions"]] != [
        inst["line"] for inst in perturbed["optimized_report"]["instructions"]
    ]
    assert _line_insensitive_core(base) == _line_insensitive_core(perturbed)


REJECTED_OBSTRUCTION_CASES = (
    pytest.param(
        """
REZ %r1, "phase"
OBSERVE %r2, %r1, %r1
""",
        "dead-shadow",
        id="dead-shadow-observe-obstruction",
    ),
    pytest.param(
        """
REZ %r1, "phase"
OBSERVER %r2, "kind"
OBSERVE %r3, %r1, %r1
COMPRESS %r4, %r3, %r2
COMPRESS %r5, %r4, %r2
ECHO %r6, %r4, %r5, %r2
""",
        "compress-idempotent",
        id="compress-idempotent-target-obstruction",
    ),
    pytest.param(
        """
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r1
COMPRESS %r4, %r1, %r1
ECHO %r5, %r3, %r4, %r2
""",
        "compress-alias",
        id="compress-alias-shadow-obstruction",
    ),
)


@pytest.mark.parametrize(("source", "pass_name"), REJECTED_OBSTRUCTION_CASES)
def test_rejected_obstruction_cases_remain_visible(tmp_path: Path, source: str, pass_name: str) -> None:
    report = _run_format("VAM0", tuple(parse_vmasm(source)), tmp_path, pass_name)
    rejected = [row for row in report["rows"] if row["pass_name"] == pass_name]

    assert rejected
    assert all(row["accepted"] is False and row["action"] == "reject" for row in rejected)
    assert "obstruction" in json.dumps(rejected, sort_keys=True).lower()
    assert _contains_obstruction(_line_insensitive_core(report))
