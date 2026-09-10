"""Fail-closed R11 Lean bridge, continuity, and anti-drift tests."""
from __future__ import annotations
from collections.abc import Mapping
from dataclasses import replace
import gc
from hashlib import sha256
import inspect
import logging
import os
from pathlib import Path
import sys
import subprocess
from types import MappingProxyType, SimpleNamespace
from unittest.mock import Mock
import pytest
from src.core.certify_observer_core import certify_observer_core_r11
from src.core.observer_core_bridge import BRIDGE_ID, CHECKED_DIAGNOSTICS, SOURCE_PATHS, THEOREM_IDS, ObserverCoreBridgeReport, check_observer_core_bridge, verify_observer_core_bridge_report
from src.core.observer_core_bridge_report import read_exact_regular_source, valid_digest_manifest, valid_observer_core_bridge_report_shape, valid_object_manifest, valid_r10_continuity_report_shape, valid_source_origins
from src.core.observer_core_lean_render import canonical_observer_artifact, canonical_observer_lean, render_observer_core_lean
from src.core.observer_core_manifest import _EXPECTED_R11_TCB_DIGEST_ROWS, EXPECTED_R11_TCB_DIGESTS
from src.core.observer_core_objects import _EXPECTED_LEAN_OBJECT_ROWS, EXPECTED_LEAN_OBJECTS
from src.core.observer_core_snapshot import SNAPSHOT_NAMES, materialize_observer_snapshot, valid_snapshot_names
from src.core.proof_elaboration_runtime_guard import guarded_closures_run
from src.core.proof_elaboration_bridge import ProofElaborationBridgeReport
from src.core.layer_derivations import META_LAYERS, SHADOW_LAYERS, WITNESS_SOURCES
from src.core.layer_theorem_contracts import theorem_contract_registry
import src.core.certify_observer_core as certificate_module
import src.core.observer_core_bridge as bridge_module
import src.core.observer_core_bridge_io as bridge_io
import src.core.observer_core_bridge_report as bridge_report_module
logger = logging.getLogger(__name__)

@pytest.fixture(scope="module")
def checked_report() -> ObserverCoreBridgeReport:
    report = check_observer_core_bridge()
    assert report.status == "checked", report.diagnostics
    return report


def _r10(report: ObserverCoreBridgeReport) -> SimpleNamespace:
    return SimpleNamespace(binding_digest=report.r10_binding_digest, status="checked")


def test_exact_manifest_artifact_r10_and_nine_stage_chain_are_bound(checked_report: ObserverCoreBridgeReport) -> None:
    artifact = canonical_observer_artifact()
    assert checked_report.bridge_id == BRIDGE_ID == "veyra.lean.r11.observer-echo-tcb.v1"
    assert checked_report.theorem_ids == THEOREM_IDS
    assert checked_report.artifact_digest == artifact.proof_digest
    assert checked_report.source_digests == tuple(EXPECTED_R11_TCB_DIGESTS.items()) and len(checked_report.source_digests) == 34
    assert checked_report.diagnostics == CHECKED_DIAGNOSTICS
    assert all((checked_report.artifact_checked, checked_report.r10_checked,
                checked_report.manifest_checked, checked_report.source_bound,
                checked_report.snapshot_checked, checked_report.lean_checked))
    assert "does not renew or widen the R8 promotion contract" in checked_report.boundary
    assert verify_observer_core_bridge_report(checked_report)

def test_generated_export_binds_exact_facts_and_has_no_dispatch_or_fallback(checked_report: ObserverCoreBridgeReport) -> None:
    artifact = canonical_observer_artifact()
    generated = canonical_observer_lean(artifact, checked_report.r10_binding_digest)
    for index in range(1, 7):
        assert f"THM_R11_{index:03d}".encode() in generated
    for fact in (b"observerAstDigest", b"observerResultDigest", b"observerArtifactDigest",
                 b"observerArtifactSupport", b"r10BindingDigest", b"canonicalOutcomeAndSeparation"):
        assert fact in generated
    assert artifact.proof_digest.encode() in generated and checked_report.r10_binding_digest.encode() in generated
    assert not any(word in generated for word in (b"sorry", b"admit", b"axiom", b"unsafe"))
    source = inspect.getsource(render_observer_core_lean)
    assert "match artifact.theorem_id" not in source and "fallback" not in source
    forged = replace(artifact, proof_digest="0" * 64)
    with pytest.raises(ValueError, match="r11-noncanonical-observer-artifact"):
        render_observer_core_lean(forged, checked_report.r10_binding_digest)

