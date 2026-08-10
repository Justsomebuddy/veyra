"""Fail-closed immutable Lean bridge for the conservative R11 observer core."""
from __future__ import annotations
from functools import lru_cache
from hashlib import sha256
import logging
from pathlib import Path
import re
from types import MappingProxyType
from typing import Mapping
from .observer_core_artifact import verify_observer_proof_artifact
from .observer_core_bridge_io import (
    LEAN_TOOLCHAIN,
    binding_digest,
    compile_snapshot,
    lean_command,
    materialize_snapshot,
    sha_digest,
    snapshot_key,
    toolchain_identity,
)
from .observer_core_bridge_report import (
    ObserverCoreBridgeReport,
    read_exact_regular_source,
    valid_digest_manifest,
    valid_observer_core_bridge_report_shape,
    valid_r10_continuity_report_shape,
    valid_source_origins,
)
from .observer_core_codec import observer_digest
from .observer_core_kernel import crest_observer, infer_observer_proof
from .observer_core_lean_render import (
    CANONICAL_THEOREM_ID,
    canonical_observer_artifact,
    canonical_observer_lean,
    canonical_observer_proof,
)
from .observer_core_manifest import (
    BRIDGE_ID,
    _EXPECTED_R11_TCB_DIGEST_ROWS,
    EXPECTED_R11_TCB_DIGESTS,
    TCB_SCHEMA,
)
from .observer_core_snapshot import _SNAPSHOT_NAME_ROWS, require_valid_snapshot_layout
from .observer_core_support import outcome_data
from .proof_core_codec import canonical_json
from .proof_core_types import ProofContext
from .proof_elaboration_bridge import (
    proof_elaboration_bridge_report,
    verify_proof_elaboration_bridge_report,
)
from .paths import PROJECT_ROOT

