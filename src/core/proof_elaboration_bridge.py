"""Fail-closed immutable bridge for source-replayed R10 proof elaboration."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import logging
from pathlib import Path
import re
from types import MappingProxyType
from typing import Mapping

from .intrinsic_mode_bridge import (
    intrinsic_mode_bridge_report, verify_intrinsic_mode_bridge_report,
)
from .proof_elaboration_bridge_io import (
    LEAN_TOOLCHAIN, binding_digest, compile_snapshot, lean_command,
    materialize_snapshot, sha_digest, snapshot_key, toolchain_identity,
)
from .proof_elaboration_artifact import verify_elaboration_artifact
from .proof_elaboration_canonical import (
    CANONICAL_SOURCE, THEOREM_ID, canonical_elaboration,
    canonical_elaboration_lean,
)
from .proof_elaboration_manifest import EXPECTED_R10_TCB_DIGESTS, TCB_SCHEMA
from .proof_elaboration_snapshot import SNAPSHOT_NAMES
from .proof_surface_codec import surface_program_data

from .paths import PROJECT_ROOT

logger = logging.getLogger(__name__)
LEAN_DIR = PROJECT_ROOT / "proofs" / "lean"
THEOREM_IDS = tuple(f"THM-R10-{index:03d}" for index in range(1, 6))
PLACEHOLDER = re.compile(r"\b(?:sorryAx|sorry|admit|axiom|unsafe)\b")
SOURCE_PATHS = MappingProxyType({
    "canonical": PROJECT_ROOT / "src/core/proof_elaboration_canonical.py",
    "surface_types": PROJECT_ROOT / "src/core/proof_surface_types.py",
    "surface_trace": PROJECT_ROOT / "src/core/proof_surface_trace.py",
    "surface_sexpr": PROJECT_ROOT / "src/core/proof_surface_sexpr.py",
    "surface_parser": PROJECT_ROOT / "src/core/proof_surface_parser.py",
    "surface_codec": PROJECT_ROOT / "src/core/proof_surface_codec.py",
    "surface_elaborator": PROJECT_ROOT / "src/core/proof_surface_elaborator.py",
    "surface_lowering": PROJECT_ROOT / "src/core/proof_surface_lowering.py",
    "surface_validation": PROJECT_ROOT / "src/core/proof_surface_validation.py",
    "dependency_support": PROJECT_ROOT / "src/core/proof_dependency_support.py",
    "elaboration_artifact": PROJECT_ROOT / "src/core/proof_elaboration_artifact.py",
    "lean_renderer": PROJECT_ROOT / "src/core/proof_elaboration_lean_render.py",
    "bridge_snapshot": PROJECT_ROOT / "src/core/proof_elaboration_snapshot.py",
    "bridge_io": PROJECT_ROOT / "src/core/proof_elaboration_bridge_io.py",
    "toolchain_runtime": PROJECT_ROOT / "src/core/proof_elaboration_toolchain.py",
    "runtime_guard": PROJECT_ROOT / "src/core/proof_elaboration_runtime_guard.py",
    "reviewed_objects": PROJECT_ROOT / "src/core/proof_elaboration_objects.py",
    "bridge": PROJECT_ROOT / "src/core/proof_elaboration_bridge.py",
    "certificate": PROJECT_ROOT / "src/core/certify_proof_elaboration.py",
    "proof_types": PROJECT_ROOT / "src/core/proof_core_types.py",
    "proof_substitution": PROJECT_ROOT / "src/core/proof_core_substitution.py",
    "proof_kernel": PROJECT_ROOT / "src/core/proof_core_kernel.py",
    "proof_codec": PROJECT_ROOT / "src/core/proof_core_codec.py",
    "proof_artifact": PROJECT_ROOT / "src/core/proof_core_artifact.py",
    "proof_artifact_decode": PROJECT_ROOT / "src/core/proof_core_artifact_decode.py",
    "proof_lean_renderer": PROJECT_ROOT / "src/core/proof_core_lean_render.py",
    "proof_resonance": PROJECT_ROOT / "src/core/proof_core_resonance.py",
    "lean_arithmetic": LEAN_DIR / "VeyraNativeArithmetic.lean",
    "lean_semantics": LEAN_DIR / "VeyraNativeSemantics.lean",
    "lean_intrinsic_runtime": LEAN_DIR / "VeyraIntrinsicRuntime.lean",
    "lean_kernel": LEAN_DIR / "VeyraProofKernel.lean",
    "lean_soundness": LEAN_DIR / "VeyraProofSoundness.lean",
    "lean_r7_export": LEAN_DIR / "VeyraProofResonance.lean",
    "lean_transport": LEAN_DIR / "VeyraRecurrenceModeBridge.lean",
    "lean_r9_export": LEAN_DIR / "VeyraProofModeTransport.lean",
    "lean_elaboration": LEAN_DIR / "VeyraElaborationSemantics.lean",
    "lean_export": LEAN_DIR / "VeyraProofElaboration.lean",
})
STAGES = len(SNAPSHOT_NAMES)
CHECKED_DIAGNOSTICS = ";".join(
    f"{index}/{STAGES}:{Path(filename).stem}:rc=0"
    for index, filename in enumerate(SNAPSHOT_NAMES.values(), 1)
)
CHECKED_BOUNDARY = (
    "closed recurrence surface proofs through exact R7 checking and the fixed-anchor "
    "R9 intrinsic image only; parser correctness remains reviewed source TCB; "
    "OS loader/glibc/ld-cache, proc/sys inputs, entropy, mount namespace, kernel, "
    "ptrace, and root compromise are outside the pinned Lean userspace integrity TCB"
)


@dataclass(frozen=True)
class ProofElaborationBridgeReport:
    """Exact origin, snapshot, toolchain, and Lean evidence for R10."""

    status: str
    theorem_ids: tuple[str, ...]
    elaboration_binding_digest: str
    surface_syntax_digest: str
    semantic_digest: str
    r7_artifact_digest: str
    r9_binding_digest: str
    source_digests: tuple[tuple[str, str], ...]
    snapshot_digest: str
    binding_digest: str
    artifact_checked: bool
    manifest_checked: bool
    source_bound: bool
    snapshot_checked: bool
    lean_checked: bool
    toolchain: str
    diagnostics: str
    boundary: str


def _read_sources(paths: Mapping[str, Path]) -> dict[str, bytes]:
    logger.debug("proof_elaboration_bridge._read_sources entry count=%d", len(paths))
    if tuple(paths) != tuple(SOURCE_PATHS):
        logger.error("proof_elaboration_bridge invalid source path set")
        raise ValueError("r10-source-path-set-invalid")
    try:
        result = {name: Path(path).read_bytes() for name, path in paths.items()}
    except OSError as exc:
        logger.error("proof_elaboration_bridge unreadable source error=%s", exc)
        raise ValueError("r10-source-unreadable") from exc
    logger.debug("proof_elaboration_bridge._read_sources exit")
    return result


def _blocked(reason: str) -> ProofElaborationBridgeReport:
    logger.error("proof_elaboration_bridge blocked reason=%s", reason)
    return ProofElaborationBridgeReport(
        "blocked", (), "", "", "", "", "", (), "", "", False,
        False, False, False, False, LEAN_TOOLCHAIN, reason,
        "no R10 certificate without exact source replay, reviewed hashes, snapshot, and pinned Lean",
    )


def _validate(sources: Mapping[str, bytes]):
    logger.debug("proof_elaboration_bridge._validate entry")
    artifact, elaborated = canonical_elaboration()
    checked = verify_elaboration_artifact(
        artifact, CANONICAL_SOURCE, surface_program_data(elaborated.surface),
        elaborated.claim, elaborated.proof,
    )
    r9 = intrinsic_mode_bridge_report()
    if not checked.ok or not verify_intrinsic_mode_bridge_report(r9):
        raise ValueError("r10-prerequisite-evidence-rejected")
    if artifact.theorem_id != THEOREM_ID or artifact.r9_binding_digest != r9.binding_digest:
        raise ValueError("r10-artifact-origin-mismatch")
    if sources["lean_export"] != canonical_elaboration_lean():
        raise ValueError("r10-generated-lean-source-drift")
    lean_bytes = b"\n".join(sources[name] for name in SNAPSHOT_NAMES)
    forbidden = tuple(sorted(set(PLACEHOLDER.findall(lean_bytes.decode("utf-8")))))
    if forbidden:
        raise ValueError("r10-forbidden-lean-placeholder:" + ",".join(forbidden))
    digests = {name: sha_digest(source) for name, source in sources.items()}
    if digests != EXPECTED_R10_TCB_DIGESTS:
        raise ValueError("r10-reviewed-tcb-drift")
    logger.debug("proof_elaboration_bridge._validate exit binding=%s", artifact.binding_digest)
    return artifact, r9, digests


def _checked_report(artifact, r9, digests, toolchain, diagnostics):
    logger.debug("proof_elaboration_bridge._checked_report entry")
    snapshot = snapshot_key(
        digests, artifact.binding_digest, r9.binding_digest, toolchain,
    )
    binding = binding_digest(
        TCB_SCHEMA, THEOREM_IDS, digests, snapshot,
        artifact.binding_digest, r9.binding_digest, toolchain,
    )
    result = ProofElaborationBridgeReport(
        "checked", THEOREM_IDS, artifact.binding_digest,
        artifact.surface_syntax_digest, artifact.semantic_digest,
        artifact.r7_artifact_digest, r9.binding_digest, tuple(digests.items()),
        snapshot, binding, True, True, True, True, True, toolchain,
        diagnostics, CHECKED_BOUNDARY,
    )
    logger.debug("proof_elaboration_bridge._checked_report exit binding=%s", binding)
    return result


def check_proof_elaboration_bridge(
    source_paths: Mapping[str, Path] | None = None,
) -> ProofElaborationBridgeReport:
    """Replay source, enforce reviewed hashes, snapshot once, and compile Lean."""
    logger.debug("check_proof_elaboration_bridge entry custom=%s", source_paths is not None)
    try:
        sources = _read_sources(SOURCE_PATHS if source_paths is None else source_paths)
        artifact, r9, digests = _validate(sources)
        command = lean_command()
        if not command:
            raise ValueError("r10-pinned-elan-not-found")
        toolchain = toolchain_identity(command)
        snapshot = materialize_snapshot(
            sources, digests, artifact.binding_digest, r9.binding_digest, toolchain,
        )
        lean_checked, diagnostics = compile_snapshot(command, snapshot, sources)
        if not lean_checked:
            raise ValueError(diagnostics)
    except (OSError, TypeError, UnicodeDecodeError, ValueError) as exc:
        return _blocked(str(exc))
    result = _checked_report(artifact, r9, digests, toolchain, diagnostics)
    logger.debug("check_proof_elaboration_bridge exit binding=%s", result.binding_digest)
    return result


def verify_proof_elaboration_bridge_report(report: object) -> bool:
    """Independently rehash origins and reverify the immutable snapshot and cache report."""
    logger.debug("verify_proof_elaboration_bridge_report entry type=%s", type(report).__name__)
    if type(report) is not ProofElaborationBridgeReport or report.status != "checked":
        logger.error("verify_proof_elaboration_bridge_report rejected shape/status")
        return False
    try:
        sources = _read_sources(SOURCE_PATHS)
        artifact, r9, digests = _validate(sources)
        command = lean_command()
        if not command:
            return False
        toolchain = toolchain_identity(command)
        snapshot = materialize_snapshot(
            sources, digests, artifact.binding_digest, r9.binding_digest, toolchain,
        )
        expected = _checked_report(
            artifact, r9, digests, toolchain, CHECKED_DIAGNOSTICS,
        )
        if report != expected:
            logger.error("verify_proof_elaboration_bridge_report exact mismatch")
            return False
        lean_checked, diagnostics = compile_snapshot(command, snapshot, sources)
        if not lean_checked or diagnostics != CHECKED_DIAGNOSTICS:
            logger.error("verify_proof_elaboration_bridge_report Lean replay failed")
            return False
    except (OSError, TypeError, UnicodeDecodeError, ValueError):
        logger.exception("verify_proof_elaboration_bridge_report trust failure")
        return False
    result = diagnostics == expected.diagnostics
    logger.debug("verify_proof_elaboration_bridge_report exit result=%s", result)
    return result


def _default_trust_key() -> str:
    logger.debug("proof_elaboration_bridge._default_trust_key entry")
    try:
        sources = _read_sources(SOURCE_PATHS)
        artifact, _ = canonical_elaboration()
        r9 = intrinsic_mode_bridge_report()
        command = lean_command()
        if not command or not verify_intrinsic_mode_bridge_report(r9):
            raise ValueError("r10-prerequisite-evidence-rejected")
        toolchain = toolchain_identity(command)
        digests = {name: sha_digest(source) for name, source in sources.items()}
        result = snapshot_key(
            digests, artifact.binding_digest, r9.binding_digest, toolchain,
        )
    except (OSError, TypeError, ValueError) as exc:
        logger.error("proof_elaboration_bridge._default_trust_key blocked=%s", exc)
        result = "blocked:" + str(exc)
    logger.debug("proof_elaboration_bridge._default_trust_key exit result=%s", result)
    return result


@lru_cache(maxsize=8)
def _cached_default_report(trust_key: str) -> ProofElaborationBridgeReport:
    logger.debug("proof_elaboration_bridge._cached_default_report entry key=%s", trust_key)
    result = check_proof_elaboration_bridge()
    logger.debug("proof_elaboration_bridge._cached_default_report exit status=%s", result.status)
    return result


def proof_elaboration_bridge_report() -> ProofElaborationBridgeReport:
    """Rehash live inputs each call; cache compilation only by their exact key."""
    logger.debug("proof_elaboration_bridge_report entry")
    result = _cached_default_report(_default_trust_key())
    if result.status == "checked" and not verify_proof_elaboration_bridge_report(result):
        result = _blocked("cached-r10-bridge-integrity-mismatch")
    logger.debug("proof_elaboration_bridge_report exit status=%s", result.status)
    return result
