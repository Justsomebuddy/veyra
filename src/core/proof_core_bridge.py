"""Fail-closed Python/Lean binding for the canonical R7 proof artifact."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import logging
import os
import re
import shutil
import subprocess

from .proof_core_codec import canonical_json
from .proof_core_lean_render import render_resonance_lean
from .proof_core_manifest import EXPECTED_TCB_DIGESTS, TCB_SCHEMA
from .proof_core_snapshot import LeanSourceSnapshot, materialize_lean_snapshot
from .proof_core_resonance import (
    IntrinsicResonanceTheorem, intrinsic_resonance_theorem,
    verify_intrinsic_theorem_binding,
)

from .paths import PROJECT_ROOT

logger = logging.getLogger(__name__)
LEAN_DIR = PROJECT_ROOT / "proofs" / "lean"
BUILD_DIR = PROJECT_ROOT / "data" / "tmp" / "r7-lean"
LEAN_TOOLCHAIN = "leanprover/lean4:v4.30.0-rc2"
LEAN_VERSION = "4.30.0-rc2"
THEOREM_IDS = tuple(f"THM-R7-{index:03d}" for index in range(1, 5))
PLACEHOLDER = re.compile(r"\b(?:sorryAx|sorry|admit|axiom|unsafe)\b")
CHECKED_DIAGNOSTICS = ";".join(
    f"{index}/4:{name}:rc=0" for index, name in enumerate(
        ("VeyraNativeArithmetic", "VeyraProofKernel", "VeyraProofSoundness", "VeyraProofResonance"), 1,
    )
)
CHECKED_BOUNDARY = "exact reviewed Python/Lean recurrence calculus and intrinsic reflexivity only; no cyclic/phase bridge"


@dataclass(frozen=True)
class ProofCoreBridgeReport:
    """Integrity, reviewed-manifest, and Lean-check report for one binding."""

    status: str
    theorem_ids: tuple[str, ...]
    artifact_digest: str
    kernel_digest: str
    soundness_digest: str
    export_digest: str
    binding_digest: str
    artifact_checked: bool
    source_bound: bool
    manifest_checked: bool
    lean_checked: bool
    toolchain: str
    diagnostics: str
    boundary: str


def _sha(data: bytes) -> str:
    logger.debug("proof_core_bridge._sha entry bytes=%d", len(data))
    result = sha256(data).hexdigest()
    logger.debug("proof_core_bridge._sha exit result=%s", result)
    return result


def _read(path: Path) -> bytes:
    logger.debug("proof_core_bridge._read entry path=%s", path)
    try:
        result = path.read_bytes()
    except OSError as exc:
        logger.error("proof_core_bridge._read error path=%s error=%s", path, exc)
        raise ValueError(f"proof-source-unreadable:{path.name}") from exc
    logger.debug("proof_core_bridge._read exit bytes=%d", len(result))
    return result


def _lean_command() -> list[str]:
    logger.debug("proof_core_bridge._lean_command entry")
    elan = shutil.which("elan")
    result = [elan, "run", LEAN_TOOLCHAIN, "lean", "-DwarningAsError=true"] if elan else []
    if not result:
        logger.error("proof_core_bridge._lean_command pinned elan unavailable")
    logger.debug("proof_core_bridge._lean_command exit result=%r", result)
    return result


def _toolchain_identity(command: list[str]) -> str:
    logger.debug("proof_core_bridge._toolchain_identity entry command=%r", command)
    proc = subprocess.run(command + ["--version"], text=True, capture_output=True, check=False)
    version = (proc.stdout or proc.stderr).strip()
    match = re.fullmatch(r"Lean \(version ([^,\s)]+)(?:,.*)?\)", version)
    if proc.returncode or match is None or match.group(1) != LEAN_VERSION:
        logger.error("proof_core_bridge._toolchain_identity mismatch rc=%d version=%r", proc.returncode, version)
        raise ValueError("pinned-lean-version-mismatch")
    stat = Path(command[0]).stat()
    result = f"{version}|path={command[0]}|inode={stat.st_ino}|size={stat.st_size}|mtime={stat.st_mtime_ns}"
    logger.debug("proof_core_bridge._toolchain_identity exit result=%s", result)
    return result


def _forbidden_source(source: bytes) -> tuple[str, ...]:
    logger.debug("proof_core_bridge._forbidden_source entry bytes=%d", len(source))
    try:
        text = source.decode("utf-8")
    except UnicodeDecodeError as exc:
        logger.error("proof_core_bridge._forbidden_source invalid UTF-8 error=%s", exc)
        raise ValueError("lean-source-not-utf8") from exc
    result = tuple(sorted(set(PLACEHOLDER.findall(text))))
    if result:
        logger.error("proof_core_bridge._forbidden_source tokens=%r", result)
    logger.debug("proof_core_bridge._forbidden_source exit count=%d", len(result))
    return result


def _compile_chain(
    command: list[str], snapshot: LeanSourceSnapshot,
) -> tuple[bool, str]:
    logger.debug("proof_core_bridge._compile_chain entry sources=%d", len(snapshot.paths))
    env = {**os.environ, "LEAN_PATH": str(snapshot.output_dir)}
    diagnostics = []
    for index, (source_name, source) in enumerate(snapshot.paths, start=1):
        name = source.stem
        emit = source_name != "export"
        output = ["-o", str(snapshot.output_dir / f"{name}.olean")] if emit else []
        proc = subprocess.run(command + ["-R", str(snapshot.root)] + output + [str(source)], cwd=snapshot.root, env=env, text=True, capture_output=True, check=False)
        combined = (proc.stderr or "") + (proc.stdout or "")
        diagnostics.append(f"{index}/4:{name}:rc={proc.returncode}")
        if proc.returncode or "warning:" in combined.lower():
            detail = combined.strip()[-600:]
            logger.error("proof_core_bridge._compile_chain blocked name=%s detail=%s", name, detail)
            return False, ";".join(diagnostics) + ":" + detail
    result = ";".join(diagnostics)
    logger.debug("proof_core_bridge._compile_chain exit diagnostics=%s", result)
    return True, result


def _blocked(
    reason: str, digest: str = "", artifact: bool = False,
    source: bool = False, manifest: bool = False,
) -> ProofCoreBridgeReport:
    logger.error("proof_core_bridge blocked reason=%s", reason)
    return ProofCoreBridgeReport(
        "blocked", (), digest, "", "", "", "", artifact, source, manifest,
        False, LEAN_TOOLCHAIN, reason,
        "no promotion unless theorem replay, reviewed TCB, byte binding, pinned Lean, and soundness all pass",
    )


def check_proof_core_bridge(
    theorem: IntrinsicResonanceTheorem | None = None,
    export_path: Path | None = None,
    arithmetic_path: Path | None = None,
    kernel_path: Path | None = None,
    soundness_path: Path | None = None,
) -> ProofCoreBridgeReport:
    """Rehash every input, enforce the reviewed TCB, then compile the chain."""
    logger.debug("check_proof_core_bridge entry custom_theorem=%s custom_paths=%s", theorem is not None, any((export_path, arithmetic_path, kernel_path, soundness_path)))
    item = intrinsic_resonance_theorem() if theorem is None else theorem
    digest = item.artifact.proof_digest
    if not verify_intrinsic_theorem_binding(item):
        return _blocked("theorem-artifact-replay-mismatch", digest)
    paths = {
        "arithmetic": Path(arithmetic_path or LEAN_DIR / "VeyraNativeArithmetic.lean"),
        "kernel": Path(kernel_path or LEAN_DIR / "VeyraProofKernel.lean"),
        "soundness": Path(soundness_path or LEAN_DIR / "VeyraProofSoundness.lean"),
        "export": Path(export_path or LEAN_DIR / "VeyraProofResonance.lean"),
    }
    try:
        sources = {name: _read(path) for name, path in paths.items()}
    except ValueError as exc:
        return _blocked(str(exc), digest, artifact=True)
    expected = render_resonance_lean(item).encode()
    if sources["export"] != expected:
        return _blocked("generated-lean-source-drift", digest, artifact=True)
    placeholders = _forbidden_source(b"\n".join(sources.values()))
    if placeholders:
        return _blocked("forbidden-lean-placeholder:" + ",".join(placeholders), digest, True, True)
    tcb_digests = {name: _sha(sources[name]) for name in EXPECTED_TCB_DIGESTS}
    if tcb_digests != EXPECTED_TCB_DIGESTS:
        return _blocked("reviewed-lean-tcb-drift", digest, True, True)
    command = _lean_command()
    if not command:
        return _blocked("pinned-elan-not-found", digest, True, True, True)
    try:
        toolchain = _toolchain_identity(command)
    except (OSError, ValueError) as exc:
        return _blocked(str(exc), digest, True, True, True)
    snapshot_key = _sha(canonical_json({
        "schema": "veyra-proof-lean-snapshot-v1",
        "sources": {name: _sha(source) for name, source in sources.items()},
        "toolchain": toolchain,
    }).encode())
    try:
        snapshot = materialize_lean_snapshot(BUILD_DIR, sources, snapshot_key)
    except ValueError as exc:
        return _blocked(str(exc), digest, True, True, True)
    lean_checked, diagnostics = _compile_chain(command, snapshot)
    if not lean_checked:
        return _blocked(diagnostics, digest, True, True, True)
    export_digest = _sha(sources["export"])
    binding = _sha(canonical_json({
        "schema": "veyra-proof-lean-binding-v1", "tcb_schema": TCB_SCHEMA,
        "artifact": digest, **tcb_digests, "export": export_digest,
        "toolchain": toolchain,
    }).encode())
    result = ProofCoreBridgeReport(
        "checked", THEOREM_IDS, digest, tcb_digests["kernel"],
        tcb_digests["soundness"], export_digest, binding, True, True, True,
        True, toolchain, diagnostics,
        CHECKED_BOUNDARY,
    )
    logger.debug("check_proof_core_bridge exit binding=%s", result.binding_digest)
    return result


def verify_proof_core_bridge_report(report: object) -> bool:
    """Independently rehash every trust field exposed by a cached checked report."""
    logger.debug("verify_proof_core_bridge_report entry type=%s", type(report).__name__)
    if type(report) is not ProofCoreBridgeReport or report.status != "checked":
        logger.error("verify_proof_core_bridge_report rejected shape/status")
        return False
    item = intrinsic_resonance_theorem()
    paths = {
        "arithmetic": LEAN_DIR / "VeyraNativeArithmetic.lean",
        "kernel": LEAN_DIR / "VeyraProofKernel.lean",
        "soundness": LEAN_DIR / "VeyraProofSoundness.lean",
        "export": LEAN_DIR / "VeyraProofResonance.lean",
    }
    try:
        sources = {name: _read(path) for name, path in paths.items()}
        command = _lean_command()
        if not command or sources["export"] != render_resonance_lean(item).encode():
            logger.error("verify_proof_core_bridge_report source/toolchain mismatch")
            return False
        toolchain = _toolchain_identity(command)
    except (OSError, ValueError):
        logger.exception("verify_proof_core_bridge_report trust input failure")
        return False
    tcb_digests = {name: _sha(sources[name]) for name in EXPECTED_TCB_DIGESTS}
    export_digest = _sha(sources["export"])
    binding = _sha(canonical_json({
        "schema": "veyra-proof-lean-binding-v1", "tcb_schema": TCB_SCHEMA,
        "artifact": item.artifact.proof_digest, **tcb_digests,
        "export": export_digest, "toolchain": toolchain,
    }).encode())
    expected = ProofCoreBridgeReport(
        "checked", THEOREM_IDS, item.artifact.proof_digest,
        EXPECTED_TCB_DIGESTS["kernel"], EXPECTED_TCB_DIGESTS["soundness"],
        export_digest, binding, True, True, True, True, toolchain,
        CHECKED_DIAGNOSTICS, CHECKED_BOUNDARY,
    )
    result = tcb_digests == EXPECTED_TCB_DIGESTS and report == expected
    if not result:
        logger.error("verify_proof_core_bridge_report exact report mismatch")
    logger.debug("verify_proof_core_bridge_report exit result=%s", result)
    return result


def _default_trust_key() -> str:
    logger.debug("proof_core_bridge._default_trust_key entry")
    item = intrinsic_resonance_theorem()
    command = _lean_command()
    if not command:
        result = "no-pinned-elan"
    else:
        try:
            toolchain = _toolchain_identity(command)
            files = [
                LEAN_DIR / "VeyraNativeArithmetic.lean", LEAN_DIR / "VeyraProofKernel.lean",
                LEAN_DIR / "VeyraProofSoundness.lean", LEAN_DIR / "VeyraProofResonance.lean",
            ]
            result = _sha(canonical_json({
                "artifact": item.artifact.proof_digest,
                "sources": [_sha(_read(path)) for path in files],
                "toolchain": toolchain,
            }).encode())
        except (OSError, ValueError) as exc:
            logger.error("proof_core_bridge._default_trust_key blocked error=%s", exc)
            result = "blocked:" + str(exc)
    logger.debug("proof_core_bridge._default_trust_key exit result=%s", result)
    return result


@lru_cache(maxsize=8)
def _cached_default_report(trust_key: str) -> ProofCoreBridgeReport:
    logger.debug("proof_core_bridge._cached_default_report entry key=%s", trust_key)
    result = check_proof_core_bridge()
    logger.debug("proof_core_bridge._cached_default_report exit status=%s", result.status)
    return result


def proof_core_bridge_report() -> ProofCoreBridgeReport:
    """Rehash trust inputs every call; cache compilation only by that exact key."""
    logger.debug("proof_core_bridge_report entry")
    result = _cached_default_report(_default_trust_key())
    if result.status == "checked" and not verify_proof_core_bridge_report(result):
        result = _blocked("cached-proof-bridge-integrity-mismatch", result.artifact_digest)
    logger.debug("proof_core_bridge_report exit status=%s", result.status)
    return result
