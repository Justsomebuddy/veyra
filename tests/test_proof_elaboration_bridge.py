from dataclasses import replace
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys
from types import MappingProxyType

import pytest

from src.core.certify_proof_elaboration import certify_proof_elaboration_r10
from src.core.proof_elaboration_bridge import (
    CHECKED_DIAGNOSTICS, SOURCE_PATHS, THEOREM_IDS,
    _cached_default_report, check_proof_elaboration_bridge,
    proof_elaboration_bridge_report, verify_proof_elaboration_bridge_report,
)
from src.core.proof_elaboration_canonical import (
    CANONICAL_SOURCE, canonical_elaboration, canonical_elaboration_lean,
)
from src.core.proof_elaboration_manifest import EXPECTED_R10_TCB_DIGESTS
import src.core.proof_elaboration_bridge as bridge_module
import src.core.proof_elaboration_bridge_io as bridge_io
from src.core.proof_elaboration_runtime_guard import (
    ProtectedClosure, guarded_closures_run, guarded_subprocess_run,
)
from src.core.proof_elaboration_toolchain import (
    GUARDED_INPUT_DOMAIN, records_digest, runtime_paths_digest,
)


def _closure(
    label: str, path: Path, root: Path, *, exact_parents: bool = False,
) -> ProtectedClosure:
    data = path.read_bytes()
    expected = records_digest(
        ((path, len(data), sha256(data).digest()),), root, GUARDED_INPUT_DOMAIN,
    )
    return ProtectedClosure(
        label, (path,), root, GUARDED_INPUT_DOMAIN, expected, exact_parents,
    )


def test_exact_manifest_snapshot_and_generated_lean_bridge_are_checked():
    report = check_proof_elaboration_bridge()
    artifact, _ = canonical_elaboration()
    assert report.status == "checked"
    assert report.theorem_ids == THEOREM_IDS
    assert report.diagnostics == CHECKED_DIAGNOSTICS
    assert report.elaboration_binding_digest == artifact.binding_digest
    assert report.r9_binding_digest == artifact.r9_binding_digest
    assert len(report.source_digests) == 37
    assert report.source_digests == tuple(EXPECTED_R10_TCB_DIGESTS.items())
    assert report.artifact_checked and report.manifest_checked
    assert report.source_bound and report.snapshot_checked and report.lean_checked
    assert verify_proof_elaboration_bridge_report(report)


def test_generated_export_is_exact_source_replay_not_name_dispatch_or_fallback():
    generated = canonical_elaboration_lean()
    checked_in = Path("proofs/lean/VeyraProofElaboration.lean").read_bytes()
    assert checked_in == generated
    assert b"THM_R10_003_elaborated_proof_accepted" in generated
    assert b"THM_R10_005_structural_support_matches" in generated
    assert b"THM-R7-004" not in generated
    assert b"sorry" not in generated and b"admit" not in generated
    assert CANONICAL_SOURCE.startswith(b"(veyra-proof 1")


def test_report_field_forgery_is_rejected_exactly():
    report = proof_elaboration_bridge_report()
    for field in (
        "elaboration_binding_digest", "surface_syntax_digest", "semantic_digest",
        "r7_artifact_digest", "r9_binding_digest", "snapshot_digest",
        "binding_digest", "toolchain", "diagnostics",
    ):
        forged = replace(report, **{field: "0" * 64})
        assert not verify_proof_elaboration_bridge_report(forged)


def test_independent_report_verification_requires_fresh_lean_compile(monkeypatch):
    report = proof_elaboration_bridge_report()
    monkeypatch.setattr(
        bridge_module, "compile_snapshot", lambda command, snapshot, sources: (False, "forced"),
    )
    assert not verify_proof_elaboration_bridge_report(report)