def test_manifest_snapshot_and_object_tables_are_exact_immutable_types(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, checked_report: ObserverCoreBridgeReport) -> None:
    assert all(type(proxy) is MappingProxyType for proxy in (
        EXPECTED_R11_TCB_DIGESTS, SOURCE_PATHS, SNAPSHOT_NAMES, EXPECTED_LEAN_OBJECTS,
    ))
    assert tuple(EXPECTED_R11_TCB_DIGESTS) == (*tuple(SOURCE_PATHS), "lean_export")
    assert tuple(EXPECTED_LEAN_OBJECTS) == tuple(SNAPSHOT_NAMES)[:-1]
    assert not valid_source_origins(SOURCE_PATHS, SOURCE_PATHS) and valid_source_origins(dict(SOURCE_PATHS), SOURCE_PATHS)
    assert valid_digest_manifest(EXPECTED_R11_TCB_DIGESTS, (*tuple(SOURCE_PATHS), "lean_export"))
    assert valid_object_manifest(EXPECTED_LEAN_OBJECTS, tuple(SNAPSHOT_NAMES)[:-1])
    assert valid_snapshot_names(SNAPSHOT_NAMES)
    for filename, size, digest in EXPECTED_LEAN_OBJECTS.values():
        assert type(filename) is str and type(size) is int and size > 0
        assert type(digest) is str and len(digest) == 64
    digest_backing = next(row for row in gc.get_referents(EXPECTED_R11_TCB_DIGESTS) if type(row) is dict)
    object_backing = next(row for row in gc.get_referents(EXPECTED_LEAN_OBJECTS) if type(row) is dict)
    snapshot_backing = next(row for row in gc.get_referents(SNAPSHOT_NAMES) if type(row) is dict)
    saved = tuple(tuple(backing.items()) for backing in (digest_backing, object_backing, snapshot_backing))
    try:
        digest_backing[_EXPECTED_R11_TCB_DIGEST_ROWS[0][0]] = "0" * 64
        assert not valid_digest_manifest(EXPECTED_R11_TCB_DIGESTS, (*tuple(SOURCE_PATHS), "lean_export"))
        digest_backing.clear()
        digest_backing.update(saved[0])
        object_name, (filename, size, _) = _EXPECTED_LEAN_OBJECT_ROWS[0]
        object_backing[object_name] = (filename, size, "0" * 64)
        assert not valid_object_manifest(EXPECTED_LEAN_OBJECTS, tuple(SNAPSHOT_NAMES)[:-1])
        snapshot_backing["lean_arithmetic"] = "../VeyraNativeArithmetic.lean"
        assert not valid_snapshot_names(SNAPSHOT_NAMES)
        with pytest.raises(ValueError, match="r11-snapshot-input-invalid"):
            materialize_observer_snapshot(tmp_path / "blocked", {}, "0" * 64)
        assert not (tmp_path / "blocked").exists()
        guards = {name: Mock(side_effect=AssertionError(name)) for name in ("_verified_r10", "_read_sources", "lean_command", "toolchain_identity", "materialize_snapshot", "compile_snapshot")}
        for name, guard in guards.items():
            monkeypatch.setattr(bridge_module, name, guard)
        blocked = check_observer_core_bridge()
        assert blocked.status == "blocked" and blocked.diagnostics == "r11-snapshot-name-manifest-invalid"
        assert not verify_observer_core_bridge_report(checked_report)
        assert bridge_module._default_trust_key() == "blocked:r11-snapshot-name-manifest-invalid"
        assert all(not guard.called for guard in guards.values())
    finally:
        for backing, rows in zip((digest_backing, object_backing, snapshot_backing), saved, strict=True):
            backing.clear()
            backing.update(rows)
    assert valid_digest_manifest(EXPECTED_R11_TCB_DIGESTS, (*tuple(SOURCE_PATHS), "lean_export"))
    assert valid_object_manifest(EXPECTED_LEAN_OBJECTS, tuple(SNAPSHOT_NAMES)[:-1])
    assert valid_snapshot_names(SNAPSHOT_NAMES)

