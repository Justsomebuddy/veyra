from dataclasses import replace
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest

import src.core.proof_core_bridge as bridge_module
from src.core.proof_core_bridge import (
    LEAN_TOOLCHAIN, check_proof_core_bridge, proof_core_bridge_report,
)
from src.core.proof_core_lean_render import render_resonance_lean
from src.core.proof_core_resonance import intrinsic_resonance_theorem
from src.core.proof_core_types import Bound, CoreType, EqRefl, Equal, Forall, ForallIntro


def test_canonical_artifact_is_byte_bound_to_compiled_lean_soundness():
    theorem = intrinsic_resonance_theorem()
    report = proof_core_bridge_report()
    assert report.status == "checked"
    assert report.artifact_checked and report.source_bound and report.manifest_checked and report.lean_checked
    assert report.artifact_digest == theorem.artifact.proof_digest
    assert report.theorem_ids == tuple(f"THM-R7-{index:03d}" for index in range(1, 5))
    assert LEAN_TOOLCHAIN in report.toolchain or "4.30.0-rc2" in report.toolchain
    assert len(report.binding_digest) == 64


def test_repository_export_is_exact_deterministic_renderer_output():
    expected = render_resonance_lean(intrinsic_resonance_theorem())
    actual = Path("proofs/lean/VeyraProofResonance.lean").read_text(encoding="utf-8")
    assert actual == expected
    assert intrinsic_resonance_theorem().artifact.proof_digest in actual


def test_forged_artifact_blocks_before_lean_acceptance():
    theorem = intrinsic_resonance_theorem()
    forged_artifact = replace(theorem.artifact, proof_digest="0" * 64)
    report = check_proof_core_bridge(replace(theorem, artifact=forged_artifact))
    assert report.status == "blocked"
    assert report.diagnostics == "theorem-artifact-replay-mismatch"
    assert not report.lean_checked


@pytest.mark.parametrize("field", ["theorem_id", "statement", "proof", "boundary"])
def test_forged_theorem_fields_cannot_reuse_canonical_artifact(field):
    theorem = intrinsic_resonance_theorem()
    values = {
        "theorem_id": "THM-FORGED",
        "statement": Forall(CoreType.RECURRENCE, Equal(Bound(0), Bound(0))),
        "proof": ForallIntro(CoreType.RECURRENCE, EqRefl(Bound(0))),
        "boundary": "forged",
    }
    forged = replace(theorem, **{field: values[field]})
    with pytest.raises(ValueError, match="noncanonical-intrinsic-resonance-theorem"):
        render_resonance_lean(forged)
    assert check_proof_core_bridge(forged).diagnostics == "theorem-artifact-replay-mismatch"