logger = logging.getLogger(__name__)
LEAN_DIR = PROJECT_ROOT / "proofs" / "lean"
THEOREM_IDS = tuple(f"THM-R11-{index:03d}" for index in range(1, 7))
PLACEHOLDER = re.compile(r"\b(?:sorryAx|sorry|admit|axiom|unsafe)\b")
SOURCE_PATHS = MappingProxyType({
    "observer_types": PROJECT_ROOT / "src/core/observer_core_types.py",
    "observer_codec": PROJECT_ROOT / "src/core/observer_core_codec.py",
    "observer_semantics": PROJECT_ROOT / "src/core/observer_core_semantics.py",
    "observer_proof_types": PROJECT_ROOT / "src/core/observer_core_proof_types.py",
    "observer_support": PROJECT_ROOT / "src/core/observer_core_support.py",
    "observer_kernel": PROJECT_ROOT / "src/core/observer_core_kernel.py",
    "observer_artifact": PROJECT_ROOT / "src/core/observer_core_artifact.py",
    "lean_renderer": PROJECT_ROOT / "src/core/observer_core_lean_render.py",
    "bridge_snapshot": PROJECT_ROOT / "src/core/observer_core_snapshot.py",
    "reviewed_objects": PROJECT_ROOT / "src/core/observer_core_objects.py",
    "bridge_report": PROJECT_ROOT / "src/core/observer_core_bridge_report.py",
    "bridge_io": PROJECT_ROOT / "src/core/observer_core_bridge_io.py",
    "bridge": PROJECT_ROOT / "src/core/observer_core_bridge.py",
    "certificate": PROJECT_ROOT / "src/core/certify_observer_core.py",
    "certificate_types": PROJECT_ROOT / "src/core/certify_types.py",
    "proof_types": PROJECT_ROOT / "src/core/proof_core_types.py",
    "proof_substitution": PROJECT_ROOT / "src/core/proof_core_substitution.py",
    "proof_kernel": PROJECT_ROOT / "src/core/proof_core_kernel.py",
    "proof_codec": PROJECT_ROOT / "src/core/proof_core_codec.py",
    "proof_artifact_decode": PROJECT_ROOT / "src/core/proof_core_artifact_decode.py",
    "proof_artifact": PROJECT_ROOT / "src/core/proof_core_artifact.py",
    "toolchain_runtime": PROJECT_ROOT / "src/core/proof_elaboration_toolchain.py",
    "runtime_guard": PROJECT_ROOT / "src/core/proof_elaboration_runtime_guard.py",
    "r10_manifest": PROJECT_ROOT / "src/core/proof_elaboration_manifest.py",
    "r10_bridge": PROJECT_ROOT / "src/core/proof_elaboration_bridge.py",
    "lean_arithmetic": LEAN_DIR / "VeyraNativeArithmetic.lean",
    "lean_semantics": LEAN_DIR / "VeyraNativeSemantics.lean",
    "lean_intrinsic_runtime": LEAN_DIR / "VeyraIntrinsicRuntime.lean",
    "lean_kernel": LEAN_DIR / "VeyraProofKernel.lean",
    "lean_soundness": LEAN_DIR / "VeyraProofSoundness.lean",
    "lean_transport": LEAN_DIR / "VeyraRecurrenceModeBridge.lean",
    "lean_observer_core": LEAN_DIR / "VeyraObserverCore.lean",
    "lean_observer_proof": LEAN_DIR / "VeyraObserverProof.lean",
})
CANONICAL_SOURCE_ROWS = tuple(SOURCE_PATHS.items())
STAGES = len(_SNAPSHOT_NAME_ROWS)
CHECKED_DIAGNOSTICS = ";".join(
    f"{index}/{STAGES}:{Path(filename).stem}:rc=0"
    for index, (_, filename) in enumerate(_SNAPSHOT_NAME_ROWS, 1)
)
CHECKED_BOUNDARY = (
    "closed finite recurrence observers and unchanged R7 evidence through the exact "
    "R9 intrinsic image; R10 continuity is independently reverified and this bridge "
    "does not renew or widen the R8 promotion contract; observer_core_manifest.py is "
    "the externally reviewed manual trust root and is not self-bound; OS loader/glibc/ld-cache, "
    "proc/sys inputs, entropy, mount namespace, kernel, ptrace, and root compromise "
    "remain outside the pinned Lean userspace integrity TCB"
)

def _verified_r10():
    logger.debug("observer_core_bridge._verified_r10 entry")
    report = proof_elaboration_bridge_report()
    if (
        not valid_r10_continuity_report_shape(report)
        or report.status != "checked"
        or not verify_proof_elaboration_bridge_report(report)
    ):
        raise ValueError("r11-r10-continuity-rejected")
    logger.debug("observer_core_bridge._verified_r10 exit binding=%s", report.binding_digest)
    return report


def _read_sources(paths: Mapping[str, Path], generated: bytes) -> dict[str, bytes]:
    logger.debug("observer_core_bridge._read_sources entry type=%s", type(paths).__name__)
    require_valid_snapshot_layout()
    trusted = paths is SOURCE_PATHS
    if not trusted and not valid_source_origins(paths, SOURCE_PATHS):
        logger.error("observer_core_bridge._read_sources rejected source authorization")
        raise ValueError("r11-source-path-set-invalid")
    result = {name: read_exact_regular_source(path) for name, path in CANONICAL_SOURCE_ROWS}
    if type(generated) is not bytes:
        logger.error("observer_core_bridge._read_sources rejected generated type=%s", type(generated).__name__)
        raise TypeError("r11-generated-export-not-bytes")
    result["lean_export"] = generated
    logger.debug("observer_core_bridge._read_sources exit count=%d", len(result))
    return result


def _blocked(reason: str) -> ObserverCoreBridgeReport:
    logger.error("observer_core_bridge blocked reason=%s", reason)
    return ObserverCoreBridgeReport(
        "blocked", BRIDGE_ID, (), "", "", "", "", (), "", "", False,
        False, False, False, False, False, LEAN_TOOLCHAIN, reason,
        "no R11 certificate without exact R10 continuity, artifact replay, manifest, snapshot, and Lean",
    )