def test_source_origin_snapshot_rejects_transplant_and_hostile_mappings(tmp_path: Path) -> None:
    paths = dict(SOURCE_PATHS)
    transplant = tmp_path / SOURCE_PATHS["observer_semantics"].name
    transplant.write_bytes(SOURCE_PATHS["observer_semantics"].read_bytes())
    paths["observer_semantics"] = transplant
    assert not valid_source_origins(paths, SOURCE_PATHS)
    backing = dict(SOURCE_PATHS)
    mutable_proxy = MappingProxyType(backing)
    backing["observer_semantics"] = transplant
    assert not valid_source_origins(mutable_proxy, SOURCE_PATHS)
    with pytest.raises(ValueError, match="r11-source-path-set-invalid"):
        bridge_module._read_sources(mutable_proxy, b"")

    class Stateful(Mapping):
        def __init__(self) -> None:
            self.calls = 0
        def _trap(self, *_args):
            self.calls += 1
            raise RuntimeError("mapping trap")
        __len__ = __iter__ = __getitem__ = items = _trap
    hostile = Stateful()
    proxy = MappingProxyType(hostile)
    assert not valid_source_origins(proxy, SOURCE_PATHS) and hostile.calls == 0
    assert not valid_digest_manifest(proxy, tuple(row[0] for row in _EXPECTED_R11_TCB_DIGEST_ROWS))
    assert not valid_object_manifest(proxy, tuple(row[0] for row in _EXPECTED_LEAN_OBJECT_ROWS))
    assert not valid_snapshot_names(proxy)
    with pytest.raises(ValueError, match="r11-source-path-set-invalid"):
        bridge_module._read_sources(proxy, b"")
    assert hostile.calls == 0

def test_source_reader_rejects_ancestor_symlink_and_live_remap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory = tmp_path / "reviewed"
    directory.mkdir()
    source = directory / "source.py"
    source.write_bytes(b"reviewed-source")
    alias = tmp_path / "alias"
    alias.symlink_to(directory, target_is_directory=True)
    with pytest.raises(ValueError, match="r11-source-ancestor-shape-invalid"):
        read_exact_regular_source(alias / source.name)
    original_read, remapped = bridge_report_module.os.read, False
    def racing_read(descriptor: int, size: int) -> bytes:
        nonlocal remapped
        data = original_read(descriptor, size)
        if not remapped:
            remapped = True
            moved = tmp_path / "moved"
            directory.rename(moved)
            directory.symlink_to(moved, target_is_directory=True)
        return data

    monkeypatch.setattr(bridge_report_module.os, "read", racing_read)
    with pytest.raises(ValueError, match="r11-source-ancestor-raced"):
        read_exact_regular_source(source)

def test_source_and_export_drift_block_before_lean(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, checked_report: ObserverCoreBridgeReport,
) -> None:
    monkeypatch.setattr(bridge_module, "_verified_r10", lambda: _r10(checked_report))
    paths = dict(SOURCE_PATHS)
    changed = tmp_path / "observer_core_semantics.py"
    changed.write_bytes(paths["observer_semantics"].read_bytes() + b"\n# drift\n")
    paths["observer_semantics"] = changed
    blocked = check_observer_core_bridge(paths)
    assert blocked.status == "blocked" and blocked.diagnostics == "r11-source-path-set-invalid"
    generated = canonical_observer_lean(canonical_observer_artifact(), checked_report.r10_binding_digest)
    blocked = check_observer_core_bridge(generated_export=generated + b"\n")
    assert blocked.diagnostics == "r11-generated-lean-source-drift"