def test_seeded_source_mutations_all_break_byte_binding(tmp_path):
    source = render_resonance_lean(intrinsic_resonance_theorem())
    positions = (0, len(source) // 5, len(source) // 2, len(source) - 2)
    for index, position in enumerate(positions):
        replacement = "X" if source[position] != "X" else "Y"
        mutated = source[:position] + replacement + source[position + 1:]
        path = tmp_path / f"mutated-{index}.lean"
        path.write_text(mutated, encoding="utf-8")
        report = check_proof_core_bridge(export_path=path)
        assert report.status == "blocked"
        assert report.diagnostics == "generated-lean-source-drift"


@pytest.mark.parametrize("payload,token", [
    ("theorem injected : True := by sorry\n", "sorry"),
    ("theorem injected : True := by admit\n", "admit"),
    ("theorem injected : True := sorryAx True true\n", "sorryAx"),
    ("axiom Injected : True\n", "axiom"),
    ("unsafe def injected : Nat := 0\n", "unsafe"),
])
def test_every_tcb_placeholder_token_is_fail_closed(tmp_path, payload, token):
    source = Path("proofs/lean/VeyraProofKernel.lean").read_text(encoding="utf-8")
    path = tmp_path / "VeyraProofKernel.lean"
    path.write_text(source + "\n" + payload, encoding="utf-8")
    report = check_proof_core_bridge(kernel_path=path)
    assert report.status == "blocked"
    assert report.diagnostics == f"forbidden-lean-placeholder:{token}"


def test_arithmetic_tcb_drift_blocks_before_compilation(tmp_path):
    source = Path("proofs/lean/VeyraNativeArithmetic.lean").read_text(encoding="utf-8")
    path = tmp_path / "VeyraNativeArithmetic.lean"
    path.write_text(source + "\n-- semantic drift\n", encoding="utf-8")
    report = check_proof_core_bridge(arithmetic_path=path)
    assert report.status == "blocked"
    assert report.diagnostics == "reviewed-lean-tcb-drift"


def test_default_report_cache_is_keyed_by_live_source_hashes(tmp_path, monkeypatch):
    lean_dir = tmp_path / "lean"
    lean_dir.mkdir()
    for name in (
        "VeyraNativeArithmetic.lean", "VeyraProofKernel.lean",
        "VeyraProofSoundness.lean", "VeyraProofResonance.lean",
    ):
        shutil.copy2(Path("proofs/lean") / name, lean_dir / name)
    monkeypatch.setattr(bridge_module, "LEAN_DIR", lean_dir)
    bridge_module._cached_default_report.cache_clear()
    assert proof_core_bridge_report().status == "checked"
    kernel = lean_dir / "VeyraProofKernel.lean"
    kernel.write_text(kernel.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    changed = proof_core_bridge_report()
    assert changed.status == "blocked"
    assert changed.diagnostics == "reviewed-lean-tcb-drift"


def test_unpinned_lean_fallback_is_not_accepted(monkeypatch):
    monkeypatch.setattr(bridge_module.shutil, "which", lambda _: None)
    report = check_proof_core_bridge()
    assert report.status == "blocked"
    assert report.diagnostics == "pinned-elan-not-found"


@pytest.mark.parametrize("version", [
    "Lean (version 4.30.0-rc20, commit deadbeef, Release)",
    "Lean (version 4.30.0-rc2-evil, commit deadbeef, Release)",
    "fake version 4.30.0-rc2",
])
def test_pinned_version_match_is_exact(monkeypatch, version):
    monkeypatch.setattr(
        bridge_module.subprocess, "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=version, stderr=""),
    )
    with pytest.raises(ValueError, match="pinned-lean-version-mismatch"):
        bridge_module._toolchain_identity(["/not-inspected-on-mismatch"])


def test_lean_command_executes_resolved_content_pinned_binary(tmp_path, monkeypatch):
    lean = tmp_path / "lean"
    lean.write_bytes(b"reviewed-lean-binary")
    monkeypatch.setattr(bridge_module, "EXPECTED_LEAN_BINARY_SHA256", bridge_module._sha(lean.read_bytes()))
    monkeypatch.setattr(bridge_module.shutil, "which", lambda _: "/runner/elan")
    monkeypatch.setattr(
        bridge_module.subprocess, "run",
        lambda command, **_kwargs: SimpleNamespace(
            returncode=0, stdout=str(lean) + "\n", stderr=""
        ) if command == ["/runner/elan", "which", "lean"] else (_ for _ in ()).throw(AssertionError(command)),
    )
    command = bridge_module._lean_command()
    assert command == [str(lean), "-DwarningAsError=true"]
    assert command[0] != "/runner/elan"


def test_lean_command_rejects_unreviewed_compiler_content(tmp_path, monkeypatch):
    lean = tmp_path / "lean"
    lean.write_bytes(b"attacker-compiler")
    monkeypatch.setattr(bridge_module.shutil, "which", lambda _: "/runner/elan")
    monkeypatch.setattr(
        bridge_module.subprocess, "run",
        lambda command, **_kwargs: SimpleNamespace(
            returncode=0, stdout=str(lean) + "\n", stderr=""
        ) if command == ["/runner/elan", "which", "lean"] else (_ for _ in ()).throw(AssertionError(command)),
    )
    assert bridge_module._lean_command() == []


def test_toolchain_identity_is_content_bound_not_filesystem_metadata(tmp_path, monkeypatch):
    lean = tmp_path / "lean"
    lean.write_bytes(b"reviewed-lean-binary")
    monkeypatch.setattr(bridge_module, "EXPECTED_LEAN_BINARY_SHA256", bridge_module._sha(lean.read_bytes()))
    version = "Lean (version 4.30.0-rc2, x86_64-test, commit deadbeef, Release)"
    monkeypatch.setattr(
        bridge_module.subprocess, "run",
        lambda command, **_kwargs: SimpleNamespace(returncode=0, stdout=version, stderr="")
        if command[-1] == "--version" else (_ for _ in ()).throw(AssertionError(command)),
    )
    command = [str(lean), "-DwarningAsError=true"]
    first = bridge_module._toolchain_identity(command)
    lean.touch()
    second = bridge_module._toolchain_identity(command)
    assert first == second
    assert f"sha256={bridge_module.EXPECTED_LEAN_BINARY_SHA256}" in first
    assert "binary=lean" in first
    assert "path=" not in first and "inode=" not in first and "mtime=" not in first


def test_compile_uses_captured_snapshot_after_original_source_mutation(tmp_path, monkeypatch):
    lean_dir = tmp_path / "mutable-originals"
    lean_dir.mkdir()
    names = (
        "VeyraNativeArithmetic.lean", "VeyraProofKernel.lean",
        "VeyraProofSoundness.lean", "VeyraProofResonance.lean",
    )
    for name in names:
        shutil.copy2(Path("proofs/lean") / name, lean_dir / name)
    original_compile = bridge_module._compile_chain

    def mutate_then_compile(command, snapshot):
        assert all(snapshot.root in path.parents for _, path in snapshot.paths)
        kernel = lean_dir / "VeyraProofKernel.lean"
        kernel.write_text("this is not Lean\n", encoding="utf-8")
        return original_compile(command, snapshot)

    monkeypatch.setattr(bridge_module, "BUILD_DIR", tmp_path / "build")
    monkeypatch.setattr(bridge_module, "_compile_chain", mutate_then_compile)
    report = check_proof_core_bridge(
        arithmetic_path=lean_dir / names[0], kernel_path=lean_dir / names[1],
        soundness_path=lean_dir / names[2], export_path=lean_dir / names[3],
    )
    assert report.status == "checked"
    assert report.lean_checked