def _validate(sources: Mapping[str, bytes], generated: bytes, artifact, r10):
    logger.debug("observer_core_bridge._validate entry")
    proof = canonical_observer_proof()
    checked = verify_observer_proof_artifact(artifact, ProofContext(), proof)
    if not checked.ok or artifact != canonical_observer_artifact():
        raise ValueError("r11-observer-artifact-rejected")
    if artifact.theorem_id != CANONICAL_THEOREM_ID:
        raise ValueError("r11-observer-artifact-origin-mismatch")
    if sources["lean_export"] != generated:
        raise ValueError("r11-generated-lean-source-drift")
    lean_bytes = b"\n".join(sources[name] for name, _ in _SNAPSHOT_NAME_ROWS)
    forbidden = tuple(sorted(set(PLACEHOLDER.findall(lean_bytes.decode("utf-8")))))
    if forbidden:
        raise ValueError("r11-forbidden-lean-placeholder:" + ",".join(forbidden))
    for index in range(1, 7):
        symbol = f"THM_R11_{index:03d}".encode()
        if symbol not in sources["lean_observer_proof"] or symbol not in generated:
            raise ValueError("r11-lean-theorem-set-incomplete")
    digests = {name: sha_digest(source) for name, source in sources.items()}
    manifest_names = (*tuple(SOURCE_PATHS), "lean_export")
    if not valid_digest_manifest(EXPECTED_R11_TCB_DIGESTS, manifest_names):
        raise ValueError("r11-manifest-mutable")
    if tuple(digests.items()) != _EXPECTED_R11_TCB_DIGEST_ROWS:
        raise ValueError("r11-reviewed-tcb-drift")
    judgment = infer_observer_proof(ProofContext(), proof)
    result_digest = sha256(canonical_json(outcome_data(judgment.outcome)).encode()).hexdigest()
    logger.debug("observer_core_bridge._validate exit artifact=%s", artifact.proof_digest)
    return digests, observer_digest(crest_observer()), result_digest


def _checked_report(artifact, r10, digests, ast_digest, result_digest, toolchain, diagnostics):
    logger.debug("observer_core_bridge._checked_report entry")
    snapshot = snapshot_key(digests, artifact.proof_digest, r10.binding_digest, toolchain)
    binding = binding_digest(
        TCB_SCHEMA, BRIDGE_ID, THEOREM_IDS, digests, snapshot,
        artifact.proof_digest, r10.binding_digest, toolchain,
    )
    result = ObserverCoreBridgeReport(
        "checked", BRIDGE_ID, THEOREM_IDS, ast_digest, result_digest,
        artifact.proof_digest, r10.binding_digest, tuple(digests.items()),
        snapshot, binding, True, True, True, True, True, True,
        toolchain, diagnostics, CHECKED_BOUNDARY,
    )
    logger.debug("observer_core_bridge._checked_report exit binding=%s", binding)
    return result


def check_observer_core_bridge(
    source_paths: Mapping[str, Path] | None = None,
    generated_export: bytes | None = None,
) -> ObserverCoreBridgeReport:
    """Verify snapshot trust root, then R10/R11, pins, snapshot, and fresh Lean."""
    logger.debug("check_observer_core_bridge entry custom=%s", source_paths is not None)
    try:
        require_valid_snapshot_layout()
        r10 = _verified_r10()
        artifact = canonical_observer_artifact()
        generated = canonical_observer_lean(artifact, r10.binding_digest)
        if generated_export is not None:
            generated = generated_export
        sources = _read_sources(SOURCE_PATHS if source_paths is None else source_paths, generated)
        expected = canonical_observer_lean(artifact, r10.binding_digest)
        digests, ast_digest, result_digest = _validate(sources, expected, artifact, r10)
        command = lean_command()
        if not command:
            raise ValueError("r11-pinned-lean-not-found")
        toolchain = toolchain_identity(command)
        snapshot = materialize_snapshot(
            sources, digests, artifact.proof_digest, r10.binding_digest, toolchain,
        )
        lean_checked, diagnostics = compile_snapshot(command, snapshot, sources)
        if not lean_checked:
            raise ValueError(diagnostics)
    except (OSError, TypeError, UnicodeDecodeError, ValueError) as exc:
        return _blocked(str(exc))
    result = _checked_report(
        artifact, r10, digests, ast_digest, result_digest, toolchain, diagnostics,
    )
    logger.debug("check_observer_core_bridge exit binding=%s", result.binding_digest)
    return result


