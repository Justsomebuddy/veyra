import json
import shutil
import subprocess
from pathlib import Path

import pytest

from vam.src import canonical_report, decode_vmbc, encode_dense, encode_vmbc, execute, optimize
from vam.src.model import Instruction
from src.core.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT
NATIVE = ROOT / "vam" / "native"


def cargo_bin() -> str:
    found = shutil.which("cargo")
    if found:
        return found
    fallback = Path.home() / ".cargo" / "bin" / "cargo"
    if fallback.exists():
        return str(fallback)
    pytest.skip("cargo/rust unavailable")


def _program() -> tuple[Instruction, ...]:
    return (
        Instruction("OBSERVER", ("%r1", "kind"), 1),
        Instruction("OBSERVER", ("%r2", "kind"), 2),
        Instruction("REZ", ("%r3", "phase"), 3),
        Instruction("ECHO", ("%r4", "%r3", "%r3", "%r2"), 4),
    )


def _run_emit(blob: bytes, suffix: str, tmp_path: Path, *, include_optimize: bool = True, slice_name: str = "observer-alias-v1"):
    sample = tmp_path / f"sample{suffix}"
    out = tmp_path / "optimized.vam0"
    sample.write_bytes(blob)
    args = [cargo_bin(), "run", "--quiet", "--manifest-path", str(NATIVE / "Cargo.toml"), "--"]
    if include_optimize:
        args += ["--optimize", slice_name]
    args += ["--emit-optimized-vam0", str(out), str(sample)]
    result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return result, json.loads(result.stdout), out


def _native_inspect(path: Path) -> dict:
    result = subprocess.run(
        [cargo_bin(), "run", "--quiet", "--manifest-path", str(NATIVE / "Cargo.toml"), "--", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    return json.loads(result.stdout)


def _comparable(program: tuple[Instruction, ...] | list[Instruction]) -> list[tuple[str, tuple[object, ...]]]:
    return [inst.comparable() for inst in program]


def _core(program: tuple[Instruction, ...] | list[Instruction]) -> dict:
    report = canonical_report(program, execute(program))
    return {
        "pc": report["final_pc"],
        "trace": report["trace"],
        "registers": report["registers"],
        "certs": report["certs"],
        "obstructions": report["obstructions"],
    }


def test_native_emits_optimized_vam0_frame_for_vam0_input(tmp_path):
    program = _program()
    py = optimize(program)
    result, body, out = _run_emit(encode_vmbc(program), ".vam0", tmp_path)

    assert result.returncode == 0, result.stderr + result.stdout
    assert body["input_magic"] == "VAM0"
    assert body["optimizer_boundary"] == "decoded-ir-report-only"
    assert body["emitted_frame"]["magic"] == "VAM0"
    assert body["emitted_frame"]["version"] == 1
    assert body["emitted_frame"]["boundary"] == "optimized-ir-to-vam0-frame"
    assert body["emitted_frame"]["source"] == "native-optimized-instructions"
    assert body["emitted_frame"]["path"] == str(out)
    assert body["emitted_frame"]["bytes"] == out.stat().st_size
    assert body["emitted_frame"]["instruction_count"] == len(py.optimized)
    assert "optimized_frame" not in body
    assert "optimized_bytes" not in body
    assert "frame" not in body["optimized_report"]
    assert _comparable(decode_vmbc(out.read_bytes())) == _comparable(py.optimized)

    emitted_report = _native_inspect(out)
    expected = _core(py.optimized)
    assert emitted_report["frame"]["magic"] == "VAM0"
    assert emitted_report["instruction_count"] == len(py.optimized)
    assert emitted_report["pc"] == expected["pc"]
    assert emitted_report["trace"] == expected["trace"]
    assert emitted_report["registers"] == expected["registers"]
    assert emitted_report["certs"] == expected["certs"]
    assert emitted_report["obstructions"] == expected["obstructions"]


def test_native_emission_rejects_vamd_input_without_file(tmp_path):
    result, body, out = _run_emit(encode_dense(_program()), ".vamd", tmp_path)

    assert result.returncode != 0
    assert body["ok"] is False
    assert body["error"]["kind"] == "unsupported-profile"
    assert not out.exists()


def test_native_emission_requires_optimizer_and_exact_slice(tmp_path):
    result, body, out = _run_emit(encode_vmbc(_program()), ".vam0", tmp_path, include_optimize=False)
    assert result.returncode != 0
    assert body["error"]["kind"] == "usage"
    assert not out.exists()

    result, body, out = _run_emit(encode_vmbc(_program()), ".vam0", tmp_path, slice_name="observer-alias")
    assert result.returncode != 0
    assert body["error"]["kind"] == "unsupported-profile"
    assert not out.exists()
