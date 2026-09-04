from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType, SimpleNamespace

import pytest

import src.core.intrinsic_mode_bridge as bridge_module
from src.core.intrinsic_mode_bridge import (
    CHECKED_DIAGNOSTICS, SOURCE_PATHS, THEOREM_IDS, check_intrinsic_mode_bridge,
    intrinsic_mode_bridge_report, verify_intrinsic_mode_bridge_report,
)
from src.core.intrinsic_mode_manifest import EXPECTED_R9_TCB_DIGESTS


def _copied_paths(tmp_path):
    copied = {}
    for name, source in SOURCE_PATHS.items():
        target = tmp_path / source.name
        target.write_bytes(source.read_bytes())
        copied[name] = target
    return MappingProxyType(copied)


def test_r9_report_binds_all_sources_r7_and_eight_theorems():
    report = intrinsic_mode_bridge_report()
    assert report.status == "checked"
    assert report.theorem_ids == THEOREM_IDS
    assert report.diagnostics == CHECKED_DIAGNOSTICS
    assert report.r7_artifact_checked and report.manifest_checked
    assert report.source_bound and report.lean_checked
    assert len(report.source_digests) == len(EXPECTED_R9_TCB_DIGESTS) == 16
    assert dict(report.source_digests) == EXPECTED_R9_TCB_DIGESTS
    assert len(report.r7_artifact_digest) == len(report.r7_bridge_digest) == 64
    assert len(report.binding_digest) == 64
    assert verify_intrinsic_mode_bridge_report(report)


@pytest.mark.parametrize("source_key,reason", [
    ("python_transport", "r9-generated-lean-source-drift"),
    ("native_runtime", "r9-generated-lean-source-drift"),
    ("lean_semantics", "r9-reviewed-tcb-drift"),
    ("lean_transport", "r9-generated-lean-source-drift"),
])
def test_any_reviewed_source_drift_blocks_before_compilation(tmp_path, source_key, reason):
    paths = _copied_paths(tmp_path)
    paths[source_key].write_bytes(paths[source_key].read_bytes() + b"\n")
    report = check_intrinsic_mode_bridge(paths)
    assert report.status == "blocked"
    assert report.diagnostics == reason
    assert not report.lean_checked


def test_generated_export_drift_has_a_specific_fail_closed_reason(tmp_path):
    paths = _copied_paths(tmp_path)
    paths["lean_export"].write_text("import VeyraProofResonance\n")
    report = check_intrinsic_mode_bridge(paths)
    assert report.status == "blocked"
    assert report.diagnostics == "r9-generated-lean-source-drift"


def test_placeholder_is_rejected_even_with_manifest_rebound(tmp_path, monkeypatch):
    paths = _copied_paths(tmp_path)
    paths["lean_semantics"].write_bytes(paths["lean_semantics"].read_bytes() + b"\n-- sorry\n")
    rebound = {
        name: sha256(path.read_bytes()).hexdigest() for name, path in paths.items()
    }
    monkeypatch.setattr(bridge_module, "EXPECTED_R9_TCB_DIGESTS", rebound)
    report = check_intrinsic_mode_bridge(paths)
    assert report.status == "blocked"
    assert report.diagnostics == "r9-forbidden-lean-placeholder:sorry"


def test_incomplete_source_path_map_is_rejected(tmp_path):
    paths = dict(_copied_paths(tmp_path))
    paths.pop("lean_export")
    report = check_intrinsic_mode_bridge(paths)
    assert report.status == "blocked"
    assert report.diagnostics == "r9-source-path-set-invalid"


def test_poisoned_cached_report_is_independently_rehashed(monkeypatch):
    checked = intrinsic_mode_bridge_report()
    forged = replace(
        checked, binding_digest="0" * 64, source_digests=(), toolchain="",
        manifest_checked=False, lean_checked=False,
    )
    monkeypatch.setattr(bridge_module, "_cached_default_report", lambda _: forged)
    report = bridge_module.intrinsic_mode_bridge_report()
    assert report.status == "blocked"
    assert report.diagnostics == "cached-r9-bridge-integrity-mismatch"


def test_r9_lean_command_executes_resolved_content_pinned_binary(tmp_path, monkeypatch):
    lean = tmp_path / "lean"
    lean.write_bytes(b"reviewed-lean-binary")
    monkeypatch.setattr(bridge_module, "EXPECTED_LEAN_BINARY_SHA256", sha256(lean.read_bytes()).hexdigest())
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


def test_r9_lean_command_rejects_unreviewed_compiler_content(tmp_path, monkeypatch):
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


def test_r9_toolchain_identity_is_content_bound_not_filesystem_metadata(tmp_path, monkeypatch):
    lean = tmp_path / "lean"
    lean.write_bytes(b"reviewed-lean-binary")
    monkeypatch.setattr(bridge_module, "EXPECTED_LEAN_BINARY_SHA256", sha256(lean.read_bytes()).hexdigest())
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


def test_toolchain_and_boundary_are_exact_not_generic_claims():
    report = intrinsic_mode_bridge_report()
    assert "4.30.0-rc2" in report.toolchain
    assert "fixed-anchor unary IntrinsicMode image" in report.boundary
    assert "no generic Mode" in report.boundary