def verify_observer_core_bridge_report(report: object) -> bool:
    """Independently rehash, reverify R10/cache evidence, and fresh-compile Lean."""
    logger.debug("verify_observer_core_bridge_report entry type=%s", type(report).__name__)
    if not valid_observer_core_bridge_report_shape(report) or report.status != "checked":
        return False
    try:
        require_valid_snapshot_layout()
        r10 = _verified_r10()
        artifact = canonical_observer_artifact()
        generated = canonical_observer_lean(artifact, r10.binding_digest)
        sources = _read_sources(SOURCE_PATHS, generated)
        digests, ast_digest, result_digest = _validate(sources, generated, artifact, r10)
        command = lean_command()
        if not command:
            return False
        toolchain = toolchain_identity(command)
        snapshot = materialize_snapshot(
            sources, digests, artifact.proof_digest, r10.binding_digest, toolchain,
        )
        expected = _checked_report(
            artifact, r10, digests, ast_digest, result_digest,
            toolchain, CHECKED_DIAGNOSTICS,
        )
        if report != expected:
            return False
        lean_checked, diagnostics = compile_snapshot(command, snapshot, sources)
    except (OSError, TypeError, UnicodeDecodeError, ValueError):
        logger.exception("verify_observer_core_bridge_report trust failure")
        return False
    result = lean_checked and diagnostics == CHECKED_DIAGNOSTICS
    logger.debug("verify_observer_core_bridge_report exit result=%s", result)
    return result


def _default_trust_key() -> str:
    logger.debug("observer_core_bridge._default_trust_key entry")
    try:
        require_valid_snapshot_layout()
        r10 = _verified_r10()
        artifact = canonical_observer_artifact()
        generated = canonical_observer_lean(artifact, r10.binding_digest)
        sources = _read_sources(SOURCE_PATHS, generated)
        command = lean_command()
        if not command:
            raise ValueError("r11-pinned-lean-not-found")
        toolchain = toolchain_identity(command)
        digests = {name: sha_digest(source) for name, source in sources.items()}
        result = snapshot_key(digests, artifact.proof_digest, r10.binding_digest, toolchain)
    except (OSError, TypeError, ValueError) as exc:
        result = "blocked:" + str(exc)
    logger.debug("observer_core_bridge._default_trust_key exit result=%s", result)
    return result


@lru_cache(maxsize=8)
def _cached_default_report(trust_key: str) -> ObserverCoreBridgeReport:
    logger.debug("observer_core_bridge._cached_default_report entry key=%s", trust_key)
    result = check_observer_core_bridge()
    logger.debug("observer_core_bridge._cached_default_report exit status=%s", result.status)
    return result


def observer_core_bridge_report() -> ObserverCoreBridgeReport:
    """Rehash live inputs; cache compilation only by the exact continuity key."""
    logger.debug("observer_core_bridge_report entry")
    result = _cached_default_report(_default_trust_key())
    if not valid_observer_core_bridge_report_shape(result):
        result = _blocked("cached-r11-bridge-shape-mismatch")
    elif result.status == "checked" and not verify_observer_core_bridge_report(result):
        result = _blocked("cached-r11-bridge-integrity-mismatch")
    logger.debug("observer_core_bridge_report exit status=%s", result.status)
    return result