def test_r10_toolchain_identity_excludes_host_local_metadata(
    tmp_path, monkeypatch,
):
    lean = tmp_path / "lean"
    lean.write_bytes(b"x" * 9024)
    version = "Lean (version 4.30.0-rc2, x86_64-test, commit deadbeef, Release)"
    monkeypatch.setattr(
        bridge_io,
        "guarded_lean_run",
        lambda *_args, **_kwargs: type(
            "Result", (), {"returncode": 0, "stdout": version, "stderr": ""}
        )(),
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


def test_fake_path_and_elan_home_cannot_replace_direct_pinned_lean(tmp_path, monkeypatch):
    fake = tmp_path / "elan"
    fake.write_text("#!/bin/sh\nexit 0\n")
    fake.chmod(0o700)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("ELAN_HOME", str(tmp_path))
    command = bridge_io.lean_command()
    assert command[0] == str(bridge_io.LEAN_BINARY)
    assert bridge_io.toolchain_identity(command).startswith("Lean (version 4.30.0-rc2")


def test_inotify_guard_rejects_modify_then_restore_during_subprocess(tmp_path):
    watched = tmp_path / "runtime-copy.bin"
    watched.write_bytes(b"reviewed-runtime")
    paths = (watched,)
    expected = runtime_paths_digest(paths, tmp_path)
    script = (
        "from pathlib import Path; import sys; "
        "p=Path(sys.argv[1]); original=p.read_bytes(); "
        "p.write_bytes(b'forged-runtime'); p.write_bytes(original)"
    )
    with pytest.raises(ValueError, match="r10-runtime-integrity-drift"):
        guarded_subprocess_run(
            [sys.executable, "-c", script, str(watched)], cwd=tmp_path,
            env=os.environ, timeout=10, paths=paths, root=tmp_path,
            expected=expected,
        )


def test_guard_rejects_snapshot_source_modify_then_restore(tmp_path):
    source = tmp_path / "Captured.lean"
    source.write_bytes(b"theorem captured : True := by trivial\n")
    script = (
        "from pathlib import Path; import sys; p=Path(sys.argv[1]); "
        "old=p.read_bytes(); p.write_bytes(b'forged'); p.write_bytes(old)"
    )
    with pytest.raises(ValueError, match="r10-runtime-integrity-drift"):
        guarded_closures_run(
            [sys.executable, "-c", script, str(source)], cwd=tmp_path,
            env=os.environ, timeout=10, closures=(_closure("snapshot-source", source, tmp_path),),
        )


def test_guard_rejects_unwatched_hardlink_modify_then_restore(tmp_path):
    protected = tmp_path / "protected"
    aliases = tmp_path / "aliases"
    protected.mkdir()
    aliases.mkdir()
    target = protected / "prior.olean"
    alias = aliases / "alias.olean"
    target.write_bytes(b"reviewed-object")
    os.link(target, alias)
    script = (
        "from pathlib import Path; import sys; p=Path(sys.argv[1]); "
        "old=p.read_bytes(); p.write_bytes(b'forged-object'); p.write_bytes(old)"
    )
    with pytest.raises(ValueError, match="r10-runtime-integrity-drift"):
        guarded_closures_run(
            [sys.executable, "-c", script, str(alias)], cwd=tmp_path,
            env=os.environ, timeout=10, closures=(_closure("prior-object", target, protected),),
        )


def test_guard_rejects_ancestor_path_remap_then_restore(tmp_path):
    anchor = tmp_path / "trust-anchor"
    parent = anchor / "nested"
    parent.mkdir(parents=True)
    target = parent / "runtime.bin"
    target.write_bytes(b"reviewed-runtime")
    backup = tmp_path / "trust-anchor.backup"
    script = (
        "from pathlib import Path; import sys; a=Path(sys.argv[1]); b=Path(sys.argv[2]); "
        "a.rename(b); p=a/'nested'; p.mkdir(parents=True); f=p/'runtime.bin'; "
        "f.write_bytes(b'forged'); f.unlink(); p.rmdir(); a.rmdir(); b.rename(a)"
    )
    with pytest.raises(ValueError, match="r10-runtime-integrity-drift"):
        guarded_closures_run(
            [sys.executable, "-c", script, str(anchor), str(backup)], cwd=tmp_path,
            env=os.environ, timeout=10, closures=(_closure("runtime", target, anchor),),
        )


def test_reviewed_prior_olean_modify_then_restore_is_rejected(tmp_path):
    stage = tmp_path / "01-VeyraNativeArithmetic"
    stage.mkdir()
    output = stage / "VeyraNativeArithmetic.olean"
    command = bridge_io.lean_command() + [
        "-R", str(Path("proofs/lean").resolve()), "-o", str(output),
        str(Path("proofs/lean/VeyraNativeArithmetic.lean").resolve()),
    ]
    proc = subprocess.run(command, capture_output=True, check=False, timeout=30)
    assert proc.returncode == 0
    reviewed = bridge_io._object_closure(
        tmp_path, (("lean_arithmetic", output),),
    )
    script = (
        "from pathlib import Path; import sys; p=Path(sys.argv[1]); "
        "old=p.read_bytes(); p.write_bytes(b'forged-object'); p.write_bytes(old)"
    )
    with pytest.raises(ValueError, match="r10-runtime-integrity-drift"):
        guarded_closures_run(
            [sys.executable, "-c", script, str(output)], cwd=tmp_path,
            env=os.environ, timeout=10, closures=(reviewed,),
        )


def test_forged_current_olean_never_becomes_a_protected_input(tmp_path):
    stage = tmp_path / "01-VeyraNativeArithmetic"
    stage.mkdir()
    output = stage / "VeyraNativeArithmetic.olean"
    output.write_bytes(b"forged-object")
    with pytest.raises(ValueError, match="r10-lean-object-digest-mismatch"):
        bridge_io._validate_fresh_object(tmp_path, "lean_arithmetic", output)


def test_preexisting_unreviewed_import_injection_is_rejected(tmp_path):
    source = tmp_path / "Captured.lean"
    source.write_bytes(b"import Reviewed\n")
    (tmp_path / "Reviewed.olean").write_bytes(b"forged-import")
    with pytest.raises(ValueError, match="r10-snapshot-source-parent-shape-mismatch"):
        guarded_closures_run(
            [sys.executable, "-c", "pass"], cwd=tmp_path, env=os.environ, timeout=10,
            closures=(_closure(
                "snapshot-source", source, tmp_path, exact_parents=True,
            ),),
        )


def test_default_resolver_shadow_create_then_remove_is_rejected(tmp_path):
    target = tmp_path / "runtime.bin"
    shadow = tmp_path / "glibc-hwcaps"
    target.write_bytes(b"reviewed-runtime")
    base = _closure("runtime", target, tmp_path)
    guarded = replace(base, absent_paths=(shadow,))
    script = (
        "from pathlib import Path; import sys; p=Path(sys.argv[1]); p.mkdir(); "
        "f=p/'libInit_shared.so'; f.write_bytes(b'forged'); f.unlink(); p.rmdir()"
    )
    with pytest.raises(ValueError, match="r10-runtime-integrity-drift"):
        guarded_closures_run(
            [sys.executable, "-c", script, str(shadow)], cwd=tmp_path,
            env=os.environ, timeout=10, closures=(guarded,),
        )


def test_preexisting_default_resolver_shadow_is_rejected(tmp_path):
    target = tmp_path / "runtime.bin"
    shadow = tmp_path / "Injected.olean"
    target.write_bytes(b"reviewed-runtime")
    shadow.write_bytes(b"forged-import")
    guarded = replace(_closure("runtime", target, tmp_path), absent_paths=(shadow,))
    with pytest.raises(ValueError, match="r10-runtime-forbidden-path-present"):
        guarded_closures_run(
            [sys.executable, "-c", "pass"], cwd=tmp_path,
            env=os.environ, timeout=10, closures=(guarded,),
        )


def test_source_and_generated_export_drift_block_before_promotion(tmp_path):
    paths = dict(SOURCE_PATHS)
    changed = tmp_path / "proof_surface_parser.py"
    changed.write_bytes(paths["surface_parser"].read_bytes() + b"\n# drift\n")
    paths["surface_parser"] = changed
    assert check_proof_elaboration_bridge(paths).diagnostics == "r10-reviewed-tcb-drift"
    export = tmp_path / "VeyraProofElaboration.lean"
    export.write_bytes(paths["lean_export"].read_bytes() + b"\n")
    paths = dict(SOURCE_PATHS)
    paths["lean_export"] = export
    assert check_proof_elaboration_bridge(paths).diagnostics == "r10-generated-lean-source-drift"


def test_independent_snapshot_rehash_rejects_cached_byte_tamper(tmp_path, monkeypatch):
    report = proof_elaboration_bridge_report()
    monkeypatch.setattr(bridge_io, "BUILD_DIR", tmp_path)
    assert verify_proof_elaboration_bridge_report(report)
    captured = tmp_path / "snapshots" / report.snapshot_digest / "VeyraElaborationSemantics.lean"
    original = captured.read_bytes()
    captured.chmod(0o600)
    captured.write_bytes(original + b"\n")
    captured.chmod(0o400)
    assert not verify_proof_elaboration_bridge_report(report)


def test_cache_key_rehashes_live_sources_instead_of_returning_stale_checked(tmp_path, monkeypatch):
    checked = proof_elaboration_bridge_report()
    paths = dict(SOURCE_PATHS)
    drift = tmp_path / "proof_surface_codec.py"
    drift.write_bytes(paths["surface_codec"].read_bytes() + b"\n# cache drift\n")
    paths["surface_codec"] = drift
    monkeypatch.setattr(bridge_module, "SOURCE_PATHS", MappingProxyType(paths))
    _cached_default_report.cache_clear()
    blocked = proof_elaboration_bridge_report()
    assert checked.status == "checked"
    assert blocked.status == "blocked"
    assert blocked.diagnostics == "r10-reviewed-tcb-drift"


def test_r10_certificate_gates_exact_composite_evidence():
    certificate = certify_proof_elaboration_r10()
    assert certificate.passed
    assert certificate.name == "proof_elaboration_r10"
    assert "theorems=5/5" in certificate.detail
