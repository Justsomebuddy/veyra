import json
import shutil
import subprocess
from pathlib import Path

import pytest

from vam.src import canonical_report, encode_vmbc, execute, optimize, parse_vmasm
from vam.src.equivalence import summarize_equivalence
from src.core.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT
NATIVE = ROOT / "vam" / "native"
NATIVE_SLICE = "observer-alias-v1"


def cargo_bin() -> str:
    found = shutil.which("cargo")
    if found:
        return found
    fallback = Path.home() / ".cargo" / "bin" / "cargo"
    if fallback.exists():
        return str(fallback)
    pytest.skip("cargo/rust unavailable")


def run_native_optimizer(blob: bytes, tmp_path: Path) -> dict:
    sample = tmp_path / "sample.vam0"
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
    assert result.returncode == 0, result.stderr + result.stdout
    return json.loads(result.stdout)


def native_comparable(report: dict) -> list[tuple[str, tuple[object, ...]]]:
    rows = []
    for inst in report["optimized_report"]["instructions"]:
        args = []
        for arg in inst["args"]:
            args.append(f"%r{arg['v']}" if arg["t"] == "reg" else arg["v"])
        rows.append((inst["op"], tuple(args)))
    return rows


def python_rows(report) -> list[dict]:
    return [
        {
            "pass_name": row.pass_name,
            "action": row.action,
            "detail": row.detail,
            "accepted": row.accepted,
        }
        for row in report.rows
    ]


def core_report(program) -> dict:
    report = canonical_report(program, execute(program))
    return {
        "pc": report["final_pc"],
        "trace": report["trace"],
        "registers": report["registers"],
        "certs": report["certs"],
        "obstructions": report["obstructions"],
    }


def assert_core_parity(py: dict, native: dict) -> None:
    optimized = native["optimized_report"]
    assert optimized["ok"] is True
    assert optimized["pc"] == py["pc"]
    assert optimized["trace"] == py["trace"]
    assert optimized["registers"] == py["registers"]
    assert optimized["certs"] == py["certs"]
    assert optimized["obstructions"] == py["obstructions"]


def assert_native_matches_python_oracle(source: str, tmp_path: Path, expected_decisions: tuple[tuple[str, bool], ...]) -> None:
    program = tuple(parse_vmasm(source))
    py = optimize(program)
    summary = summarize_equivalence(program, py.optimized)
    native = run_native_optimizer(encode_vmbc(program), tmp_path)

    assert summary.status == "equivalent"
    assert summary.safe is True
    for pass_name, accepted in expected_decisions:
        assert any(row.pass_name == pass_name and row.accepted is accepted for row in py.rows)

    assert native["optimizer_contract"] == "native-optimizer-parity-v1"
    assert native["optimizer_slice"] == NATIVE_SLICE
    assert native["rows"] == python_rows(py)
    assert native_comparable(native) == [inst.comparable() for inst in py.optimized]
    assert native["optimized_instruction_count"] == len(py.optimized)
    assert_core_parity(core_report(py.optimized), native)


def test_native_observer_alias_surface_with_compress_context(tmp_path: Path) -> None:
    assert_native_matches_python_oracle(
        '''
OBSERVER %r1, "kind"
OBSERVER %r2, "kind"
REZ %r3, "phase"
COMPRESS %r4, %r3, %r2
ECHO %r5, %r4, %r4, %r2
CERT %r6, "observer-alias", %r5, "aliased observer reaches compress context"
''',
        tmp_path,
        (("observer-alias", True),),
    )


EXPANSION_CASES = [
    pytest.param(
        "duplicate-compress-alias",
        '''
REZ %r1, "phase"
NOD %r2, %r1, "0"
NOD %r3, %r1, "1"
TACT %r4, %r2, %r3, "step"
BREATH %r5, %r4
MODE %r6, %r5
OBSERVER %r7, "kind"
COMPRESS %r8, %r6, %r7
COMPRESS %r9, %r6, %r7
ECHO %r10, %r8, %r9, %r7
CERT %r11, "compressed-kind", %r10, "same compressed witness"
''',
        (("compress-alias", True),),
    ),
    pytest.param(
        "same-observer-compress-idempotent",
        '''
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r2
COMPRESS %r4, %r3, %r2
ECHO %r5, %r3, %r4, %r2
CERT %r6, "idempotent-compress", %r5, "same observer visible"
''',
        (("compress-idempotent", True),),
    ),
    pytest.param(
        "dead-shadow-prunes-safe-unused-compress",
        '''
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r2
ECHO %r4, %r1, %r1, %r2
''',
        (("dead-shadow", True),),
    ),
    pytest.param(
        "duplicate-compress-preserves-obstruction-shadow",
        '''
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r1
COMPRESS %r4, %r1, %r1
ECHO %r5, %r3, %r4, %r2
''',
        (("compress-alias", False),),
    ),
    pytest.param(
        "compress-idempotent-preserves-target-obstruction",
        '''
REZ %r1, "phase"
OBSERVER %r2, "kind"
OBSERVE %r3, %r1, %r1
COMPRESS %r4, %r3, %r2
COMPRESS %r5, %r4, %r2
ECHO %r6, %r4, %r5, %r2
''',
        (("compress-idempotent", False),),
    ),
    pytest.param(
        "dead-shadow-preserves-obstruction-shadow",
        '''
REZ %r1, "phase"
COMPRESS %r2, %r1, %r1
''',
        (("dead-shadow", False),),
    ),
]


@pytest.mark.parametrize(("name", "source", "expected_decisions"), EXPANSION_CASES)
def test_native_optimizer_future_expansion_matches_python_oracle(
    name: str,
    source: str,
    expected_decisions: tuple[tuple[str, bool], ...],
    tmp_path: Path,
) -> None:
    assert name
    assert_native_matches_python_oracle(source, tmp_path, expected_decisions)