def test_report_forgery_and_continuity_subclasses_are_rejected(
    monkeypatch: pytest.MonkeyPatch, checked_report: ObserverCoreBridgeReport,
) -> None:
    monkeypatch.setattr(bridge_module, "_verified_r10", lambda: _r10(checked_report))
    monkeypatch.setattr(bridge_module, "lean_command", lambda: ["lean"])
    monkeypatch.setattr(bridge_module, "toolchain_identity", lambda _command: checked_report.toolchain)
    monkeypatch.setattr(bridge_module, "materialize_snapshot", lambda *_args: object())
    forged = replace(checked_report, binding_digest="0" * 64)
    assert not verify_observer_core_bridge_report(forged)
    class AlwaysEqual(str):
        def __eq__(self, _other: object) -> bool: return True
        def __ne__(self, _other: object) -> bool: return False
        __hash__ = str.__hash__
    forged = replace(
        bridge_module._blocked("test"), status="checked",
        binding_digest=AlwaysEqual("forged"),
    )
    assert not valid_observer_core_bridge_report_shape(forged)
    assert not verify_observer_core_bridge_report(forged)
    r10 = ProofElaborationBridgeReport(
        status="checked", theorem_ids=(), elaboration_binding_digest="",
        surface_syntax_digest="", semantic_digest="", r7_artifact_digest="",
        r9_binding_digest="", source_digests=(), snapshot_digest="",
        binding_digest="", artifact_checked=True, manifest_checked=True,
        source_bound=True, snapshot_checked=True, lean_checked=True,
        toolchain="", diagnostics="", boundary="",
    )
    forged_r10 = replace(r10, binding_digest=AlwaysEqual("forged"))
    assert not valid_r10_continuity_report_shape(forged_r10)

def test_certificate_gates_exact_shape(monkeypatch: pytest.MonkeyPatch, checked_report: ObserverCoreBridgeReport) -> None:
    forged = replace(bridge_module._blocked("test"), theorem_ids=1, source_digests=2)
    monkeypatch.setattr(certificate_module, "observer_core_bridge_report", lambda: forged)
    assert not certify_observer_core_r11().passed
    monkeypatch.setattr(certificate_module, "observer_core_bridge_report", lambda: checked_report)
    monkeypatch.setattr(certificate_module, "verify_observer_core_bridge_report", lambda _report: True)
    certificate = certify_observer_core_r11()
    assert certificate.passed and certificate.name == "observer_core_r11"
    assert "theorems=6/6" in certificate.detail and "sources=34/34" in certificate.detail

def test_cached_snapshot_tamper(monkeypatch: pytest.MonkeyPatch, checked_report: ObserverCoreBridgeReport) -> None:
    captured = bridge_io.BUILD_DIR / "snapshots" / checked_report.snapshot_digest / "VeyraObserverCore.lean"
    original, mode = captured.read_bytes(), captured.stat().st_mode
    monkeypatch.setattr(bridge_module, "_verified_r10", lambda: _r10(checked_report))
    monkeypatch.setattr(bridge_module, "lean_command", lambda: ["lean"])
    monkeypatch.setattr(bridge_module, "toolchain_identity", lambda _command: checked_report.toolchain)
    try:
        captured.chmod(0o600)
        captured.write_bytes(original + b"\n")
        captured.chmod(0o400)
        assert not verify_observer_core_bridge_report(checked_report)
    finally:
        captured.chmod(0o600)
        captured.write_bytes(original)
        captured.chmod(mode & 0o777)

def test_forged_current_and_hardlinked_olean_are_rejected(tmp_path: Path) -> None:
    stage = tmp_path / "01-VeyraNativeArithmetic"
    stage.mkdir()
    output = stage / "VeyraNativeArithmetic.olean"
    output.write_bytes(b"forged-object")
    with pytest.raises(ValueError, match="r11-lean-object-digest-mismatch"):
        bridge_io._validate_fresh_object(tmp_path, "lean_arithmetic", output)
    alias = tmp_path / "alias.olean"
    os.link(output, alias)
    with pytest.raises(ValueError, match="r11-lean-object-shape-mismatch"):
        bridge_io._validate_fresh_object(tmp_path, "lean_arithmetic", output)

