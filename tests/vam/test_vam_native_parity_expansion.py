import json
import shutil
import subprocess
from pathlib import Path

import pytest

from vam.src import (
    canonical_report,
    compile_source,
    decode_dense,
    decode_vmbc,
    encode_dense,
    encode_vmbc,
    execute,
    lower_hl1_source,
)
from vam.src.model import Instruction
from src.core.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT
NATIVE = ROOT / "vam" / "native"
FORMATS = ("VAM0", "VAMD")


def cargo_bin() -> str:
    found = shutil.which("cargo")
    if found:
        return found
    fallback = Path.home() / ".cargo" / "bin" / "cargo"
    if fallback.exists():
        return str(fallback)
    pytest.skip("cargo/rust unavailable")


def _native_cli(blob: bytes, fmt: str, name: str, tmp_path: Path) -> dict:
    suffix = ".vam0" if fmt == "VAM0" else ".vamd"
    safe_name = "".join(ch if ch.isalnum() else "-" for ch in name)
    sample = tmp_path / f"{safe_name}{suffix}"
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


def _encode(fmt: str, program: tuple[Instruction, ...]) -> bytes:
    return encode_vmbc(program) if fmt == "VAM0" else encode_dense(program)


def _decode(fmt: str, blob: bytes) -> tuple[Instruction, ...]:
    return tuple(decode_vmbc(blob) if fmt == "VAM0" else decode_dense(blob))


def _python_core_report(program: tuple[Instruction, ...]) -> dict:
    report = canonical_report(program, execute(program))
    return {
        "profile": report["profile"],
        "pc": report["final_pc"],
        "trace": report["trace"],
        "registers": report["registers"],
        "certs": report["certs"],
        "obstructions": report["obstructions"],
    }


def _assert_core_parity(py: dict, rust: dict, fmt: str, count: int) -> None:
    assert rust["ok"] is True
    assert rust["profile"] == py["profile"]
    assert rust["frame"]["magic"] == fmt
    assert rust["instruction_count"] == count
    assert rust["pc"] == py["pc"]
    assert rust["trace"] == py["trace"]
    assert rust["registers"] == py["registers"]
    assert rust["certs"] == py["certs"]
    assert rust["obstructions"] == py["obstructions"]


def _base_mode(prefix: str = "%r") -> list[Instruction]:
    return [
        Instruction("REZ", (f"{prefix}1", "phase"), 1),
        Instruction("NOD", (f"{prefix}2", f"{prefix}1", "0"), 2),
        Instruction("NOD", (f"{prefix}3", f"{prefix}1", "1"), 3),
        Instruction("TACT", (f"{prefix}4", f"{prefix}2", f"{prefix}3", "step"), 4),
        Instruction("BREATH", (f"{prefix}5", f"{prefix}4"), 5),
        Instruction("MODE", (f"{prefix}6", f"{prefix}5"), 6),
    ]


def _duplicate_compress_program() -> tuple[Instruction, ...]:
    return tuple(
        _base_mode()
        + [
            Instruction("OBSERVER", ("%r7", "kind"), 7),
            Instruction("COMPRESS", ("%r8", "%r6", "%r7"), 8),
            Instruction("COMPRESS", ("%r9", "%r6", "%r7"), 9),
            Instruction("ECHO", ("%r10", "%r8", "%r9", "%r7"), 10),
            Instruction("CERT", ("%r11", "duplicate-compress", "%r10", "native parity"), 11),
        ]
    )


def _idempotent_compress_program() -> tuple[Instruction, ...]:
    return tuple(
        _base_mode()
        + [
            Instruction("OBSERVER", ("%r7", "boundary"), 7),
            Instruction("COMPRESS", ("%r8", "%r6", "%r7"), 8),
            Instruction("COMPRESS", ("%r9", "%r8", "%r7"), 9),
            Instruction("OBSERVE", ("%r10", "%r9", "%r7"), 10),
            Instruction("ECHO", ("%r11", "%r8", "%r9", "%r7"), 11),
            Instruction("CERT", ("%r12", "idempotent-compress", "%r11", "native parity"), 12),
        ]
    )


def _obstruction_chain_program() -> tuple[Instruction, ...]:
    return (
        Instruction("REZ", ("%r1", "phase"), 1),
        Instruction("NOD", ("%r2", "%r404", "bad-nod"), 2),
        Instruction("TACT", ("%r3", "%r2", "%r1", "bad-tact"), 3),
        Instruction("BREATH", ("%r4", "%r3"), 4),
        Instruction("MODE", ("%r5", "%r4"), 5),
        Instruction("OBSERVER", ("%r6", "trace"), 6),
        Instruction("OBSERVE", ("%r7", "%r5", "%r6"), 7),
        Instruction("OBSTRUCT", ("%r8", "manual-after-chain", "%r7"), 8),
        Instruction("CERT", ("%r9", "chain-must-not-accept", "%r8", "obstruction parity"), 9),
    )


def _compiled_core_programs() -> list[tuple[str, tuple[Instruction, ...]]]:
    sources = {
        "core-small-self-echo": "echo(nod:a,nod:a,observer:length)",
        "core-mode-length-echo": "echo(mode(breath(tact(nod:a,nod:b),tact(nod:b,nod:a))),mode(breath(tact(nod:b,nod:a),tact(nod:a,nod:b))),observer:length)",
        "core-single-nod-cert-boundary": "nod:a",
        "shell-report-carrier": "shell(echo(nod:a,nod:a,observer:length),echo(nod:b,nod:b,observer:kind))",
        "shell-blocked-child-carrier": "shell(echo(nod:a,nod:bbb,observer:label),echo(nod:c,nod:c,observer:kind))",
    }
    return [(name, tuple(compile_source(src, certify=not name.startswith("shell-")).program)) for name, src in sources.items()]


def _hl1_programs() -> list[tuple[str, tuple[Instruction, ...]]]:
    source = "observer len := length\nprocess demo { claim same := echo(nod:a,nod:a) under len }"
    lowering = lower_hl1_source(source)
    assert lowering.ok and lowering.core_source is not None
    program = tuple(compile_source(lowering.core_source, claim="hl1-same").program)
    return [("hl1-claim-lowered", program)]


def _cases() -> tuple[tuple[str, tuple[Instruction, ...]], ...]:
    return tuple(
        [
            ("duplicate-compress-handwritten", _duplicate_compress_program()),
            ("idempotent-compress-handwritten", _idempotent_compress_program()),
            ("obstruction-chain-handwritten", _obstruction_chain_program()),
        ]
        + _compiled_core_programs()
        + _hl1_programs()
    )


CASES = _cases()


@pytest.mark.parametrize("fmt", FORMATS)
@pytest.mark.parametrize(("name", "program"), CASES, ids=[name for name, _ in CASES])
def test_native_cli_expanded_python_parity(name: str, program: tuple[Instruction, ...], fmt: str, tmp_path: Path) -> None:
    blob = _encode(fmt, program)
    decoded_program = _decode(fmt, blob)
    rust = _native_cli(blob, fmt, name, tmp_path)
    py = _python_core_report(decoded_program)

    _assert_core_parity(py, rust, fmt, len(decoded_program))