def test_reviewed_object_modify_restore_is_detected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    stage = tmp_path / "01-Reviewed"
    stage.mkdir()
    target = stage / "Reviewed.olean"
    content = b"reviewed-object"
    target.write_bytes(content)
    records = (("reviewed", ("Reviewed.olean", len(content), sha256(content).hexdigest())),)
    monkeypatch.setattr(bridge_io, "_EXPECTED_LEAN_OBJECT_ROWS", records)
    closure = bridge_io._object_closure(tmp_path, (("reviewed", target),))
    script = (
        "from pathlib import Path; import sys; p=Path(sys.argv[1]); "
        "old=p.read_bytes(); p.write_bytes(b'forged'); p.write_bytes(old)"
    )
    with pytest.raises(ValueError, match="r10-runtime-integrity-drift"):
        guarded_closures_run([sys.executable, "-c", script, str(target)], cwd=tmp_path, env=os.environ,
                             timeout=10, closures=(closure,))

def test_preexisting_import_and_loader_shadow_surfaces_are_closed(tmp_path: Path) -> None:
    source = tmp_path / "Captured.lean"
    source.write_bytes(b"import Injected\n")
    (tmp_path / "Injected.olean").write_bytes(b"forged-import")
    records = ((source, source.stat().st_size, sha256(source.read_bytes()).digest()),)
    closure = bridge_io._reviewed_closure("r11-snapshot-source", tmp_path, records)
    with pytest.raises(ValueError, match="r10-r11-snapshot-source-parent-shape-mismatch"):
        guarded_closures_run([sys.executable, "-c", "pass"], cwd=tmp_path, env=os.environ,
                             timeout=10, closures=(closure,))
    absences = bridge_io._default_runtime_absences()
    assert any(path.name == "glibc-hwcaps" for path in absences)
    assert {row[0] for row in EXPECTED_LEAN_OBJECTS.values()} <= {path.name for path in absences}

def test_r11_toolchain_identity_excludes_host_local_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    lean = tmp_path / "lean"
    lean.write_bytes(b"x" * 9024)
    version = "Lean (version 4.30.0-rc2, x86_64-test, commit deadbeef, Release)"
    monkeypatch.setattr(
        bridge_io,
        "guarded_lean_run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0, stdout=version, stderr="",
        ),
    )
    monkeypatch.setattr(
        bridge_io,
        "_runtime_identity",
        lambda: "merkle=abc|files=2365|bytes=522231408",
    )
    first = bridge_io.toolchain_identity([str(lean)])
    os.utime(lean, None)
    second = bridge_io.toolchain_identity([str(lean)])
    assert first == second
    assert "toolchain=leanprover/lean4:v4.30.0-rc2" in first
    assert "sha256=" in first and "binary=lean" in first
    assert "path=" not in first and "inode=" not in first and "mtime=" not in first


def test_toolchain_timeout_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(*_args: object, **_kwargs: object) -> object:
        raise subprocess.TimeoutExpired("lean", 30)
    monkeypatch.setattr(bridge_io, "guarded_lean_run", timeout)
    with pytest.raises(ValueError, match="r11-pinned-lean-version-timeout"):
        bridge_io.toolchain_identity(["lean"])

def test_r11_does_not_promote_layers_or_change_taxonomy() -> None:
    logger.info("R11 nonpromotion regression start")
    contracts = theorem_contract_registry()
    assert tuple(contracts) == ("intrinsic-resonance", "intrinsic-observer-echo")
    assert all(not contract.theorem_id.startswith("THM-R11") for contract in contracts.values())
    assert (len(contracts), len(WITNESS_SOURCES), len(SHADOW_LAYERS), len(META_LAYERS)) == (2, 4, 25, 5)
    logger.info("R11 nonpromotion regression complete contracts=%d", len(contracts))
